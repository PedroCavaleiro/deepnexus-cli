from deepnexus.utils import run_command, parse_mount_targets
from deepnexus.vars import COLORS, DISKS_CONFIG_PATH
from diskmanagement.sas import show_sas_all, start_locate_drive, end_locate_drive
import os
import json
from pathlib import Path
from tabulate import tabulate
from deepnexus.utils import status_message, Status, load_config
from deepnexus.escape import Ansi
from deepnexus.vars import APP_CONFIG_PATH
font = Ansi.escape

def show_all_disks(config):
    if len(config) > 0:
        mounted_paths = parse_mount_targets()
        data = []
        for disk in config:
            mount_point = f"/mnt/{disk['mnt']}"
            normalized_mount = os.path.normpath(os.path.realpath(mount_point))
            is_mounted = normalized_mount in mounted_paths
            status_icon = f"{font('fg_green')}   ●  {font('reset')}" if is_mounted else f"{font('fg_red')}   ●  {font('reset')}"
            entry = [status_icon, disk['label'], mount_point, disk['uuid'], disk['phy'], disk['card'] if disk['card'] == -1 else "N/A", disk['slt'] if disk['slt'] == -1 else "N/A"]
            data.append(entry)
        if data:
            print(tabulate(data, headers=["Status", "Label", "Mount Point", "Partition UUID", "Physical Location", "SAS Card", "SAS Slot"]))
        else:
            print("None")
    else:
        print(f"{status_message(Status.ERROR)} There are no configured disks")
    print()

def show_mounted_disks(config):
    if len(config) > 0:
        mounted_paths = parse_mount_targets()
        data = []
        for disk in config:
            mount_point = f"/mnt/{disk['mnt']}"
            normalized_mount = os.path.normpath(os.path.realpath(mount_point))
            status_icon = f"{font('fg_green')}   ●  {font('reset')}"
            if normalized_mount in mounted_paths:
                data.append([status_icon, disk['label'], mount_point, disk['uuid'], disk['phy'], disk['card'] if disk['card'] == -1 else "N/A", disk['slt'] if disk['slt'] == -1 else "N/A"])
        if data:
            print(tabulate(data, headers=["Status", "Label", "Mount Point", "Partition UUID", "Physical Location", "SAS Card", "SAS Slot"]))
        else:
            print("No configured disks are currently mounted.")
    else:
        print(f"{status_message(Status.ERROR)} There are no configured disks")
    print()

def prepare_new_disk(config):

    app_config = load_config(APP_CONFIG_PATH)

    print(f"{status_message(Status.INFO)} Scanning for unmounted /dev/sdX disks...\n")

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
        print(f"{status_message(Status.ERROR)}No eligible unmounted /dev/sdX disks found.")
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
            print(f"{font('fg_red')}Invalid choice.{font('reset')}")
            return
    except ValueError:
        print(f"{font('fg_red')}Invalid input.{font('reset')}")
        return

    disk = eligible_disks[choice - 1]
    print(f"\n{font('fg_yellow')}Selected disk: {disk}{font('reset')}")
    confirm = input(f"This will erase all data on {disk}. Proceed? (yes/[no]): ").lower()
    if confirm != "yes":
        print("Operation aborted.")
        return

    print(f"{status_message(Status.INFO)} Creating GPT partition table on {disk}...")
    run_command(f"parted -s {disk} mklabel gpt")

    print(f"{status_message(Status.INFO)} Creating primary ext4 partition spanning the entire disk...")
    run_command(f"parted -s {disk} mkpart primary ext4 0% 100%")

    partition = disk + "1"
    print(f"{status_message(Status.INFO)} Formatting {partition} as ext4...")
    run_command(f"mkfs.ext4 -F {partition}")

    label = input("Enter label for the new partition: ").strip()
    if label:
        print(f"{status_message(Status.INFO)} Labeling partition as '{label}'...")
        run_command(f"e2label {partition} '{label}'")
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
        print(f"{status_message(Status.ERROR)} Failed to retrieve UUID for {partition}.")
        return

    # Get mount 
    nomnt_mount_point = input("Enter mount point (e.g., sdc1): ").strip().lower()
    mount_point = f"/mnt/{nomnt_mount_point}"

    os.makedirs(mount_point, exist_ok=True)

    fstab_choice = input(f"Do you want to add this disk to fstab? (yes/[no]): ").strip().lower()
    # Append to /etc/fstab
    if fstab_choice == "yes":
        fstab_line = f"UUID={uuid} {mount_point} ext4 defaults,nofail,x-systemd.device-timeout=0 0 2\n"
        with open("/etc/fstab", "a") as fstab:
            fstab.write(fstab_line)

        print(f"{status_message(Status.SUCCESS)} Entry added to /etc/fstab")
        print(fstab_line)

        run_command("systemctl daemon-reload")

    # Ask to mount
    choice = input(f"Do you want to mount the disk now? (yes/[no]): ").strip().lower()
    if choice == "yes":
        result = run_command(f"mount {mount_point}")
        print(result)
        print(f"{status_message(Status.SUCCESS)}Disk mounted at {mount_point}.")

    card = -1
    slot = -1

    if app_config['enable_sas']:
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
    config_path = Path(DISKS_CONFIG_PATH)

    tmpLabel = ""
    if label:
        tmpLabel = label
    else:
        tmpLabel = "NO LABEL"

    try:
        phy = input("Enter the physical location in the case (enter for none): ")
        config.append({
            "label": tmpLabel,
            "phy": phy if phy == "" else "Unknown",
            "mnt": mount_point,
            "card": card,
            "slt": slot,
            "uuid": uuid
        })

        with open(config_path, "w") as f:
           json.dump(config, f, indent=2)

        print(f"{status_message(Status.SUCCESS)}Disk added to {DISKS_CONFIG_PATH}.")
    except Exception as e:
        print(f"{status_message(Status.ERROR)}Failed to update config: {e}")


    print(f"{status_message(Status.SUCCESS)}Disk preparation complete!\n")

def locate_disk(config, target=None):
    app_config = load_config(APP_CONFIG_PATH)
    if app_config['enable_sas'] == False:
        print(f"{status_message(Status.ERROR)} SAS Functionality Disabled! This functionality currently only works on SAS")
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
        match = next((d for d in config if d['mnt'] == f"mnt/{target}"), None)
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