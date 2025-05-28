from deepnexus.helpmenus import command_not_found
from diskmanagement.helpmenu import disks_help, sas_submenu_help
from deepnexus.vars import COLORS, DISKS_CONFIG_PATH
from deepnexus.utils import load_config, get_prompt_text, clear_screen, status_message, Status, run_command
from diskmanagement.disks import show_all_disks, locate_disk, mount_disk, show_disks_tree
from diskmanagement.sas import show_sas_all, show_sas_disk, show_disk_smart
from diskmanagement.fstab_manager import run_fstab_menu
from diskmanagement.initialize_disk import initialize_disk

def disks_menu(app_config):
    disks_config = load_config(DISKS_CONFIG_PATH)
    print()
    print(f"{COLORS['purple']}DeepNexus{COLORS['reset']} Disk CLI Tool. Type 'help' for commands.")
    print()
    while True:
        try:
            cmd = input(get_prompt_text(app_config, ["disks"])).strip()
            if cmd == "exit":
                break
            elif cmd == "mount disk":
                mount_disk(disks_config)
            elif cmd == "initialize disk" or cmd == "init disk":
                initialize_disk(disks_config, app_config)
            elif cmd == "back" or cmd == "..":
                break
            elif cmd.startswith("lsblk"):
                print()
                print(run_command(cmd))
            elif cmd == "fstab":
                run_fstab_menu()
            elif cmd == "sas":
                if app_config["enable_sas"]:                    
                    goback = sas_submenu(app_config, disks_config)
                    if goback:
                        break
                    else:
                        continue
                else:
                    print(f"{status_message(Status.ERROR)} SAS Functionality Disabled!")
                    print()
            elif cmd == "show all":
                print()
                show_all_disks(disks_config)
            elif cmd == "show":
                print()
                if app_config["enable_sas"]:
                    show_disks_tree(disks_config)
                else:
                    show_all_disks(disks_config)
            elif cmd.startswith("locate disk"):
                parts = cmd.split()
                if len(parts) == 2:
                    locate_disk(disks_config)
                elif len(parts) == 3:
                    locate_disk(disks_config, parts[2])
                else:
                    print("Invalid syntax. Use 'locate disk' or 'locate disk sda'")
            elif cmd == "help":
                disks_help()
            elif cmd == "clear":
                clear_screen()
            elif cmd == "":
                continue
            else:
                command_not_found(cmd)
        except KeyboardInterrupt:
            print("Interrupted Detected! Exiting Disk Management Tool...")
            break
    
def sas_submenu(app_config, config):
    goback = False
    while True:
        try:
            cmd = input(get_prompt_text(app_config, ["disks", "sas"])).strip()
            if cmd == "exit":
                goback = True
                break
            elif cmd == "back" or cmd == "..":
                break
            elif cmd == "show all":
                show_sas_all()
            elif cmd.startswith("show disk "):
                arg = cmd[10:].strip().lower()
                disk = next((d for d in config if d.get("mnt") == f"/mnt/{arg}"), None)
                if disk:
                    card = disk.get("card")
                    slot = disk.get("slt")
                    if card is not None and slot is not None:
                        if card == -1 or slot == -1:
                            print(f"Disk {arg} found but missing card/slot info.\n")
                        else:
                            show_sas_disk(card, slot)
                    else:
                        print(f"Disk {arg} found but missing card/slot info.\n")
                else:
                    print(f"No disk found with mount point {arg}.\n")
            elif cmd.startswith("smart "):
                arg = cmd[6:].strip().lower()
                disk = next((d for d in config if d.get("mnt") == f"/mnt/{arg}"), None)
                if disk:
                    card = disk.get("card")
                    slot = disk.get("slt")
                    if card is not None and slot is not None:
                        if card == -1 or slot == -1:
                            print(f"Disk {arg} found but missing card/slot info.\n")
                        else:
                            show_disk_smart(card, slot)
                    else:
                        print(f"Disk {arg} found but missing card/slot info.\n")
                else:
                    print(f"No disk found with mount point {arg}.\n")
            elif cmd == "help":
                sas_submenu_help()
            elif cmd == "clear":
                clear_screen()
            elif cmd == "":
                continue
            else:
                command_not_found(cmd)
        except KeyboardInterrupt:
            print("Interrupted Detected! Exiting Disk Management Tool...")
            break
    return goback