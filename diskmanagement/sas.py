from ..utils import run_command

def show_sas_all():
    output = run_command("/opt/MegaRAID/storcli/storcli64 /call/sall show")
    print(output)

def show_sas_disk(card, slot):
    output = run_command(f"/opt/MegaRAID/storcli/storcli64 /c{card}/s{slot} show")
    print(output)

def show_disk_smart(card, slot):
    output = run_command(f"/opt/MegaRAID/storcli/storcli64 /c{card}/s{slot} show smart")
    print(output)