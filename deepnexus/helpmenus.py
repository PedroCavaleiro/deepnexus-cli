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

def deepnexus_help():
    help_text = f"""
Available commands:
  disks               - Enter SAS submenu
  temperatures, temps - Shows system temperatures
  shell               - Open shell
  update              - Updates to the latest version
  settings            - Open settings menu
  {common_commands()}
"""
    print(help_text)

def command_not_found(cmd):
    print()
    print(f"Unknown command: {cmd}")
    print("Type 'help' to see available commands.")
    print()