from deepnexus.menus import main_menu
from deepnexus.utils import load_config
from deepnexus.vars import APP_CONFIG_PATH
import pyfiglet

def main():

    config = load_config(APP_CONFIG_PATH)
    ascii_art = pyfiglet.figlet_format(config["banner"])

    print(ascii_art)
    print()
    print("DeepNexus Server managemnet tool. Type 'help' for commands.")
    main_menu()

if __name__ == "__main__":    
    main()