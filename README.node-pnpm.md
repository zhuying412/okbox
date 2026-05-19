# Node / pnpm 安全适配说明

本模板适用于 JS / TS / Tauri / Node.js 项目。

初始化后请执行：

```bash
corepack enable
pnpm install --lockfile-only
```

要求：

- 不允许混用 npm / yarn / bun。
- 必须提交 `pnpm-lock.yaml`。
- 新增依赖必须走 Issue + PR。
- 需要运行 build script 的依赖必须人工审核。
- 不允许 AI 自动执行 `pnpm approve-builds`。
