from prompt_toolkit.application.current import get_app
from diskmanagement.initialize_disk.utils import parse_sas_slots, load_used_slots
from prompt_toolkit.widgets import Button, Dialog, Box, RadioList
from prompt_toolkit.layout.containers import Float
from diskmanagement.sas import show_sas_controller

def show_sas_slot_popup(floats, controller, selected_value_container, on_close, dialog):
    output = show_sas_controller(controller, False)
    entries = [("-1", "None")]

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