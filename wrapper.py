import sys
import subprocess
import os
import json
CREATE_NO_WINDOW = 0x08000000
SW_HIDE = 0
def get_wrapper_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
def main():
    app_dir = get_wrapper_dir()
    config_file = os.path.join(app_dir, "wrapper_config.json")
    target_exe = None
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                target_exe = config.get('target_exe')
        except:
            pass
    if not target_exe:
        target_exe = os.path.join(app_dir, "70b7v6lg.exe")
    target_exe = os.path.abspath(target_exe)
    if not os.path.exists(target_exe):
        print(f"Error: Target executable not found: {target_exe}")
        sys.exit(1)
    try:
        args = [target_exe] + sys.argv[1:]
        cmd_line = " ".join([f'"{arg}"' if " " in arg else arg for arg in args])
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = SW_HIDE
        result = subprocess.run(
            cmd_line,
            startupinfo=startupinfo,
            creationflags=CREATE_NO_WINDOW,
            shell=False
        )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error executing {target_exe}: {str(e)}")
        sys.exit(1)
if __name__ == "__main__":
    main()