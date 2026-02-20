import sys
import os
import ctypes
from pathlib import Path
def is_running_as_admin():
    try:
        return ctypes.windll.shell.IsUserAnAdmin()
    except:
        return False
def run_as_admin():
    import subprocess
    script = os.path.abspath(__file__)
    ctypes.windll.shell.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
    sys.exit()
def main():
    from main import main as app_main
    app_main()
if __name__ == "__main__":
    main()