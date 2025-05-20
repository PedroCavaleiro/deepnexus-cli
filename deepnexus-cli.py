from .menus import main_menu
from .utils import load_config
from .vars import CONFIG_PATH

def main():
    config = load_config(CONFIG_PATH)
    main_menu(config)

if __name__ == "__main__":    
    main()