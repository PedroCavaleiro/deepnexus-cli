from diskmanagement.sas import get_storcli_temperatures

def show_temperatures():
    temps = get_storcli_temperatures()
    for ctrl, temp in temps.items():
        print(f"{ctrl}: {temp}")