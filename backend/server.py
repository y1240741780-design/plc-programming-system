"""
PLC编程体系 - Flask Web 服务器
提供 REST API：ST代码生成、平台适配、模板管理、项目管理
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS

# 添加项目根目录到路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from st_generator import STGenerator
from platform_adapter import PlatformAdapter
from template_engine import TemplateEngine
from io_mapper import IOMapper
from doc_generator import DocGenerator
from project_packer import ProjectPacker

app = Flask(__name__, static_folder=str(BASE_DIR / "web"), static_url_path="")
CORS(app)

# 加载配置
with open(BASE_DIR / "配置" / "config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# 初始化引擎
st_gen = STGenerator(CONFIG)
platform_adapter = PlatformAdapter(CONFIG)
template_engine = TemplateEngine(CONFIG, BASE_DIR)
io_mapper = IOMapper(CONFIG)
doc_generator = DocGenerator(CONFIG)
project_packer = ProjectPacker(CONFIG, BASE_DIR)

OUTPUT_DIR = BASE_DIR / "输出"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────
#  首页
# ──────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR / "web"), "index.html")


# ──────────────────────────────────────────────────
#  系统信息
# ──────────────────────────────────────────────────
@app.route("/api/system/info")
def system_info():
    return jsonify({
        "name": CONFIG["system"]["name"],
        "version": CONFIG["system"]["version"],
        "platforms": list(CONFIG["platforms"].keys()),
        "scenarios": CONFIG["scenarios"],
        "status": "running"
    })


# ──────────────────────────────────────────────────
#  平台管理
# ──────────────────────────────────────────────────
@app.route("/api/platforms")
def list_platforms():
    """列出所有支持的平台"""
    platforms = []
    for key, info in CONFIG["platforms"].items():
        platforms.append({
            "id": key,
            "name": info["name"],
            "extension": info["extension"],
            "features": info["features"]
        })
    return jsonify(platforms)


@app.route("/api/platforms/<platform_id>")
def get_platform(platform_id):
    """获取单个平台详情"""
    if platform_id in CONFIG["platforms"]:
        return jsonify(CONFIG["platforms"][platform_id])
    return jsonify({"error": "平台不存在"}), 404


# ──────────────────────────────────────────────────
#  模板管理
# ──────────────────────────────────────────────────
@app.route("/api/templates")
def list_templates():
    """列出所有模板"""
    templates = template_engine.list_templates()
    return jsonify(templates)


@app.route("/api/templates/<scenario>")
def get_scenario_templates(scenario):
    """获取某个场景下的模板"""
    tmpls = template_engine.get_templates_by_scenario(scenario)
    return jsonify(tmpls)


@app.route("/api/templates/<scenario>/<template_name>")
def get_template(scenario, template_name):
    """获取具体模板内容"""
    content = template_engine.load_template(scenario, template_name)
    if content:
        return jsonify({"scenario": scenario, "name": template_name, "content": content})
    return jsonify({"error": "模板不存在"}), 404


# ──────────────────────────────────────────────────
#  ST 代码生成（核心 API）
# ──────────────────────────────────────────────────
@app.route("/api/generate", methods=["POST"])
def generate_st():
    """
    生成 ST 代码
    请求体:
    {
        "platform": "siemens",           // 目标平台
        "scenario": "basic_logic",       // 场景类型
        "template": "motor_start_stop",  // 模板名(可选)
        "params": {                      // 参数
            "program_name": "ConveyorControl",
            "io_points": [...],
            "config": {...}
        },
        "options": {
            "generate_io_map": true,     // 同时生成 IO 映射表
            "generate_docs": true,       // 同时生成文档
            "pack_project": false        // 打包为项目文件
        }
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "请求体不能为空"}), 400

    platform_id = data.get("platform", "generic")
    scenario = data.get("scenario", "basic_logic")
    template_name = data.get("template")
    params = data.get("params", {})
    options = data.get("options", {})

    # 1. 生成 ST 代码
    if template_name:
        st_code = st_gen.generate_from_template(scenario, template_name, params, platform_id)
    else:
        st_code = st_gen.generate_from_params(scenario, params, platform_id)

    # 2. 平台适配
    adapted_code = platform_adapter.adapt(st_code, platform_id, params)

    result = {
        "platform": platform_id,
        "scenario": scenario,
        "code": adapted_code,
        "language": "ST (Structured Text)"
    }

    # 3. IO 映射
    if options.get("generate_io_map"):
        result["io_map"] = io_mapper.generate(adapted_code, platform_id, params)

    # 4. 文档生成
    if options.get("generate_docs"):
        result["docs"] = doc_generator.generate(adapted_code, platform_id, params, result.get("io_map"))

    # 5. 项目打包
    if options.get("pack_project"):
        project_path = project_packer.pack(adapted_code, platform_id, params, result.get("io_map"), result.get("docs"))
        result["project_path"] = project_path

    return jsonify(result)


