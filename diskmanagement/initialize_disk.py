from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Button, Dialog, Label, TextArea, Box, Frame, RadioList
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application.current import get_app
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.layout.containers import FloatContainer, Float
import os
import json
import subprocess
from deepnexus.utils import run_command
from deepnexus.vars import APP_CONFIG_PATH

def list_unmounted_disks():
    output = subprocess.check_output(['lsblk', '-J', '-o', 'NAME,MOUNTPOINT']).decode()
    data = json.loads(output)

    unmounted_disks = []

    for device in data['blockdevices']:
        if device['name'].startswith('sd') and len(device['name']) == 3:
            has_mounted_partition = False

            # Check if any child partition is mounted
            if 'children' in device:
                for child in device['children']:
                    if child.get('mountpoint'):
                        has_mounted_partition = True
                        break

            if not has_mounted_partition:
                unmounted_disks.append(f"/dev/{device['name']}")

    return unmounted_disks

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

def show_confirmation_dialog(floats, on_confirm, on_cancel):
    confirm_text = FormattedTextControl(
        text=[("class:confirmation-text", "Are you sure you want to proceed with disk initialization?")]
    )

    centered_text_window = VSplit([
        Window(width=D(weight=1)),
        Window(content=confirm_text, height=1),
        Window(width=D(weight=1)),
    ])

    confirm_body = HSplit([
        centered_text_window
    ])

    yes_button = Button(text="Yes", handler=lambda: (floats.clear(), on_confirm()))
    no_button = Button(text="No", handler=lambda: (floats.clear(), on_cancel()))

    confirm_dialog = Dialog(
        title="Confirm Action",
        body=confirm_body,
        buttons=[yes_button, no_button],
        width=80
    )

    floats.append(Float(content=confirm_dialog))

    # Focus on the "Yes" button (first button)
    get_app().layout.focus(yes_button)

    get_app().invalidate()

def log_message(output_lines, output_control, style, message):
        output_lines.append((style, message + '\n'))
        output_control.text = FormattedText(output_lines)
        get_app().invalidate()

def show_log_popup(floats, output_control, on_close):
    output_window = Window(
        content=output_control,
        wrap_lines=True,
        height=10,
        right_margins=[ScrollbarMargin()],
        always_hide_cursor=True
    )

    dialog = Dialog(
        title="Operation Log",
        body=HSplit([output_window]),
        buttons=[
            Button(text="Close", handler=lambda: (floats.clear(), on_close()))
        ],
        width=120
    )

    floats.append(Float(content=dialog))
    get_app().layout.focus(dialog)
    get_app().invalidate()

def interactive_disk_setup(app_config, disk_config, dry_run=False):
    disks = list_unmounted_disks()
    spacer = Window(height=1, content=FormattedTextControl(''))

    selected_disk = [disks[0]] if disks else ["/dev/sdx"]

    disk_radio = RadioList([(d, d) for d in disks])
    label_input = TextArea(prompt='Label: ', height=1)
    mount_input = TextArea(prompt='Mount point name: /mnt/', height=1)
    phy_input = TextArea(prompt='Physical location: ', height=1)
    fstab_input = RadioList([(True, 'Yes'), (False, 'No')])
    config_input = RadioList([(True, 'Yes'), (False, 'No')])
    sas_card_input = TextArea(prompt='SAS controller (-1 for none): ', height=1)
    sas_slot_input = TextArea(prompt='SAS slot (-1 for none): ', height=1)

    output_lines = []
    output_control = FormattedTextControl(lambda: FormattedText(output_lines), focusable=False)

    def accept():
        show_log_popup(floats, output_control, on_close=lambda: get_app().exit())

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
            log_message(output_lines, output_control, 'fg:blue', f'[DRY RUN] DISK/PARTITION: {disk}/{partition} UUID: {uuid} LABEL: {label} MOUNT NAME: {mount_name}')
            log_message(output_lines, output_control, 'fg:blue', f'[DRY RUN] PHYSICAL LOCATION: {phy} FSTAB: {add_fstab} CONFIG: {add_config} CARD: {card} SLOT: {slt}')

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

        log_message(output_lines, output_control, 'fg:green', 'Disk setup complete. Press ESC to exit.')

    layout_items = [
        Label("Select a disk to initialize:"),
        disk_radio,
        spacer,
        Label("Enter the partition label (optional)"),
        label_input,
        spacer,
        Label("Available mount points: " + ", ".join(list_available_mounts())),
        mount_input,
        spacer,
        Label("Add to /etc/fstab?"),
        fstab_input,
        spacer,
        Label("Add to disk_config?"),
        config_input,
        spacer,
        Label("Enter physical location (optional):"),
        phy_input,
        spacer,
    ]

    if app_config.get("enable_sas"):
        layout_items += [
            Label("Enter SAS controller number:"),
            sas_card_input,
            spacer,
            Label("Enter SAS slot number:"),
            sas_slot_input,
            spacer,
        ]

    
    floats = []

    layout_items.append(Window(height=D(weight=1)))
    layout_items.append(Button(
        text="Apply",
        handler=lambda: show_confirmation_dialog(
            floats,            
            lambda: (get_app().layout.focus(dialog), get_app().invalidate(), accept()),
            lambda: (get_app().layout.focus(dialog), get_app().invalidate())
        )
    ))    
    layout_items.append(Label("Press ESC to exit"))

    body = HSplit(layout_items, width=D(), height=D())
    dialog = Dialog(title="Disk Initialization", body=body, buttons=[], width=80, with_background=False)
    
    root_container = FloatContainer(
        content=dialog,
        floats=floats
    )

    layout = Layout(container=root_container)

    kb = KeyBindings()

    @kb.add('escape')
    def exit_(event):
        event.app.exit()


    style = Style.from_dict({
        "window": "bg:default",
        "frame.label": "bg:#000000 fg:#ffffff",
        "frame.border": "fg:#ffffff",
        "label": "fg:#ffffff",
        
        "radio-list": "fg:#ffffff bg:",
        "radio-list.focused": "fg:#ffffff bg:",
        "radio": "fg:#ffffff bg:#000000",
        "radio-selected": "fg:#ffffff bold",
        "radio-checked": "fg:#ffffff bg:#000000",
        "radio-unchecked": "fg:#ffffff bg:#000000",

        "confirmation-text": "fg:white",
        "dialog": "bg:",
        "dialog.body": "bg:",
        "dialog.shadow": "bg:",        
        "dialog.frame": "fg:#ffffff",
        "button": "bg:#444444 #ffffff",
        "button.focused": "bg:#666666 #ffffff",
        
        "text-area": "bg:#111111 fg:#cccccc",
        "output-field": "bg:",
    })


    app = Application(layout=layout, key_bindings=kb, full_screen=True, mouse_support=False, style=style)
    app.run()

    

def initialize_disk(disk_config, app_config):
    dry_run = True
    interactive_disk_setup(app_config, disk_config, dry_run=dry_run)
