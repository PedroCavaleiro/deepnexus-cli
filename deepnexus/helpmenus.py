def common_commands():
    help_text = """
  clear               - Clear the terminal screen
  help                - Show this help menu
  exit                - Exit the DeepNexus CLI
"""
    print(help_text)
    print()

def common_commands_with_back():
    help_text = """
  clear               - Clear the terminal screen
  help                - Show this help menu
  back, ..            - Exit the DeepNexus Disk Utility
  exit                - Exit the DeepNexus CLI
"""
    print(help_text)
    print()


def disks_help():
    help_text = """
Available commands:
  sas                 - Enter SAS submenu
  initialize disk     - Initializes a disk (interactive)
  show mounted        - Show only mounted disks from the config
  show all            - Show all disks from the config, grouped by mount state
  locate disk     - Interactively locate a disk
  locate disk ID  - Locate a specific disk by mount ID (e.g., r0c1)
"""
    print(help_text)
    common_commands_with_back()

def sas_submenu_help():
    help_text = """
Available commands:
  show all            - Show all SAS disks using storcli64
  show disk rXcY      - Show SMART info for disk at row X col Y
  smart rXcY          - Show SMART info for disk at row X col Y
"""
    print(help_text)
    common_commands_with_back()

def deepnexus_help():
    help_text = """
Available commands:
  disks               - Enter SAS submenu
"""
    print(help_text)
    common_commands()

def command_not_found(cmd):
    print()
    print(f"Unknown command: {cmd}")
    print("Type 'help' to see available commands.")
    print()