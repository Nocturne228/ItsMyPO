import io
import json
import queue
import threading
from contextlib import redirect_stdout

from flask import Response

from pixelforge_core import OperationResult

_SENTINEL = object()


def _result_success(result):
    if isinstance(result, OperationResult):
        return result.ok
    return result is not False


def _result_payload(result):
    if not isinstance(result, OperationResult):
        return None
    return {
        "total": result.total,
        "success": result.success,
        "skipped": result.skipped,
        "failed": result.failed,
        "outputs": [str(p) for p in result.outputs],
    }


class StreamBuf:
    """Thread-safe stdout capture.

    Newline output is appended as normal log lines. Carriage-return output is
    sent as a replaceable line so browser logs can update progress in place.
    """

    def __init__(self):
        self.q = queue.Queue()
        self._buf = ""

    def write(self, s):
        if not s:
            return
        for char in s:
            if char == "\r":
                line = self._buf.strip()
                if line:
                    self.q.put({"line": line, "replace": True})
                self._buf = ""
            elif char == "\n":
                line = self._buf.strip()
                if line:
                    self.q.put({"line": line, "replace": False})
                self._buf = ""
            else:
                self._buf += char

    def flush(self):
        if self._buf.strip():
            self.q.put({"line": self._buf.strip(), "replace": False})
            self._buf = ""


def stream_task(func, *args, **kwargs):
    """Run func in a background thread, streaming its stdout as SSE events."""
    buf = StreamBuf()

    def worker():
        try:
            with redirect_stdout(buf):
                result = func(*args, **kwargs)
                success = _result_success(result)
        except Exception as e:
            buf.write(f"[错误] {e}\n")
            success = False
            result = None
        buf.flush()
        buf.q.put(_SENTINEL)
        buf.success = success
        buf.result = _result_payload(result)

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    def generate():
        while True:
            try:
                item = buf.q.get(timeout=120)
            except queue.Empty:
                yield f"data: {json.dumps({'line': '[超时] 操作超时'}, ensure_ascii=False)}\n\n"
                break
            if item is _SENTINEL:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

        t.join(timeout=1)
        yield f"data: {json.dumps({'done': True, 'success': getattr(buf, 'success', False), 'result': getattr(buf, 'result', None)}, ensure_ascii=False)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


def capture(func, *args, **kwargs):
    """Non-streaming capture for simple endpoints."""
    buf = io.StringIO()
    success = True
    try:
        with redirect_stdout(buf):
            result = func(*args, **kwargs)
            if not _result_success(result):
                success = False
    except Exception as e:
        buf.write(f"\n[错误] {e}\n")
        success = False
    return success, buf.getvalue()
