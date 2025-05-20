import os
import json
import subprocess

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def load_config(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return []
    
def run_command(command):
    try:
        return subprocess.check_output(command, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        return e.output
    
def parse_mount_targets():
    mount_targets = set()
    with open("/proc/mounts") as f:
        for line in f:
            parts = line.split()
            mount_point = parts[1]
            mount_targets.add(os.path.normpath(os.path.realpath(mount_point)))
    return mount_targets

def format_physical_slot(phy):
    try:
        row, col = map(int, phy.split('-'))
        return f"Row {row} Col {col}"
    except Exception:
        return phy