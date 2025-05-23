# deepnexus-cli
A python utility to manage a Proxmox instance mainly for storage. This was developed for **my** needs but aditions and improvements are welcomed.

## Installation, Update and Uninstall

* Install: `bash <(curl -fsSL https://raw.githubusercontent.com/PedroCavaleiro/deepnexus-cli/main/install.sh)`
* Update: `deepnexus-cli update`
* Uninstall: `deepnexus-cli uninstall`

It's possible, and recommended, to run the update from within the tool by typing `update` instead of running from this script

## Dependencies

* **tabulate**: You can install it using `apt install python3-tabulate` (installed automatically by install script)
* **pyfiglet**: You can install it using `apt install python3-pyfiglet` (installed automatically by install script)
* **storcli64**

## Common Commands
* **exit**: Exists DeepNexus CLI tool (or the currently active tool)
* **back, ..**: Goes to the previous menu
* **help**: Shows the help message for the current menu
* **clear**: Clear the terminal screen

Pressing ctrl+c at any moment will exit DeepNexus CLI or the currently active tool

## Main App Commands

* **disks**: Opens DeepNexus Disk CLI
* **shell**: Opens a shell (typing exit on this shell will return to this tool)
* **update**: Updates this tool
* **settings**: Configures the tool [view available settings](#available-settings)

## Available Settings

* Enable SAS: Enables/Disables SAS module, this will disable the SAS step during the disk initialization and SAS sub-menu
* Update Source: Selects the source of the updates (tag, main, dev) recommended tag it will only pull tested and released versions while main might have a couple bugs and dev might be quite unstable
* Shell: The shell to use when running `shell`
* Banner: The text to display when the script opens
* Prompt:
  * Default Prompt (yes/no): It displys the default prompt **deepnexus-cli >** or a custom one (see below)
  * Username: (These changes are visible only when default prompt is disabled)
    * Name: It will display **username@hostname >** (for hostname see hostname settings)
    * Color: Enter the color for the username in rgb format comma separated no spaces eg. *233,112,002*
  * Hostname: (These changes are visible only when default prompt is disabled)
    * Name: It will display **hostname >** or **username@hostname >** if username is set
    * Color: Enter the color for the hostname in rgb format comma separated no spaces eg. *233,112,002*

## Docs for modules

* [Disk Manager CLI](docs/disk-manager-tool.md)