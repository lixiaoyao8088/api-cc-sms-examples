#!/usr/bin/env node
/**
 * 合规短信验证码（OTP）受控轮询与脱敏日志模板（Node.js 18+ 原生 fetch）。
 *
 * 注意：
 * - 请按 API.CC 当前正式文档配置 SMS_POLL_URL、鉴权方式与响应字段解析；
 * - 日志严格脱敏，绝不输出明文验证码、原始短信全文、完整手机号或完整 Token。
 */

const args = process.argv.slice(2);
function getArg(flag, fallback) {
  const i = args.indexOf(flag);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
}

const sampleId = getArg("--sample-id", "sample-001");
const timeoutSec = Math.max(10, Number(getArg("--timeout", "90")));
const intervalSec = Math.max(3, Number(getArg("--interval", "5")));
const endpoint = (process.env.SMS_POLL_URL || "").trim();
const token = (process.env.SMS_POLL_TOKEN || "").trim();

const maskSecret = (v) => (!v || v.length <= 6 ? "***" : `${v.slice(0, 2)}***${v.slice(-2)}`);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function pollOnce() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10_000);
  try {
    const headers = { Accept: "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(endpoint, { method: "GET", headers, signal: controller.signal });
    if (!res.ok) return { kind: "http_error", httpCode: res.status, hasRecord: false };
    let payload = null;
    try {
      payload = await res.json();
    } catch {
      return { kind: "non_json_response", httpCode: res.status, hasRecord: false };
    }
    const hasRecord = Boolean(payload && (payload.has_record || (Array.isArray(payload.records) && payload.records.length > 0)));
    return { kind: "ok", httpCode: res.status, hasRecord };
  } catch {
    return { kind: "network_timeout", httpCode: null, hasRecord: false };
  } finally {
    clearTimeout(timer);
  }
}

async function main() {
  if (!endpoint) {
    console.log(JSON.stringify({
      ts: new Date().toISOString(),
      sample_id: sampleId,
      status: "config_missing",
      hint: "请先按当前正式 API 文档设置环境变量 SMS_POLL_URL 与 SMS_POLL_TOKEN",
    }));
    process.exit(2);
  }

  const deadline = Date.now() + timeoutSec * 1000;
  let attempt = 0;

  while (Date.now() < deadline) {
    attempt += 1;
    const { kind, httpCode, hasRecord } = await pollOnce();
    console.log(JSON.stringify({
      ts: new Date().toISOString(),
      sample_id: sampleId,
      attempt,
      token_masked: maskSecret(token),
      transport_status: kind,
      http_code: httpCode,
      record_detected: hasRecord,
    }));

    if (hasRecord) process.exit(0);
    if (kind === "http_error" && [401, 403, 404].includes(httpCode)) process.exit(1);
    await sleep(intervalSec * 1000);
  }

  console.log(JSON.stringify({
    ts: new Date().toISOString(),
    sample_id: sampleId,
    status: "timeout_no_record",
    attempts: attempt,
    next_step: "请分开核对发信端记录与后台接码记录，切勿死循环重试",
  }));
  process.exit(1);
}

main();
