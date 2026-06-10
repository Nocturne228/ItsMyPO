import io

from flask import Blueprint, jsonify, request, send_file
from pypdf import PdfReader

from pixelforge_core import (
    OperationResult,
    clean_image_outputs,
    clean_page_backups,
    clean_resize_backups,
    clean_zip_files,
    crop_png,
    delete_file,
    delete_folder,
    extract_pdf,
    extract_png,
    get_pdf_metadata,
    render_page_image,
    resize_file,
    resize_folder,
    resolve_dpi,
    update_pdf_metadata,
    zip_file,
    zip_folder,
)
from pixelforge_web.route_helpers import json_error, resolve_file_arg, resolve_folder_arg
from pixelforge_web.streaming import stream_task

pdf_api_bp = Blueprint("pdf_api", __name__)


@pdf_api_bp.route("/resize", methods=["POST"])
def do_resize():
    data = request.get_json() or {}
    folder, error = resolve_folder_arg(data.get("folder"))
    if error:
        return error

    file_arg = data.get("file")
    width = float(data.get("width", 210))
    height = float(data.get("height", 297))
    strip = bool(data.get("strip", False))

    def run():
        if file_arg:
            return resize_file(folder, file_arg, width, height, strip)
        return resize_folder(folder, width, height, strip)

    return stream_task(run)


@pdf_api_bp.route("/delete", methods=["POST"])
def do_delete():
    data = request.get_json() or {}
    folder, error = resolve_folder_arg(data.get("folder"))
    if error:
        return error

    file_arg = data.get("file")
    single = int(data["single"]) if data.get("single") is not None else None
    range_count = int(data["range"]) if data.get("range") is not None else None
    range_start = int(data["range_start"]) if data.get("range_start") is not None else None
    range_end = int(data["range_end"]) if data.get("range_end") is not None else None
    from_back = bool(data.get("back", False))

    if single is None and range_count is None and (range_start is None or range_end is None):
        return json_error("请指定删除模式和页码参数")

    def run():
        if file_arg:
            return delete_file(folder, file_arg, single, range_count, range_start, range_end, from_back)
        return delete_folder(folder, single, range_count, range_start, range_end, from_back)

    return stream_task(run)


@pdf_api_bp.route("/extract-png", methods=["POST"])
def do_extract_png():
    data = request.get_json() or {}
    folder = data.get("folder")
    file_arg = data.get("file")
    page = data.get("page")

    if not folder or not file_arg or page is None:
        return json_error("缺少必要参数 (folder, file, page)")
    folder, error = resolve_folder_arg(folder)
    if error:
        return error

    dpi = resolve_dpi(data.get("dpi_mode", "bw"))
    output_arg = data.get("output")

    return stream_task(extract_png, folder, file_arg, int(page), output_arg, dpi=dpi)


@pdf_api_bp.route("/extract-pdf", methods=["POST"])
def do_extract_pdf():
    data = request.get_json() or {}
    folder = data.get("folder")
    file_arg = data.get("file")
    start = data.get("start")
    end = data.get("end")

    if not folder or not file_arg or start is None or end is None:
        return json_error("缺少必要参数 (folder, file, start, end)")
    folder, error = resolve_folder_arg(folder)
    if error:
        return error

    output_arg = data.get("output")

    return stream_task(extract_pdf, folder, file_arg, int(start), int(end), output_arg)


@pdf_api_bp.route("/crop-png", methods=["POST"])
def do_crop_png():
    data = request.get_json() or {}
    folder = data.get("folder")
    file_arg = data.get("file")
    page = data.get("page")
    crop_box = data.get("crop")

    if not folder or not file_arg or page is None or not crop_box:
        return json_error("缺少必要参数 (folder, file, page, crop)")
    folder, error = resolve_folder_arg(folder)
    if error:
        return error

    dpi = int(data.get("dpi", 300))
    output_arg = data.get("output")

    return stream_task(crop_png, folder, file_arg, int(page), crop_box, output_arg, dpi=dpi)


