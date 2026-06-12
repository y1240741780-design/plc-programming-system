"""
模板引擎 — 管理 PLC 程序模板库
支持：模板列表、按场景分类、加载模板内容、创建新模板
"""
import json
import os
from pathlib import Path
from typing import Optional


class TemplateEngine:
    """PLC 程序模板管理引擎"""

    def __init__(self, config: dict, base_dir: Path):
        self.config = config
        self.templates_dir = base_dir / "模板"
        self._template_index = None

    def list_templates(self) -> list:
        """列出所有模板及其元信息"""
        templates = []
        for scenario_dir in sorted(self.templates_dir.iterdir()):
            if not scenario_dir.is_dir():
                continue
            scenario = scenario_dir.name
            for tmpl_file in sorted(scenario_dir.glob("*.st")):
                name = tmpl_file.stem
                meta = self._get_template_meta(scenario, name, tmpl_file)
                templates.append(meta)

        # 也加载 JSON 索引
        index = self._load_index()
        for entry in index:
            if not any(t["name"] == entry["name"] and t["scenario"] == entry["scenario"] for t in templates):
                templates.append({
                    "scenario": entry["scenario"],
                    "name": entry["name"],
                    "description": entry.get("description", ""),
                    "platform_compat": entry.get("platform_compat", ["generic"]),
                    "tags": entry.get("tags", []),
                    "has_file": False
                })

        return templates

    def get_templates_by_scenario(self, scenario: str) -> list:
        """获取某个场景下的所有模板"""
        all_tmpl = self.list_templates()
        return [t for t in all_tmpl if t["scenario"] == scenario]

    def load_template(self, scenario: str, template_name: str) -> Optional[str]:
        """加载具体模板内容"""
        tmpl_path = self.templates_dir / scenario / f"{template_name}.st"
        if tmpl_path.exists():
            return tmpl_path.read_text(encoding="utf-8")

        # 尝试从 JSON 索引获取内置模板
        index = self._load_index()
        for entry in index:
            if entry["scenario"] == scenario and entry["name"] == template_name:
                return entry.get("content", "")
        return None

    def save_template(self, scenario: str, template_name: str, content: str, meta: dict = None) -> bool:
        """保存新模板"""
        scenario_dir = self.templates_dir / scenario
        scenario_dir.mkdir(parents=True, exist_ok=True)

        tmpl_path = scenario_dir / f"{template_name}.st"
        tmpl_path.write_text(content, encoding="utf-8")

        # 更新索引
        if meta:
            index = self._load_index()
            index.append({
                "scenario": scenario,
                "name": template_name,
                "description": meta.get("description", ""),
                "platform_compat": meta.get("platform_compat", ["generic"]),
                "tags": meta.get("tags", []),
            })
            self._save_index(index)

        return True

    def _get_template_meta(self, scenario: str, name: str, filepath: Path) -> dict:
        """从模板文件头部注释提取元信息"""
        meta = {
            "scenario": scenario,
            "name": name,
            "description": "",
            "platform_compat": ["generic"],
            "tags": [],
            "has_file": True,
            "size": filepath.stat().st_size,
        }

        try:
            content = filepath.read_text(encoding="utf-8")
            # 提取头部注释
            lines = content.split("\n")[:20]
            for line in lines:
                line = line.strip()
                if line.startswith("// @description"):
                    meta["description"] = line.split(":", 1)[-1].strip()
                elif line.startswith("// @platform"):
                    meta["platform_compat"] = [p.strip() for p in line.split(":", 1)[-1].split(",")]
                elif line.startswith("// @tags"):
                    meta["tags"] = [t.strip() for t in line.split(":", 1)[-1].split(",")]
        except:
            pass

        return meta

    def _load_index(self) -> list:
        """加载模板索引"""
        index_path = self.templates_dir / "模板索引.json"
        if index_path.exists():
            try:
                return json.loads(index_path.read_text(encoding="utf-8"))
            except:
                pass
        return []

    def _save_index(self, index: list):
        """保存模板索引"""
        index_path = self.templates_dir / "模板索引.json"
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


