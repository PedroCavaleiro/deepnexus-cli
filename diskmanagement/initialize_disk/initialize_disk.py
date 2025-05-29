from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Button, Dialog, Label, TextArea, RadioList
from prompt_toolkit.layout.containers import HSplit, Window, FloatContainer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application.current import get_app
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
import os
from deepnexus.utils import run_command
from diskmanagement.initialize_disk.utils import list_unmounted_disks, get_partition_uuid, log_message
from diskmanagement.initialize_disk.popups import show_mount_popup, show_sas_controller_popup, show_sas_slot_popup, show_log_popup, show_confirmation_dialog

def initialize_disk(disk_config, app_config):
    dry_run = True
    interactive_disk_setup(app_config, disk_config, dry_run=dry_run)

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
            floats, sas_controller_value[0], sas_slot_value, lambda: get_app().invalidate(), dialog
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
            log_message(output_lines, output_control, 'fg:#DC3545', f'[DRY RUN] DISK/PARTITION: {disk}/{partition} UUID: {uuid} LABEL: {label} MOUNT NAME: {mount_name}')
            log_message(output_lines, output_control, 'fg:#DC3545', f'[DRY RUN] PHYSICAL LOCATION: {phy} FSTAB: {add_fstab} CONFIG: {add_config} CARD: {card} SLOT: {slt}')

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

        log_message(output_lines, output_control, 'fg:#198754', 'Disk setup complete. Press ESC to exit.')

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
