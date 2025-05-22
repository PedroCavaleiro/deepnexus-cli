from deepnexus.utils import run_command

# Commands supported by storcli64
# https://techdocs.broadcom.com/us/en/storage-and-ethernet-connectivity/enterprise-storage-solutions/storcli-12gbs-megaraid-tri-mode/1-0/v11869215/v11673749/v11675603/v11675913.html

def show_sas_all():
    output = run_command("/opt/MegaRAID/storcli/storcli64 /call/sall show")
    print(output)

def show_sas_disk(card, slot):
    output = run_command(f"/opt/MegaRAID/storcli/storcli64 /c{card}/s{slot} show")
    print(output)

def show_disk_smart(card, slot):
    output = run_command(f"/opt/MegaRAID/storcli/storcli64 /c{card}/s{slot} show smart")
    print(output)

def start_locate_drive(card, slot):
    output = run_command(f"/opt/MegaRAID/storcli/storcli64 /c{card}/s{slot} start locate")
    print(output)

def end_locate_drive(card, slot):
    output = run_command(f"/opt/MegaRAID/storcli/storcli64 /c{card}/s{slot} stop locate")
    print(output)