
import requests
from nautobot.apps.jobs import Job, ObjectVar, register_jobs
from nautobot.dcim.models import Device, Location


name = "API Requests"


class RemoteRouteAPI(Job):
    class Meta:
        name = "Remote Route API"
        has_sensitive_variables = False
        description = "Make API calls to retrieve routing table from a device using the requests library"

    # Define ObjectVars for device location and device selection
    device_location = ObjectVar(
        model=Location, 
        required=False
    )
    
    device = ObjectVar(
        model=Device,
        query_params={
            "location": "$device_location",
        },
    )

    def run(self, device_location, device):
        self.logger.info(f"Checking all routes for {device.name}.")

        # Verify the device has a primary IP
        if device.primary_ip is None:
            self.logger.fatal(f"Device '{device.name}' does not have a primary IP address set.")
            return

        # Verify the device has a platform associated
        if device.platform is None:
            self.logger.fatal(f"Device '{device.name}' does not have a platform set.")
            return

        # Construct the API URL 
        url = f"https://{str(device.primary_ip).split('/')[0]}/command-api"
        
        # identify command based on device platform
        command_map = {
            "cisco_ios": "show ip route",
            "arista_eos": "show ip route",
            "juniper_junos": "show route"
        }
        
        platform_name = device.platform.network_driver
        cmd = command_map[platform_name]        
             
        # Define the payload for the API call based on device type
        payload = {
            "jsonrpc": "2.0",
            "method": "runCmds",
            "params": {
                "version": 1,
                "cmds": [cmd],  # Command must be passed as a list
                "format": "json"
            },
            "id": 1
        }

        # Set up basic authentication
        auth = ("admin", "admin")  # Update with actual credentials if needed

        # Make the API call
        try:
            response = requests.post(url, json=payload, auth=auth, verify=False) 
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the JSON response and show as log output
            route_data = response.json()
            self.logger.info(f"Routing table from {device.name}:\n{route_data}")

            return route_data  # You can modify this to return specific data if needed

        # Generate error mesages as both return value and log entry
        except requests.exceptions.RequestException as e:
            self.logger.fatal(f"Error connecting to {device.name}. Device unreachable.")
            raise Exception(f"Error connecting to {device.name}: {e}")


# Required step for Nautobot to recognize the job
register_jobs(
    RemoteRouteAPI
)
