from src.models import VMDetails


class CustomService:
    def __init__(self, vm_details: VMDetails) -> None:
        self.vm_details = vm_details

    def retrieve_config(self) -> str:
        config_contents = f"""[virt-viewer]
    type=spice
    kiosk-quit=on-disconnect
    host={self.vm_details["spice_proxy"].split(":")[0]}
    port={self.vm_details["spice_proxy"].split(":")[1]}
    password={self.vm_details["vm_password"]}
    title={self.vm_details["vm_name"]}
    """
        config_contents += "\ndisable-effects=all"
        if self.vm_details["usb"]:
            config_contents += "\nenable-usb-autoshare=1\nenable-usbredir=1\nspice-usbredir-auto-redirect-filter=0x08,-1,-1,-1,1|-1,-1,-1,-1,0"
        print(config_contents)
        return config_contents
