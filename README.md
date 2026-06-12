# PLC 编程体系 — Hermes Agent 驱动

> 基于 IEC 61131-3 标准的 ST（结构化文本）PLC 程序生成体系  
> 支持 Siemens / Beckhoff / CODESYS / Allen-Bradley / Mitsubishi / Omron 多平台

## 🎯 核心功能

- ⚡ **ST 代码生成**：从需求描述自动生成 IEC 61131-3 结构化文本程序
- 🔌 **多平台适配**：Siemens (.scl)、Beckhoff (.TcPOU)、CODESYS (.exp)、AB (.L5X) 等
- 📋 **模板库**：内置 9+ 个常用模板（启停/互锁/状态机/PID/传送带/伺服/HVAC/泵站/Modbus）
- 📊 **IO 映射**：自动提取 IO 点，生成输入输出映射表
- 📄 **文档生成**：自动生成功能说明、IO 清单、变量表
- 📦 **项目打包**：按平台格式打包完整项目文件
- 💬 **Hermes 对话驱动**：在聊天中分步交互式生成程序
- 🌐 **Web 界面**：Neon Protocol 暗色风格前端

## 🚀 快速启动

```bash
cd D:\fanben\PLC编程体系
python backend/server.py
# Web 界面: http://localhost:5001
```

## 📂 项目结构

```
PLC编程体系/
├── backend/              # Python 后端引擎
│   ├── server.py         # Flask Web 服务器
│   ├── st_generator.py   # ST 代码生成引擎（核心）
│   ├── platform_adapter.py  # 多平台适配器
│   ├── template_engine.py   # 模板管理引擎
│   ├── io_mapper.py         # IO 映射表生成
│   ├── doc_generator.py     # 文档自动生成
│   └── project_packer.py    # 项目打包导出
├── web/
│   └── index.html           # Web 前端界面
├── 技能/
│   └── plc-st-generator.md  # Hermes Agent 技能
├── 模板/                    # ST 程序模板库（7大场景）
├── 知识库/                  # IEC 61131-3 / 平台差异 / 最佳实践
├── 配置/
│   └── config.json          # 系统配置
└── 输出/                    # 生成的程序和文档
```

## 🖥️ API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/generate` | POST | 生成 ST 代码 |
| `/api/validate` | POST | 语法校验 |
| `/api/templates` | GET | 模板列表 |
| `/api/platforms` | GET | 支持的平台 |
| `/api/projects` | GET/POST | 项目管理 |
| `/api/export` | POST | 项目导出 |

## 📋 支持平台

| 平台 | 扩展名 | IO 格式 |
|------|--------|---------|
| Siemens TIA Portal | `.scl` | `%I0.0` / `%Q0.0` |
| Beckhoff TwinCAT | `.TcPOU` | `AT %I*` / `AT %Q*` |
| CODESYS 通用 | `.exp` | `AT %I*` / `AT %Q*` |
| Allen-Bradley | `.L5X` | 标签体系 |
| Mitsubishi GX Works | `.st` | `X0` / `Y0` |
| Omron Sysmac | `.st` | `%地址` |

## 🔗 技术栈

- **后端**: Python 3.11 + Flask + flask-cors
- **前端**: HTML5 + Tailwind CSS + Vanilla JS
- **驱动**: Hermes Agent (Nous Research)
- **标准**: IEC 61131-3 ST
