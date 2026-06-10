import tempfile
import unittest
import zipfile
from importlib.util import find_spec
from pathlib import Path

from pixelforge_core.pdf.zip_convert import _safe_extract
from pixelforge_core.pdf.page_ops import delete_folder

if find_spec("flask"):
    from pixelforge_web import create_app
    from pixelforge_web.route_helpers import resolve_file_arg, resolve_folder_arg
    from pixelforge_web.streaming import StreamBuf
else:
    create_app = None
    resolve_file_arg = None
    resolve_folder_arg = None
    StreamBuf = None


class SafetyTests(unittest.TestCase):
    def test_safe_extract_blocks_paths_outside_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "payload.zip"
            out_dir = root / "out"

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("../outside.txt", "bad")
                zf.writestr("images/page1.jpg", "ok")

            _safe_extract(zip_path, out_dir)

            self.assertFalse((root / "outside.txt").exists())
            self.assertEqual((out_dir / "images" / "page1.jpg").read_text(), "ok")

    def test_delete_requires_an_explicit_page_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                delete_folder(tmp)

    @unittest.skipIf(StreamBuf is None, "Flask is not installed")
    def test_stream_buffer_marks_carriage_return_as_replaceable(self):
        buf = StreamBuf()
        buf.write("生成进度: 10%\r")
        buf.write("PDF 生成完成\n")

        self.assertEqual(buf.q.get_nowait(), {"line": "生成进度: 10%", "replace": True})
        self.assertEqual(buf.q.get_nowait(), {"line": "PDF 生成完成", "replace": False})

    @unittest.skipIf(create_app is None, "Flask is not installed")
    def test_route_helpers_validate_allowed_paths_and_file_types(self):
        app = create_app()
        with app.app_context(), tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            root = Path(tmp)
            image = root / "sample.png"
            image.write_bytes(b"not a real image")

            folder, folder_error = resolve_folder_arg(str(root))
            self.assertIsNone(folder_error)
            self.assertEqual(folder, str(root.resolve()))

            file_path, file_error = resolve_file_arg(str(image), {".png"}, "图片")
            self.assertIsNone(file_error)
            self.assertEqual(file_path, image.resolve())

            _, mismatch_error = resolve_file_arg(str(image), {".pdf"}, "PDF")
            self.assertIsNotNone(mismatch_error)


if __name__ == "__main__":
    unittest.main()
