import os
import sys

def open_shell(app_config):
    home_dir = os.path.expanduser("~")
    os.chdir(home_dir)

    shell = os.environ.get("SHELL", app_config["shell"])
    os.system(shell)

    os.system('clear')

    python = sys.executable
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script_path = os.path.join(root_dir, "deepnexus-cli.py")
    os.chdir(root_dir)
    os.execv(python, [python, script_path])

if __name__ == "__main__":
    app_config = {"shell": os.environ.get("SHELL", "/bin/bash")}
    open_shell()