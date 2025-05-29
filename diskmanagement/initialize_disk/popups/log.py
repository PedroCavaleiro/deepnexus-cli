from prompt_toolkit.widgets import Button, Dialog
from prompt_toolkit.layout.containers import HSplit, Window, Float
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.margins import ScrollbarMargin

def show_log_popup(floats, output_control, on_close):
    output_window = Window(
        content=output_control,
        wrap_lines=True,
        height=10,
        right_margins=[ScrollbarMargin()],
        always_hide_cursor=True
    )

    dialog = Dialog(
        title="Operation Log",
        body=HSplit([output_window]),
        buttons=[
            Button(text="Close", handler=lambda: (floats.clear(), on_close()))
        ],
        width=120
    )

    floats.append(Float(content=dialog))
    get_app().layout.focus(dialog)
    get_app().invalidate()