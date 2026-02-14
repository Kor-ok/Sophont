from __future__ import annotations

import multiprocessing
import os
import platform
import sys
from typing import Any

import numpy as np
from colorama import Style
from colorama import init as colorama_init
from pympler.asizeof import asizeof

CACHE_SIZES: dict[int, int] = {
    1: 32768,   # L1 cache size in bytes (for my system=32768)
    2: 524288,  # L2 cache size in bytes (for my system=524288)
    3: 33554432,  # L3 cache size in bytes (for my system=33554432)
}

colorama_init(autoreset=True, convert=True)  # Initialize colorama for colored output in the terminal

def _format_bytes(n: int) -> str:
    if n is None:
        return "unknown"
    else:
        if n < 1024:
            return f"{n} B"
        elif n < 1024**2:
            return f"{n / 1024:.0f} KB"
        else:
            return f"{n / 1024:,.0f} KB"

def get_cache_info() -> None:
	"""Return cache sizes in bytes for L1, L2, L3 where available."""
	system = platform.system()
	if system == "Windows":
		_get_cache_info_windows()
	else:
		raise NotImplementedError(f"Cache info retrieval not implemented for {system}")

def _get_cache_info_windows() -> None:
    try:
        import ctypes
        from ctypes import POINTER, byref, cast, create_string_buffer, sizeof

        DWORD = ctypes.c_uint32
        ULONG_PTR = ctypes.c_size_t
        class CACHE_DESCRIPTOR(ctypes.Structure):
            _fields_ = [
                ("Level", ctypes.c_ubyte),
                ("Associativity", ctypes.c_ubyte),
                ("LineSize", ctypes.c_ushort),
                ("Size", ctypes.c_uint32),
                ("Type", ctypes.c_uint32),
            ]

        class PROCESSORCORE(ctypes.Structure):
            _fields_ = [("Flags", ctypes.c_ubyte)]

        class NUMANODE(ctypes.Structure):
            _fields_ = [("NodeNumber", ctypes.c_uint32)]

        class _U(ctypes.Union):
            _fields_ = [
                ("ProcessorCore", PROCESSORCORE),
                ("NumaNode", NUMANODE),
                ("Cache", CACHE_DESCRIPTOR),
                ("Reserved", ctypes.c_ulonglong * 2),
            ]

        class SYSTEM_LOGICAL_PROCESSOR_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("ProcessorMask", ULONG_PTR),
                ("Relationship", ctypes.c_uint32),
                ("u", _U),
            ]

        GetLogicalProcessorInformation = ctypes.windll.kernel32.GetLogicalProcessorInformation
        buffer_size = ctypes.c_ulong(0)
        # First call to get required buffer size
        res = GetLogicalProcessorInformation(None, byref(buffer_size))
        # Allocate buffer
        buf = create_string_buffer(buffer_size.value)
        res = GetLogicalProcessorInformation(buf, byref(buffer_size))
        if not res:
            raise ctypes.WinError()
        entry_size = sizeof(SYSTEM_LOGICAL_PROCESSOR_INFORMATION)
        count = int(buffer_size.value // entry_size)
        array_type = SYSTEM_LOGICAL_PROCESSOR_INFORMATION * count
        entries = cast(buf, POINTER(array_type)).contents
        RELATION_CACHE = 2
        for entry in entries:
            if entry.Relationship == RELATION_CACHE:
                level = int(entry.u.Cache.Level)
                size = int(entry.u.Cache.Size)
                if level in (1, 2, 3) and size is not None:
                    CACHE_SIZES[level] = size
    except Exception:
        raise RuntimeError("Failed to retrieve cache information on Windows")

def display_system_info(recompute: bool, sanity_test_object: Any) -> None:
    print(f"Number of CPUs: {multiprocessing.cpu_count()}")
    print(f"Number of CPUs available to this process: {os.cpu_count()}")
    if recompute:
        get_cache_info()
    print("CPU Cache Sizes:")
    print(f"- L1: {_format_bytes(CACHE_SIZES.get(1, -1))}")
    print(f"- L2: {_format_bytes(CACHE_SIZES.get(2, -1))}")
    print(f"- L3: {_format_bytes(CACHE_SIZES.get(3, -1))}")

    print("\n---------------SANITY CHECKS---------------")
    print(f"For an integer value of {Style.BRIGHT}{sanity_test_object}:")
    print(f"Native CPython object size: {Style.BRIGHT}{sys.getsizeof(sanity_test_object)} bytes")           # native CPython object size
    print(f"Deep size pympler reports: {Style.BRIGHT}{asizeof.asizeof(sanity_test_object)} bytes")             # deep size pympler reports
    print(f"Numpy 8-bit Int scalar footprint (wrapper+payload): {Style.BRIGHT}{asizeof.asizeof(np.int8(sanity_test_object))} bytes")   # numpy scalar footprint (wrapper+payload)
    print(f"Numpy 8-bit Int Payload size: {Style.BRIGHT}{np.int8(sanity_test_object).itemsize} bytes")           # payload size: 1
    print("--------------------------------------------")