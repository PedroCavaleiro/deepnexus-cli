from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Button, Dialog, Label, TextArea, Box, RadioList
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, FloatContainer, Float, ConditionalContainer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application.current import get_app
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.filters import Condition
import os
import json
import subprocess
from deepnexus.utils import run_command, load_config
from deepnexus.vars import DISKS_CONFIG_PATH, APP_CONFIG_PATH
from diskmanagement.sas import show_sas_all
import re

def parse_sas_slots(output: str):
    slot_pattern = re.compile(
        r'(?P<eid_col>:)?(?P<slot>\d+)\s+'
        r'\d+\s+\S+\s+-\s+(?P<size>\d+\.\d+ TB)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<model>\S+)'
    )
    return [(slot, model, size) for _, slot, size, model in slot_pattern.findall(output)]

def load_used_slots():
    config = load_config(DISKS_CONFIG_PATH)
    return {str(d.get("slt")) for d in config if "slt" in d}

def parse_sas_controllers(sas_output: str):
    controllers = re.findall(r'^Controller\s+=\s+(\d+)', sas_output, re.MULTILINE)
    return list(set(controllers))

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

    # Get all active mount points
    mounted = subprocess.check_output(['lsblk', '-nr', '-o', 'MOUNTPOINT']).decode().splitlines()
    mounted = set(filter(None, mounted))  # Remove empty lines

    # Check each /mnt subdirectory to see if it's not actively mounted
    return [d for d in os.listdir('/mnt')
        if os.path.isdir(f"/mnt/{d}") and f"/mnt/{d}" not in mounted]

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

