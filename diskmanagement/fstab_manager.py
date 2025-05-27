from deepnexus.utils import get_fstab_uuids, format_size
import os
from deepnexus.escape import Ansi
from deepnexus.vars import FSTAB_PATH, MOUNT_OPTIONS
import subprocess
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Frame
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout.controls import FormattedTextControl
import asyncio
font = Ansi.escape

def run_fstab_menu():
    asyncio.run(run_fstab_menu_async())

def build_lines(disks, fstab_uuids, selected_index):
    lines = []
    for i, disk in enumerate(disks):
        checked = "[x]" if disk["uuid"] in fstab_uuids else "[ ]"
        pointer = "=> " if i == selected_index else "   "
        line = f"{pointer}{checked} {disk['mount']} ({disk['size']}) UUID={disk['uuid']}"
        style = "class:highlight" if i == selected_index else ""
        lines.append((style, line + "\n"))
    return FormattedText(lines)

async def run_fstab_menu_async():
    disks = get_mounted_disks()
    fstab_uuids = get_fstab_uuids()
    selected = [0]

    def get_display_text():
        return build_lines(disks, fstab_uuids, selected[0])

    text_control = FormattedTextControl(get_display_text, focusable=True)
    disk_window = Window(content=text_control, always_hide_cursor=True)
    footer = Window(height=1, content=FormattedTextControl("Press (space) to toggle or q to quit"))

    root_container = HSplit([disk_window, footer])
    body = Frame(root_container, title="FSTAB Manager")

    kb = KeyBindings()

    @kb.add("up")
    def up(event):
        selected[0] = (selected[0] - 1) % len(disks)

    @kb.add("down")
    def down(event):
        selected[0] = (selected[0] + 1) % len(disks)

    @kb.add(" ")
    def toggle(event):
        disk = disks[selected[0]]
        uuid = disk["uuid"]
        mount = disk["mount"]
        present = uuid in fstab_uuids
        toggle_fstab_entry(uuid, mount, present)
        fstab_uuids.clear()
        fstab_uuids.update(get_fstab_uuids())

    @kb.add("q")
    @kb.add("escape")
    def exit_app(event):
        event.app.exit()

    app = Application(layout=Layout(body), key_bindings=kb, full_screen=True)
    await app.run_async()

def get_mounted_disks():
    result = subprocess.run(['lsblk', '-b', '-o', 'MOUNTPOINT,UUID,SIZE'], capture_output=True, text=True)
    disks = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.strip().split(None, 2)
        if len(parts) == 3:
            mount, uuid, size = parts
            if mount.startswith("/mnt/") and uuid != "":
                disks.append({
                    "mount": mount,
                    "uuid": uuid,
                    "size": format_size(int(size))
                })
    return disks

def toggle_fstab_entry(uuid, mount, present):
    lines = []
    if os.path.exists(FSTAB_PATH):
        with open(FSTAB_PATH, "r") as f:
            lines = f.readlines()

    new_line = f"UUID={uuid} {mount} {MOUNT_OPTIONS}\n"

    if present:
        lines = [line for line in lines if f"UUID={uuid}" not in line]
    else:
        lines.append(new_line)

    with open(FSTAB_PATH, "w") as f:
        f.writelines(lines)