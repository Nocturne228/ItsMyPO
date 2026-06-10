import os
import threading

from flask import Blueprint, jsonify, render_template, request

from pixelforge_core import EXCLUDE_DIRS, open_folder
from pixelforge_web.config import HOME_DIR, VISIBLE_FILE_EXTENSIONS
from pixelforge_web.security import path_error_response, resolve_allowed_path
from pixelforge_web.streaming import capture

main_bp = Blueprint("main", __name__, template_folder="templates", static_folder="static")
api_bp = Blueprint("api", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html", home=HOME_DIR)


@api_bp.route("/browse", methods=["POST"])
def browse():
    data = request.get_json() or {}
    try:
        p = resolve_allowed_path(data.get("path", HOME_DIR))
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)

    if not p.is_dir():
        return jsonify({"error": "无法访问该目录"}), 400

    dirs = []
    files = []
    try:
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.name.startswith("."):
                continue
            if item.is_dir():
                dirs.append({"name": item.name, "path": str(item)})
            else:
                ext = item.suffix.lower()
                if ext not in VISIBLE_FILE_EXTENSIONS:
                    continue
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "ext": ext,
                    "size": item.stat().st_size,
                })
    except PermissionError:
        return jsonify({"error": "权限不足"}), 403

    return jsonify({"path": str(p), "name": p.name or str(p), "dirs": dirs, "files": files})


@api_bp.route("/scan", methods=["POST"])
def scan():
    data = request.get_json() or {}
    try:
        p = resolve_allowed_path(data.get("path", HOME_DIR))
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)

    if not p.is_dir():
        return jsonify({"error": "路径不存在或不是目录"}), 400

    pdfs = []
    zips = []
    for f in sorted(p.rglob("*.pdf")):
        if not any(d in f.parts for d in EXCLUDE_DIRS):
            pdfs.append({"name": f.name, "path": str(f), "rel": str(f.relative_to(p))})
    for f in sorted(p.glob("*.zip")):
        zips.append({"name": f.name, "path": str(f), "rel": str(f.relative_to(p))})

    return jsonify({"path": str(p), "pdfs": pdfs, "zips": zips})


@api_bp.route("/home", methods=["GET"])
def home():
    return jsonify({"home": HOME_DIR})


@api_bp.route("/open-folder", methods=["POST"])
def do_open_folder():
    data = request.get_json() or {}
    folder = data.get("folder")
    if not folder:
        return jsonify({"error": "缺少 folder 参数"}), 400
    try:
        folder = str(resolve_allowed_path(folder))
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)

    success, output = capture(open_folder, folder)
    return jsonify({"success": success, "output": output})


@api_bp.route("/shutdown", methods=["POST"])
def shutdown():
    def do_shutdown():
        os._exit(0)

    threading.Timer(0.5, do_shutdown).start()
    return jsonify({"success": True, "message": "服务正在关闭..."})
