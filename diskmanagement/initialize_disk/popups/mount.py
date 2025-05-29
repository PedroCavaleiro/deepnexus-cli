from prompt_toolkit.application.current import get_app
from prompt_toolkit.widgets import Button, Dialog, Box, RadioList, TextArea
from prompt_toolkit.layout.containers import Float
from prompt_toolkit.layout.containers import HSplit, Float, ConditionalContainer
from prompt_toolkit.filters import Condition
from diskmanagement.initialize_disk.utils import list_available_mounts

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
            floats.clear()
            get_app().invalidate()
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