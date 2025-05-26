from diskmanagement.sas import get_storcli_temperatures
import re
import subprocess

def show_temperatures():
    temps = get_storcli_temperatures()
    for ctrl, temp in temps.items():
        print(f"{ctrl}: {temp}")

def build_temperature_tree():
    return {
        "SAS": get_storcli_temperatures(),
        **get_sensor_temperatures()
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

def get_sensor_temperatures():
    try:
        result = subprocess.run(
            ["sensors"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        output = result.stdout
        lines = output.splitlines()

        cpu_data = {}
        gpu_temp = None

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("coretemp-isa-0000"):
                current_section = "cpu"
                continue
            elif line.startswith("nouveau-pci-0800"):
                current_section = "gpu"
                continue
            elif not line or not re.match(r'^[\w\s\-]+:', line):
                current_section = None

            if current_section == "cpu":
                match = re.match(r'(Package id \d+|Core \d+):\s+\+([\d\.]+)°C', line)
                if match:
                    label, temp = match.groups()
                    cpu_data[label] = float(temp)

            elif current_section == "gpu":
                match = re.match(r'temp1:\s+\+([\d\.]+)°C', line)
                if match:
                    gpu_temp = float(match.group(1))

        return {"CPU": cpu_data, "GPU": {"Core": gpu_temp} if gpu_temp is not None else {}}
    except Exception as e:
        print(f"sensors error: {e}")
        return {"CPU": {}, "GPU": {}}