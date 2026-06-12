// @description: 电机启停控制（带自锁）
// @platform: siemens, beckhoff, codesys, generic
// @tags: 启停, 电机, 自锁

PROGRAM MotorStartStop
VAR
    StartButton AT %I0.0 : BOOL;    // 启动按钮（常开）
    StopButton  AT %I0.1 : BOOL;    // 停止按钮（常闭）
    Overload    AT %I0.2 : BOOL;    // 热过载保护
    MotorOutput AT %Q0.0 : BOOL;    // 电机输出
    RunFeedback AT %I0.3 : BOOL;    // 运行反馈
    Running     : BOOL := FALSE;    // 运行状态
    StartDelay  : TON;              // 启动延时定时器
END_VAR

// 启动延时（防抖动）
StartDelay(IN := StartButton AND NOT StopButton, PT := T#500MS);

// 启动逻辑
IF StartDelay.Q AND NOT Overload THEN
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
    // TODO: 反馈异常处理
END_IF;

END_PROGRAM
