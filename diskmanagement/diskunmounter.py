from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Button, Dialog, Label, RadioList
from prompt_toolkit.layout.containers import HSplit, Window, FloatContainer, Float
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application.current import get_app
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
import os
import subprocess
import stat
from deepnexus.utils import run_command
from diskmanagement.utils import log_message
from diskmanagement.initialize_disk.popups import show_log_popup
from deepnexus.vars import COLORS

def get_mount_point_device(mount_point):
    """Get the device associated with a mount point using findmnt."""
    try:
        result = subprocess.run(
            ['findmnt', '-no', 'SOURCE', mount_point],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None

def list_mounted_disks():
    """Return a list of mounted block devices under /mnt/."""
    valid_devices = []

    # List all directories in /mnt/
    try:
        for mount_point in os.listdir('/mnt'):
            full_path = os.path.join('/mnt', mount_point)
            if not os.path.isdir(full_path):
                continue

            # Get the associated device
            device = get_mount_point_device(full_path)
            if device and is_block_device(device):
                valid_devices.append((device, full_path))
    except (FileNotFoundError, PermissionError) as e:
        log_message(f"Failed to list mounted disks: {e}")

    return [device for device, path in valid_devices]

def is_block_device(path):
    """Check if a given path refers to a block device."""
    try:
        stat_result = os.stat(path)
        return stat.S_ISBLK(stat_result.st_mode)
    except OSError as e:
        log_message(f"Failed to check {path}: {e}")
        return False

def get_disk_size(device):
    """Get the size of a block device."""
    try:
        result = subprocess.run(['blockdev', '--getsize64', device],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            return int(result.stdout) // (1024 * 1024)
    except Exception as e:
        log_message(f"Failed to get size for {device}: {e}")
    return None

def interactive_unmount_disk(dry_run=False):
    floats = []

    output_lines = []
    output_control = FormattedTextControl()

    force_unmount_value = [False]

    disk_radio_options = list_mounted_disks()
    if not disk_radio_options:
        log_message(output_lines, output_control, "fg:#ff0000", "No disks found to unmount.")
        return

    def update_force(choice):
        force_unmount_value[0] = choice

    def accept():
        show_log_popup(floats, output_control, on_close=lambda: get_app().exit())

        disk = disk_radio.current_value
        force = force_unmount_value[0]

        if not dry_run:
            log_message(output_lines, output_control, "fg:#00ff00", f"Unmounting {disk}")
            result = run_command(f"umount {disk}")

            if "failed" in result.lower() or "error" in result.lower():
                if force:
                    log_message(output_lines, output_control, "fg:#ffa500", f"Failed to unmount. Trying to force unmount.")
                    result = run_command(f"umount -f {disk}")
                    if "failed" in result.lower() or "error" in result.lower():
                        log_message(output_lines, output_control, "fg:#ff0000", f"Force unmount failed.")
                    else:
                        log_message(output_lines, output_control, "fg:#008000", f"Disk {disk} force unmounted successfully.")
                else:
                    log_message(output_lines, output_control, "fg:#ff0000", f"Unmount failed. Consider using force unmount.")
            else:
                log_message(output_lines, output_control, "fg:#008000", f"Disk {disk} unmounted successfully.")
        else:
            uuid = 'dry-run-uuid'
            log_message(output_lines, output_control, "fg:#00ff00", f"[DRY RUN] DISK: {disk} UUID: {uuid} FORCE: {force}")

        log_message(output_lines, output_control, "fg:#008000", 'Disk unmounted successfully. Press ESC to exit.')

    # Define the disk_radio variable
    disk_radio = RadioList(disk_radio_options)

    force_label_text = FormattedText([("label", "Force Unmount")])
    force_radio_list = RadioList(
        [(True, 'Yes'), (False, 'No')],
        handler=update_force
    )

    spacer = Window(height=1)
    layout_items = [
        Label("Select a disk to unmount:"),
        disk_radio,
        spacer,
        Window(content=FormattedTextControl(text=force_label_text)),
        force_radio_list,
        spacer,
        Button(
            text="Apply",
            handler=lambda: show_confirmation_disk_unmount_dialog(
                floats,
                lambda: (get_app().layout.focus(dialog), get_app().invalidate(), accept()),
                lambda: (get_app().layout.focus(dialog), get_app().invalidate())
            )
        ),
    ]

    body = HSplit(layout_items, width=D(weight=1))
    dialog = Dialog(title="Disk Unmount", body=body, buttons=[], width=80)

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

def show_confirmation_disk_unmount_dialog(floats, confirm_handler):
    confirmation_text = "Confirm unmount?"

    dialog = Dialog(
        title="Confirmation",
        body=[
            Window(content=FormattedTextControl(text=FormattedText([("confirmation-text", confirmation_text)]))),
            HSplit([
                Button(text="Confirm", handler=lambda: (floats.clear(), confirm_handler())),
                Button(text="Cancel", handler=lambda: (floats.clear()))
            ])
        ],
        buttons=[]
    )

    floats.append(Float(content=dialog))
    get_app().layout.focus(dialog)
    get_app().invalidate()