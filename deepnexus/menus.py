from deepnexus.helpmenus import disks_help, sas_submenu_help, deepnexus_help, command_not_found
from deepnexus.vars import COLORS, DISKS_CONFIG_PATH, APP_CONFIG_PATH
from deepnexus.utils import clear_screen, load_config, get_prompt_text
from diskmanagement.disks import show_all_disks, show_mounted_disks, prepare_new_disk, locate_disk
from diskmanagement.sas import show_sas_all, show_sas_disk, show_disk_smart
from deepnexus.updater import update_tool

def main_menu():
    app_config = load_config(APP_CONFIG_PATH)
    while True:
        try:
            cmd = input(get_prompt_text(app_config)).strip()
            if cmd == "exit":
                break
            elif cmd == "disks":
                disks_menu(app_config)
            elif cmd == "help":
                deepnexus_help()
            elif cmd == "clear":
                clear_screen()
            elif cmd == "update":
                print()
                update_tool()
            elif cmd == "":
                continue
            else:
                command_not_found(cmd)
        except KeyboardInterrupt:
            print("Interrupted Detected! Exiting...")
            exit()
            break

def disks_menu(app_config):
    disks_config = load_config(DISKS_CONFIG_PATH)
    print()
    print(f"{COLORS['purple']}DeepNexus{COLORS['reset']} Disk CLI Tool. Type 'help' for commands.")
    print()
    while True:
        try:
            cmd = input(get_prompt_text(app_config, ["disks"])).strip()
            if cmd == "exit":
                exit()
                break
            elif cmd == "initialize disk":
                prepare_new_disk(disks_config)
            elif cmd == "back" or cmd == "..":
                break
            elif cmd == "sas":
                sas_submenu(app_config, disks_config)
            elif cmd == "show mounted":
                print()
                show_mounted_disks(disks_config)
            elif cmd == "show all":
                print()
                show_all_disks(disks_config)
            elif cmd.startswith("locate disk"):
                parts = cmd.split()
                if len(parts) == 2:
                    locate_disk(disks_config)
                elif len(parts) == 3:
                    locate_disk(disks_config, parts[2])
                else:
                    print("Invalid syntax. Use 'locate disk' or 'locate disk r0c1'")
            elif cmd == "help":
                disks_help()
            elif cmd == "clear":
                clear_screen()
            elif cmd == "":
                continue
            else:
                command_not_found(cmd)
        except KeyboardInterrupt:
            print("Interrupted Detected! Exiting...")
            exit()
            break
    
def sas_submenu(app_config, config):
    while True:
        try:
            cmd = input(get_prompt_text(app_config, ["disks", "sas"])).strip()
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
                command_not_found(cmd)
        except KeyboardInterrupt:
            print("Interrupted Detected! Exiting...")
            exit()
            break