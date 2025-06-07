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
from prompt_toolkit.styles import Style
import asyncio
font = Ansi.escape

def run_fstab_menu():
    asyncio.run(run_fstab_menu_async())

def build_lines(disks, fstab_uuids, selected_index, mounted_disks):
    # Determine column widths
    mount_width = max(len(d["mount"]) for d in disks) if disks else 10
    size_width = max(len(d["size"]) for d in disks) if disks else 10
    uuid_width = max(len(d["uuid"]) for d in disks) if disks else 10

    lines = []
    for i, disk in enumerate(disks):
        checked = "[x]" if disk["uuid"] in fstab_uuids else "[ ]"
        pointer = "=> " if i == selected_index else "   "
        connected = disk["uuid"] in mounted_disks
        status = "" if connected else " (not connected)"

        # Format each column with padding
        mount = disk["mount"].ljust(mount_width)
        size = disk["size"].rjust(size_width)
        uuid = disk["uuid"].ljust(uuid_width)

        line = f"{pointer}{checked} {mount}  {size}  UUID={uuid}{status}"
        style = "class:highlight" if i == selected_index else "class:dim" if not connected else ""
        lines.append((style, line + "\n"))

    return FormattedText(lines)

async def run_fstab_menu_async():
    mounted_disks = get_mounted_disks()
    fstab_entries = get_fstab_entries()

    # Merge fstab entries with mounted disks (mounted takes precedence)
    all_disks = {**fstab_entries, **mounted_disks}  # mounted_disks overrides same UUIDs
    disks = sorted(all_disks.values(), key=lambda disk: disk.get("mount", ""))
    fstab_uuids = set(fstab_entries.keys())
    selected = [0]

    def get_display_text():
        return build_lines(disks, fstab_uuids, selected[0], mounted_disks)

    text_control = FormattedTextControl(get_display_text, focusable=True)
    disk_window = Window(content=text_control, always_hide_cursor=True)
    footer = Window(height=1, content=FormattedTextControl(
        "Use ↑/↓ to navigate, space to toggle, r to remove, q to quit"
    ))


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
        fstab_uuids.update(get_fstab_entries().keys())

    @kb.add("r")
    def remove(event):
        disk = disks[selected[0]]
        uuid = disk["uuid"]
        mount = disk["mount"]
        present = uuid in fstab_uuids
        remove_fstab_entry(uuid, mount, present)
        fstab_uuids.clear()
        fstab_uuids.update(get_fstab_entries().keys())


    @kb.add("q")
    @kb.add("escape")
    def exit_app(event):
        event.app.exit()

    style = Style.from_dict({
        "highlight": "bold underline",
        "dim": "fg:#888888",
    })

    app = Application(
        layout=Layout(body),
        key_bindings=kb,
        full_screen=True,
        style=style
    )
    await app.run_async()

def get_mounted_disks():
    result = subprocess.run(['lsblk', '-b', '-o', 'MOUNTPOINT,UUID,SIZE'], capture_output=True, text=True)
    disks = {}
    for line in result.stdout.splitlines()[1:]:
        parts = line.strip().split(None, 2)
        if len(parts) == 3:
            mount, uuid, size = parts
            if mount and mount.startswith("/mnt/") and uuid:
                disks[uuid] = {
                    "mount": mount,
                    "uuid": uuid,
                    "size": format_size(int(size)) if size.isdigit() else "unknown"
                }
    return disks

def get_fstab_entries():
    entries = {}
    if os.path.exists(FSTAB_PATH):
        with open(FSTAB_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("UUID="):
                    parts = line.split()
                    if len(parts) >= 2:
                        uuid = parts[0].split("=")[1]
                        mount = parts[1]
                        if mount.startswith("/mnt/"):
                            entries[uuid] = {
                                "uuid": uuid,
                                "mount": mount,
                                "size": "not connected"
                            }
    return entries


def remove_fstab_entry(uuid, mount, present):
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

def toggle_fstab_entry(uuid, mount, present):
    lines = []
    new_line = f"UUID={uuid} {mount} {MOUNT_OPTIONS}\n"
    updated = False

    if os.path.exists(FSTAB_PATH):
        with open(FSTAB_PATH, "r") as f:
            for line in f:
                stripped = line.strip()
                if f"UUID={uuid}" in stripped:
                    if present:
                        # Cement: comment it out if not already
                        if not stripped.startswith("#"):
                            line = "# " + line
                    else:
                        # Reactivate: uncomment if commented
                        if stripped.startswith("#"):
                            line = line.lstrip("# ").rstrip() + "\n"
                        else:
                            # already active, skip duplication
                            updated = True
                    updated = True
                lines.append(line)

    if not updated and not present:
        lines.append(new_line)

    with open(FSTAB_PATH, "w") as f:
        f.writelines(lines)
