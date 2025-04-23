# gather_ospf_neighbors.py
from pyats.topology import Testbed
import re

def gather_neighbors(testbed: Testbed) -> dict:
    """Gathers OSPF neighbors for all devices in a pyATS Testbed object."""
    device_neighbors = {}
    for device_name, device in testbed.devices.items():
        print(f"Connecting to {device_name} to gather neighbors...")
        try:
            device.connect(log_stdout=False)
            output = device.execute("show ip ospf neighbor")
            neighbor_ips = re.findall(r"^\s*(\d{1,3}(?:\.\d{1,3}){3})\s+\d+\s+FULL", output, re.MULTILINE)
            device_neighbors[device_name] = neighbor_ips
        except Exception as e:
            print(f"Error gathering neighbors from {device_name}: {e}")
        finally:
            if device.connected:
                device.disconnect()
    return device_neighbors