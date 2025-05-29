from deepnexus.utils import run_command, parse_mount_targets, is_disk_mounted, get_fstab_uuids
from deepnexus.vars import COLORS, DISKS_CONFIG_PATH
from diskmanagement.sas import show_sas_all, start_locate_drive, end_locate_drive
import os
import json
from pathlib import Path
from tabulate import tabulate
from deepnexus.utils import status_message, Status, load_config, get_available_mounts, get_fstab_uuids
from deepnexus.escape import Ansi
from deepnexus.vars import APP_CONFIG_PATH, DISKS_CONFIG_PATH
import subprocess
import re
from collections import defaultdict
font = Ansi.escape

def show_all_disks(config):
    if len(config) > 0:
        mounted_paths = parse_mount_targets()
        data = []
        for disk in config:
            mount_point = f"/mnt/{disk['mnt']}"            
            is_mounted = is_disk_mounted(mounted_paths, mount_point)
            status_icon = f"{font('fg_green')}   ●  {font('reset')}" if is_mounted else f"{font('fg_red')}   ●  {font('reset')}"
            entry = [status_icon, disk['label'], mount_point, disk['uuid'], disk['phy'], disk['card'] if disk['card'] != -1 else "N/A", disk['slt'] if disk['slt'] != -1 else "N/A"]
            data.append(entry)
        if data:
            print(tabulate(data, headers=["Status", "Label", "Mount Point", "Partition UUID", "Physical Location", "SAS Card", "SAS Slot"]))
        else:
            print("None")
    else:
        print(f"{status_message(Status.ERROR)} There are no configured disks")
    print()

def mount_disk(config):
    print(f"{status_message(Status.INFO)} Scanning for unmounted /dev/sdX disks...\n")
    lsblk_output = run_command("lsblk -nr -o NAME,MOUNTPOINT,SIZE")

    eligible_partitions = []

    for line in lsblk_output.strip().splitlines():
        parts = line.split(None, 2)  # split into max 3 parts
        if len(parts) == 3:
            name, mountpoint, size = parts
        elif len(parts) == 2:
            name = parts[0]
            if parts[1].startswith('/'):
                mountpoint = parts[1]
                size = ""
            else:
                mountpoint = ""
                size = parts[1]
        else:
            continue  # Skip malformed lines

        base = os.path.basename(name)

        # Match sdXY pattern (e.g. sda1, sdb9, sdc123)
        if base.startswith("sd") and len(base) > 3:
            if not mountpoint:  # Only include unmounted
                eligible_partitions.append((name, size))

    if not eligible_partitions:
        print(f"{status_message(Status.ERROR)}No eligible unmounted /dev/sdXY partitions found.")
        return

    print("Available unmounted disks:")
    for idx, (disk, size) in enumerate(eligible_partitions, 1):
        print(f"  {idx}. {disk} ({size})")
    print()

    try:
        choice = int(input("Select a partition number to mount (or 0 to cancel): "))
        if choice == 0:
            print("Operation cancelled.")
            return
        if not (1 <= choice <= len(eligible_partitions)):
            print(f"{font('fg_red')}Invalid choice.{font('reset')}")
            return
    except ValueError:
        print(f"{font('fg_red')}Invalid input.{font('reset')}")
        return

    target_partition, _ = eligible_partitions[choice - 1]
    print("Available mount points:")
    available_mounts = get_available_mounts()
    if len(available_mounts) > 0:
        print(f"  1. Create new mount point")
        for idx, point in enumerate(available_mounts, 2):
            print(f"  {idx}. {point.replace('/mnt/', '')}")
        print()
        try:
            mp_choice = int(input("Select a mount point option (or 0 to cancel): "))
            if mp_choice == 0:
                print("Operation cancelled.")
                return
            if not (1 <= mp_choice <= len(available_mounts) + 1):
                print(f"{font('fg_red')}Invalid choice.{font('reset')}")
                return
        except ValueError:
            print(f"{font('fg_red')}Invalid input.{font('reset')}")
            return
    else:
        print("No available mount points")
        return

    if mp_choice == 1:
        mount_point = input("Enter the new mount point (e.g., sdc1): ")
    else:
        mount_point = available_mounts[mp_choice - 2]

    os.makedirs(mount_point, exist_ok=True)
    
    result = run_command(f"mount /dev/{target_partition} /mnt/{mount_point.replace('/mnt/', '')}")
    print(result)
    print(f"{status_message(Status.SUCCESS)} Disk mounted at /mnt/{mount_point.replace('/mnt/', '')}.")

