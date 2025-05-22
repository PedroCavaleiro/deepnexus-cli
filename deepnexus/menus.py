from deepnexus.helpmenus import deepnexus_help, command_not_found
from deepnexus.vars import APP_CONFIG_PATH
from deepnexus.utils import clear_screen, load_config, get_prompt_text
from deepnexus.updater import update_tool
from diskmanagement.menu import disks_menu

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

