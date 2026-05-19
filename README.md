# okbox

## 项目简介

okbox 是一个多语言项目，使用 Node.js (pnpm) 和 Python (uv) 技术栈。

本仓库从第一天起即遵循 AI 原生安全基线，防范 AI 误操作、提示注入、供应链投毒、CI/CD 权限滥用和敏感信息泄露。

## 技术栈

- **Node.js / TypeScript** — pnpm 包管理器，供应链安全策略已启用
- **Python** — uv 包管理器，依赖冷却期已配置
- **CI/CD** — GitHub Actions，最小权限原则
- **安全扫描** — gitleaks 密钥扫描、依赖审计
- **依赖更新** — Renovate，7 天冷却期

## 本地开发

### 前置条件

- Node.js >= 22.0.0
- pnpm >= 10.21.0（通过 corepack 启用）
- Python >= 3.12
- uv（Python 包管理器）
- gitleaks（密钥扫描）

### 初始化

```bash
# 启用 Git hooks
bash scripts/setup-hooks.sh
# Windows:
# ./scripts/setup-hooks.ps1

# Node.js 依赖
corepack enable
pnpm install --frozen-lockfile

# Python 依赖
uv sync --locked
```

## 配置说明

所有配置通过环境变量注入。参考 `.env.example` 了解可配置项。

禁止将真实密钥、token、密码提交到仓库。

## 常用命令

### Node.js

```bash
pnpm run lint          # 代码检查
pnpm run typecheck     # 类型检查
pnpm run test          # 运行测试
pnpm run build         # 构建
pnpm audit             # 依赖漏洞扫描
```

### Python

```bash
uv run ruff check .    # 代码检查
uv run pytest          # 运行测试
uv run pip-audit       # 依赖漏洞扫描
```

## 测试方式

- Node.js：通过 `pnpm run test` 执行
- Python：通过 `uv run pytest` 执行
- CI 中测试失败会阻断合并

## 构建方式

- Node.js：通过 `pnpm run build` 执行
- Python：按项目需要配置
- 生产构建禁止开启 devtools、debug 端口、mock 登录

## 安全说明

- 所有安全规则见 `AGENTS.md` 和 `SECURITY.md`
- AI Agent 规则见 `AGENTS.md`、`CLAUDE.md`、`CODEX.md`
- 依赖策略见 `docs/DEPENDENCY_POLICY.md`
- CI 安全策略见 `docs/CI_SECURITY_POLICY.md`
- 日志脱敏策略见 `docs/LOGGING_POLICY.md`
- 密钥泄露处理见 `SECURITY.md`

## 分支与提交规范

- 分支格式：`feat/issue-12-add-login`
- 提交格式：Conventional Commits + Issue 引用
- 详见 `CONTRIBUTING.md`

## 许可证

MIT License
