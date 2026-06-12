"""
多平台适配器 — 将通用 ST 代码适配到不同 PLC 平台
处理：IO地址格式、定时器/计数器命名、注释语法、特殊指令
"""
import re
from typing import Optional


class PlatformAdapter:
    """PLC 多平台代码适配器"""

    def __init__(self, config: dict):
        self.config = config
        self.platforms = config["platforms"]

    def adapt(self, st_code: str, platform_id: str, params: dict) -> str:
        """将通用 ST 代码适配到指定平台"""
        platform = self.platforms.get(platform_id)
        if not platform:
            return st_code

        code = st_code

        # 1. 适配注释语法
        code = self._adapt_comments(code, platform)

        # 2. 适配 IO 地址格式
        code = self._adapt_io_format(code, platform, params)

        # 3. 适配定时器/计数器
        code = self._adapt_timers_counters(code, platform)

        # 4. 平台特殊适配
        if platform_id == "siemens":
            code = self._adapt_siemens(code, params)
        elif platform_id == "mitsubishi":
            code = self._adapt_mitsubishi(code, params)
        elif platform_id == "allen_bradley":
            code = self._adapt_allen_bradley(code, params)

        return code

    def _adapt_comments(self, code: str, platform: dict) -> str:
        """适配注释语法"""
        comment_syntax = platform.get("comment_syntax", "//")

        if comment_syntax == "(* ... *)":
            # 将 // 注释转为 (* ... *) 注释
            lines = code.split("\n")
            adapted = []
            for line in lines:
                if "//" in line and not line.strip().startswith("(*"):
                    # 分离代码和注释
                    parts = line.split("//", 1)
                    if len(parts) == 2:
                        code_part = parts[0]
                        comment_part = parts[1].strip()
                        if code_part.strip():
                            adapted.append(f"{code_part}(* {comment_part} *)")
                        else:
                            adapted.append(f"(* {comment_part} *)")
                    else:
                        adapted.append(line)
                else:
                    adapted.append(line)
            return "\n".join(adapted)
        return code

    def _adapt_io_format(self, code: str, platform: dict, params: dict) -> str:
        """适配 IO 地址格式"""
        io_format = platform.get("io_format", "")

        if "mitsubishi" in platform.get("name", "").lower():
            # 三菱: %I0.0 → X0, %Q0.0 → Y0
            code = re.sub(r'AT\s+%I(\d+)\.(\d+)', r'AT X\1', code)
            code = re.sub(r'AT\s+%Q(\d+)\.(\d+)', r'AT Y\1', code)
            code = re.sub(r'%I(\d+)\.(\d+)', r'X\1', code)
            code = re.sub(r'%Q(\d+)\.(\d+)', r'Y\1', code)

        elif "allen_bradley" in platform.get("name", "").lower():
            # AB: 移除 AT %I/Q 格式，改用标签
            code = re.sub(r'AT\s+%[IQ](\d+)\.(\d+)\s*', '', code)

        return code

    def _adapt_timers_counters(self, code: str, platform: dict) -> str:
        """适配定时器和计数器命名"""
        timer_type = platform.get("timer_type", "TON")
        counter_type = platform.get("counter_type", "CTU")

        # 三菱使用 TIM/CNT
        if timer_type == "TIM":
            code = re.sub(r'\bTON\b', 'TIM', code)
            code = re.sub(r'\bTOF\b', 'TIM', code)

        if counter_type == "CNT":
            code = re.sub(r'\bCTU\b', 'CNT', code)
            code = re.sub(r'\bCTD\b', 'CNT', code)
            code = re.sub(r'\bCTUD\b', 'CNT', code)

        return code

    def _adapt_siemens(self, code: str, params: dict) -> str:
        """Siemens TIA Portal 特殊适配"""
        # SIMATIC 标准块头部
        header = (
            "// SIMATIC S7 程序块\n"
            "// TIA Portal 兼容\n"
        )
        # 确保使用 SCL 兼容语法
        code = code.replace("END_PROGRAM", "END_PROGRAM\n// Block End")
        return header + code

    def _adapt_mitsubishi(self, code: str, params: dict) -> str:
        """Mitsubishi GX Works 特殊适配"""
        # 三菱使用 M 作为内部继电器
        code = re.sub(r'\bBOOL\s*;\s*//\s*内部继电器', r'BIT;', code)
        return code

    def _adapt_allen_bradley(self, code: str, params: dict) -> str:
        """Allen-Bradley Studio 5000 特殊适配"""
        # AB 使用标签，不需要 AT 地址
        header = (
            "// Studio 5000 Logix Designer\n"
            "// 标签需在 Controller Tags 中定义\n"
        )
        return header + code

    def get_platform_features(self, platform_id: str) -> dict:
        """获取平台特性"""
        platform = self.platforms.get(platform_id, {})
        return {
            "id": platform_id,
            "name": platform.get("name", platform_id),
            "extension": platform.get("extension", ".st"),
            "features": platform.get("features", ["st"]),
            "io_format": platform.get("io_format", ""),
            "timer_type": platform.get("timer_type", "TON"),
            "counter_type": platform.get("counter_type", "CTU"),
        }
