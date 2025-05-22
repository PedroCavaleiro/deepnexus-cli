from deepnexus.helpmenus import common_commands_with_back

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