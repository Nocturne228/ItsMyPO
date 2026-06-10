from pathlib import Path

from flask import jsonify

from pixelforge_web.config import ALLOWED_ROOTS, HOME_DIR


def resolve_allowed_path(path):
    p = Path(path or HOME_DIR).expanduser().resolve()
    for root in ALLOWED_ROOTS:
        try:
            p.relative_to(root)
            return p
        except ValueError:
            continue
    roots = "、".join(str(root) for root in ALLOWED_ROOTS)
    raise PermissionError(f"路径不在允许访问范围内: {p}。允许范围: {roots}")


def path_error_response(exc):
    status = 403 if isinstance(exc, PermissionError) else 400
    return jsonify({"error": str(exc)}), status
