import re
from deepnexus.utils import run_command
from deepnexus.vars import STORCLI
import subprocess

# Commands supported by storcli64
# https://techdocs.broadcom.com/us/en/storage-and-ethernet-connectivity/enterprise-storage-solutions/storcli-12gbs-megaraid-tri-mode/1-0/v11869215/v11673749/v11675603/v11675913.html

def show_sas_all():
    output = run_command(f"{STORCLI} /call/sall show")
    print(output)

def show_sas_disk(card, slot):
    output = run_command(f"{STORCLI} /c{card}/s{slot} show")
    print(output)

def show_disk_smart(card, slot):
    output = run_command(f"{STORCLI} /c{card}/s{slot} show smart")
    print(output)

def start_locate_drive(card, slot):
    output = run_command(f"{STORCLI} /c{card}/s{slot} start locate")
    print(output)

def end_locate_drive(card, slot):
    output = run_command(f"{STORCLI} /c{card}/s{slot} stop locate")
    print(output)

def get_storcli_temperatures():
    try:
        result = subprocess.run(
            ["./storcli64", "/call", "show", "temperature"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        output = result.stdout
        temperatures = {}

        controller_blocks = output.split("Controller = ")
        for block in controller_blocks[1:]:
            lines = block.strip().splitlines()
            controller_id = lines[0].strip()
            for line in lines:
                match = re.search(r'ROC temperature\(Degree Celsius\)\s+(\d+)', line)
                if match:
                    temp = int(match.group(1))
                    temperatures[f"Controller {controller_id}"] = temp
                    break

        return temperatures

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(e.stderr)
        return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}