def locate_disk(config, target=None):
    app_config = load_config(APP_CONFIG_PATH)
    if app_config['enable_sas'] == False: # type: ignore
        print(f"{status_message(Status.ERROR)} SAS Functionality Disabled! This functionality currently only works on SAS connected disks\n")
        return

    if target is None:
        print("Available disks:")
        for i, disk in enumerate(config):
            print(f"  {i + 1}. {disk['label']} {disk['mnt']} ({disk['phy']})")
        try:
            index = int(input("Select a disk by number: ")) - 1
            if 0 <= index < len(config):
                selected_disk = config[index]
                run_locate_disk_action(selected_disk['mnt'], selected_disk['phy'], selected_disk['card'], selected_disk['slt'])  # type: ignore
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input.")
    else:
        match = next((d for d in config if d['mnt'] == f"/mnt/{target}"), None)
        if match:
            run_locate_disk_action(target, match['phy'], match['card'], match['slt']) # type: ignore
        else:
            print(f"Disk with mount ID '{target}' not found in config.")

def run_locate_disk_action(mount_id, card, slot):
    print(f"Locating disk: {mount_id} (Card {card}, Slot {slot})")
    print("The disk indicator light is now blinking.")
    print("Press Enter to stop the indicator.")
    start_locate_drive(card, slot)
    input()
    end_locate_drive(card, slot)
    print("Indicator stopped.")

def get_smart_temperatures():
    disks = load_config(DISKS_CONFIG_PATH)
    temperatures = {}
    for disk in disks:
        if 'dev' not in disk:
            print(f"Warning: Disk entry missing 'dev' field. Skipping: {disk}")
            continue

        dev = f"/dev/{disk['dev']}"
        name = disk["label"]

        try:
            result = subprocess.run(
                ["smartctl", "-A", dev],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=True
            )
            output = result.stdout

            # Match known temperature attributes
            for line in output.splitlines():
                if re.search(r'Temperature_Celsius|Temperature_Internal|Temperature', line):
                    parts = line.split()
                    if len(parts) >= 10 and parts[9].isdigit():
                        temperatures[name] = int(parts[9])
                        break
                    elif len(parts) >= 2 and parts[1].isdigit():
                        temperatures[name] = int(parts[1])
                        break
        except Exception as e:
            print(f"smartctl failed for {dev}: {e}")
            temperatures[name] = None
    return temperatures

def print_tree(data, prefix=""):
    mounted_paths = parse_mount_targets()
    fstab_uuids = get_fstab_uuids()
    keys = list(data.keys())
    for i, key in enumerate(keys):
        is_last = i == len(keys) - 1
        branch = "└── " if is_last else "├── "
        print(f"{prefix}{branch}{key}")
        if isinstance(data[key], list):
            for j, item in enumerate(data[key]):
                is_mounted = is_disk_mounted(mounted_paths, f"/mnt/{item['mnt']}")
                status_icon = f"{font('fg_green')}● {font('reset')}" if is_mounted else f"{font('fg_red')}● {font('reset')}"
                sub_prefix = prefix + ("    " if is_last else "│   ")
                sub_branch = "└── " if j == len(data[key]) - 1 else "├── "
                print(f"{sub_prefix}{sub_branch}{status_icon} {item['label']}")
                details_prefix = sub_prefix + ("    " if j == len(data[key]) - 1 else "│   ")
                print(f"{details_prefix}├── Mount Point: /mnt/{item['mnt']}")
                print(f"{details_prefix}├── Partition UUID: {item['uuid']}")
                print(f"{details_prefix}├── Physical Location: {item['phy']}")
                print(f"{details_prefix}├── Device: /dev/{item['dev']}")
                if item['uuid'] in fstab_uuids:
                    print(f"{details_prefix}├── Automount: YES")
                else:
                    print(f"{details_prefix}├── Automount: NO")
                print(f"{details_prefix}└── SAS Slot: {item['slt']}")
    print()

def show_disks_tree(config):
    if not config:
        print("There are no configured disks")
        return

    grouped = defaultdict(list)
    for disk in config:
        if disk.get("card", -1) == -1 or disk.get("slt", -1) == -1:
            continue
        grouped[disk["card"]].append(disk)

    if not grouped:
        print("No valid disks with SAS card and slot info")
        return

    output_tree = {}
    for card in sorted(grouped.keys()):
        output_tree[f"SAS Controller {card}"] = grouped[card]

    print("Disks")
    print_tree(output_tree)
