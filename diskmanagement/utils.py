import re
import subprocess
import json
import os
from deepnexus.utils import load_config, run_command
from deepnexus.vars import DISKS_CONFIG_PATH
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.application.current import get_app

def parse_sas_slots(output: str):
    slot_pattern = re.compile(
        r'(?P<eid_col>:)?(?P<slot>\d+)\s+'
        r'\d+\s+\S+\s+-\s+(?P<size>\d+\.\d+ TB)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<model>\S+)'
    )
    return [(slot, model, size) for _, slot, size, model in slot_pattern.findall(output)]

def load_used_slots():
    config = load_config(DISKS_CONFIG_PATH)
    return {str(d.get("slt")) for d in config if "slt" in d}

def parse_sas_controllers(sas_output: str):
    controllers = re.findall(r'^Controller\s+=\s+(\d+)', sas_output, re.MULTILINE)
    return list(set(controllers))

def list_unmounted_disks():
    output = subprocess.check_output(['lsblk', '-J', '-o', 'NAME,MOUNTPOINT']).decode()
    data = json.loads(output)

    unmounted_disks = []

    for device in data['blockdevices']:
        if device['name'].startswith('sd') and len(device['name']) == 3:
            has_mounted_partition = False

            if 'children' in device:
                for child in device['children']:
                    if child.get('mountpoint'):
                        has_mounted_partition = True
                        break

            if not has_mounted_partition:
                unmounted_disks.append(f"/dev/{device['name']}")

    return unmounted_disks

def list_unmounted_partitions():
    output = subprocess.check_output(['lsblk', '-J', '-o', 'NAME,MOUNTPOINT']).decode()
    data = json.loads(output)

    unmounted_partitions = []

    for device in data['blockdevices']:
        if device['name'].startswith('sd') and len(device['name']) == 3:
            if 'children' in device:
                for child in device['children']:
                    if not child.get('mountpoint'):
                        unmounted_partitions.append(f"/dev/{child['name']}")

    return unmounted_partitions

def get_disk_size(device):
    output = subprocess.check_output(['lsblk', '-dn', '-o', 'SIZE', device])
    return output.decode().strip()

def list_available_mounts():
    if not os.path.exists('/mnt'):
        os.makedirs('/mnt')

    mounted = subprocess.check_output(['lsblk', '-nr', '-o', 'MOUNTPOINT']).decode().splitlines()
    mounted = set(filter(None, mounted))

    return [d for d in os.listdir('/mnt')
        if os.path.isdir(f"/mnt/{d}") and f"/mnt/{d}" not in mounted]

def get_partition_uuid(partition):
    return run_command(f"blkid -s UUID -o value {partition}")

def log_message(output_lines, output_control, style, message):
        output_lines.append((style, message + '\n'))
        output_control.text = FormattedText(output_lines)
        get_app().invalidate()