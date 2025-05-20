from ..utils import run_command, parse_mount_targets, format_physical_slot
from ..vars import COLORS, CONFIG_PATH
from .sas import show_sas_all, start_locate_drive, end_locate_drive
import os
import json
from pathlib import Path
from tabulate import tabulate

def show_all_disks(config):
    mounted_paths = parse_mount_targets()
    data = []
    for disk in config:
        mount_point = f"/mnt/{disk['mnt']}"
        normalized_mount = os.path.normpath(os.path.realpath(mount_point))
        is_mounted = normalized_mount in mounted_paths
        status_icon = f"{COLORS['green']}   ●  {COLORS['reset']}" if is_mounted else f"{COLORS['red']}   ●  {COLORS['reset']}"
        entry = [status_icon, format_physical_slot(disk['phy']), disk['mnt'], disk['card'], disk['slt'], mount_point]
        data.append(entry)
    if data:
        print(tabulate(data, headers=["Status", "Physical Slot", "Mount", "Card", "Slot", "Mount Path"]))
    else:
        print("None")
    print()

def show_mounted_disks(config):
    mounted_paths = parse_mount_targets()
    data = []
    for disk in config:
        mount_point = f"/mnt/{disk['mnt']}"
        normalized_mount = os.path.normpath(os.path.realpath(mount_point))
        status_icon = f"{COLORS['green']}   ●  {COLORS['reset']}"
        if normalized_mount in mounted_paths:
            data.append([status_icon, disk['label'], mount_point, format_physical_slot(disk['phy']), disk['card'], disk['slt']])
    if data:
        print(tabulate(data, headers=["Status", "Label", "Mount Path", "Physical Slot","Card", "Slot"]))
    else:
        print("No configured disks are currently mounted.")
    print()

