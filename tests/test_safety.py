import tempfile
import unittest
import zipfile
from importlib.util import find_spec
from pathlib import Path

from pixelforge_core.pdf.zip_convert import _safe_extract
from pixelforge_core.pdf.page_ops import delete_folder

if find_spec("flask"):
    from pixelforge_web.streaming import StreamBuf
else:
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


if __name__ == "__main__":
    unittest.main()
