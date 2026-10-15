"""Windows CPU-test isolation: assign a suspended worker before it can fork."""
import ctypes
from ctypes import wintypes


class WindowsJob:
    def __init__(self, process):
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateJobObjectW.restype=wintypes.HANDLE
        self.api.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]
        self.api.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
        self.api.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p]
        self.api.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT]
        self.api.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
        self.api.CloseHandle.argtypes=[wintypes.HANDLE]
        self.handle=self.api.CreateJobObjectW(None,None)
        class BasicLimits(ctypes.Structure):
            _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),
                ('flags',wintypes.DWORD),('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),
                ('active',wintypes.DWORD),('affinity',ctypes.c_size_t),
                ('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
        class ExtendedLimits(ctypes.Structure):
            _fields_=[('basic',BasicLimits),('io',ctypes.c_ulonglong*6),('memory',ctypes.c_size_t*4)]
        limits=ExtendedLimits()
        limits.basic.flags=0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if self.handle and not self.api.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            process.kill()
            raise ctypes.WinError(ctypes.get_last_error())
        if not self.handle or not self.api.AssignProcessToJobObject(self.handle,int(process._handle)):
            process.kill()
            raise ctypes.WinError(ctypes.get_last_error())
        # subprocess closes its primary thread handle; psutil resumes the process.
        import psutil
        psutil.Process(process.pid).resume()

    def active(self):
        class Accounting(ctypes.Structure):
            _fields_=[('timers',ctypes.c_longlong*4),('page_faults',wintypes.DWORD),
                      ('total',wintypes.DWORD),('active',wintypes.DWORD),('terminated',wintypes.DWORD)]
        data=Accounting()
        if not self.api.QueryInformationJobObject(self.handle,1,ctypes.byref(data),ctypes.sizeof(data),None):
            raise ctypes.WinError(ctypes.get_last_error())
        return data.active

    def terminate(self):
        if not self.api.TerminateJobObject(self.handle,1):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle=None
