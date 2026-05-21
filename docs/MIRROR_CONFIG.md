# 国内镜像源配置说明

本项目已配置国内镜像源以加速依赖下载。以下是各组件的配置说明。

## 当前已配置

### Python (pip/uv)

- **镜像源**：清华大学 PyPI 镜像 `https://pypi.tuna.tsinghua.edu.cn/simple`
- **配置位置**：
  - `packages/backend/pyproject.toml` → `[tool.uv]` 段
  - `packages/backend/Dockerfile` → `UV_INDEX_URL` 环境变量

### npm/pnpm

- **镜像源**：npmmirror `https://registry.npmmirror.com`
- **配置位置**：
  - `.npmrc` → `registry` 字段
  - `packages/frontend/Dockerfile` → `npm config set registry`

### apt (Debian/Ubuntu)

- **镜像源**：阿里云 `mirrors.aliyun.com`
- **配置位置**：
  - `packages/backend/Dockerfile` → sed 替换源

## Docker 镜像加速

Docker 基础镜像加速需要在 **宿主机** 配置 Docker daemon：

```bash
# 编辑 Docker daemon 配置
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
```

## 切换回默认源（海外部署）

如果在海外环境部署，需要切换回默认源：

### Python
注释或删除 `packages/backend/pyproject.toml` 中的 `[tool.uv]` 段：
```toml
# [tool.uv]
# index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

并删除 `packages/backend/Dockerfile` 中的 `UV_INDEX_URL` 环境变量行。

### npm/pnpm
删除 `.npmrc` 中的 `registry` 行：
```ini
# registry=https://registry.npmmirror.com
```

### apt
删除 `Dockerfile` 中的 sed 替换行。

### Docker
清空或删除 `/etc/docker/daemon.json` 中的 `registry-mirrors` 配置。

## 备选镜像源

| 组件 | 备选源 |
|------|--------|
| Python | 阿里源 `https://mirrors.aliyun.com/pypi/simple` |
| apt | 清华源 `https://mirrors.tuna.tsinghua.edu.cn/debian` |
| npm | 华为源 `https://repo.huaweicloud.com/repository/npm/` |
| Docker | 华为 `https://mirrors.huaweicloud.com` |
