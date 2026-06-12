"""
ST 代码生成引擎 — PLC编程体系核心
负责：需求解析、模板匹配、ST代码生成、语法校验
"""
import re
import json
from pathlib import Path
from typing import Optional


class STGenerator:
    """IEC 61131-3 ST 结构化文本代码生成器"""

    def __init__(self, config: dict):
        self.config = config
        self.platforms = config["platforms"]

    # ────────────────────────────────────────────
    #  从参数生成
    # ────────────────────────────────────────────
    def generate_from_params(self, scenario: str, params: dict, platform_id: str) -> str:
        """根据场景和参数生成 ST 代码"""
        program_name = params.get("program_name", "MainProgram")
        description = params.get("description", "")
        io_points = params.get("io_points", [])
        control_config = params.get("config", {})

        lines = []
        lines.append(f"// ============================================")
        lines.append(f"// 程序名称: {program_name}")
        lines.append(f"// 场景类型: {self.config['scenarios'].get(scenario, scenario)}")
        lines.append(f"// 目标平台: {self.platforms.get(platform_id, {}).get('name', platform_id)}")
        if description:
            lines.append(f"// 描述: {description}")
        lines.append(f"// 生成时间: {self._now()}")
        lines.append(f"// 生成工具: Hermes Agent PLC编程体系")
        lines.append(f"// ============================================")
        lines.append("")

        # PROGRAM 声明
        lines.append(f"PROGRAM {program_name}")
        lines.append("VAR")

        # 变量声明
        var_lines = self._generate_var_declarations(io_points, control_config, platform_id)
        lines.extend(var_lines)

        lines.append("END_VAR")
        lines.append("")

        # 逻辑体
        logic_lines = self._generate_logic_body(scenario, io_points, control_config, platform_id)
        lines.extend(logic_lines)

        lines.append("")
        lines.append(f"END_PROGRAM")

        return "\n".join(lines)

    # ────────────────────────────────────────────
    #  从模板生成
    # ────────────────────────────────────────────
    def generate_from_template(self, scenario: str, template_name: str, params: dict, platform_id: str) -> str:
        """从模板生成 ST 代码"""
        template = self._load_template_content(scenario, template_name)
        if not template:
            return self.generate_from_params(scenario, params, platform_id)

        # 替换模板变量
        code = template
        replacements = {
            "{{PROGRAM_NAME}}": params.get("program_name", "MainProgram"),
            "{{DESCRIPTION}}": params.get("description", ""),
            "{{DATE}}": self._now(),
            "{{PLATFORM}}": platform_id,
        }
        for key, val in params.get("custom_vars", {}).items():
            replacements[f"{{{{{key}}}}}"] = str(val)

        for old, new in replacements.items():
            code = code.replace(old, new)

        return code

    # ────────────────────────────────────────────
    #  语法校验
    # ────────────────────────────────────────────
    def validate(self, st_code: str, platform_id: str = "generic") -> dict:
        """校验 ST 代码基本语法"""
        errors = []
        warnings = []

        # 检查 PROGRAM/END_PROGRAM 配对
        program_count = len(re.findall(r'\bPROGRAM\b', st_code, re.IGNORECASE))
        end_program_count = len(re.findall(r'\bEND_PROGRAM\b', st_code, re.IGNORECASE))
        if program_count == 0:
            errors.append("缺少 PROGRAM 声明")
        if program_count != end_program_count:
            errors.append(f"PROGRAM/END_PROGRAM 不匹配 ({program_count} vs {end_program_count})")

        # 检查 IF/END_IF 配对
        if_count = len(re.findall(r'\bIF\b', st_code, re.IGNORECASE))
        end_if_count = len(re.findall(r'\bEND_IF\b', st_code, re.IGNORECASE))
        if if_count != end_if_count:
            errors.append(f"IF/END_IF 不匹配 ({if_count} vs {end_if_count})")

        # 检查 FOR/END_FOR 配对
        for_count = len(re.findall(r'\bFOR\b', st_code, re.IGNORECASE))
        end_for_count = len(re.findall(r'\bEND_FOR\b', st_code, re.IGNORECASE))
        if for_count != end_for_count:
            errors.append(f"FOR/END_FOR 不匹配 ({for_count} vs {end_for_count})")

        # 检查 CASE/END_CASE 配对
        case_count = len(re.findall(r'\bCASE\b', st_code, re.IGNORECASE))
        end_case_count = len(re.findall(r'\bEND_CASE\b', st_code, re.IGNORECASE))
        if case_count != end_case_count:
            errors.append(f"CASE/END_CASE 不匹配 ({case_count} vs {end_case_count})")

        # 检查 VAR/END_VAR 配对
        var_count = len(re.findall(r'\bVAR\b', st_code))
        end_var_count = len(re.findall(r'\bEND_VAR\b', st_code))
        if var_count != end_var_count:
            errors.append(f"VAR/END_VAR 不匹配 ({var_count} vs {end_var_count})")

        # 检查分号
        lines = st_code.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith("//") and not stripped.startswith("(*"):
                if any(stripped.upper().startswith(kw) for kw in
                       ["PROGRAM", "END_PROGRAM", "VAR", "END_VAR", "IF", "ELSE", "ELSIF",
                        "END_IF", "FOR", "END_FOR", "WHILE", "END_WHILE", "REPEAT",
                        "END_REPEAT", "CASE", "END_CASE", "FUNCTION_BLOCK", "END_FUNCTION_BLOCK",
                        "FUNCTION", "END_FUNCTION", "TYPE", "END_TYPE"]):
                    continue
                if ";" not in stripped and "//" not in stripped:
                    warnings.append(f"第{i}行: 可能缺少分号")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": {
                "lines": len(lines),
                "programs": program_count,
                "if_blocks": if_count,
                "for_loops": for_count
            }
        }

    # ────────────────────────────────────────────
    #  内部方法
    # ────────────────────────────────────────────
    def _generate_var_declarations(self, io_points: list, config: dict, platform_id: str) -> list:
        """生成变量声明区"""
        lines = []
        platform = self.platforms.get(platform_id, {})

        # IO 点声明
        for io in io_points:
            name = io.get("name", "Unnamed")
            addr = io.get("address", "")
            io_type = io.get("type", "BOOL")
            direction = io.get("direction", "input")
            comment = io.get("comment", "")

            addr_str = f"AT {addr} " if addr else ""
            comment_str = f"  // {comment}" if comment else ""
            lines.append(f"    {name} {addr_str}: {io_type};{comment_str}")

        # 内部变量
        internal_vars = config.get("internal_vars", [])
        for var in internal_vars:
            name = var.get("name", "")
            var_type = var.get("type", "BOOL")
            init = var.get("init", "")
            comment = var.get("comment", "")
            init_str = f" := {init}" if init else ""
            comment_str = f"  // {comment}" if comment else ""
            lines.append(f"    {name} : {var_type}{init_str};{comment_str}")

        if not lines:
            lines.append("    // 请在参数中定义 IO 点和内部变量")

        return lines

    def _generate_logic_body(self, scenario: str, io_points: list, config: dict, platform_id: str) -> list:
        """生成逻辑体"""
        lines = []
        lines.append("// === 主控制逻辑 ===")
        lines.append("")

        control_type = config.get("control_type", "basic")

        if control_type == "start_stop":
            lines.extend(self._gen_start_stop_logic(io_points, config))
        elif control_type == "interlock":
            lines.extend(self._gen_interlock_logic(io_points, config))
        elif control_type == "sequential":
            lines.extend(self._gen_sequential_logic(io_points, config))
        elif control_type == "pid":
            lines.extend(self._gen_pid_logic(io_points, config))
        elif control_type == "conveyor":
            lines.extend(self._gen_conveyor_logic(io_points, config))
        elif control_type == "motor_control":
            lines.extend(self._gen_motor_control_logic(io_points, config))
        else:
            lines.extend(self._gen_basic_framework(io_points, config))

        return lines

    def _gen_start_stop_logic(self, io_points: list, config: dict) -> list:
        """生成启停控制逻辑"""
        lines = []
        start = config.get("start_signal", io_points[0]["name"] if io_points else "Start")
        stop = config.get("stop_signal", io_points[1]["name"] if len(io_points) > 1 else "Stop")
        output = config.get("output_signal", io_points[2]["name"] if len(io_points) > 2 else "Output")

        lines.append(f"// 启停控制: {start} 启动, {stop} 停止 → {output}")
        lines.append(f"IF {start} THEN")
        lines.append(f"    {output} := TRUE;")
        lines.append(f"END_IF;")
        lines.append("")
        lines.append(f"IF {stop} THEN")
        lines.append(f"    {output} := FALSE;")
        lines.append(f"END_IF;")
        return lines

    def _gen_interlock_logic(self, io_points: list, config: dict) -> list:
        """生成互锁控制逻辑"""
        lines = []
        conditions = config.get("conditions", [])
        output = config.get("output_signal", "Output")

        lines.append("// 互锁控制")
        lines.append(f"IF ({' AND '.join(conditions)}) THEN")
        lines.append(f"    {output} := TRUE;")
        lines.append("ELSE")
        lines.append(f"    {output} := FALSE;")
        lines.append("END_IF;")
        return lines

    def _gen_sequential_logic(self, io_points: list, config: dict) -> list:
        """生成顺序控制（状态机）"""
        lines = []
        steps = config.get("steps", ["Init", "Step1", "Step2", "Done"])
        step_var = config.get("step_var", "Step")

        lines.append("// 顺序控制 - 状态机")
        lines.append(f"CASE {step_var} OF")
        for i, step in enumerate(steps):
            lines.append(f"    {i}:  // {step}")
            lines.append(f"        // TODO: {step} 逻辑")
            lines.append(f"        ;")
        lines.append("END_CASE;")
        return lines

    def _gen_pid_logic(self, io_points: list, config: dict) -> list:
        """生成 PID 控制逻辑"""
        lines = []
        lines.append("// PID 控制")
        lines.append("// 使用标准 PID 功能块")
        lines.append("TON_PID(IN := Enable,")
        lines.append(f"    PV := {config.get('pv', 'ProcessValue')},")
        lines.append(f"    SP := {config.get('sp', 'Setpoint')},")
        lines.append(f"    KP := {config.get('kp', 1.0)},")
        lines.append(f"    TI := {config.get('ti', 10.0)},")
        lines.append(f"    TD := {config.get('td', 0.0)},")
        lines.append(f"    OUT => {config.get('output', 'ControlOutput')});")
        return lines

    def _gen_conveyor_logic(self, io_points: list, config: dict) -> list:
        """生成传送带控制逻辑"""
        lines = []
        lines.append("// 传送带控制")
        lines.append("IF StartButton AND NOT EmergencyStop THEN")
        lines.append("    ConveyorMotor := TRUE;")
        lines.append("END_IF;")
        lines.append("")
        lines.append("IF EmergencyStop OR StopButton THEN")
        lines.append("    ConveyorMotor := FALSE;")
        lines.append("END_IF;")
        lines.append("")
        lines.append("// 速度控制")
        lines.append("IF ConveyorMotor THEN")
        lines.append("    CurrentSpeed := SpeedSetpoint;")
        lines.append("ELSE")
        lines.append("    CurrentSpeed := 0;")
        lines.append("END_IF;")
        return lines

    def _gen_motor_control_logic(self, io_points: list, config: dict) -> list:
        """生成电机控制逻辑"""
        lines = []
        lines.append("// 电机控制（正反转 + 星三角启动）")
        lines.append("// 正转")
        lines.append("IF ForwardButton AND NOT ReverseButton AND NOT Overload THEN")
        lines.append("    ForwardContactor := TRUE;")
        lines.append("END_IF;")
        lines.append("")
        lines.append("// 反转")
        lines.append("IF ReverseButton AND NOT ForwardButton AND NOT Overload THEN")
        lines.append("    ReverseContactor := TRUE;")
        lines.append("END_IF;")
        lines.append("")
        lines.append("// 停止/过载保护")
        lines.append("IF StopButton OR Overload THEN")
        lines.append("    ForwardContactor := FALSE;")
        lines.append("    ReverseContactor := FALSE;")
        lines.append("END_IF;")
        return lines

    def _gen_basic_framework(self, io_points: list, config: dict) -> list:
        """生成基础框架"""
        lines = []
        lines.append("// === 请补充控制逻辑 ===")
        lines.append("// 在此编写您的 PLC 控制程序")
        lines.append("")
        lines.append("// 示例：主循环")
        lines.append("IF TRUE THEN")
        lines.append("    // 您的逻辑代码")
        lines.append("END_IF;")
        return lines

    def _load_template_content(self, scenario: str, template_name: str) -> Optional[str]:
        """加载模板内容"""
        base = Path(__file__).resolve().parent.parent
        tmpl_path = base / "模板" / scenario / f"{template_name}.st"
        if tmpl_path.exists():
            return tmpl_path.read_text(encoding="utf-8")
        return None

    def _now(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
