from flask import jsonify

from pixelforge_web.security import path_error_response, resolve_allowed_path


def json_error(message, status=400):
    return jsonify({"error": message}), status


def resolve_folder_arg(value, missing_message="缺少 folder 参数", invalid_message="路径不存在或不是目录"):
    if not value:
        return None, json_error(missing_message)
    try:
        folder = resolve_allowed_path(value)
    except (PermissionError, OSError) as exc:
        return None, path_error_response(exc)
    if not folder.is_dir():
        return None, json_error(invalid_message)
    return str(folder), None


def resolve_file_arg(value, suffixes, kind_label):
    if not value:
        return None, json_error("缺少 path 参数")
    try:
        path = resolve_allowed_path(value)
    except (PermissionError, OSError) as exc:
        return None, path_error_response(exc)
    allowed = {suffix.lower() for suffix in suffixes}
    if not path.is_file() or path.suffix.lower() not in allowed:
        return None, json_error(f"文件不存在或不是 {kind_label}", 404)
    return path, None
