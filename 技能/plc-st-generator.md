# PLC ST 编程助手

使用此技能生成 IEC 61131-3 ST（结构化文本）语言 PLC 程序。

## 触发条件

- 用户提到"PLC"、"ST语言"、"结构化文本"、"梯形图"、"IEC 61131-3"
- 用户要求写 PLC 程序、控制逻辑
- 用户需要工业自动化程序

## 核心流程（分步交互式）

### 步骤 1：确认需求
每次只问一个问题，逐步确认：

1. **目标平台** — Siemens / Beckhoff / CODESYS / Allen-Bradley / Mitsubishi / Omron / 通用
2. **应用场景** — 基础逻辑 / 产线自动化 / 过程控制(PID) / 运动控制 / 楼宇自控 / 水处理 / 通信
3. **程序名称和功能描述** — 一句话说清楚要做什么
4. **控制类型** — 启停 / 互锁 / 顺序控制(状态机) / PID / 传送带 / 电机控制
5. **IO 点** — 有哪些输入输出信号

### 步骤 2：生成框架
确认需求后生成程序框架（PROGRAM 声明 + VAR 变量区 + 逻辑体大纲），让用户确认。

### 步骤 3：逐段生成
按逻辑模块分段生成，每段都让用户审核。典型分段：
- 变量声明区（IO 映射 + 内部变量）
- 主控制逻辑
- 安全保护逻辑
- 报警/诊断逻辑

### 步骤 4：完整输出
生成完整 ST 代码 + IO 映射表 + 功能说明。

## 后端 API

Web 服务运行在 `http://localhost:5001`

### 生成代码
```bash
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "siemens",
    "scenario": "basic_logic",
    "params": {
      "program_name": "ConveyorControl",
      "description": "传送带控制系统",
      "io_points": [
        {"name":"Start","address":"%I0.0","type":"BOOL","direction":"input","comment":"启动"},
        {"name":"Motor","address":"%Q0.0","type":"BOOL","direction":"output","comment":"电机"}
      ],
      "config": {"control_type": "conveyor"}
    },
    "options": {"generate_io_map": true, "generate_docs": true}
  }'
```

### 校验代码
```bash
curl -X POST http://localhost:5001/api/validate \
  -H "Content-Type: application/json" \
  -d '{"code": "PROGRAM Main ... END_PROGRAM", "platform": "siemens"}'
```

### 查看模板
```bash
curl http://localhost:5001/api/templates
```

### 项目管理
```bash
# 列出项目
curl http://localhost:5001/api/projects

# 保存项目
curl -X POST http://localhost:5001/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"MyProject","platform":"siemens","code":"..."}'
```

## 可用模板

| 场景 | 模板名 | 说明 |
|------|--------|------|
| 基础逻辑 | `motor_start_stop` | 电机启停控制（带自锁） |
| 基础逻辑 | `interlock_control` | 多条件互锁控制 |
| 基础逻辑 | `state_machine` | 通用状态机框架 |
| 过程控制 | `pid_control` | 标准 PID 过程控制 |
| 产线自动化 | `conveyor_control` | 传送带控制系统 |
| 运动控制 | `servo_positioning` | 伺服电机定位控制 |
| 楼宇自控 | `hvac_control` | 空调 AHU 控制 |
| 水处理 | `pump_control` | 泵站轮换控制 |
| 通信协议 | `modbus_rtu_master` | Modbus RTU 主站通信 |

## 支持的平台

| 平台 ID | 名称 | 扩展名 | IO 格式 |
|---------|------|--------|---------|
| `siemens` | Siemens TIA Portal | `.scl` | `%I0.0` / `%Q0.0` |
| `beckhoff` | Beckhoff TwinCAT | `.TcPOU` | `AT %I*` / `AT %Q*` |
| `codesys` | CODESYS 通用 | `.exp` | `AT %I*` / `AT %Q*` |
| `allen_bradley` | Allen-Bradley | `.L5X` | 标签体系 |
| `mitsubishi` | Mitsubishi GX Works | `.st` | `X0` / `Y0` |
| `omron` | Omron Sysmac | `.st` | `%地址` |
| `generic` | IEC 61131-3 通用 | `.st` | `AT %I*` / `AT %Q*` |

## 项目结构

```
D:\fanben\PLC编程体系\
├── backend/          # Python 引擎
├── web/              # 前端界面
├── 技能/             # Hermes 技能
├── 模板/             # ST 模板库
├── 知识库/            # 规范与参考
├── 配置/             # config.json
└── 输出/             # 生成的程序和文档
```

## 启动

```bash
cd D:\fanben\PLC编程体系
python backend/server.py
# → Web 界面: http://localhost:5001
```

## 注意事项

- Siemens 平台地址格式：`%I0.0`(输入) / `%Q0.0`(输出)
- 三菱平台地址格式：`X0`(输入) / `Y0`(输出)，注释语法 `(* ... *)`
- AB 平台使用标签体系，不直接使用 `AT %I/%Q` 地址
- 生成代码后务必进行语法检查

## 对话框示例

用户："帮我写一个西门子 PLC 的传送带控制程序"

Agent：
1. 先确认 IO 点："需要哪些输入输出？比如启动按钮、停止按钮、急停、电机输出？"
2. 确认功能："需要速度控制吗？堵料检测？"
3. 生成框架让用户确认
4. 逐段完善
5. 输出完整代码
