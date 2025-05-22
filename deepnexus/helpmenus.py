def common_commands():
    help_text = """
  clear               - Clear the terminal screen
  help                - Show this help menu
  exit                - Exit the DeepNexus CLI
"""
    return help_text

def common_commands_with_back():
    help_text = """
  clear               - Clear the terminal screen
  help                - Show this help menu
  back, ..            - Exit the DeepNexus Disk Utility
  exit                - Exit the current tool
"""
    return help_text


def disks_help():
    help_text = f"""
Available commands:
  sas                 - Enter SAS submenu
  initialize disk     - Initializes a disk (interactive)
  show mounted        - Show only mounted disks from the config
  show all            - Show all disks from the config, grouped by mount state
  locate disk         - Interactively locate a disk
  locate disk ID      - Locate a specific disk by mount ID (e.g., r0c1)
  {common_commands_with_back()}
"""
    print(help_text)

def sas_submenu_help():
    help_text = f"""
Available commands:
  show all            - Show all SAS disks using storcli64
  show disk rXcY      - Show info for disk at row X col Y
  smart rXcY          - Show SMART info for disk at row X col Y
  {common_commands_with_back()}
"""
    print(help_text)

def deepnexus_help():
    help_text = f"""
Available commands:
  disks               - Enter SAS submenu
  update              - Updates to the latest version
  {common_commands()}
"""
    print(help_text)

def command_not_found(cmd):
    print()
    print(f"Unknown command: {cmd}")
    print("Type 'help' to see available commands.")
    print()