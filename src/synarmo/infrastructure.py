from __future__ import annotations

import os
import sys
from ctypes import CDLL, Structure, byref, c_int, c_uint64, sizeof
from pathlib import Path
from threading import Lock


_nvml_lock = Lock()
_nvml_initialized = False


def collect_infrastructure_diagnostics(
    *,
    model_path: Path | None,
    kv_cache_tokens_current: int | None,
    kv_cache_tokens_max: int | None,
) -> dict[str, object]:
    """Return an on-demand snapshot without touching the inference path."""
    diagnostics: dict[str, object] = {
        "model_file_bytes": _file_size(model_path),
        "model_mapped_resident_ram_bytes": _mapped_resident_ram(model_path),
        "process_resident_ram_bytes": _process_resident_ram(),
        "kv_cache_tokens_current": kv_cache_tokens_current,
        "kv_cache_tokens_max": kv_cache_tokens_max,
        "gpu": _gpu_diagnostics(),
    }
    if kv_cache_tokens_current is not None and kv_cache_tokens_max:
        diagnostics["kv_cache_utilization_pct"] = round(
            kv_cache_tokens_current / kv_cache_tokens_max * 100, 2
        )
    return diagnostics


def _file_size(path: Path | None) -> int | None:
    if path is None:
        return None
    try:
        return path.stat().st_size
    except OSError:
        return None


def _process_resident_ram() -> int | None:
    if sys.platform.startswith("linux"):
        try:
            resident_pages = int(Path("/proc/self/statm").read_text().split()[1])
            return resident_pages * os.sysconf("SC_PAGE_SIZE")
        except (IndexError, OSError, ValueError):
            return None
    if sys.platform == "darwin":
        return _macos_process_resident_ram()
    return None


def _macos_process_resident_ram() -> int | None:
    class ProcessTaskInfo(Structure):
        _fields_ = [
            ("virtual_size", c_uint64),
            ("resident_size", c_uint64),
            ("total_user", c_uint64),
            ("total_system", c_uint64),
            ("threads_user", c_uint64),
            ("threads_system", c_uint64),
            ("policy", c_int),
            ("faults", c_int),
            ("pageins", c_int),
            ("cow_faults", c_int),
            ("messages_sent", c_int),
            ("messages_received", c_int),
            ("syscalls_mach", c_int),
            ("syscalls_unix", c_int),
            ("csw", c_int),
            ("threadnum", c_int),
            ("numrunning", c_int),
            ("priority", c_int),
        ]

    try:
        info = ProcessTaskInfo()
        library = CDLL("/usr/lib/libproc.dylib")
        result = library.proc_pidinfo(
            os.getpid(), 4, 0, byref(info), sizeof(info)
        )
        return int(info.resident_size) if result else None
    except OSError:
        return None


def _mapped_resident_ram(path: Path | None) -> int | None:
    """Return RSS for this GGUF mapping on Linux, where smaps provides it."""
    if path is None or not sys.platform.startswith("linux"):
        return None
    try:
        resolved_path = str(path.resolve())
        total = 0
        mapped_path: str | None = None
        for line in Path("/proc/self/smaps").read_text().splitlines():
            if "-" in line and line[:1].isalnum() and " " in line:
                fields = line.split(maxsplit=5)
                mapped_path = fields[5] if len(fields) == 6 else None
            elif mapped_path == resolved_path and line.startswith("Rss:"):
                total += int(line.split()[1]) * 1024
        return total
    except (OSError, ValueError):
        return None


def _gpu_diagnostics() -> dict[str, object]:
    """Read NVIDIA device and this-process VRAM when NVML is available."""
    try:
        import pynvml
    except ImportError:
        return {"available": False, "reason": "NVML support is not installed"}

    global _nvml_initialized
    try:
        with _nvml_lock:
            if not _nvml_initialized:
                pynvml.nvmlInit()
                _nvml_initialized = True
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        process_memory = _nvml_process_memory(pynvml, handle)
        return {
            "available": True,
            "device_memory_used_bytes": int(memory.used),
            "device_memory_total_bytes": int(memory.total),
            "device_utilization_pct": int(utilization.gpu),
            "process_memory_bytes": process_memory,
        }
    except Exception as exc:
        return {"available": False, "reason": str(exc)}


def _nvml_process_memory(pynvml, handle) -> int | None:
    process_query = getattr(pynvml, "nvmlDeviceGetComputeRunningProcesses", None)
    if process_query is None:
        return None
    try:
        return sum(
            int(process.usedGpuMemory)
            for process in process_query(handle)
            if process.pid == os.getpid() and process.usedGpuMemory >= 0
        )
    except Exception:
        return None