@pdf_api_bp.route("/pdf-metadata", methods=["POST"])
def pdf_metadata():
    data = request.get_json() or {}
    folder = data.get("folder")
    file_arg = data.get("file")
    if not folder or not file_arg:
        return json_error("缺少必要参数 (folder, file)")
    folder, error = resolve_folder_arg(folder)
    if error:
        return error
    try:
        return jsonify(get_pdf_metadata(folder, file_arg))
    except Exception as exc:
        return json_error(str(exc))


@pdf_api_bp.route("/pdf-metadata-save", methods=["POST"])
def save_pdf_metadata():
    data = request.get_json() or {}
    folder = data.get("folder")
    file_arg = data.get("file")
    metadata = data.get("metadata")
    if not folder or not file_arg or metadata is None:
        return json_error("缺少必要参数 (folder, file, metadata)")
    folder, error = resolve_folder_arg(folder)
    if error:
        return error
    return stream_task(update_pdf_metadata, folder, file_arg, metadata)


@pdf_api_bp.route("/zip2pdf", methods=["POST"])
def do_zip2pdf():
    data = request.get_json() or {}
    folder, error = resolve_folder_arg(data.get("folder"))
    if error:
        return error

    file_arg = data.get("file")
    dpi = resolve_dpi(data.get("dpi_mode", "bw"))

    def run():
        if file_arg:
            return zip_file(folder, file_arg, dpi=dpi)
        return zip_folder(folder, dpi=dpi)

    return stream_task(run)


@pdf_api_bp.route("/clean", methods=["POST"])
def do_clean():
    data = request.get_json() or {}
    folder = data.get("folder")
    clean_type = data.get("type", "backup_resize")

    if not folder:
        return json_error("缺少 folder 参数")
    if clean_type not in {"backup_resize", "backup_page_ops", "zip", "output_images", "all"}:
        return json_error("未知清理类型")
    folder, error = resolve_folder_arg(folder)
    if error:
        return error

    def run():
        if clean_type == "backup_resize":
            return clean_resize_backups(folder)
        elif clean_type == "backup_page_ops":
            return clean_page_backups(folder)
        elif clean_type == "zip":
            return clean_zip_files(folder)
        elif clean_type == "output_images":
            return clean_image_outputs(folder)
        elif clean_type == "all":
            result = OperationResult()
            for clean_func in (
                clean_resize_backups,
                clean_page_backups,
                clean_zip_files,
                clean_image_outputs,
            ):
                item = clean_func(folder)
                if isinstance(item, OperationResult):
                    result.total += item.total
                    result.success += item.success
                    result.skipped += item.skipped
                    result.failed += item.failed
                    result.outputs.extend(item.outputs)
            return result

    return stream_task(run)


@pdf_api_bp.route("/pdf-file", methods=["GET"])
def serve_pdf_file():
    path = request.args.get("path", "")
    p, error = resolve_file_arg(path, {".pdf"}, "PDF")
    if error:
        return error

    return send_file(str(p), mimetype="application/pdf")


@pdf_api_bp.route("/page-image", methods=["GET"])
def serve_page_image():
    path = request.args.get("path", "")
    page = request.args.get("page", "1")
    dpi = request.args.get("dpi", "150")
    p, error = resolve_file_arg(path, {".pdf"}, "PDF")
    if error:
        return error

    try:
        root = str(p.parent)
        image = render_page_image(root, str(p), int(page), dpi=int(dpi))
        buf = io.BytesIO()
        image.save(buf, "PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")
    except Exception as exc:
        return json_error(str(exc))


@pdf_api_bp.route("/pdf-info", methods=["POST"])
def pdf_info():
    data = request.get_json() or {}
    path = data.get("path", "")
    p, error = resolve_file_arg(path, {".pdf"}, "PDF")
    if error:
        return error

    try:
        reader = PdfReader(str(p))
        total_pages = len(reader.pages)
        if total_pages > 0:
            page = reader.pages[0]
            w = round(float(page.mediabox.width) / 2.83465, 1)
            h = round(float(page.mediabox.height) / 2.83465, 1)
        else:
            w, h = 0, 0

        return jsonify({
            "name": p.name,
            "path": str(p),
            "pages": total_pages,
            "width_mm": w,
            "height_mm": h,
            "size": p.stat().st_size,
        })
    except Exception as exc:
        return json_error(str(exc), 500)
