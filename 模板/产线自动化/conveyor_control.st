// @description: 传送带控制系统
// @platform: siemens, beckhoff, codesys, generic
// @tags: 传送带, 产线, 电机, 传感器

PROGRAM ConveyorControl
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
    StartTimer     : TON;             // 启动延时
    StopTimer      : TON;             // 停止延时
END_VAR

// 急停（最高优先级）
IF EmergencyStop THEN
    Running := FALSE;
    ConveyorMotor := FALSE;
    SpeedOutput := 0;
END_IF;

// 启动逻辑（带延时防抖）
StartTimer(IN := StartButton AND NOT EmergencyStop, PT := T#300MS);

IF StartTimer.Q AND NOT EmergencyStop THEN
    Running := TRUE;
END_IF;

// 停止逻辑
IF StopButton OR NOT PhotoSensor THEN
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

// 堵料检测（3秒持续堵料报警）
JamTimer(IN := JamSensor, PT := T#3S);
JamDetected := JamTimer.Q;

// 报警输出
AlarmLight := JamDetected OR EmergencyStop;

END_PROGRAM
