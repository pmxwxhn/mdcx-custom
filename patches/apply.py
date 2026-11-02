"""把「色花中文标题」功能补回 MDCx。

用法: python patches/apply.py <源码目录>

做法是用锚点文本做精确替换，找不到锚点就报错退出（让 CI 直接失败），
避免上游代码变动后补丁被"悄悄打歪"。
"""

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "src")


def patch(rel: str, old: str, new: str) -> None:
    p = ROOT / rel
    with open(p, encoding="utf-8", newline="") as f:
        text = f.read()
    if old not in text:
        raise SystemExit(f"[PATCH FAIL] 锚点未找到: {rel}")
    if text.count(old) != 1:
        raise SystemExit(f"[PATCH FAIL] 锚点不唯一({text.count(old)}): {rel}")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace(old, new, 1))
    print(f"[PATCH OK] {rel}")


# 1) 配置模型：加回两个开关
patch(
    "mdcx/config/models.py",
    '''    actor_realname: bool = Field(default=True, title="演员真名")
    outline_format: list[OutlineShow] = Field(default_factory=list, title="简介格式")
    # endregion''',
    '''    actor_realname: bool = Field(default=True, title="演员真名")
    outline_format: list[OutlineShow] = Field(default_factory=list, title="简介格式")
    title_sehua: bool = Field(default=True, title="使用色花标题")
    title_sehua_zh: bool = Field(default=True, title="使用色花中文标题")
    # endregion''',
)

# 2) v1 配置模型：让旧的 config.ini 迁移时不丢这三个字段
patch(
    "mdcx/config/v1.py",
    '''    title_language: str = r"zh_cn"
    title_translate: bool = True
''',
    '''    title_language: str = r"zh_cn"
    title_translate: bool = True
    title_sehua: bool = True
    title_sehua_zh: bool = True
    title_yesjav: bool = False
''',
)

# 3) 资源模块：载入 c_number.json + 提供查表方法
patch(
    "mdcx/config/resources.py",
    '''import os
import sys
import traceback''',
    '''import json
import os
import re
import sys
import traceback''',
)

patch(
    "mdcx/config/resources.py",
    '''        self.actor_mapping_data = None  # 演员映射表数据
        self.info_mapping_data = None  # 信息映射表数据''',
    '''        self.actor_mapping_data = None  # 演员映射表数据
        self.info_mapping_data = None  # 信息映射表数据
        self.sehua_title_data = {}  # 色花标题数据(番号 -> 中文标题)''',
)

patch(
    "mdcx/config/resources.py",
    "    def get_actor_data(self, actor):",
    '''    def get_sehua_title(self, movie_number: str) -> str:
        """按番号取色花中文标题，兼容大小写与分隔符差异"""
        if not self.sehua_title_data:
            return ""
        index = getattr(self, "_sehua_index", None)
        if index is None:
            index = {}
            for key, title in self.sehua_title_data.items():
                raw = str(key).strip().upper()
                index[raw] = title
                index[re.sub(r"[^0-9A-Z]", "", raw)] = title
            self._sehua_index = index
        num = str(movie_number or "").strip().upper()
        if not num:
            return ""
        return index.get(num) or index.get(re.sub(r"[^0-9A-Z]", "", num)) or ""

    def get_actor_data(self, actor):''',
)

patch(
    "mdcx/config/resources.py",
    '''    def _get_or_generate_local_data(self):
        """如果用户数据目录下已有数据则直接读取, 否则根据内置数据生成"""
        # 载入 mapping_actor.xml mapping_info.xml 数据''',
    '''    def _get_or_generate_local_data(self):
        """如果用户数据目录下已有数据则直接读取, 否则根据内置数据生成"""
        # 载入色花标题数据(c_number.json)
        try:
            sehua_path = self.r("c_number/c_number.json")
            if os.path.exists(sehua_path):
                with open(sehua_path, encoding="UTF-8") as f:
                    self.sehua_title_data = json.load(f)
                signal.show_log_text(f" 🌸 色花标题数据已载入：{len(self.sehua_title_data)} 条")
            else:
                signal.show_log_text(f" 🌸 色花标题数据文件不存在：{sehua_path}")
        except Exception:
            signal.show_traceback_log(traceback.format_exc())

        # 载入 mapping_actor.xml mapping_info.xml 数据''',
)

# 4) 标题处理：命中色花表就覆盖标题并跳过翻译
patch(
    "mdcx/core/translate.py",
    '''    # 处理title
    if title_language != Language.JP:
        # 使用json_data数据
        if title_translate and (title_is_jp or title_is_en):
            trans_title = json_data.title''',
    '''    # 处理title
    if title_language != Language.JP:
        sehua_title = ""
        # 匹配本地高质量标题(色花标题数据)
        if manager.config.title_sehua_zh or (title_is_jp and manager.config.title_sehua):
            start_time = time.time()
            sehua_title = resources.get_sehua_title(movie_number)
            if sehua_title:
                json_data.title = sehua_title
                LogBuffer.log().write(f"\\n 🌸 Sehua title done!({get_used_time(start_time)}s)")
        # 使用json_data数据
        if not sehua_title and title_translate and (title_is_jp or title_is_en):
            trans_title = json_data.title''',
)

print("全部补丁已应用")
