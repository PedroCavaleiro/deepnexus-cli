from .helpmenus import disks_help, sas_submenu_help, deepnexus_help, command_not_found
from .vars import COLORS, CONFIG_PATH
from .utils import clear_screen
from .diskmanagement.disks import show_all_disks, show_mounted_disks, prepare_new_disk
from .diskmanagement.sas import show_sas_all, show_sas_disk, show_disk_smart

def main_menu(config):
    while True:
        try:
            cmd = input(f"{COLORS['purple']}deepnexus-cli{COLORS['reset']} > ").strip()
            if cmd == "exit":
                break
            elif cmd == "disks":
                disks_menu(config)
            elif cmd == "help":
                deepnexus_help()
            elif cmd == "clear":
                clear_screen()
            elif cmd == "":
                continue
            else:
                command_not_found()
        except KeyboardInterrupt:
            print("Interrupted Detected! Exiting...")
            exit()
            break

def disks_menu(config):
    print()
    print(f"{COLORS['purple']}DeepNexus{COLORS['reset']} Disk CLI Tool. Type 'help' for commands.")
    print()
    while True:
        try:
            cmd = input(f"{COLORS['purple']}deepnexus-cli{COLORS['reset']} ({COLORS['yellow']}disks{COLORS['reset']}) > ").strip()
            if cmd == "exit":
                exit()
                break
            elif cmd == "initialize disk":
                prepare_new_disk(config)
            elif cmd == "back" or cmd == "..":
                break
            elif cmd == "sas":
                sas_submenu(config)
            elif cmd == "show mounted":
                print()
                show_mounted_disks(config)
            elif cmd == "show all":
                print()
                show_all_disks(config)
            elif cmd == "help":
                disks_help()
            elif cmd == "clear":
                clear_screen()
            elif cmd == "":
                continue
            else:
                command_not_found()
        except KeyboardInterrupt:
            print("Interrupted Detected! Exiting...")
            exit()
            break
    
def sas_submenu(config):
    while True:
        try:
            prompt = f"{COLORS['purple']}deepnexus-cli{COLORS['reset']} ({COLORS['yellow']}disks > sas{COLORS['reset']}) > "
            cmd = input(prompt).strip()
            if cmd == "exit":
                exit()
                break
            elif cmd == "back" or cmd == "..":
                break
            elif cmd == "show all":
                show_sas_all()
            elif cmd.startswith("show disk "):
                arg = cmd[10:].strip().lower()
                if arg.startswith("r") and "c" in arg:
                    target_mnt = f"hdd-{arg}"
                    disk = next((d for d in config if d.get("mnt") == target_mnt), None)
                    if disk:
                        card = disk.get("card")
                        slot = disk.get("slt")
                        if card is not None and slot is not None:
                            show_sas_disk(card, slot)
                        else:
                            print(f"Disk {target_mnt} found but missing card/slot info.\n")
                    else:
                        print(f"No disk found with mount point {target_mnt}.\n")
                else:
                    print("Invalid format. Use: show disk rXcY (e.g. show disk r1c4)\n")
            elif cmd.startswith("smart "):
                arg = cmd[6:].strip().lower()
                if arg.startswith("r") and "c" in arg:
                    target_mnt = f"hdd-{arg}"
                    disk = next((d for d in config if d.get("mnt") == target_mnt), None)
                    if disk:
                        card = disk.get("card")
                        slot = disk.get("slt")
                        if card is not None and slot is not None:
                            show_disk_smart(card, slot)
                        else:
                            print(f"Disk {target_mnt} found but missing card/slot info.\n")
                    else:
                        print(f"No disk found with mount point {target_mnt}.\n")
                else:
                    print("Invalid format. Use: smart rXcY (e.g. smart r1c4)\n")
            elif cmd == "help":
                sas_submenu_help()
            elif cmd == "clear":
                clear_screen()
            elif cmd == "":
                continue
            else:
                command_not_found()
        except KeyboardInterrupt:
            print("Interrupted Detected! Exiting...")
            exit()
            break