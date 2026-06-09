import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OperationResult:
    total: int = 0
    success: int = 0
    skipped: int = 0
    failed: int = 0
    corrupted: list = field(default_factory=list)
    outputs: list[Path] = field(default_factory=list)

    @property
    def ok(self):
        return self.failed == 0


def open_folder(folder_path):
    path = Path(folder_path).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"目录不存在: {path}")
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=True)
    elif sys.platform == "win32":
        subprocess.run(["explorer", str(path)], check=True)
    else:
        subprocess.run(["xdg-open", str(path)], check=True)
    print(f"已打开: {path}", flush=True)


def resolve_pdf_file(root, file_arg, exclude_dirs):
    if not file_arg:
        raise ValueError("需要指定 --file")
    root = Path(root).expanduser().resolve()
    candidate = Path(file_arg).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("PDF 文件必须位于目标文件夹内") from exc
    if not candidate.is_file() or candidate.suffix.lower() != ".pdf":
        raise FileNotFoundError(f"PDF 文件不存在: {candidate}")
    if any(d in candidate.parts for d in exclude_dirs):
        raise ValueError("不能处理备份目录中的 PDF 文件")
    return candidate


def resolve_output_path(root, pdf_path, output_arg, default_name):
    if not output_arg:
        return pdf_path.with_name(default_name)
    root = Path(root).expanduser().resolve()
    output = Path(output_arg).expanduser()
    if not output.is_absolute():
        output = pdf_path.parent / output
    output = output.resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise ValueError("输出路径必须位于目标文件夹内") from exc
    return output


def resolve_dpi(mode, presets):
    if mode not in presets:
        raise ValueError(f"未知 DPI 模式: {mode}")
    return presets[mode]
