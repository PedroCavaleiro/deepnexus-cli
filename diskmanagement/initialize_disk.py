import curses
import os
import subprocess
import json
from uuid import UUID
from deepnexus.utils import run_command, load_config
from deepnexus.vars import APP_CONFIG_PATH

def list_unmounted_disks():
    all_disks = [d for d in os.listdir('/dev') if d.startswith('sd') and len(d) == 3]
    mounted = subprocess.check_output('lsblk -nr -o MOUNTPOINT /dev/sd*', shell=True).decode().splitlines()
    mounted_devices = set(filter(None, mounted))
    return [f"/dev/{d}" for d in all_disks if not any(d in m for m in mounted_devices)]

def list_available_mounts():
    if not os.path.exists('/mnt'):
        os.makedirs('/mnt')
    return [d for d in os.listdir('/mnt') if os.path.isdir(f"/mnt/{d}")]

def get_partition_uuid(partition):
    return run_command(f"blkid -s UUID -o value {partition}")

def disk_init(disk, label):
    run_command(f"parted -s {disk} mklabel gpt")
    run_command(f"parted -s {disk} mkpart primary ext4 0% 100%")
    partition = disk + '1'
    run_command(f"mkfs.ext4 -F {partition}")
    run_command(f"e2label {partition} \"{label}\"")
    return partition

def add_to_fstab(uuid, mount_point):
    fstab_entry = f"UUID={uuid} {mount_point} ext4 defaults,nofail,x-systemd.device-timeout=0 0 2"
    with open('/etc/fstab', 'a') as f:
        f.write(fstab_entry + '\n')

def interactive_disk_setup(stdscr, app_config, disk_config, dry_run=False):
    curses.curs_set(0)
    curses.use_default_colors()
    stdscr.clear()
    unmounted_disks = list_unmounted_disks()
    current_idx = 0
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Select a disk to initialize")

        for i, disk in enumerate(unmounted_disks):
            if i == current_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(i + 2, 2, disk)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(i + 2, 2, disk)

        stdscr.addstr(len(unmounted_disks) + 4, 0, "Use ↑/↓ to navigate, Enter to select, q to quit")
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_idx = (current_idx - 1) % len(unmounted_disks)
        elif key == curses.KEY_DOWN:
            current_idx = (current_idx + 1) % len(unmounted_disks)
        elif key == 27:  # ESC key
            break
        elif key == ord('\n'):
            disk = unmounted_disks[current_idx]
            curses.echo()

            stdscr.clear()
            stdscr.addstr(0, 0, "Enter label (optional): ")
            label = stdscr.getstr().decode().strip() or "NO LABEL"

            stdscr.addstr(1, 0, "Available mount points:")
            mounts = list_available_mounts()
            for i, m in enumerate(mounts):
                stdscr.addstr(2 + i, 2, m)
            stdscr.addstr(2 + len(mounts), 0, "Enter mount point name (will be under /mnt/): ")
            mount_point = stdscr.getstr().decode().strip()
            if not os.path.exists(f"/mnt/{mount_point}"):
                os.makedirs(f"/mnt/{mount_point}")

            stdscr.addstr(4 + len(mounts), 0, "Add to /etc/fstab? (y/n): ")
            add_fstab = stdscr.getstr().decode().strip().lower() == 'y'

            stdscr.addstr(5 + len(mounts), 0, "Add to disk_config? (y/n): ")
            add_config = stdscr.getstr().decode().strip().lower() == 'y'

            stdscr.addstr(6 + len(mounts), 0, "Enter physical location (optional): ")
            phy = stdscr.getstr().decode().strip() or "Unknown"

            if app_config.get("enable_sas"):
                stdscr.addstr(7 + len(mounts), 0, "Enter SAS controller number: ")
                card = int(stdscr.getstr().decode().strip())
                stdscr.addstr(8 + len(mounts), 0, "Enter SAS slot number: ")
                slt = int(stdscr.getstr().decode().strip())
            else:
                card, slt = -1, -1

            stdscr.clear()
            stdscr.addstr(0, 0, f"Initializing {disk}...")
            stdscr.refresh()

            if not dry_run:
                partition = disk_init(disk, label)
                uuid = get_partition_uuid(partition)
                run_command(f"mount {partition} /mnt/{mount_point}")
                if add_fstab:
                    add_to_fstab(uuid, f"/mnt/{mount_point}")
            else:
                partition = disk + '1'
                uuid = "dry-run-uuid"

            if add_config:
                disk_config.append({
                    "label": label,
                    "phy": phy,
                    "mnt": mount_point,
                    "card": card,
                    "slt": slt,
                    "uuid": uuid,
                    "dev": disk.replace("/dev/", "")
                })

            stdscr.addstr(2, 0, "Disk setup complete. Press any key to continue...")
            stdscr.getch()
            break

def initialize_disk(disk_config, app_config):
    dry_run = True
    curses.wrapper(interactive_disk_setup, app_config, disk_config, dry_run=dry_run)
