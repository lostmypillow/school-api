import logging
from time import sleep

import proxmoxer

from app.domains.vm.schemas import VMDetails


class ProxmoxService:
    def __init__(self, vm_details: VMDetails) -> None:
            self.vm_details = vm_details
            self.proxmox_obj = proxmoxer.ProxmoxAPI(
                host=self.vm_details["pve_host"].split(":")[0],
                port=self.vm_details["pve_host"].split(":")[1],
                user=f"{self.vm_details['pve_token_username']}@pve",
                token_name=self.vm_details["pve_token_name"],
                token_value=self.vm_details["pve_token_value"],
                verify_ssl=False,
            )
            self.node_name = self.vm_details["pve_proxy"].split(".")[0]
            self.available_nodes = self.proxmox_obj.cluster.resources.get(type="node")

    def retrieve_config(self):
            logging.info(f"Available nodes: {self.available_nodes}")
            # TODO: node not found
            existing_node = next(
                online_node
                for online_node in self.available_nodes
                if online_node["node"] == self.node_name
            )
            logging.info(f"Existing nodes: {existing_node}")
            # TODO: node not online

            vm_resource = self.proxmox_obj.nodes(self.node_name).qemu(str(self.vm_details["pve_vm_id"]))
            # TODO: vm not found

            status = vm_resource.status.current.get()["status"]
            if status == "stopped":
                logging.info("Starting VM..")
                vm_resource.status.start.post()
                logging.info("Started")
                sleep(2)
            config_contents = "[virt-viewer]\n" + "\n".join(
                f"{k}={v}" for k, v in vm_resource.spiceproxy.post().items() if k != "proxy"
            ) + f"\nproxy={self.vm_details['spice_proxy']}\n"
            return config_contents
