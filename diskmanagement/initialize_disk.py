from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Button, Dialog, Label, TextArea, Box, Frame, RadioList
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application.current import get_app
from prompt_toolkit.styles import Style
import os
import subprocess
import json
from deepnexus.utils import run_command
from deepnexus.vars import APP_CONFIG_PATH

def list_unmounted_disks():
    all_disks = [d for d in os.listdir('/dev') if d.startswith('sd') and len(d) == 3]
    mounted = subprocess.check_output('lsblk -nr -o MOUNTPOINT /dev/sd*', shell=True).decode().splitlines()
    mounted_devices = set(filter(None, mounted))
    return [f"/dev/{d}" for d in all_disks if not any(d in m for m in mounted_devices)]

def list_available_mounts():
    if not os.path.exists('/mnt'):
        os.makedirs('/mnt')
    return [d for d in os.listdir('/mnt') if os.path.isdir(f"/mnt/{d}")]

def get_partition_uuid(partition):
    return run_command(f"blkid -s UUID -o value {partition}")

def disk_init(disk, label):
    run_command(f"parted -s {disk} mklabel gpt")
    run_command(f"parted -s {disk} mkpart primary ext4 0% 100%")
    partition = disk + '1'
    run_command(f"mkfs.ext4 -F {partition}")
    run_command(f"e2label {partition} \"{label}\"")
    return partition

def add_to_fstab(uuid, mount_point):
    fstab_entry = f"UUID={uuid} {mount_point} ext4 defaults,nofail,x-systemd.device-timeout=0 0 2"
    with open('/etc/fstab', 'a') as f:
        f.write(fstab_entry + '\n')

def interactive_disk_setup(app_config, disk_config, dry_run=False):
    disks = list_unmounted_disks()
    selected_disk = [disks[0]] if disks else ["/dev/sdx"]

    disk_radio = RadioList([(d, d) for d in disks])
    label_input = TextArea(prompt='Label (optional): ', height=1)
    mount_input = TextArea(prompt='Mount point name (under /mnt/): ', height=1)
    phy_input = TextArea(prompt='Physical location (optional): ', height=1)
    fstab_input = RadioList([(True, 'Yes'), (False, 'No')])
    config_input = RadioList([(True, 'Yes'), (False, 'No')])
    sas_card_input = TextArea(prompt='SAS controller: ', height=1)
    sas_slot_input = TextArea(prompt='SAS slot: ', height=1)

    messages = TextArea(style='class:output-field', height=2, read_only=True)

    def accept():
        disk = disk_radio.current_value
        label = label_input.text.strip() or "NO LABEL"
        mount_name = mount_input.text.strip()
        mount_point = f"/mnt/{mount_name}"
        phy = phy_input.text.strip() or "Unknown"
        add_fstab = fstab_input.current_value
        add_config = config_input.current_value
        card = int(sas_card_input.text.strip()) if app_config.get("enable_sas") else -1
        slt = int(sas_slot_input.text.strip()) if app_config.get("enable_sas") else -1

        os.makedirs(mount_point, exist_ok=True)

        if not dry_run:
            partition = disk_init(disk, label)
            uuid = get_partition_uuid(partition)
            run_command(f"mount {partition} {mount_point}")
            if add_fstab:
                add_to_fstab(uuid, mount_point)
        else:
            partition = disk + '1'
            uuid = 'dry-run-uuid'

        if add_config:
            disk_config.append({
                "label": label,
                "phy": phy,
                "mnt": mount_name,
                "card": card,
                "slt": slt,
                "uuid": uuid,
                "dev": disk.replace("/dev/", "")
            })

        messages.text = "Disk setup complete. Press ESC to exit."

    layout_items = [
        Label("Select a disk to initialize:"),
        disk_radio,
        label_input,
        Label("Available mount points: " + ", ".join(list_available_mounts())),
        mount_input,
        Label("Add to /etc/fstab?"),
        fstab_input,
        Label("Add to disk_config?"),
        config_input,
        Label("Enter physical location (optional):"),
        phy_input,
    ]

    if app_config.get("enable_sas"):
        layout_items += [
            Label("Enter SAS controller number:"),
            sas_card_input,
            Label("Enter SAS slot number:"),
            sas_slot_input,
        ]

    layout_items.append(Button(text="Apply", handler=accept))
    layout_items.append(messages)
    layout_items.append(Label("Press ESC to exit"))

    body = HSplit(layout_items)
    dialog = Dialog(title="Interactive Disk Setup", body=body, buttons=[], width=80, with_background=False)

    layout = Layout(container=dialog)

    kb = KeyBindings()

    @kb.add('escape')
    def exit_(event):
        event.app.exit()

    style = Style.from_dict({})

    app = Application(layout=layout, key_bindings=kb, full_screen=True, mouse_support=True, style=style)
    app.run()

def initialize_disk(disk_config, app_config):
    dry_run = True
    interactive_disk_setup(app_config, disk_config, dry_run=dry_run)
