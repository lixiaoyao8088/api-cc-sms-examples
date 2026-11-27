# API.CC 合规短信验证码（OTP）测试与轮询模板示例

本仓库提供面向开发者与 QA 测试工程师的 **合规 OTP 短信验证测试工程模板**（Python / Node.js），重点解决自动化测试中最常见的三类工程问题：

1. **先人工基线，再程序联调**：防止未确认国家/项目归属就直接批量跑脚本；
2. **把“接口请求响应”与“实际短信接收记录”分开判断**：避免将网络超时或轮询窗口偏差误判为号码无码；
3. **日志严格脱敏与安全重试**：内置指数退避、最大等待上限与敏感字段脱敏（不打印完整手机号、验证码、Token 或原始短信全文）。

> **重要边界声明**
> - 本仓库中的示例请求地址、查询参数与响应解析结构为**通用脱敏工程模板**，**不代表任何固定字段或未核验接口承诺**；正式接入前请务必核对 [API.CC 当前官方 API 文档说明](https://apismsapp.com/api-docs/) 与后台实时接口文档。
> - 本示例仅用于合规产品测试、开发调试、OTP 到达率验证与跨境本地化测试，严禁用于欺诈、批量垃圾注册或绕过平台规则。

---

## 目录结构

```text
github-api-cc-examples/
├── README.md
├── python/
│   └── otp_poll_template.py      # Python 3 标准库实现（零第三方依赖）
└── node/
    └── otp_poll_template.mjs     # Node.js 18+ 原生 fetch 实现
```

---

## 接入前 3 步最小核对（强烈建议）

1. **先用 1 个号码完成人工收码测试**：确认国家（尤其注意美国与加拿大共用 `+1`）、卡类型（虚拟卡 vs 实体 SIM）和目标项目名称无误，且后台「接码记录」能查到当次短信。
2. **配置环境变量，绝不把 Token 写进代码或日志**：
   ```bash
   export SMS_POLL_URL="请替换为当前正式文档确认的只读查询端点"
   export SMS_POLL_TOKEN="请替换为后台分配的脱敏测试凭证"
   ```
3. **运行单样本受控轮询**：默认 5 秒间隔、最多等待 90 秒即停止并输出三类独立状态（`http_error` / `timeout_no_record` / `record_detected`），避免死循环高频刷接口。

---

## 快速运行

### Python 3（无需安装额外依赖）
```bash
python3 python/otp_poll_template.py --sample-id test-us-001 --timeout 90 --interval 5
```

### Node.js 18+
```bash
node node/otp_poll_template.mjs --sample-id test-us-001 --timeout 90 --interval 5
```

---

## 相关公开技术文档

- [短信接码平台怎么选：独占机制、有效期与 API 能力 5 项标准](https://apismsapp.com/blog/how-to-choose-sms-verification-platform/)
- [API.CC API 文档接入与排查边界说明](https://apismsapp.com/api-docs/)
- [美国接码自测指南与三行定位排查表](https://apismsapp.com/tutorials/us-sms-tutorial/)
- [API.CC 官网入口](https://www.api.cc)
