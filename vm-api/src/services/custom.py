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
        if self.vm_details["usb"]:
            config_contents += "enable-usb-autoshare=1\nenable-usbredir=1"
        return config_contents
