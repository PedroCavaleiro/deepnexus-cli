from deepnexus.helpmenus import common_commands_with_back

def disks_help():
    help_text = f"""
Available commands:
  sas                 - Enter SAS submenu
  initialize disk     - Initializes a disk (interactive)
  show                - If SAS enabled shows SAS connected disks otherwise shows all disks
  show all            - Shows all connected disks
  fstab               - Shows the fstab menu
  locate disk         - Interactively locate a disk
  locate disk ID      - Locate a specific disk by mount ID (e.g., sda)
  {common_commands_with_back()}
"""
    print(help_text)

def sas_submenu_help():
    help_text = f"""
Available commands:
  show all            - Show all SAS disks using storcli64
  show disk sda       - Show info for disk at row X col Y
  smart sda           - Show SMART info for disk at row X col Y
  {common_commands_with_back()}
"""
    print(help_text)