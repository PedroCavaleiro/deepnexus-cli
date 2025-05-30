import os
import json
import subprocess
from enum import Enum
from deepnexus.escape import Ansi
font = Ansi.escape

def format_size(bytes_value):
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}P"

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
    
def get_prompt_text(app_config, menu = []):
    if app_config["prompt"]["use_app_name"]:
        return f"{font('bold')}deepnexus-cli > {font('reset')}"
    else:
        prompt = f"{font('bold')}"
        if app_config["prompt"]["username"]["name"] != "":
            if app_config["prompt"]["username"]["color"] == "":            
                prompt = f"{prompt}{app_config['prompt']['username']['name']}@"
            else:
                colors = app_config["prompt"]["username"]["color"].split(",")
                prompt = f"{prompt}{font('fg', colors[0], colors[1], colors[2])}{app_config['prompt']['username']['name']}{font('reset')}{font('bold')}@"
        
        if app_config["prompt"]["hostname"]["color"] == "":            
            prompt = f"{prompt}{app_config['prompt']['hostname']['name']}{font('reset')} "
        else:
            colors = app_config["prompt"]["hostname"]["color"].split(",")
            prompt = f"{prompt}{font('fg', colors[0], colors[1], colors[2])}{app_config['prompt']['hostname']['name']}{font('reset')} "

        if len(menu) > 0:
            menu_builder = f"({font('fg_yellow')}"
            for idx, val in enumerate(menu):
                if idx == 0:
                    menu_builder = f"{menu_builder} {val} "
                else:                    
                    menu_builder = f"{menu_builder}> {val} "
            prompt = f"{prompt}{menu_builder}{font('reset')}) "
        
        return f"{prompt}{font('bold')}> {font('reset')}"

class Status(Enum):
    SUCCESS = 1,
    ERROR = 2,
    WARNING = 3,
    INFO = 4

def status_message(message):
    if message == Status.SUCCESS:
        return f"{font('bold')}[{font('fg_green')}SUCCESS{font('reset')}{font('bold')}]{font('reset')}"
    elif message == Status.ERROR:
        return f"{font('bold')}[{font('fg_red')} ERROR {font('reset')}{font('bold')}]{font('reset')}"
    elif message == Status.WARNING:
        return f"{font('bold')}[{font('fg_yellow')}WARNING{font('reset')}{font('bold')}]{font('reset')}"
    elif message == Status.INFO:
        return f"{font('bold')}[{font('fg_blue')} INFO  {font('reset')}{font('bold')}]{font('reset')}"
    
def get_available_mounts():
    mnt_base = "/mnt"
    all_mnt_dirs = [os.path.join(mnt_base, d) for d in os.listdir(mnt_base)
                    if os.path.isdir(os.path.join(mnt_base, d))]
    
    with open("/proc/mounts", "r") as f:
        mounted_points = set(line.split()[1] for line in f)
        
    return [d for d in all_mnt_dirs if d not in mounted_points]

def is_disk_mounted(mounted_paths, mount_point):
    normalized_mount = os.path.normpath(os.path.realpath(mount_point))
    return normalized_mount in mounted_paths

def get_fstab_uuids():
    fstab_uuids = set()
    try:
        with open("/etc/fstab", "r") as fstab:
            for line in fstab:
                line = line.strip()
                if line.startswith("UUID="):
                    parts = line.split()
                    if parts:
                        uuid = parts[0].replace("UUID=", "")
                        fstab_uuids.add(uuid)
    except Exception as e:
        print(f"Error reading /etc/fstab: {e}")
    return fstab_uuids