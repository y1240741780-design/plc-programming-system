// @description: 标准 PID 过程控制
// @platform: siemens, beckhoff, codesys, generic
// @tags: PID, 过程控制, 模拟量, 温控

PROGRAM PIDControl
VAR
    Enable       : BOOL := TRUE;    // PID使能
    AutoMode     : BOOL := TRUE;    // 自动/手动模式
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
    
    // 积分限幅
    IF Integral > OutMax / KP THEN
        Integral := OutMax / KP;
    ELSIF Integral < OutMin / KP THEN
        Integral := OutMin / KP;
    END_IF;
    
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
    // 手动模式
    ControlOutput := ManualOutput;
    Integral := 0.0;
    PrevError := 0.0;
END_IF;

END_PROGRAM
