# IEC 61131-3 ST 语言快速参考

## 基本语法

```st
// 单行注释
(* 多行注释 *)

// 赋值
variable := value;

// 条件
IF condition THEN
    // ...
ELSIF other_condition THEN
    // ...
ELSE
    // ...
END_IF;

// 多分支
CASE selector OF
    0: // ...
    1,2: // ...
ELSE
    // ...
END_CASE;

// 循环
FOR i := 0 TO 10 BY 1 DO
    // ...
END_FOR;

WHILE condition DO
    // ...
END_WHILE;

REPEAT
    // ...
UNTIL condition
END_REPEAT;
```

## 数据类型

| 类型 | 范围 | 说明 |
|------|------|------|
| BOOL | TRUE/FALSE | 布尔 |
| BYTE | 0..255 | 8位 |
| WORD | 0..65535 | 16位 |
| DWORD | 0..2^32-1 | 32位 |
| INT | -32768..32767 | 有符号整数 |
| DINT | -2^31..2^31-1 | 双整数 |
| REAL | 浮点数 | 实数 |
| STRING | 字符串 | 文本 |
| TIME | T# | 时间 |
| DATE | D# | 日期 |

## 定时器

```st
// TON - 接通延时
TON_Instance(IN := trigger, PT := T#2S);
IF TON_Instance.Q THEN
    // 延时到
END_IF;

// TOF - 断开延时
// TP  - 脉冲定时器
```

## 计数器

```st
// CTU - 加计数器
CTU_Instance(CU := pulse, RESET := reset, PV := 100);
IF CTU_Instance.Q THEN
    // 计数到
END_IF;

// CTD - 减计数器
// CTUD - 加减计数器
```

## 程序结构

```st
PROGRAM ProgramName
VAR
    // 变量声明
END_VAR
    // 程序体
END_PROGRAM

FUNCTION_BLOCK FBName
VAR_INPUT
END_VAR
VAR_OUTPUT
END_VAR
    // 功能块体
END_FUNCTION_BLOCK
```

## 常用指令

```st
// 数学
result := ABS(value);     // 绝对值
result := SQRT(value);    // 平方根
result := SIN(angle);     // 正弦

// 比较
IF a > b THEN ... END_IF;
IF a = b THEN ... END_IF;
IF a <> b THEN ... END_IF;  // 不等于

// 逻辑
IF a AND b THEN ... END_IF;
IF a OR b THEN ... END_IF;
IF NOT a THEN ... END_IF;

// 选择
result := SEL(condition, value1, value2);
result := MAX(a, b);
result := MIN(a, b);
result := LIMIT(min, value, max);
```

## 最佳实践

1. **变量命名**：使用有意义的名称，如 `MotorStart`、`ConveyorSpeed`
2. **注释**：关键逻辑必须注释
3. **安全优先**：急停、过载保护放在最前面
4. **状态机**：复杂逻辑用 CASE 实现状态机
5. **避免**：过深的嵌套 IF（超过 3 层考虑重构）
