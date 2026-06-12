"""
文档生成器 — 自动生成 IO 清单、功能说明、变量表等配套文档
支持：Markdown 格式文档、IO 清单表格、功能描述
"""
from datetime import datetime


class DocGenerator:
    """PLC 项目文档自动生成器"""

    def __init__(self, config: dict):
        self.config = config

    def generate(self, st_code: str, platform_id: str, params: dict, io_map: dict = None) -> dict:
        """生成文档集合"""
        docs = {}

        # 提取程序名
        program_name = params.get("program_name", "MainProgram")

        # 1. IO 清单
        docs["io_list"] = self._gen_io_list(io_map, program_name)

        # 2. 功能说明
        docs["function_description"] = self._gen_function_description(st_code, params, program_name)

        # 3. 变量表
        docs["variable_table"] = self._gen_variable_table(st_code, program_name)

        # 4. 完整 Markdown 文档
        docs["full_document"] = self._gen_full_doc(program_name, platform_id, params, docs)

        return docs

    def _gen_io_list(self, io_map: dict, program_name: str) -> str:
        """生成 IO 清单（Markdown 表格）"""
        if not io_map:
            return ""

        lines = [
            f"# IO 清单 — {program_name}",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**目标平台**: {io_map.get('platform_name', '')}",
            "",
            "## 统计汇总",
            "",
        ]

        summary = io_map.get("summary", {})
        lines.append("| 类型 | 数量 |")
        lines.append("|------|------|")
        lines.append(f"| 数字量输入 (DI) | {summary.get('digital_inputs', 0)} |")
        lines.append(f"| 模拟量输入 (AI) | {summary.get('analog_inputs', 0)} |")
        lines.append(f"| 数字量输出 (DO) | {summary.get('digital_outputs', 0)} |")
        lines.append(f"| 模拟量输出 (AO) | {summary.get('analog_outputs', 0)} |")
        lines.append(f"| 内部变量 | {summary.get('internal_vars', 0)} |")
        lines.append(f"| **总计** | **{summary.get('total_points', 0)}** |")
        lines.append("")

        # 输入点表
        inputs = io_map.get("inputs", [])
        if inputs:
            lines.append("## 输入点表")
            lines.append("")
            lines.append("| 序号 | 名称 | 地址 | 类型 | 信号类型 | 说明 |")
            lines.append("|------|------|------|------|----------|------|")
            for i, pt in enumerate(inputs, 1):
                lines.append(f"| {i} | {pt['name']} | {pt['address']} | {pt['type']} | {pt['signal_type']} | {pt['comment']} |")
            lines.append("")

        # 输出点表
        outputs = io_map.get("outputs", [])
        if outputs:
            lines.append("## 输出点表")
            lines.append("")
            lines.append("| 序号 | 名称 | 地址 | 类型 | 信号类型 | 说明 |")
            lines.append("|------|------|------|------|----------|------|")
            for i, pt in enumerate(outputs, 1):
                lines.append(f"| {i} | {pt['name']} | {pt['address']} | {pt['type']} | {pt['signal_type']} | {pt['comment']} |")
            lines.append("")

        return "\n".join(lines)

    def _gen_function_description(self, st_code: str, params: dict, program_name: str) -> str:
        """生成功能说明"""
        description = params.get("description", "")
        scenario = params.get("scenario", "")
        control_type = params.get("config", {}).get("control_type", "")

        lines = [
            f"# 功能说明 — {program_name}",
            "",
            "## 1. 程序概述",
            "",
            f"- **程序名称**: {program_name}",
            f"- **场景类型**: {scenario}",
        ]
        if description:
            lines.append(f"- **功能描述**: {description}")
        if control_type:
            lines.append(f"- **控制类型**: {control_type}")

        lines.extend([
            "",
            "## 2. 控制逻辑",
            "",
            "### 主要功能模块",
            "",
        ])

        # 从代码注释提取功能模块
        import re
        sections = re.findall(r'//\s*={3,}\s*\n//\s*(.+?)\n//\s*={3,}\s*\n((?:(?!//\s*={3,}).|\n)*)', st_code)
        if sections:
            for title, _ in sections:
                lines.append(f"- **{title.strip()}**")
        else:
            # 从普通注释提取
            comments = re.findall(r'//\s*(.+?)(?:\n|$)', st_code)
            seen = set()
            for c in comments[:10]:
                c = c.strip()
                if c and len(c) > 5 and c not in seen and not c.startswith("@") and not c.startswith("==="):
                    seen.add(c)
                    lines.append(f"- {c}")

        lines.extend([
            "",
            "## 3. 安全保护",
            "",
            "程序包含以下安全保护机制：",
            "",
        ])

        # 检测安全相关逻辑
        if "EmergencyStop" in st_code or "急停" in st_code:
            lines.append("- ✅ 急停保护")
        if "Overload" in st_code or "过载" in st_code:
            lines.append("- ✅ 过载保护")
        if "Interlock" in st_code or "互锁" in st_code:
            lines.append("- ✅ 互锁逻辑")
        if "Fault" in st_code or "故障" in st_code:
            lines.append("- ✅ 故障诊断")

        if not any(kw in st_code for kw in ["EmergencyStop", "Overload", "Interlock", "Fault"]):
            lines.append("- ⚠️ 建议添加安全保护逻辑")

        return "\n".join(lines)

    def _gen_variable_table(self, st_code: str, program_name: str) -> str:
        """生成变量表"""
        import re

        lines = [
            f"# 变量表 — {program_name}",
            "",
            "| 名称 | 类型 | 初始值 | 说明 |",
            "|------|------|--------|------|",
        ]

        # 提取变量声明
        var_pattern = r'(\w+)\s+(?:AT\s+\S+\s+)?:\s*(\w+(?:\[[^\]]+\])?)\s*(:=\s*([^;]+))?\s*;\s*(?://\s*(.*))?'
        matches = re.findall(var_pattern, st_code)

        for match in matches:
            name, var_type, _, init_val, comment = match
            init_str = init_val.strip() if init_val else "-"
            comment_str = comment.strip() if comment else ""
            lines.append(f"| {name} | {var_type} | {init_str} | {comment_str} |")

        return "\n".join(lines)

    def _gen_full_doc(self, program_name: str, platform_id: str, params: dict, docs: dict) -> str:
        """生成完整文档"""
        sections = [
            f"# {program_name} — 完整项目文档",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**目标平台**: {platform_id}",
            f"**生成工具**: Hermes Agent PLC编程体系 v{self.config['system']['version']}",
            "",
            "---",
            "",
            docs.get("function_description", ""),
            "",
            "---",
            "",
            docs.get("io_list", ""),
            "",
            "---",
            "",
            docs.get("variable_table", ""),
        ]
        return "\n".join(sections)
