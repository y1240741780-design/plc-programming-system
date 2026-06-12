"""
I/O 映射器 — 从 ST 代码提取 IO 点，生成 IO 映射表
支持：输入/输出点提取、地址映射、类型推断、按平台格式化
"""
import re
from datetime import datetime


class IOMapper:
    """PLC I/O 映射表生成器"""

    def __init__(self, config: dict):
        self.config = config
        self.platforms = config["platforms"]

    def generate(self, st_code: str, platform_id: str, params: dict) -> dict:
        """生成 IO 映射表"""
        platform = self.platforms.get(platform_id, {})

        # 提取 IO 点
        io_points = self._extract_io_points(st_code, platform)

        # 分类
        inputs = [p for p in io_points if p["direction"] == "input"]
        outputs = [p for p in io_points if p["direction"] == "output"]
        internals = [p for p in io_points if p["direction"] == "internal"]

        # 统计
        di_count = sum(1 for p in inputs if p["type"] == "BOOL")
        ai_count = sum(1 for p in inputs if p["type"] in ("INT", "REAL", "WORD", "DINT"))
        do_count = sum(1 for p in outputs if p["type"] == "BOOL")
        ao_count = sum(1 for p in outputs if p["type"] in ("INT", "REAL", "WORD", "DINT"))

        return {
            "platform": platform_id,
            "platform_name": platform.get("name", platform_id),
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_points": len(io_points),
                "digital_inputs": di_count,
                "analog_inputs": ai_count,
                "digital_outputs": do_count,
                "analog_outputs": ao_count,
                "internal_vars": len(internals)
            },
            "inputs": inputs,
            "outputs": outputs,
            "internal_vars": internals,
            "io_format": platform.get("io_format", ""),
        }

    def _extract_io_points(self, st_code: str, platform: dict) -> list:
        """从 ST 代码提取 IO 点定义"""
        points = []

        # 匹配变量声明行
        # 格式: Name AT %I0.0 : TYPE;  // comment
        pattern = r'(\w+)\s+(AT\s+%?[IQ]?[XY]?[\w.]+\s+)?:\s*(\w+)\s*;\s*(?://\s*(.*))?'
        matches = re.findall(pattern, st_code)

        for match in matches:
            name, addr_part, var_type, comment = match
            addr = addr_part.replace("AT ", "").strip() if addr_part else ""

            # 判断方向
            direction = "internal"
            if re.match(r'%I|X\d', addr):
                direction = "input"
            elif re.match(r'%Q|Y\d', addr):
                direction = "output"
            elif "Button" in name or "Sensor" in name or "Switch" in name:
                direction = "input"
            elif "Output" in name or "Motor" in name or "Valve" in name or "Contactor" in name:
                direction = "output"

            # 判断信号类型
            signal_type = "digital" if var_type == "BOOL" else "analog"

            point = {
                "name": name,
                "address": addr,
                "type": var_type,
                "signal_type": signal_type,
                "direction": direction,
                "comment": comment.strip() if comment else "",
            }
            points.append(point)

        return points

    def export_to_csv(self, io_map: dict) -> str:
        """导出为 CSV 格式"""
        lines = ["名称,地址,类型,方向,信号类型,说明"]
        for section in ["inputs", "outputs", "internal_vars"]:
            for point in io_map.get(section, []):
                lines.append(
                    f"{point['name']},{point['address']},{point['type']},"
                    f"{point['direction']},{point['signal_type']},{point['comment']}"
                )
        return "\n".join(lines)

    def export_to_json(self, io_map: dict) -> str:
        """导出为 JSON"""
        import json
        return json.dumps(io_map, ensure_ascii=False, indent=2)