def prepare_new_disk(config):
    print(f"{COLORS['yellow']}Scanning for unmounted /dev/sdX disks...{COLORS['reset']}\n")

    lsblk_output = run_command("lsblk -o NAME,MOUNTPOINT -n -p")

    # Collect mounted devices (partitions or disks)
    mounted_devices = set()
    disk_to_children = {}

    for line in lsblk_output.strip().splitlines():
        parts = line.split()
        name = parts[0]  # /dev/sdX or /dev/sdXY
        mount = parts[1] if len(parts) > 1 else ""
        base = os.path.basename(name)

        if mount and mount != "":
            mounted_devices.add(name)
            
        if base.startswith("sd") and len(base) > 3:
            parent = "/dev/" + base[:3]
            disk_to_children.setdefault(parent, []).append(name)

    # List eligible unmounted disks (ignoring partitions)
    eligible_disks = []
    for device in sorted(set("/dev/" + os.path.basename(l.split()[0]) for l in lsblk_output.strip().splitlines()
                             if os.path.basename(l.split()[0]).startswith("sd") and len(os.path.basename(l.split()[0])) == 3)):
        children = disk_to_children.get(device, [])
        if device not in mounted_devices and not any(c in mounted_devices for c in children):
            eligible_disks.append(device)

    if not eligible_disks:
        print(f"{COLORS['red']}No eligible unmounted /dev/sdX disks found.{COLORS['reset']}\n")
        return

    print("Available unmounted disks:")
    for idx, disk in enumerate(eligible_disks, 1):
        print(f"  {idx}. {disk}")
    print()

    try:
        choice = int(input("Select a disk number to format (or 0 to cancel): "))
        if choice == 0:
            print("Operation cancelled.")
            return
        if not (1 <= choice <= len(eligible_disks)):
            print(f"{COLORS['red']}Invalid choice.{COLORS['reset']}")
            return
    except ValueError:
        print(f"{COLORS['red']}Invalid input.{COLORS['reset']}")
        return

    disk = eligible_disks[choice - 1]
    print(f"\n{COLORS['yellow']}Selected disk: {disk}{COLORS['reset']}")
    confirm = input(f"This will erase all data on {disk}. Proceed? (yes/[no]): ").lower()
    if confirm != "yes":
        print("Operation aborted.")
        return

    print(f"{COLORS['blue']}Creating GPT partition table on {disk}...{COLORS['reset']}")
    run_command(f"parted -s {disk} mklabel gpt")

    print("Creating primary ext4 partition spanning the entire disk...")
    run_command(f"parted -s {disk} mkpart primary ext4 0% 100%")

    partition = disk + "1"
    print(f"Formatting {partition} as ext4...")
    run_command(f"mkfs.ext4 -F {partition}")

    label = input("Enter label for the new partition: ").strip()
    if label:
        print(f"Labeling partition as '{label}'...")
        run_command(f"e2label {partition} '{label}'")
        print(f"{COLORS['green']}Partition labeled successfully!{COLORS['reset']}")
    else:
        print("No label set.")

    # Get UUID Partition
    blkid_output = run_command(f"blkid {partition}")
    uuid = None
    for part in blkid_output.split():
        if part.startswith("UUID="):
            uuid = part.split("=")[1].strip('"')
            break

    if not uuid:
        print(f"{COLORS['red']}Failed to retrieve UUID for {partition}.{COLORS['reset']}")
        return

    # Get mount location by specifying row and column
    while True:
        mount_id = input("Enter mount identifier (e.g., r0c1): ").strip().lower()
        if mount_id and mount_id.startswith("r") and "c" in mount_id:
            break
        print("Invalid mount ID format. Use format like 'r0c1'.")

    mount_point = f"/mnt/hdd-{mount_id}"
    
    os.makedirs(mount_point, exist_ok=True)

    # Append to /etc/fstab
    fstab_line = f"UUID={uuid} {mount_point} ext4 defaults,nofail,x-systemd.device-timeout=0 0 2\n"
    with open("/etc/fstab", "a") as fstab:
        fstab.write(fstab_line)

    print(f"{COLORS['green']}Entry added to /etc/fstab:{COLORS['reset']}")
    print(fstab_line)

    run_command("systemctl daemon-reload")

    # Ask to mount
    choice = input(f"Do you want to mount the disk now? (yes/[no]): ").strip().lower()
    if choice == "yes":
        result = run_command(f"mount {mount_point}")
        print(result)
        print(f"{COLORS['green']}Disk mounted at {mount_point}.{COLORS['reset']}")
    else:
        print("You can mount later with:")
        print(f"  mount {mount_point}")

    # Configure Disks.json
    # Show SAS info and prompt for card and slot
    print("\nDisplaying SAS card/slot info to help with identification:\n")
    show_sas_all()

    try:
        card = int(input("Enter SAS card number: ").strip())
        slot = int(input("Enter SAS slot number: ").strip())
    except ValueError:
        print(f"{COLORS['red']}Invalid input for card or slot. Skipping config update.{COLORS['reset']}")
        return

    # Append to config
    config_path = Path(CONFIG_PATH)

    tmpLabel = ""
    if label:
        tmpLabel = label
    else:
        tmpLabel = "NO LABEL"

    try:
        phy = mount_id.replace('r', '').replace('c', '-')
        config.append({
            "label": tmpLabel,
            "phy": phy,
            "mnt": f"hdd-{mount_id}",
            "card": card,
            "slt": slot
        })

        with open(config_path, "w") as f:
           json.dump(config, f, indent=2)

        print(f"{COLORS['green']}Disk added to {CONFIG_PATH}.{COLORS['reset']}")
    except Exception as e:
        print(f"{COLORS['red']}Failed to update config: {e}{COLORS['reset']}")


    print(f"{COLORS['green']}Disk preparation complete!{COLORS['reset']}\n")

def locate_disk(config, target=None):
    if target is None:
        print("Available disks:")
        for i, disk in enumerate(config):
            print(f"  {i + 1}. {disk['mnt']} ({format_physical_slot(disk['phy'])})")
        try:
            index = int(input("Select a disk by number: ")) - 1
            if 0 <= index < len(config):
                selected_disk = config[index]
                run_locate_disk_action(selected_disk['mnt'], selected_disk['phy'], selected_disk['card'], selected_disk['slt'])
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input.")
    else:
        match = next((d for d in config if d['mnt'] == f"hdd-{target}"), None)
        if match:
            run_locate_disk_action(target, match['phy'], match['card'], match['slt'])
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