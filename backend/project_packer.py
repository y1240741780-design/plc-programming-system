"""
项目打包器 — 将 ST 代码和相关文档打包为平台工程文件
支持：纯 ST 导出、平台特定格式、完整项目文件夹
"""
import os
import shutil
from datetime import datetime
from pathlib import Path


class ProjectPacker:
    """PLC 项目打包导出"""

    def __init__(self, config: dict, base_dir: Path):
        self.config = config
        self.base_dir = base_dir
        self.output_dir = base_dir / "输出"

    def pack(self, st_code: str, platform_id: str, params: dict,
             io_map: dict = None, docs: dict = None) -> str:
        """
        打包完整项目
        返回项目目录路径
        """
        platform = self.config["platforms"].get(platform_id, {})
        ext = platform.get("extension", ".st")
        program_name = params.get("program_name", "MainProgram")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 创建项目目录
        project_dir = self.output_dir / f"{timestamp}_{program_name}"
        project_dir.mkdir(parents=True, exist_ok=True)

        # 1. 保存 ST 源文件
        st_file = project_dir / f"{program_name}{ext}"
        st_file.write_text(st_code, encoding="utf-8")

        # 2. 保存通用 .st 文件（方便跨平台查看）
        if ext != ".st":
            generic_st = project_dir / f"{program_name}.st"
            generic_st.write_text(st_code, encoding="utf-8")

        # 3. 保存 IO 映射表
        if io_map:
            from io_mapper import IOMapper
            mapper = IOMapper(self.config)
            csv_path = project_dir / f"{program_name}_IO清单.csv"
            csv_path.write_text(mapper.export_to_csv(io_map), encoding="utf-8-sig")

            json_path = project_dir / f"{program_name}_IO映射.json"
            json_path.write_text(mapper.export_to_json(io_map), encoding="utf-8")

        # 4. 保存文档
        if docs:
            readme = project_dir / "README.md"
            readme.write_text(docs.get("full_document", ""), encoding="utf-8")

            io_doc = project_dir / f"{program_name}_IO清单.md"
            io_list = docs.get("io_list", "")
            if io_list:
                io_doc.write_text(io_list, encoding="utf-8")

            func_doc = project_dir / f"{program_name}_功能说明.md"
            func_desc = docs.get("function_description", "")
            if func_desc:
                func_doc.write_text(func_desc, encoding="utf-8")

        # 5. 平台特定文件
        self._pack_platform_specific(project_dir, platform_id, st_code, params)

        # 6. 生成项目清单
        manifest = {
            "program_name": program_name,
            "platform": platform_id,
            "created": datetime.now().isoformat(),
            "generator": f"Hermes Agent PLC编程体系 v{self.config['system']['version']}",
            "files": [f.name for f in project_dir.iterdir() if f.is_file()]
        }
        import json
        (project_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return str(project_dir)

    def _pack_platform_specific(self, project_dir: Path, platform_id: str, st_code: str, params: dict):
        """打包平台特定文件"""
        if platform_id == "siemens":
            self._pack_siemens(project_dir, st_code, params)
        elif platform_id == "beckhoff":
            self._pack_beckhoff(project_dir, st_code, params)
        elif platform_id == "allen_bradley":
            self._pack_allen_bradley(project_dir, st_code, params)

    def _pack_siemens(self, project_dir: Path, st_code: str, params: dict):
        """Siemens TIA Portal 项目结构"""
        src_dir = project_dir / "Sources"
        src_dir.mkdir(exist_ok=True)

        # SCL 源文件
        program_name = params.get("program_name", "MainProgram")
        scl_file = src_dir / f"{program_name}.scl"
        scl_file.write_text(st_code, encoding="utf-8")

        # 导入说明
        notes = project_dir / "TIA_Portal_导入说明.txt"
        notes.write_text(
            "TIA Portal 导入步骤:\n"
            "1. 打开 TIA Portal 项目\n"
            "2. 在程序块文件夹中，右键 → '添加新外部源文件'\n"
            "3. 选择 Sources 文件夹中的 .scl 文件\n"
            "4. 右键源文件 → '从源生成块'\n",
            encoding="utf-8"
        )

    def _pack_beckhoff(self, project_dir: Path, st_code: str, params: dict):
        """Beckhoff TwinCAT 项目结构"""
        pou_dir = project_dir / "POUs"
        pou_dir.mkdir(exist_ok=True)

        program_name = params.get("program_name", "MainProgram")
        pou_file = pou_dir / f"{program_name}.TcPOU"
        pou_file.write_text(st_code, encoding="utf-8")

    def _pack_allen_bradley(self, project_dir: Path, st_code: str, params: dict):
        """Allen-Bradley Studio 5000 项目"""
        routines_dir = project_dir / "Routines"
        routines_dir.mkdir(exist_ok=True)

        program_name = params.get("program_name", "MainProgram")
        routine_file = routines_dir / f"{program_name}.L5X"
        routine_file.write_text(st_code, encoding="utf-8")

        # 标签导入文件
        tags_file = project_dir / "Tags.csv"
        tags_file.write_text(
            "Name,Type,Description\n"
            "# 请在 Studio 5000 中导入此标签表\n",
            encoding="utf-8"
        )

    def export_single_file(self, st_code: str, platform_id: str, output_path: str = None) -> str:
        """导出单个 ST 文件"""
        ext = self.config["platforms"].get(platform_id, {}).get("extension", ".st")
        if not output_path:
            output_path = str(self.output_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(st_code)

        return output_path