# ────────────────────────────────────────
#  内置模板定义（通过 JSON 索引提供）
# ────────────────────────────────────────
BUILTIN_TEMPLATES = [
    {
        "scenario": "基础逻辑",
        "name": "motor_start_stop",
        "description": "电机启停控制（带自锁）",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys"],
        "tags": ["启停", "电机", "自锁"],
        "content": '''// @description: 电机启停控制（带自锁）
// @platform: siemens, beckhoff, codesys, generic
// @tags: 启停, 电机, 自锁

PROGRAM {{PROGRAM_NAME}}
VAR
    StartButton AT %I0.0 : BOOL;    // 启动按钮（常开）
    StopButton  AT %I0.1 : BOOL;    // 停止按钮（常闭）
    Overload    AT %I0.2 : BOOL;    // 热过载保护
    MotorOutput AT %Q0.0 : BOOL;    // 电机输出
    RunFeedback AT %I0.3 : BOOL;    // 运行反馈
    Running     : BOOL := FALSE;    // 运行状态
    TON1        : TON;              // 启动延时定时器
END_VAR

// 启动延时（防抖动）
TON1(IN := StartButton AND NOT StopButton, PT := T#500MS);

// 启动逻辑
IF TON1.Q AND NOT Overload THEN
    MotorOutput := TRUE;
    Running := TRUE;
END_IF;

// 停止逻辑
IF StopButton OR Overload THEN
    MotorOutput := FALSE;
    Running := FALSE;
END_IF;

// 运行反馈超时报警
IF MotorOutput AND NOT RunFeedback THEN
    // 反馈异常处理
END_IF;

END_PROGRAM'''
    },
    {
        "scenario": "基础逻辑",
        "name": "interlock_control",
        "description": "多条件互锁控制",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys", "allen_bradley"],
        "tags": ["互锁", "安全", "逻辑"],
        "content": '''// @description: 多条件互锁控制
// @platform: siemens, beckhoff, codesys, allen_bradley, generic
// @tags: 互锁, 安全, 逻辑

PROGRAM {{PROGRAM_NAME}}
VAR
    Condition1 : BOOL;    // 安全条件1
    Condition2 : BOOL;    // 安全条件2
    Condition3 : BOOL;    // 安全条件3
    Enable     : BOOL;    // 使能信号
    Output     : BOOL;    // 控制输出
    Fault      : BOOL;    // 故障指示
END_VAR

// 互锁判断
IF Condition1 AND Condition2 AND Condition3 AND Enable THEN
    Output := TRUE;
    Fault := FALSE;
ELSE
    Output := FALSE;
    IF Enable AND NOT (Condition1 AND Condition2 AND Condition3) THEN
        Fault := TRUE;
    ELSE
        Fault := FALSE;
    END_IF;
END_IF;

END_PROGRAM'''
    },
    {
        "scenario": "基础逻辑",
        "name": "state_machine",
        "description": "通用状态机框架",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys", "allen_bradley", "omron"],
        "tags": ["状态机", "顺序控制", "SFC"],
        "content": '''// @description: 通用状态机框架
// @platform: siemens, beckhoff, codesys, allen_bradley, omron, generic
// @tags: 状态机, 顺序控制, SFC

PROGRAM {{PROGRAM_NAME}}
VAR
    State     : INT := 0;      // 当前状态
    NextState : INT := 0;      // 下一状态
    StepDone  : BOOL;          // 当前步完成标志
    AutoMode  : BOOL := TRUE;  // 自动模式
    Reset     : BOOL;          // 复位信号
END_VAR

// 状态机主循环
CASE State OF
    0:  // 初始状态
        // 等待启动条件
        IF AutoMode THEN
            NextState := 10;
        END_IF;
        
    10: // 步骤1
        // 执行步骤1逻辑
        IF StepDone THEN
            NextState := 20;
        END_IF;
        
    20: // 步骤2
        // 执行步骤2逻辑
        IF StepDone THEN
            NextState := 30;
        END_IF;
        
    30: // 步骤3
        // 执行步骤3逻辑
        IF StepDone THEN
            NextState := 0;
        END_IF;
        
    99: // 故障状态
        IF Reset THEN
            NextState := 0;
        END_IF;
END_CASE;

// 状态更新
State := NextState;

END_PROGRAM'''
    },
    {
        "scenario": "过程控制",
        "name": "pid_control",
        "description": "标准 PID 过程控制",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys"],
        "tags": ["PID", "过程控制", "模拟量"],
        "content": '''// @description: 标准 PID 过程控制
// @platform: siemens, beckhoff, codesys, generic
// @tags: PID, 过程控制, 模拟量

PROGRAM {{PROGRAM_NAME}}
VAR
    Enable       : BOOL := TRUE;    // PID使能
    AutoMode     : BOOL := TRUE;    // 自动/手动
    ProcessValue : REAL;            // 过程值 (PV)
    Setpoint     : REAL := 50.0;    // 设定值 (SP)
    ControlOutput: REAL;            // 控制输出 (CV)
    ManualOutput : REAL := 0.0;     // 手动输出值
    KP           : REAL := 1.0;     // 比例增益
    TI           : REAL := 10.0;    // 积分时间 (s)
    TD           : REAL := 0.0;     // 微分时间 (s)
    OutMin       : REAL := 0.0;     // 输出下限
    OutMax       : REAL := 100.0;   // 输出上限
    
    Error        : REAL;            // 误差
    Integral     : REAL;            // 积分项
    Derivative   : REAL;            // 微分项
    PrevError    : REAL;            // 上一次误差
    CycleTime    : REAL := 0.1;     // 循环时间 (s)
END_VAR

// 误差计算
Error := Setpoint - ProcessValue;

IF AutoMode AND Enable THEN
    // 积分项（带抗积分饱和）
    Integral := Integral + Error * CycleTime;
    
    // 微分项
    Derivative := (Error - PrevError) / CycleTime;
    
    // PID 输出
    ControlOutput := KP * (Error + Integral / TI + TD * Derivative);
    
    // 输出限幅
    IF ControlOutput > OutMax THEN
        ControlOutput := OutMax;
        Integral := Integral - Error * CycleTime;  // 抗积分饱和
    ELSIF ControlOutput < OutMin THEN
        ControlOutput := OutMin;
        Integral := Integral - Error * CycleTime;
    END_IF;
    
    PrevError := Error;
ELSE
    ControlOutput := ManualOutput;
    Integral := 0.0;
END_IF;

END_PROGRAM'''
    },
    {
        "scenario": "产线自动化",
        "name": "conveyor_control",
        "description": "传送带控制系统",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys"],
        "tags": ["传送带", "产线", "电机"],
        "content": '''// @description: 传送带控制系统
// @platform: siemens, beckhoff, codesys, generic
// @tags: 传送带, 产线, 电机

PROGRAM {{PROGRAM_NAME}}
VAR
    StartButton    AT %I0.0 : BOOL;   // 启动按钮
    StopButton     AT %I0.1 : BOOL;   // 停止按钮
    EmergencyStop  AT %I0.2 : BOOL;   // 急停按钮
    PhotoSensor    AT %I0.3 : BOOL;   // 光电传感器（物料检测）
    JamSensor      AT %I0.4 : BOOL;   // 堵料传感器
    
    ConveyorMotor  AT %Q0.0 : BOOL;   // 传送带电机
    SpeedOutput    AT %QW0 : INT;      // 速度给定（模拟量）
    AlarmLight     AT %Q0.1 : BOOL;   // 报警指示灯
    
    Running        : BOOL := FALSE;   // 运行状态
    SpeedSetpoint  : INT := 1500;     // 速度设定
    JamTimer       : TON;             // 堵料计时器
    JamDetected    : BOOL;            // 堵料报警
END_VAR

// 启动/停止逻辑
IF StartButton AND NOT EmergencyStop THEN
    Running := TRUE;
END_IF;

IF StopButton OR EmergencyStop THEN
    Running := FALSE;
END_IF;

// 电机控制
IF Running AND NOT JamDetected THEN
    ConveyorMotor := TRUE;
    SpeedOutput := SpeedSetpoint;
ELSE
    ConveyorMotor := FALSE;
    SpeedOutput := 0;
END_IF;

// 堵料检测
JamTimer(IN := JamSensor, PT := T#3S);
JamDetected := JamTimer.Q;

// 报警输出
AlarmLight := JamDetected OR EmergencyStop;

END_PROGRAM'''
    },
    {
        "scenario": "运动控制",
        "name": "servo_positioning",
        "description": "伺服电机定位控制",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys"],
        "tags": ["伺服", "定位", "运动控制"],
        "content": '''// @description: 伺服电机定位控制
// @platform: siemens, beckhoff, codesys, generic
// @tags: 伺服, 定位, 运动控制

PROGRAM {{PROGRAM_NAME}}
VAR
    Enable        : BOOL;            // 伺服使能
    HomeDone      : BOOL;            // 回零完成
    StartPos      : BOOL;            // 启动定位
    EmergencyStop : BOOL;            // 急停
    
    TargetPos     : REAL := 100.0;   // 目标位置 (mm)
    CurrentPos    : REAL;            // 当前位置 (mm)
    Speed         : REAL := 50.0;    // 运行速度 (mm/s)
    Accel         : REAL := 100.0;   // 加速度 (mm/s²)
    Decel         : REAL := 100.0;   // 减速度 (mm/s²)
    
    InPosition    : BOOL;            // 到位信号
    Positioning   : BOOL;            // 定位中
    Fault         : BOOL;            // 故障
    Tolerance     : REAL := 0.1;     // 到位容差 (mm)
END_VAR

// 伺服使能
IF NOT EmergencyStop AND HomeDone THEN
    Enable := TRUE;
ELSE
    Enable := FALSE;
END_IF;

// 定位控制
IF Enable AND StartPos AND NOT InPosition THEN
    Positioning := TRUE;
    
    // 梯形速度曲线定位（简化）
    IF ABS(TargetPos - CurrentPos) > Tolerance THEN
        // 运动中
        // 实际项目中此处调用运动控制功能块 MC_MoveAbsolute
    ELSE
        InPosition := TRUE;
        Positioning := FALSE;
    END_IF;
END_IF;

// 到位判断
IF ABS(TargetPos - CurrentPos) <= Tolerance AND Positioning THEN
    InPosition := TRUE;
    Positioning := FALSE;
END_IF;

// 故障诊断
Fault := EmergencyStop OR NOT HomeDone;

END_PROGRAM'''
    },
    {
        "scenario": "楼宇自控",
        "name": "hvac_control",
        "description": "空调 AHU 控制",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys"],
        "tags": ["HVAC", "空调", "楼宇"],
        "content": '''// @description: 空调 AHU 控制
// @platform: siemens, beckhoff, codesys, generic
// @tags: HVAC, 空调, 楼宇

PROGRAM {{PROGRAM_NAME}}
VAR
    SystemOn      : BOOL;           // 系统启停
    ScheduleOn    : BOOL;           // 时间表控制
    
    RoomTemp      : REAL := 22.0;   // 房间温度
    TempSetpoint  : REAL := 24.0;   // 温度设定
    SupplyTemp    : REAL;           // 送风温度
    ReturnTemp    : REAL;           // 回风温度
    OutdoorTemp   : REAL;           // 室外温度
    
    CoolValve     : REAL := 0.0;    // 冷水阀开度 (0-100%)
    HeatValve     : REAL := 0.0;    // 热水阀开度 (0-100%)
    FanSpeed      : REAL := 50.0;   // 风机转速 (0-100%)
    DamperPos     : REAL := 20.0;   // 新风阀开度 (0-100%)
    
    FilterDirty   : BOOL;           // 滤网脏堵
    FreezeAlarm   : BOOL;           // 防冻报警
    FireAlarm     : BOOL;           // 火警信号
END_VAR

// 系统启停（时间表 + 火警联锁）
SystemOn := ScheduleOn AND NOT FireAlarm;

IF SystemOn THEN
    // 温度 PID 控制（简化逻辑）
    IF RoomTemp > TempSetpoint + 0.5 THEN
        // 制冷模式
        CoolValve := MIN(100.0, (RoomTemp - TempSetpoint) * 20.0);
        HeatValve := 0.0;
    ELSIF RoomTemp < TempSetpoint - 0.5 THEN
        // 制热模式
        HeatValve := MIN(100.0, (TempSetpoint - RoomTemp) * 20.0);
        CoolValve := 0.0;
    ELSE
        CoolValve := 0.0;
        HeatValve := 0.0;
    END_IF;
    
    // 风机运行
    FanSpeed := 50.0;
    DamperPos := 20.0;
ELSE
    CoolValve := 0.0;
    HeatValve := 0.0;
    FanSpeed := 0.0;
    DamperPos := 0.0;
END_IF;

// 防冻保护
IF SupplyTemp < 5.0 AND OutdoorTemp < 2.0 THEN
    FreezeAlarm := TRUE;
    HeatValve := 100.0;
    FanSpeed := 0.0;
    DamperPos := 0.0;
END_IF;

END_PROGRAM'''
    },
    {
        "scenario": "水处理",
        "name": "pump_control",
        "description": "泵站轮换控制",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys"],
        "tags": ["水泵", "轮换", "水处理"],
        "content": '''// @description: 泵站轮换控制
// @platform: siemens, beckhoff, codesys, generic
// @tags: 水泵, 轮换, 水处理

PROGRAM {{PROGRAM_NAME}}
VAR
    LevelHigh    : BOOL;            // 高液位
    LevelLow     : BOOL;            // 低液位
    LevelAlarm   : BOOL;            // 超高液位报警
    
    Pump1_Run    AT %Q0.0 : BOOL;   // 1#泵运行
    Pump2_Run    AT %Q0.1 : BOOL;   // 2#泵运行
    Pump3_Run    AT %Q0.2 : BOOL;   // 3#泵运行
    
    Pump1_Fault  AT %I0.0 : BOOL;   // 1#泵故障
    Pump2_Fault  AT %I0.1 : BOOL;   // 2#泵故障
    Pump3_Fault  AT %I0.2 : BOOL;   // 3#泵故障
    
    Pump1_Hours  : DINT := 0;       // 1#泵运行时间
    Pump2_Hours  : DINT := 0;       // 2#泵运行时间
    Pump3_Hours  : DINT := 0;       // 3#泵运行时间
    
    LeadPump     : INT := 1;        // 主泵编号 (1-3)
    PumpsRunning : INT := 0;        // 当前运行泵数
    NeedsPumps   : INT := 0;        // 需求泵数
END_VAR

// 需求泵数计算
IF LevelAlarm THEN
    NeedsPumps := 3;    // 紧急，全开
ELSIF LevelHigh THEN
    NeedsPumps := 2;    // 高液位，开两台
ELSIF NOT LevelLow THEN
    NeedsPumps := 1;    // 正常，开一台
ELSE
    NeedsPumps := 0;    // 低液位，全停
END_IF;

// 泵轮换逻辑（运行时间均衡）
// 按需求依次启动，故障泵跳过

// 每日轮换主泵（简化）
IF LeadPump = 3 THEN
    LeadPump := 1;
ELSE
    LeadPump := LeadPump + 1;
END_IF;

END_PROGRAM'''
    },
    {
        "scenario": "通信协议",
        "name": "modbus_rtu_master",
        "description": "Modbus RTU 主站通信",
        "platform_compat": ["generic", "siemens", "beckhoff", "codesys"],
        "tags": ["Modbus", "RTU", "通信"],
        "content": '''// @description: Modbus RTU 主站通信
// @platform: siemens, beckhoff, codesys, generic
// @tags: Modbus, RTU, 通信

PROGRAM {{PROGRAM_NAME}}
VAR
    Enable         : BOOL := TRUE;     // 通信使能
    CommOK         : BOOL;             // 通信正常
    CommError      : BOOL;             // 通信故障
    ErrorCode      : WORD;             // 错误码
    
    SlaveAddr      : BYTE := 1;        // 从站地址
    FuncCode       : BYTE := 3;        // 功能码 (03=读保持寄存器)
    StartReg       : WORD := 0;        // 起始寄存器地址
    RegCount       : WORD := 10;       // 寄存器数量
    
    ReadData       : ARRAY[0..9] OF WORD;  // 读取数据缓冲区
    WriteData      : ARRAY[0..9] OF WORD;  // 写入数据缓冲区
    
    ReadDone       : BOOL;             // 读取完成
    WriteDone      : BOOL;             // 写入完成
    Timeout        : TON;              // 超时定时器
    RetryCount     : INT := 0;         // 重试计数
    MaxRetry       : INT := 3;         // 最大重试次数
END_VAR

// 通信超时检测
Timeout(IN := Enable AND NOT CommOK, PT := T#2S);

IF Timeout.Q THEN
    CommError := TRUE;
    RetryCount := RetryCount + 1;
    
    IF RetryCount >= MaxRetry THEN
        Enable := FALSE;   // 超过重试次数，停止通信
    END_IF;
END_IF;

// 通信状态
IF CommOK THEN
    CommError := FALSE;
    RetryCount := 0;
END_IF;

// 实际 Modbus 通信需调用专用通信功能块
// 如 Siemens: MB_MASTER, Codesys: ModbusMaster

END_PROGRAM'''
    }
]
