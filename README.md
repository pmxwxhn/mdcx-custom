# mdcx-custom

把 MDCx 上游 **220260517** 版本的源码，加上「色花堂中文标题」功能后重新编译，
产出可直接在飞牛 NAS 等 Docker 环境运行的镜像。

## 为什么需要这个仓库

MDCx 从 `220260511` 起删掉了「使用色花标题 / 使用色花中文标题」两个开关和查表逻辑
（`resources/c_number/c_number.json` 数据文件本身仍在，只是没人读了）。
此仓库把这段逻辑补回去，其余代码保持与上游一致。

## 产物

```
ghcr.io/<你的用户名>/mdcx-custom:220260517-sehua
```

## 补丁内容（`patches/apply.py`）

| 文件 | 改动 |
|---|---|
| `mdcx/config/models.py` | 加回 `title_sehua` / `title_sehua_zh` 两个配置项（默认 True） |
| `mdcx/config/v1.py` | 旧版 `config.ini` 迁移时不丢这三个字段 |
| `mdcx/config/resources.py` | 启动时载入 `resources/c_number/c_number.json`，并提供 `get_sehua_title()`（大小写/分隔符容错） |
| `mdcx/core/translate.py` | 刮削后先查色花表，命中就覆盖标题并跳过翻译 |

补丁使用**锚点精确替换**：上游代码一旦变化导致锚点对不上，CI 会直接失败，
不会产出"静默错位"的二进制。

## 使用

```yaml
services:
  mdcx:
    image: ghcr.io/<你的用户名>/mdcx-custom:220260517-sehua
    container_name: mdcx
    ports:
      - "5800:5800"
    volumes:
      - ./mdcx-config:/mdcx-config
      - ./logs:/app/log
      - /path/to/media:/data
    restart: unless-stopped
```

配置文件名与上游一致：`220260517` 使用 `/mdcx-config/config.v2.json`。

## 升级上游

改 `.github/workflows/build.yml` 里的 `UPSTREAM_TAG` 以及 `Dockerfile` 最后一行的基础镜像 tag，
再跑一次 workflow。如果上游改了相关代码，补丁会在校验步骤失败，届时按新代码调整 `apply.py`。

## 许可

上游 MDCx 为 GPL-3.0，本仓库对其源码的修改同样遵循 GPL-3.0。
`resources/c_number/c_number.json` 数据来自上游仓库，未做改动。
