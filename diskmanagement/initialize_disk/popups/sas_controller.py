from diskmanagement.sas import show_sas_all
from diskmanagement.utils import parse_sas_controllers
from prompt_toolkit.widgets import Button, Dialog, Box, RadioList
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import HSplit, Float

def show_sas_controller_popup(floats, selected_sas_container, on_close, dialog):
    sas_output = show_sas_all(False)
    controller_ids = parse_sas_controllers(sas_output)

    entries = [('-1', "None")]
    entries.extend([(cid, f"Controller {cid}") for cid in controller_ids])
    
    radio = RadioList(entries)
    radio.current_value = '-1'

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