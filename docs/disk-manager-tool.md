# DeepNexus Disk CLI Tool (disk management)

The objective is to manage SATA/SAS Drives via SAS interface, although some steps can work with SATA connected drives it might fail.

My case has support for 20 hot-swapable disks and the disks.json file is prepared in a way so I can easily locate them and both in the OS and Physically

The structure of the file is the following
```json
[
  {
    "phy": "0-0",
    "mnt": "sda",
    "dev": "",
    "card": 1,
    "slt": 3,
    "label": "EXOS X18",
    "uuid": ""
  }
]
```
* **phy**: The location in the case
* **mnt**: The mount location (these are inside /mnt/)
* **card**: The SAS interface on which the disk is located
* **slt**: The SAS slot on which the disk is located
* **label**: This label will also be written into the partition label
* **uuid**: The UUID of the partition

## Supported Commands 

### Main Menu

* **sas**: Enter the SAS sub-menu
* **initialize disk**: Initializes a disk (remember this match my needs might not be the same for you, read more [here](#initialize-disk-command))
* **show**: Shows all disks, configured within `disks.json`

### SAS Sub-menu

These commands make use of storcli64

* **show all**: Shows all disks connected to all SAS interfaces
* **show disk rXcY**: Shows a disk info at row X and col Y
* **smart rXcY**: Shows a disk info at row X and col Y (*NOTE: This hasn't been tested since it's not a supported command by storcli64*)

## Initialize Disk Command

The following steps are taken to initialize a disk

1. Displays all connected HDDs/SSDs through SAS/SATA and not mounted
2. Presents a list of disks to pick in order to format to EXT4, this will format the disk with GPT Partition Table with a single partition spawning the entire disk. A prompt will be presented to confirm after selecting a disk
3. After the filesystem is created it prompts the user to add a label (this is optional, pressing enter will not add a label)
4. Prompts the user to enter the mount point (partially) it only asks for r{ROW}c{COL} it will be assumed the mountpoint /mnt/hdd-r{ROW}c{COL}
5. A entry will be added to the /etc/fstab with **nofail** flag
6. Refreshes the systemctl daemon
7. Asks if the user wants to mount the disk immidiatly
8. Asks the user for the card nd slot number, a SAS functionality will be called to list all disks
9. Saves the new disk into the disks.json