# ──────────────────────────────────────────────────
#  IO 映射
# ──────────────────────────────────────────────────
@app.route("/api/io-map", methods=["POST"])
def generate_io_map():
    """根据代码和平台生成 IO 映射表"""
    data = request.get_json()
    st_code = data.get("code", "")
    platform_id = data.get("platform", "generic")
    params = data.get("params", {})
    io_map = io_mapper.generate(st_code, platform_id, params)
    return jsonify(io_map)


# ──────────────────────────────────────────────────
#  代码校验
# ──────────────────────────────────────────────────
@app.route("/api/validate", methods=["POST"])
def validate_code():
    """校验 ST 代码语法"""
    data = request.get_json()
    st_code = data.get("code", "")
    platform_id = data.get("platform", "generic")
    result = st_gen.validate(st_code, platform_id)
    return jsonify(result)


# ──────────────────────────────────────────────────
#  项目导出
# ──────────────────────────────────────────────────
@app.route("/api/export", methods=["POST"])
def export_project():
    """导出完整项目包"""
    data = request.get_json()
    st_code = data.get("code", "")
    platform_id = data.get("platform", "generic")
    params = data.get("params", {})
    io_map = data.get("io_map")
    docs = data.get("docs")
    project_path = project_packer.pack(st_code, platform_id, params, io_map, docs)
    return jsonify({"project_path": project_path, "status": "ok"})


# ──────────────────────────────────────────────────
#  文件下载
# ──────────────────────────────────────────────────
@app.route("/api/download/<path:filepath>")
def download_file(filepath):
    """下载生成的文件"""
    full_path = OUTPUT_DIR / filepath
    if full_path.exists():
        return send_file(str(full_path), as_attachment=True)
    return jsonify({"error": "文件不存在"}), 404


# ──────────────────────────────────────────────────
#  项目管理（历史记录）
# ──────────────────────────────────────────────────
PROJECTS_FILE = BASE_DIR / "输出" / "项目索引.json"

def load_projects():
    if PROJECTS_FILE.exists():
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_projects(projects):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)


@app.route("/api/projects")
def list_projects():
    """列出历史项目"""
    return jsonify(load_projects())


@app.route("/api/projects", methods=["POST"])
def save_project():
    """保存项目"""
    data = request.get_json()
    projects = load_projects()
    project = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "name": data.get("name", "未命名"),
        "platform": data.get("platform", "generic"),
        "scenario": data.get("scenario", ""),
        "created": datetime.now().isoformat(),
        "code": data.get("code", ""),
        "params": data.get("params", {}),
        "io_map": data.get("io_map"),
        "docs": data.get("docs")
    }
    projects.append(project)
    save_projects(projects)

    # 也保存单独的 .st 文件
    ext = CONFIG["platforms"].get(data.get("platform", "generic"), {}).get("extension", ".st")
    st_file = OUTPUT_DIR / f"{project['id']}_{project['name']}{ext}"
    with open(st_file, "w", encoding="utf-8") as f:
        f.write(data.get("code", ""))

    project["file_path"] = str(st_file)
    return jsonify(project)


@app.route("/api/projects/<project_id>")
def get_project(project_id):
    """获取单个项目"""
    projects = load_projects()
    for p in projects:
        if p["id"] == project_id:
            return jsonify(p)
    return jsonify({"error": "项目不存在"}), 404


# ──────────────────────────────────────────────────
#  启动
# ──────────────────────────────────────────────────
if __name__ == "__main__":
    port = CONFIG["system"]["port"]
    print(f"🔌 PLC编程体系 v{CONFIG['system']['version']}")
    print(f"🌐 Web界面: http://localhost:{port}")
    print(f"📡 API接口: http://localhost:{port}/api/")
    print(f"📋 支持平台: {', '.join(CONFIG['platforms'].keys())}")
    app.run(host=CONFIG["system"]["host"], port=port, debug=True)
