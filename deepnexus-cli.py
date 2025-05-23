from deepnexus.menus import main_menu
from deepnexus.utils import load_config
from deepnexus.vars import APP_CONFIG_PATH
import pyfiglet
import os
import sys
from deepnexus.escape import Ansi
font = Ansi.escape

def main():

    root_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(root_dir)

    config = load_config(APP_CONFIG_PATH)
    ascii_art = pyfiglet.figlet_format(config["banner"]) # type: ignore

    print(ascii_art)    
    print(f"    {font('italic')}DeepNexus Server management tool.")
    print(f"    {font('italic')}Type 'help' for commands.{font('reset')}")
    print()
    print()
    main_menu()

if __name__ == "__main__":    
    main()