import os
import subprocess
import sys
from deepnexus.utils import status_message, Status

def open_shell(app_config):
    home_dir = os.path.expanduser("~")
    os.chdir(home_dir)
    
    try:
        subprocess.run(os.environ.get("SHELL", app_config["shell"]), check=True)
    except subprocess.CalledProcessError as e:
        print(f"{status_message(Status.ERROR)} Shell exited with error: {e}")
    
    python = sys.executable
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script_path = os.path.join(root_dir, "deepnexus-cli.py")
    os.chdir(script_path)
    os.execv(python, [python, script_path])

if __name__ == "__main__":
    open_shell()
