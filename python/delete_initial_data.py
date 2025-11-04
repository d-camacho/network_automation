from nautobot.apps.jobs import Job, register_jobs
from nautobot.dcim.models import Device, DeviceType, Manufacturer, Platform, Location, LocationType
from nautobot.extras.models import Role, Status, ExternalIntegration
from nautobot.tenancy.models import Tenant
from nautobot.extras.models.secrets import Secret, SecretsGroup, SecretsGroupAssociation
from nautobot.dcim.models import SoftwareVersion
from nautobot.dcim.models import Interface
from nautobot.ipam.models import Prefix, IPAddress

name = "Initial Data for Citrix SSOT App"

# Constants
LOCATION_TYPE = "Site"
LOCATION = "Sample"
ROLE_NAME = "Sample Role"
TENANT = "Test Tenant"
DEVICES = ["DEV01", "DEV02"]
SECRET_USER = "Service Acct Username"
SECRET_PW = "Service Acct Password"
SECRETS_GROUP = "Service Account"
EXTERNAL_INTEGRATION_NAME = "Citrix ADM"
PARENT_LOCATION_TYPE = "Region"
PARENT_LOCATION = "Regional Data Centers"

class DeleteInitialData(Job):
    class Meta:
        name = "Delete Initial Data for Citrix SSOT App"
        description = "Deletes all initial data created for the Citrix SSOT App for quick testing reset."

    def run(self):
        # Devices first (most dependent)
        devices = Device.objects.all()
        device_count = devices.count()
        if device_count > 0:
            self.logger.info("Deleting all %s devices.", device_count)
            devices.delete()
        else:
            self.logger.info("No devices found to delete.")

        # Delete all software versions
        software = SoftwareVersion.objects.all()
        software_count = software.count()
        if software_count > 0:
            self.logger.info("Deleting all %s software versions.", software_count)
            software.delete()
        else:
            self.logger.info("No software versions found to delete.")

        # Delete all interfaces
        interfaces = Interface.objects.all()
        interface_count = interfaces.count()
        if interface_count > 0:
            self.logger.info("Deleting all %s interfaces.", interface_count)
            interfaces.delete()
        else:
            self.logger.info("No interfaces found to delete.")
        
        # Delete all Prefixes and IP Addresses
        ip_addresses = IPAddress.objects.all()
        ip_count = ip_addresses.count()
        if ip_count > 0:
            self.logger.info("Deleting all %s IP addresses.", ip_count)
            ip_addresses.delete()
        else:
            self.logger.info("No IP addresses found to delete.")
            
        prefixes = Prefix.objects.all()
        prefix_count = prefixes.count()
        if prefix_count > 0:
            self.logger.info("Deleting all %s prefixes.", prefix_count)
            prefixes.delete()
        else:
            self.logger.info("No prefixes found to delete.")
        

        

        # # DeviceType
        # device_type = DeviceType.objects.filter(model="NetScaler ADC VPX")
        # if device_type.exists():
        #     self.logger.info("Deleting device type NetScaler ADC VPX")
        #     device_type.delete()
        # else:
        #     self.logger.info("Device type NetScaler ADC VPX does not exist.")

        # # Role
        # role = Role.objects.filter(name=ROLE_NAME)
        # if role.exists():
        #     self.logger.info("Deleting role %s", ROLE_NAME)
        #     role.delete()
        # else:
        #     self.logger.info("Role %s does not exist.", ROLE_NAME)

        # # Platform
        # platform = Platform.objects.filter(name="citrix.adc")
        # if platform.exists():
        #     self.logger.info("Deleting platform citrix.adc")
        #     platform.delete()
        # else:
        #     self.logger.info("Platform citrix.adc does not exist.")

        # # Manufacturer
        # manufacturer = Manufacturer.objects.filter(name="Citrix")
        # if manufacturer.exists():
        #     self.logger.info("Deleting manufacturer Citrix")
        #     manufacturer.delete()
        # else:
        #     self.logger.info("Manufacturer Citrix does not exist.")

        # # Tenant
        # tenant = Tenant.objects.filter(name=TENANT)
        # if tenant.exists():
        #     self.logger.info("Deleting tenant %s", TENANT)
        #     tenant.delete()
        # else:
        #     self.logger.info("Tenant %s does not exist.", TENANT)

        # # External Integration
        # ext_integration = ExternalIntegration.objects.filter(name=EXTERNAL_INTEGRATION_NAME)
        # if ext_integration.exists():
        #     self.logger.info("Deleting external integration %s", EXTERNAL_INTEGRATION_NAME)
        #     ext_integration.delete()
        # else:
        #     self.logger.info("External integration %s does not exist.", EXTERNAL_INTEGRATION_NAME)

        # # SecretsGroupAssociation
        # for secret_name in [SECRET_USER, SECRET_PW]:
        #     try:
        #         secret = Secret.objects.get(name=secret_name)
        #         sga = SecretsGroupAssociation.objects.filter(secret=secret)
        #         if sga.exists():
        #             self.logger.info("Deleting secrets group associations for secret %s", secret_name)
        #             sga.delete()
        #     except Secret.DoesNotExist:
        #         pass

        # # SecretsGroup
        # secrets_group = SecretsGroup.objects.filter(name=SECRETS_GROUP)
        # if secrets_group.exists():
        #     self.logger.info("Deleting secrets group %s", SECRETS_GROUP)
        #     secrets_group.delete()
        # else:
        #     self.logger.info("Secrets group %s does not exist.", SECRETS_GROUP)

        # # Secret
        # for secret_name in [SECRET_USER, SECRET_PW]:
        #     secret = Secret.objects.filter(name=secret_name)
        #     if secret.exists():
        #         self.logger.info("Deleting secret %s", secret_name)
        #         secret.delete()
        #     else:
        #         self.logger.info("Secret %s does not exist.", secret_name)

        # Locations (child before parent)
        location = Location.objects.all()
        if location.exists():
            self.logger.info("Deleting location %s", LOCATION)
            location.delete()
        else:
            self.logger.info("Location %s does not exist.", LOCATION)

        # parent_location = Location.objects.filter(name=PARENT_LOCATION)
        # if parent_location.exists():
        #     self.logger.info("Deleting parent location %s", PARENT_LOCATION)
        #     parent_location.delete()
        # else:
        #     self.logger.info("Parent location %s does not exist.", PARENT_LOCATION)

        # # LocationTypes (child before parent)
        # location_type = LocationType.objects.filter(name=LOCATION_TYPE)
        # if location_type.exists():
        #     self.logger.info("Deleting location type %s", LOCATION_TYPE)
        #     location_type.delete()
        # else:
        #     self.logger.info("Location type %s does not exist.", LOCATION_TYPE)

        # parent_location_type = LocationType.objects.filter(name=PARENT_LOCATION_TYPE)
        # if parent_location_type.exists():
        #     self.logger.info("Deleting parent location type %s", PARENT_LOCATION_TYPE)
        #     parent_location_type.delete()
        # else:
        #     self.logger.info("Parent location type %s does not exist.", PARENT_LOCATION_TYPE)

        # self.logger.info("Cleanup process completed.")
        return "Cleanup process completed."

