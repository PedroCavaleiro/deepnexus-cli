import os
import json
import subprocess
import shutil
import tempfile
import sys
from deepnexus.vars import APP_CONFIG_PATH
from deepnexus.utils import load_config, Status, status_message

REPO_URL = 'https://github.com/PedroCavaleiro/deepnexus-cli.git'
BACKUP_DIR = 'backups'

def create_backup():
    # Clear existing backups
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, 'latest_backup')
    os.makedirs(backup_path, exist_ok=True)

    for item in os.listdir('.'):
        if item in ['.git', BACKUP_DIR]:
            continue
        s = os.path.join('.', item)
        d = os.path.join(backup_path, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    print(f"{status_message(Status.SUCCESS)} Backup created at {backup_path}")


def get_latest_tag():
    result = subprocess.run(["git", "ls-remote", "--tags", REPO_URL], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"{status_message(Status.ERROR)} Failed to retrieve tags:", result.stderr.decode())
        return None

    lines = result.stdout.decode().splitlines()
    tags = [line.split("refs/tags/")[1] for line in lines if "refs/tags/" in line and not line.endswith("^")]  # ignore annotated tag refs
    if not tags:
        return None
    tags.sort(key=lambda s: list(map(int, s.strip('v').split('.'))))  # sort by semantic version
    return tags[-1] if tags else None


def update_tool():
    settings = load_config(APP_CONFIG_PATH)
    source = settings.get("update_source", "main")

    if source.lower() == "tag":
        source = get_latest_tag()
        if not source:
            print(f"{status_message(Status.ERROR)} No tags found. Aborting update.")
            return
        print(f"{status_message(Status.INFO)} Latest tag resolved to: {source}")
    else:
        print(f"{status_message(Status.INFO)} Updating from source: {source}...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        clone_cmd = ["git", "clone", REPO_URL, tmp_dir, "--branch", source, "--depth", "1"]
        result = subprocess.run(clone_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            print(f"{status_message(Status.ERROR)} Update failed:", result.stderr.decode())
            return

        create_backup()

        for item in os.listdir(tmp_dir):
            if item in ['.git', 'configs']:
                continue
            s = os.path.join(tmp_dir, item)
            d = os.path.join(os.getcwd(), item)
            if os.path.exists(d):
                if os.path.isdir(d):
                    shutil.rmtree(d)
                else:
                    os.remove(d)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        print(f"{status_message(Status.SUCCESS)} Update complete. Restarting the tool...\n")
        python = sys.executable
        os.execv(python, [python] + sys.argv)


if __name__ == "__main__":
    update_tool()