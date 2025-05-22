import os
import json
import subprocess
from deepnexus.escape import Ansi
font = Ansi.escape

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
    if app_config["prompt"]["useAppName"]:
        return f"{font('bold')}deepnexus-cli > {font('reset')}"
    else:
        prompt = f"{font('bold')}"
        if app_config["prompt"]["username"]["name"] != "":
            if app_config["prompt"]["username"]["color"] == "":            
                prompt = f"{prompt}{app_config['prompt']['username']['name']}@"
            else:
                colors = app_config["prompt"]["username"]["color"].strip()
                prompt = f"{prompt}{font('fg', colors[0], colors[1], colors[2])}{app_config['prompt']['username']['name']}{font('reset')}{font('bold')}@"
        
        if app_config["prompt"]["hostname"]["color"] == "":            
            prompt = f"{prompt}{app_config['prompt']['hostname']['name']}{font('reset')}"
        else:
            colors = app_config["prompt"]["hostname"]["color"].strip()
            prompt = f"{prompt}{font('fg', colors[0], colors[1], colors[2])}{app_config['prompt']['hostname']['name']}{font('reset')}"

        if len(menu) > 0:
            menu_builder = f"({font('fg_yellow')}"
            for idx, val in menu:
                if idx == 0:
                    menu_builder = f"{menu_builder} {val} "
                else:                    
                    menu_builder = f"{menu_builder}> {val} "
            prompt = f"{prompt}{font('reset')}) "
        
        return f"{prompt}{font('bold')}> {font('reset')}"