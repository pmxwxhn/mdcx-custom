# syntax=docker/dockerfile:1.4
# ---------------------------------------------------------------
# MDCx 定制版：上游 220260517 + 色花中文标题
#   1) 用官方构建镜像把源码编译成单一二进制（与官方发布链路一致）
#   2) 把二进制替换进官方运行镜像，noVNC / gui-base 全部沿用
# ---------------------------------------------------------------

FROM stainless403/build-mdcx-base:v2-latest-pyqt6 AS builder

COPY src /tmp/mdcx
WORKDIR /tmp/mdcx

# 安装依赖（与官方 build-mdcx/Dockerfile.build-mdcx 完全一致）
RUN uv sync --all-extras --dev && \
    uv pip install -e .

# 编译（参数照抄官方，唯一区别是源码已打上色花标题补丁）
RUN mkdir -p ./dist && echo "custom-sehua" > ./dist/app-version && \
    uv run pyinstaller -n MDCx \
      -F -w main.py \
      --add-data "resources:resources" \
      --add-data "libs:." \
      --hidden-import socks \
      --hidden-import urllib3 \
      --hidden-import _cffi_backend \
      --hidden-import PIL \
      --hidden-import PIL.Image \
      --hidden-import PIL.ImageFile \
      --hidden-import PIL.ImageFilter \
      --hidden-import PIL._imaging \
      --hidden-import PyQt6 \
      --collect-all PyQt6 \
      --collect-all curl_cffi && \
    rm -rf /tmp/mdcx/build /tmp/mdcx/__pycache__ /root/.cache

# 运行镜像：沿用官方 220260517，只替换主程序
FROM stainless403/mdcx-builtin-gui-base:v2-220260517

COPY --from=builder --chmod=+x /tmp/mdcx/dist/MDCx /app/MDCx

LABEL description="MDCx 220260517 with Sehua(色花) Chinese title restored"
