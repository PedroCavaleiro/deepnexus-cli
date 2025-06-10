import os
import subprocess
from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Button, Dialog, Label, RadioList
from prompt_toolkit.layout.containers import HSplit, Window, Float, FloatContainer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application.current import get_app
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout.margins import ScrollbarMargin
from diskmanagement.utils import list_mounted_disks, log_message
from diskmanagement.initialize_disk.popups.log import show_log_popup
from deepnexus.vars import COLORS

def run_command(cmd_list):
    """Run a command list and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)
    
def unmount_disk(selected_disk, force, output_lines, output_control, dry_run):
    log_message(output_lines, output_control, COLORS['info'], f"Unmounting {selected_disk}")
    if not dry_run:
        ret, out, err = run_command(["umount", selected_disk])
        if ret != 0:
            log_message(output_lines, output_control, COLORS['error'],
                        f"Failed to unmount {selected_disk} with error: {err.strip()}")
            if force:
                log_message(output_lines, output_control, COLORS['info'],
                            "Forcing unmount")
                ret_f, out_f, err_f = run_command(["umount", "-f", selected_disk])
                if ret_f != 0:
                    log_message(output_lines, output_control, COLORS['error'],
                                f"Force unmount failed with error: {err_f.strip()}")
                else:
                    log_message(output_lines, output_control, COLORS['success'],
                                f"Force unmount succeeded for {selected_disk}")
        else:
            log_message(output_lines, output_control, COLORS['success'],
                        f"Unmounted {selected_disk} successfully")
    else:
        log_message(output_lines, output_control, COLORS['info'],
                    f"[DRY RUN] Unmounting {selected_disk}")
        if force:
            log_message(output_lines, output_control, COLORS['info'],
                        f"[DRY RUN] Would force unmount {selected_disk}")
        else:
            log_message(output_lines, output_control, COLORS['success'],
                        f"[DRY RUN] Unmount command simulated for {selected_disk}")

def show_confirmation_unmount_dialog(floats, selected_disk, output_lines, output_control, dry_run):
    force_unmount = [False]

    def toggle_force():
        force_unmount[0] = not force_unmount[0]
        checkbox_button.text = f"Force unmount: [{'X' if force_unmount[0] else ' '}]"
        get_app().invalidate()

    checkbox_button = Button(text="Force unmount: [ ]", handler=toggle_force)

    dialog_body = HSplit([
        Label(text=f"Do you really want to unmount {selected_disk}?"),
        checkbox_button,
    ])

    def on_ok():
        floats.clear()
        unmount_disk(selected_disk, force_unmount[0], output_lines, output_control, dry_run)
        show_log_popup(floats, output_control, on_close=lambda: get_app().exit())

    def on_cancel():
        floats.clear()
        get_app().layout.focus_previous()
        get_app().invalidate()

    dialog = Dialog(
        title="Confirm Unmount",
        body=dialog_body,
        buttons=[
            Button(text="OK", handler=on_ok),
            Button(text="Cancel", handler=on_cancel)
        ],
        width=60
    )
    floats.append(Float(content=dialog))
    get_app().layout.focus(dialog)
    get_app().invalidate()

def interactive_unmount_disk(dry_run=False):
    floats = []

    disks = list_mounted_disks()
    if not disks:
        disks = ["<none>"]

    # Create a RadioList to let the user select one.
    disk_radio = RadioList([(d, d) for d in disks])

    output_lines = []
    output_control = FormattedTextControl(
        lambda: FormattedText([(None, line + "\n") for line in output_lines]),
        focusable=False
    )

    def do_unmount():
        selected_disk = disk_radio.current_value
        if selected_disk == "<none>":
            return
        show_confirmation_unmount_dialog(floats, selected_disk, output_lines, output_control, dry_run)

    kb = KeyBindings()

    @kb.add("enter")
    def unmount_event(event):
        do_unmount()

    @kb.add("escape")
    def exit_(event):
        event.app.exit()

    # Build the main layout.
    layout_items = [
        Label("Select a mounted disk under /mnt to unmount:"),
        disk_radio,
        Label("Press ENTER to unmount the selected disk."),
        Label("Press ESC to exit."),
        Window(height=D(weight=1)),
    ]

    body = HSplit(layout_items)
    root_container = FloatContainer(content=body, floats=floats)
    layout = Layout(root_container)

    style = Style.from_dict({
        "window": "bg:default",
        "frame.label": "bg:#000000 fg:#ffffff",
        "dialog": "bg:",
        "button": "bg:#444444 fg:#ffffff",
        "button.focused": "bg:#666666 fg:#ffffff",
        "label": "fg:#ffffff",
        "radio-list": "fg:#ffffff",
        "output-field": "bg:#111111 fg:#cccccc",
    })

    app = Application(layout=layout, key_bindings=kb, full_screen=True, mouse_support=False, style=style)
    app.run()

def unmount_disk_module():
    interactive_unmount_disk(dry_run=True)