from prompt_toolkit.widgets import Button, Dialog
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, Float
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.controls import FormattedTextControl
from deepnexus.utils import load_config
from deepnexus.vars import APP_CONFIG_PATH

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

    get_app().layout.focus(yes_button)

    get_app().invalidate()