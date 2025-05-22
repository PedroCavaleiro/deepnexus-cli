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
    script_path = os.path.abspath(__file__)
    os.execv(python, [python, script_path])

if __name__ == "__main__":
    open_shell()
