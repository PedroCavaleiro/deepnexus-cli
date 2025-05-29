from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Button, Dialog, Label, RadioList
from prompt_toolkit.layout.containers import HSplit, Window, FloatContainer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application.current import get_app
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
import os
from deepnexus.utils import run_command
from diskmanagement.utils import list_unmounted_partitions, get_partition_uuid, log_message, get_disk_size
from diskmanagement.initialize_disk.popups import show_mount_popup, show_log_popup, show_confirmation_disk_mount_dialog
from deepnexus.vars import COLORS

def mount_disk_module():
    dry_run = True
    interactive_mount_disk(dry_run=dry_run)

def add_to_fstab(uuid, mount_point, output_lines, output_control):
    fstab_entry = f"UUID={uuid} {mount_point} ext4 defaults,nofail,x-systemd.device-timeout=0 0 2"
    log_message(output_lines, output_control, f"fg:{COLORS['success']}", f"Partition {uuid} added to fstab on mount point {mount_point}")
    with open('/etc/fstab', 'a') as f:
        f.write(fstab_entry + '\n')

def interactive_mount_disk(dry_run=False):
    floats = []
    
    partitions = list_unmounted_partitions()
    spacer = Window(height=1, content=FormattedTextControl(''))

    disk_radio = RadioList([(p, f"{p} ({get_disk_size(p)})") for p in partitions])    
    mount_point_value = [None]
    mount_button = Button(
        text="Select mount point", 
        handler=lambda: show_mount_popup(
            floats, mount_point_value, lambda: get_app().invalidate(), dialog
        )
    )

    fstab_input = RadioList([(True, 'Yes'), (False, 'No')])

    output_lines = []
    output_control = FormattedTextControl(lambda: FormattedText(output_lines), focusable=False)

    def get_mount_text():
        value = mount_point_value[0]
        text = f"Selected mount: {value}" if value else "Selected mount: <none>"
        return FormattedText([("white", text)])

    def accept():
        show_log_popup(floats, output_control, on_close=lambda: get_app().exit())

        partition = disk_radio.current_value        
        mount_name = mount_point_value[0]
        mount_point = f"/mnt/{mount_name}"        
        add_fstab = fstab_input.current_value

        if not dry_run:
            os.makedirs(mount_point, exist_ok=True)
            log_message(output_lines, output_control, f"fg:{COLORS['success']}", f"Mount point {mount_point} ready")
            log_message(output_lines, output_control, f"fg:{COLORS['info']}", f"Mounting {partition}")
            run_command(f"mount {partition} {mount_point}")
            log_message(output_lines, output_control, f"fg:{COLORS['success']}", f"Mounted {partition}")
            uuid = get_partition_uuid(partition)
            if add_fstab:
                add_to_fstab(uuid, mount_point)
        else:
            uuid = 'dry-run-uuid'
            log_message(output_lines, output_control, f"fg:{COLORS['info']}", f'[DRY RUN] PARTITION: {partition} UUID: {uuid} MOUNT NAME: {mount_name} FSTAB: {add_fstab}')

        log_message(output_lines, output_control, f"fg:{COLORS['success']}", 'Disk mounted successfully. Press ESC to exit.')

    mount_label_control = FormattedTextControl(text=get_mount_text)
    mount_label_window = Window(content=mount_label_control, height=1)

    layout_items = [
        Label("Select a disk to initialize:"),
        disk_radio,
        spacer,
        mount_label_window,
        mount_button,
        spacer,
        Label("Add to /etc/fstab?"),
        fstab_input,
        spacer,
    ] 

    layout_items.append(Window(height=D(weight=1)))
    layout_items.append(Button(
        text="Apply",
        handler=lambda: show_confirmation_disk_mount_dialog(
            floats,            
            lambda: (get_app().layout.focus(dialog), get_app().invalidate(), accept()),
            lambda: (get_app().layout.focus(dialog), get_app().invalidate()),
            {
                "dev": disk_radio.current_value,
                "mnt": mount_point_value[0],
                "fstab": fstab_input.current_value,
            }
        )
    ))    
    layout_items.append(Label("Press ESC to exit"))

    body = HSplit(layout_items, width=D(), height=D())
    dialog = Dialog(title="Disk Mount", body=body, buttons=[], width=80, with_background=False)
    
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
