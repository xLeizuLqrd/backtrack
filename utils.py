import os
import ctypes
import sys
import subprocess
import shutil
import json
from pathlib import Path
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
def is_admin():
    try:
        return ctypes.windll.shell.IsUserAnAdmin()
    except:
        return False
def is_system_folder(file_path: str) -> bool:
    system_folders = [
        os.path.expandvars("%WINDIR%").lower(),
        os.path.expandvars("%ProgramFiles%").lower(),
        os.path.expandvars("%ProgramFiles(x86)%").lower(),
        "c:\\windows",
        "c:\\program files",
    ]
    file_path_lower = os.path.abspath(file_path).lower()
    return any(file_path_lower.startswith(folder) for folder in system_folders)
def get_file_size(file_path: str) -> int:
    try:
        return os.path.getsize(file_path)
    except:
        return 0
def copy_and_pad_file(source: str, target: str, target_size: int) -> bool:
    try:
        shutil.copy2(source, target)
        current_size = get_file_size(target)
        if current_size < target_size:
            bytes_to_add = target_size - current_size
            with open(target, 'ab') as f:
                f.write(b'\x00' * bytes_to_add)
        return True
    except:
        return False
def create_wrapper_config(original_exe: str, target_exe: str) -> bool:
    try:
        config_dir = os.path.dirname(original_exe)
        config_file = os.path.join(config_dir, "wrapper_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({"target_exe": target_exe}, f)      
        return True
    except:
        return False
def replace_exe_file(original_exe: str, target_exe: str) -> bool:
    try:
        if is_system_folder(original_exe) and not is_admin():
            return False
        original_exe = os.path.abspath(original_exe)
        target_exe = os.path.abspath(target_exe)
        if not os.path.exists(target_exe):
            return False
        app_dir = get_app_dir()
        wrapper_exe = os.path.join(app_dir, "wrapper.exe")
        if not os.path.exists(wrapper_exe):
            return False
        original_size = get_file_size(original_exe)
        original_mtime = None
        original_atime = None
        try:
            original_stat = os.stat(original_exe)
            original_mtime = original_stat.st_mtime
            original_atime = original_stat.st_atime
        except:
            pass
        try:
            os.remove(original_exe)
        except:
            return False
        if not copy_and_pad_file(wrapper_exe, original_exe, original_size):
            return False
        create_wrapper_config(original_exe, target_exe)
        if original_mtime and original_atime:
            try:
                os.utime(original_exe, (original_atime, original_mtime))
            except:
                pass
        return True
    except:
        return False