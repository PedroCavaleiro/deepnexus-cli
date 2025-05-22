import json
from deepnexus.utils import Status, status_message, load_config
from deepnexus.vars import APP_CONFIG_PATH

def save_settings(settings):
    with open(APP_CONFIG_PATH, 'w') as f:
        json.dump(settings, f, indent=4)

def prompt_menu(settings):
    if "prompt" not in settings:
        settings["prompt"] = {}
    prompt = settings["prompt"]

    while True:
        print("\nPrompt Configuration")
        print("1. Default prompt (yes/no)")
        print("2. Username")
        print("3. Username color")
        print("4. Hostname")
        print("5. Hostname color")
        print("0. Back")
        choice = input("Select an option: ")

        if choice == '1':
            prompt["default"] = input("Use default prompt? (yes/no): ").strip().lower() == 'yes'
        elif choice == '2':
            prompt["username"] = input("Enter username: ").strip()
        elif choice == '3':
            prompt["username_color"] = input("Enter username color (r,g,b): ").strip()
        elif choice == '4':
            prompt["hostname"] = input("Enter hostname: ").strip()
        elif choice == '5':
            prompt["hostname_color"] = input("Enter hostname color (r,g,b): ").strip()
        elif choice == '0':
            break
        else:
            print(f"{status_message(Status.ERROR)} Invalid option.")
            continue

        settings["prompt"] = prompt
        save_settings(settings)
        print(f"{status_message(Status.SUCCESS)}  Prompt setting updated.")

def settings_menu():
    settings = load_config(APP_CONFIG_PATH)

    while True:
        print("\nSettings Menu")
        print("1. Set update channel (dev, main, tag)")
        print("2. Enable/disable SAS submenu")
        print("3. Change banner text")
        print("4. Prompt configuration")
        print("0. Back")
        choice = input("Select an option: ")

        if choice == '1':
            channel = input("Enter update channel (dev, main, tag): ").strip()
            settings["update_source"] = channel
            save_settings(settings)
            print(f"{status_message(Status.SUCCESS)} Update channel saved.")

        elif choice == '2':
            value = input("Enable SAS submenu? (yes/no): ").strip().lower()
            settings["sas_enabled"] = (value == 'yes')
            save_settings(settings)
            print(f"{status_message(Status.SUCCESS)} SAS setting saved.")

        elif choice == '3':
            banner = input("Enter new banner text: ")
            settings["banner"] = banner
            save_settings(settings)
            print(f"{status_message(Status.SUCCESS)} Banner updated.")

        elif choice == '4':
            prompt_menu(settings)

        elif choice == '0':
            break

        else:
            print(f"{status_message(Status.ERROR)} Invalid option.")


if __name__ == "__main__":
    settings_menu()