from flask import Blueprint, jsonify, request, send_file

from pixelforge_core import (
    image_compress,
    image_convert,
    image_crop,
    image_merge,
    image_resize,
)
from pixelforge_web.config import VISIBLE_FILE_EXTENSIONS
from pixelforge_web.security import path_error_response, resolve_allowed_path
from pixelforge_web.streaming import stream_task

image_api_bp = Blueprint("image_api", __name__)


@image_api_bp.route("/image-resize", methods=["POST"])
def do_image_resize():
    data = request.get_json() or {}
    folder = data.get("folder")
    file_arg = data.get("file")
    mode = data.get("mode", "percent")
    width = data.get("width", data.get("width_pct"))
    height = data.get("height", data.get("height_pct"))
    if not folder or not file_arg or width is None or height is None:
        return jsonify({"error": "缺少必要参数 (folder, file, width, height)"}), 400
    try:
        folder = str(resolve_allowed_path(folder))
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)
    return stream_task(
        image_resize,
        folder,
        file_arg,
        float(width),
        float(height),
        mode=mode,
        keep_ratio=bool(data.get("keep_ratio", False)),
        no_enlarge=bool(data.get("no_enlarge", False)),
    )


@image_api_bp.route("/image-merge", methods=["POST"])
def do_image_merge():
    data = request.get_json() or {}
    folder = data.get("folder")
    if not folder:
        return jsonify({"error": "缺少 folder 参数"}), 400
    try:
        folder = str(resolve_allowed_path(folder))
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)
    return stream_task(image_merge, folder, data.get("mode", "grid"), bool(data.get("border", False)))


@image_api_bp.route("/image-crop", methods=["POST"])
def do_image_crop():
    data = request.get_json() or {}
    folder = data.get("folder")
    file_arg = data.get("file")
    crop_box = data.get("crop")
    if not folder or not file_arg or not crop_box:
        return jsonify({"error": "缺少必要参数 (folder, file, crop)"}), 400
    try:
        folder = str(resolve_allowed_path(folder))
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)
    return stream_task(image_crop, folder, file_arg, crop_box, data.get("output"))


@image_api_bp.route("/image-convert", methods=["POST"])
def do_image_convert():
    data = request.get_json() or {}
    folder = data.get("folder")
    if not folder:
        return jsonify({"error": "缺少 folder 参数"}), 400
    try:
        folder = str(resolve_allowed_path(folder))
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)
    file_arg = data.get("file") if data.get("scope") == "selected" else None
    return stream_task(image_convert, folder, file_arg, data.get("format", "png"))


@image_api_bp.route("/image-compress", methods=["POST"])
def do_image_compress():
    data = request.get_json() or {}
    folder = data.get("folder")
    if not folder:
        return jsonify({"error": "缺少 folder 参数"}), 400
    try:
        folder = str(resolve_allowed_path(folder))
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)
    file_arg = data.get("file") if data.get("scope") == "selected" else None
    return stream_task(
        image_compress,
        folder,
        file_arg,
        int(data.get("quality", 75)),
        data.get("max_side"),
        data.get("target_kb"),
        bool(data.get("best_quality", False)),
    )


@image_api_bp.route("/image-file", methods=["GET"])
def serve_image_file():
    path = request.args.get("path", "")
    if not path:
        return jsonify({"error": "缺少 path 参数"}), 400
    try:
        p = resolve_allowed_path(path)
    except (PermissionError, OSError) as exc:
        return path_error_response(exc)
    if not p.is_file() or p.suffix.lower() not in VISIBLE_FILE_EXTENSIONS - {".pdf", ".zip"}:
        return jsonify({"error": "文件不存在或不是图片"}), 404
    return send_file(str(p))