def show_confirmation_dialog(floats, on_confirm, on_cancel, initialization_info):
    app_config = load_config(APP_CONFIG_PATH)
    text=[
        ("class:confirmation-text", "Are you sure you want to proceed with disk initialization?")    
    ]

    table_rows = [
        ("Disk", initialization_info['dev']),
        ("Mount", initialization_info['mnt']),
        ("Label", initialization_info['label'] if initialization_info['label'] else "NO LABEL"),
        ("Add to fstab", str(initialization_info['fstab'])),
        ("Add to configuration", str(initialization_info['disk_config'])),
        ("Physical location", initialization_info['phy'] if initialization_info['phy'] else "Unknown"),
    ]

    if app_config['enable_sas']:
        table_rows.append(("SAS Controller", initialization_info['controller'] if int(initialization_info['controller']) != -1 else 'NONE'))
        table_rows.append(("SAS Slot", initialization_info['slot'] if int(initialization_info['slot']) != -1 else 'NONE'))

    formatted_table = [
        ("class:confirmation-text", f"{key:<22}: {value}\n")
        for key, value in table_rows
    ]

    centered_text_window = VSplit([
        Window(width=D(weight=1)),
        HSplit([
            Window(content=FormattedTextControl(text)),
            Window(height=1, content=FormattedTextControl('')),
            Window(content=FormattedTextControl(formatted_table)),
        ]),
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
    mount_point_value = [None]
    mount_button = Button(
        text="Select mount point", 
        handler=lambda: show_mount_popup(
            floats, mount_point_value, lambda: get_app().invalidate(), dialog
        )
    )
    phy_input = TextArea(prompt='Physical location: ', height=1)
    fstab_input = RadioList([(True, 'Yes'), (False, 'No')])
    config_input = RadioList([(True, 'Yes'), (False, 'No')])
    sas_controller_value = [-1]
    sas_controller_button = Button(
        text="Select SAS controller", 
        handler=lambda: show_sas_controller_popup(
            floats, sas_controller_value, lambda: get_app().invalidate(), dialog
        )
    )
    sas_slot_value = [-1]
    sas_slot_button = Button(
        text="Select SAS slot", 
        handler=lambda: show_sas_slot_popup(
            floats, sas_slot_value, lambda: get_app().invalidate(), dialog
        )
    )

    output_lines = []
    output_control = FormattedTextControl(lambda: FormattedText(output_lines), focusable=False)

    def get_mount_text():
        value = mount_point_value[0]
        text = f"Selected mount: {value}" if value else "Selected mount: <none>"
        return FormattedText([("white", text)])

    def get_sas_controller_text():
        value = sas_controller_value[0]
        text = f"SAS Controler: {value}" if int(value) != -1 else "SAS Controller: None"
        return FormattedText([("white", text)])
    
    def get_sas_slot_text():
        value = sas_slot_value[0]
        text = f"SAS Slot: {value}" if int(value) != -1 else "SAS Slot: None"
        return FormattedText([("white", text)])

    def accept():
        show_log_popup(floats, output_control, on_close=lambda: get_app().exit())

        disk = disk_radio.current_value
        label = label_input.text.strip() or "NO LABEL"
        mount_name = mount_point_value[0]
        mount_point = f"/mnt/{mount_name}"
        phy = phy_input.text.strip() or "Unknown"
        add_fstab = fstab_input.current_value
        add_config = config_input.current_value
        card = int(sas_controller_value[0]) if app_config.get("enable_sas") else -1
        slt = int(sas_slot_value[0]) if app_config.get("enable_sas") else -1

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

    mount_label_control = FormattedTextControl(text=get_mount_text)
    mount_label_window = Window(content=mount_label_control, height=1)
    sas_controller_label_control = FormattedTextControl(text=get_sas_controller_text)
    sas_controller_label_window = Window(content=sas_controller_label_control, height=1)
    sas_slot_label_control = FormattedTextControl(text=get_sas_slot_text)
    sas_slot_label_window = Window(content=sas_slot_label_control, height=1)

    layout_items = [
        Label("Select a disk to initialize:"),
        disk_radio,
        spacer,
        Label("Enter the partition label (optional)"),
        label_input,
        spacer,
        mount_label_window,
        mount_button,
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
            sas_controller_label_window,
            sas_controller_button,
            spacer,
            sas_slot_label_window,
            sas_slot_button,
            spacer,
        ]

    
    floats = []

    layout_items.append(Window(height=D(weight=1)))
    layout_items.append(Button(
        text="Apply",
        handler=lambda: show_confirmation_dialog(
            floats,            
            lambda: (get_app().layout.focus(dialog), get_app().invalidate(), accept()),
            lambda: (get_app().layout.focus(dialog), get_app().invalidate()),
            {
                "dev": disk_radio.current_value,
                "mnt": mount_point_value[0],
                "label": label_input.text,
                "fstab": fstab_input.current_value,
                "disk_config": config_input.current_value,
                "phy": phy_input.text.strip(),
                "controller": sas_controller_value[0],
                "slot": sas_slot_value[0]
            }
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

def show_mount_popup(floats, selected_value_container, on_close, dialog):
    mounts = list_available_mounts()
    entries = [(f"/mnt/{m}", m) for m in mounts]
    entries.append(("custom", "Enter new mount point..."))

    radio = RadioList(entries)
    custom_input = TextArea(prompt="New mount point name: /mnt/", height=1)

    showing_custom_input = [False]

    radio_container = ConditionalContainer(
        content=Box(radio, padding=1),
        filter=Condition(lambda: not showing_custom_input[0])
    )

    custom_container = ConditionalContainer(
        content=Box(custom_input, padding=1),
        filter=Condition(lambda: showing_custom_input[0])
    )

    body = HSplit([radio_container, custom_container])

    def close_popup():
        if floats:
            floats.clear()
        get_app().layout.focus(dialog)
        get_app().invalidate()
        on_close()

    def on_custom_ok():
        value = custom_input.text.strip()
        if value:
            selected_value_container[0] = f"/mnt/{value}"
            close_popup()

    def on_custom_cancel():
        close_popup()

    def on_select():
        choice = radio.current_value
        if choice == "custom":
            showing_custom_input[0] = True
            floats.clear()  # remove old popup
            get_app().invalidate()
            # recreate dialog with new buttons
            new_popup = Dialog(
                title="Select Mount Point",
                body=body,
                buttons=[
                    Button(text="OK", handler=on_custom_ok),
                    Button(text="Cancel", handler=on_custom_cancel),
                ],
                width=60
            )
            floats.append(Float(content=new_popup))
            get_app().invalidate()
            get_app().layout.focus(custom_input)
        else:
            selected_value_container[0] = choice
            close_popup()

    popup_dialog = Dialog(
        title="Select Mount Point",
        body=body,
        buttons=[
            Button(text="OK", handler=on_select),
            Button(text="Cancel", handler=close_popup),
        ],
        width=60,
    )

    floats.append(Float(content=popup_dialog))
    get_app().invalidate()
    get_app().layout.focus(popup_dialog)

def show_sas_controller_popup(floats, selected_sas_container, on_close, dialog):
    sas_output = show_sas_all(False)
    controller_ids = parse_sas_controllers(sas_output)

    # Build entries with default -1 (None) selected
    entries = [('-1', "None")]
    entries.extend([(cid, f"Controller {cid}") for cid in controller_ids])
    
    radio = RadioList(entries)
    radio.current_value = '-1'  # Default to "None"

    def on_select():
        selected_sas_container[0] = int(radio.current_value)
        floats.clear()
        get_app().layout.focus(dialog)
        on_close()

    popup_dialog = Dialog(
        title="Select SAS Controller",
        body=Box(HSplit([radio]), padding=1),
        buttons=[
            Button(text="OK", handler=on_select),
            Button(text="Cancel", handler=lambda: (
                floats.clear(),
                get_app().layout.focus(dialog),
                on_close()
            )),
        ],
        width=60
    )

    floats.append(Float(content=popup_dialog))
    get_app().layout.focus(popup_dialog)
    get_app().invalidate()

def show_sas_slot_popup(floats, selected_value_container, on_close, dialog):
    output = show_sas_all(False)
    entries = [("-1", "None")]  # default option

    used_slots = load_used_slots()
    parsed_slots = parse_sas_slots(output)

    for slot, model, size in parsed_slots:
        label = f"Slot {slot} ({model} {size})"
        if slot in used_slots:
            label += " (in use)"
        entries.append((slot, label))

    radio = RadioList(entries)
    radio.current_value = "-1"

    def on_select():
        selected_value_container[0] = radio.current_value
        floats.clear()
        get_app().layout.focus(dialog)
        on_close()

    popup_dialog = Dialog(
        title="Select SAS Slot",
        body=Box(radio, padding=1),
        buttons=[
            Button(text="OK", handler=on_select),
            Button(text="Cancel", handler=lambda: (
                floats.clear(),
                get_app().layout.focus(dialog),
                on_close()
            )),
        ],
        width=60
    )

    floats.append(Float(content=popup_dialog))
    get_app().layout.focus(popup_dialog)
    get_app().invalidate()

def initialize_disk(disk_config, app_config):
    dry_run = True
    interactive_disk_setup(app_config, disk_config, dry_run=dry_run)
