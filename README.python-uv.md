# Python / uv 安全适配说明

初始化后请执行：

```bash
uv lock
uv sync --locked
```

要求：

- 必须提交 `uv.lock`。
- 不允许直接 `pip install xxx` 绕过锁文件。
- 新增依赖必须走 Issue + PR。
- 新增依赖前必须说明用途、维护状态、替代方案和安全风险。
