from diskmanagement.sas import get_storcli_temperatures

def show_temperatures():
    temps = get_storcli_temperatures()
    for ctrl, temp in temps.items():
        print(f"{ctrl}: {temp}")

def build_temperature_tree():
    return {
        "SAS": get_storcli_temperatures()
    }

def print_tree(data, prefix=""):
    last_key = list(data.keys())[-1]
    for key in data:
        is_last = (key == last_key)
        branch = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        value = data[key]
        if isinstance(value, dict):
            print(f"{prefix}{branch}{key}")
            print_tree(value, prefix + extension)
        else:
            print(f"{prefix}{branch}{key}: {value}°C")