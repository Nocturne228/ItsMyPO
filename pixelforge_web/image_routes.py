from flask import Blueprint, request, send_file

from pixelforge_core import (
    image_compress,
    image_convert,
    image_crop,
    image_merge,
    image_resize,
)
from pixelforge_web.config import VISIBLE_FILE_EXTENSIONS
from pixelforge_web.route_helpers import json_error, resolve_file_arg, resolve_folder_arg
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
        return json_error("缺少必要参数 (folder, file, width, height)")
    folder, error = resolve_folder_arg(folder)
    if error:
        return error
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
    folder, error = resolve_folder_arg(data.get("folder"))
    if error:
        return error
    return stream_task(image_merge, folder, data.get("mode", "grid"), bool(data.get("border", False)))


@image_api_bp.route("/image-crop", methods=["POST"])
def do_image_crop():
    data = request.get_json() or {}
    folder = data.get("folder")
    file_arg = data.get("file")
    crop_box = data.get("crop")
    if not folder or not file_arg or not crop_box:
        return json_error("缺少必要参数 (folder, file, crop)")
    folder, error = resolve_folder_arg(folder)
    if error:
        return error
    return stream_task(image_crop, folder, file_arg, crop_box, data.get("output"))


@image_api_bp.route("/image-convert", methods=["POST"])
def do_image_convert():
    data = request.get_json() or {}
    folder, error = resolve_folder_arg(data.get("folder"))
    if error:
        return error
    file_arg = data.get("file") if data.get("scope") == "selected" else None
    return stream_task(image_convert, folder, file_arg, data.get("format", "png"))


@image_api_bp.route("/image-compress", methods=["POST"])
def do_image_compress():
    data = request.get_json() or {}
    folder, error = resolve_folder_arg(data.get("folder"))
    if error:
        return error
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
    p, error = resolve_file_arg(path, VISIBLE_FILE_EXTENSIONS - {".pdf", ".zip"}, "图片")
    if error:
        return error
    return send_file(str(p))
