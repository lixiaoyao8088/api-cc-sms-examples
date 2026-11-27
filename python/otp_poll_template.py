#!/usr/bin/env python3
"""
合规短信验证码（OTP）受控轮询与脱敏日志模板（Python 3 标准库，零外部依赖）。

使用前须知：
1. 本脚本仅演示轮询间隔、超时停止与日志脱敏结构，接口 URL、请求头及响应结构
   请一律以 API.CC 当前正式后台文档为准，切勿凭旧示例猜字段。
2. 严禁在标准输出或日志文件中打印完整手机号、明文验证码、原始短信全文或完整 Token。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional, Tuple


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mask_secret(value: str) -> str:
    if not value or len(value) <= 6:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


def poll_once(endpoint: str, token: str, timeout_sec: int = 10) -> Tuple[str, Optional[int], bool]:
    """
    发起单次只读查询，返回 (状态分类, HTTP状态码, 是否检测到脱敏记录)。
    请按当前正式文档替换鉴权头与响应判定逻辑。
    """
    headers = {
        "Accept": "application/json",
        "User-Agent": "otp-compliant-test-client/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(endpoint, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", "replace")
            # 仅检查结构化响应是否包含非空记录，不打印短信原文或验证码
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return ("non_json_response", status, False)
            has_record = bool(
                isinstance(payload, dict)
                and (payload.get("has_record") or payload.get("records"))
            )
            return ("ok", status, has_record)
    except urllib.error.HTTPError as exc:
        return ("http_error", exc.code, False)
    except (urllib.error.URLError, TimeoutError):
        return ("network_timeout", None, False)


def main() -> int:
    parser = argparse.ArgumentParser(description="受控 OTP 轮询与脱敏日志模板")
    parser.add_argument("--sample-id", required=True, help="不含号码/账号的内部脱敏样本编号")
    parser.add_argument("--timeout", type=int, default=90, help="最大总等待秒数（默认 90）")
    parser.add_argument("--interval", type=int, default=5, help="最小轮询间隔秒数（建议 >= 5）")
    args = parser.parse_args()

    endpoint = os.environ.get("SMS_POLL_URL", "").strip()
    token = os.environ.get("SMS_POLL_TOKEN", "").strip()
    if not endpoint:
        print(
            json.dumps(
                {
                    "ts": now_iso(),
                    "sample_id": args.sample_id,
                    "status": "config_missing",
                    "hint": "请先按当前正式 API 文档设置环境变量 SMS_POLL_URL 与 SMS_POLL_TOKEN",
                },
                ensure_ascii=False,
            )
        )
        return 2

    interval = max(3, args.interval)
    deadline = time.monotonic() + max(10, args.timeout)
    attempt = 0

    while time.monotonic() < deadline:
        attempt += 1
        kind, http_code, has_record = poll_once(endpoint, token)
        log_entry = {
            "ts": now_iso(),
            "sample_id": args.sample_id,
            "attempt": attempt,
            "token_masked": mask_secret(token),
            "transport_status": kind,
            "http_code": http_code,
            "record_detected": has_record,
        }
        print(json.dumps(log_entry, ensure_ascii=False))

        if has_record:
            return 0
        if kind == "http_error" and http_code in (401, 403, 404):
            # 鉴权或端点错误立即停止，禁止死循环重试
            return 1
        time.sleep(interval)

    print(
        json.dumps(
            {
                "ts": now_iso(),
                "sample_id": args.sample_id,
                "status": "timeout_no_record",
                "attempts": attempt,
                "next_step": "请分开核对目标应用发信记录与后台接码记录，再决定是否单次复测",
            },
            ensure_ascii=False,
        )
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
