from deepnexus.menus import main_menu
from deepnexus.utils import load_config
from deepnexus.vars import APP_CONFIG_PATH
import pyfiglet
from deepnexus.escape import Ansi
font = Ansi.escape

def main():

    config = load_config(APP_CONFIG_PATH)
    ascii_art = pyfiglet.figlet_format(config["banner"])

    print(ascii_art)    
    print(f"    {font('italic')}DeepNexus Server managemnet tool.")
    print(f"    {font('italic')}Type 'help' for commands.{font('reset')}")
    print()
    print()
    main_menu()

if __name__ == "__main__":    
    main()