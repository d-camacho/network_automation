from nautobot.apps.jobs import Job, register_jobs
from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import Device, DeviceType, Location, LocationType, Manufacturer, Platform
from nautobot.extras.models import Status, Role, ExternalIntegration
from nautobot.ipam.models import Prefix, VLAN, IPAddress
from nautobot.tenancy.models import Tenant
from nautobot.extras.models.secrets import Secret, SecretsGroup, SecretsGroupAssociation
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices

name = "Initial Data for Citrix SSOT App"

LOCATION_TYPE = "Site"
LOCATION = "Test Site"
ROLES = (
    "Internal Load-Balancer", 
    "External Load-Balancer", 
    "SDC LAB Load-Balancer", 
    "SDC Production Load-Balancer", 
    "P6 LAB Load-Balancer", 
    "RDC Load-Balancer", 
    "Central Video Load-Balancer"
    )
TENANT = "Test Tenant"
DEVICES = ["DEV01", "DEV02"]
SECRET_USER = "Service Acct Username"
SECRET_PW = "Service Acct Password"
SECRETS_GROUP = "Service Account"
EXTERNAL_INTEGRATION_NAME = "Citrix ADM"
EXTERNAL_INTEGRATION_URL = "url"
PARENT_LOCATION_TYPE = "Region"
PARENT_LOCATION = "Regional Data Centers"


class CreateInitialData(Job):
    class Meta:
        name = "Create Initial Data for Citrix SSOT App"
        description = "Creates initial data required for the Citrix SSOT App to function properly."
    
    def run(self):
        results = []
        try:
            active_status = Status.objects.get(name="Active")
        except Status.DoesNotExist:
            self.logger.error("Could not find an 'Active' status. Please create this first.")
            return "Failed: Required Status 'Active' not found."
        
        # Create Secrets, Secrets Groups, and Associations
        param_user = {"variable": "ENV_VAR_USERNAME"}
        param_pw = {"variable": "ENV_VAR_PASSWORD"}
        sec_user, created = Secret.objects.get_or_create(
            name=SECRET_USER,
            provider="environment-variable",
            parameters=param_user
        )
        if created:
            sec_user.validated_save()
            self.logger.info("Successfully created %s Secret.", sec_user)
        else:
            self.logger.info("Secret %s already exists.", sec_user)
        
        sec_pw, created = Secret.objects.get_or_create(
            name=SECRET_PW,
            provider="environment-variable",
            parameters=param_pw
        )
        if created:
            sec_pw.validated_save()
            self.logger.info("Successfully created %s Secret.", sec_pw)
        else:
            self.logger.info("Secret %s already exists.", sec_pw)
        
        sec_group, created = SecretsGroup.objects.get_or_create(name=SECRETS_GROUP)
        if created:
            sec_group.validated_save()
            self.logger.info("Successfully created %s Secrets Group.", sec_group)
        else:
            self.logger.info("Secrets Group %s already exists.", sec_group)
        
        sga_user, created = SecretsGroupAssociation.objects.get_or_create(
            secrets_group=sec_group,
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
            secret=sec_user
        )
        if created:
            sga_user.validated_save()
            self.logger.info("Successfully created %s Secrets Group Association.", sga_user)
        else:
            self.logger.info("Secrets Group Association %s already exists.", sga_user)
        
        sga_pw, created = SecretsGroupAssociation.objects.get_or_create(
            secrets_group=sec_group,
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
            secret=sec_pw
        )
        if created:
            sga_pw.validated_save()
            self.logger.info("Successfully created %s Secrets Group Association.", sga_pw)
        else:
            self.logger.info("Secrets Group Association %s already exists.", sga_pw)

        # External Integration
        ext_int, created = ExternalIntegration.objects.get_or_create(
            name=EXTERNAL_INTEGRATION_NAME,
            remote_url=EXTERNAL_INTEGRATION_URL,
            secrets_group=sec_group,
            verify_ssl=False,
            timeout=30
        )
        if created:
            ext_int.http_method = "GET"
            ext_int.headers = {
                "Accept": "application/json",
                "Connection": "keep-alive",
                "Content-Type": "application/json"
            }
            ext_int.validated_save()
            self.logger.info("Successfully created %s External Integration.", ext_int)
        else:
            self.logger.info("External Integration %s already exists.", ext_int)

        # Create Role, LocationType, Locations
        # for role in ROLES:
        #     role, created = Role.objects.get_or_create(name=role)
        #     if created:
        #         role.content_types.add(ContentType.objects.get_for_model(Device))
        #         role.validated_save()
        #         self.logger.info("Successfully created %s Role.", role)
        #     else:
        #         self.logger.info("Role %s already exists.", role)
            
        par_loc_type, created = LocationType.objects.get_or_create(name=PARENT_LOCATION_TYPE)
        if created:
            par_loc_type.content_types.add(ContentType.objects.get_for_model(Device))
            par_loc_type.validated_save()
            self.logger.info("Successfully created %s Location Type.", par_loc_type)
        else:
            self.logger.info("Location Type %s already exists.", par_loc_type)
        
        par_loc, created = Location.objects.get_or_create(
            name=PARENT_LOCATION,
            status=active_status,
            location_type=par_loc_type
        )
        if created:
            par_loc.validated_save()
            self.logger.info("Successfully created %s Location.", par_loc)
        else:
            self.logger.info("Location %s already exists.", par_loc)

        # Create child LocationType with parent before saving
        loc_type, created = LocationType.objects.get_or_create(name=LOCATION_TYPE)
        if created:
            loc_type.parent = par_loc_type
            loc_type.validated_save()
            loc_type.content_types.add(ContentType.objects.get_for_model(Device))
            self.logger.info("Successfully created %s Location Type.", loc_type)
        else:
            self.logger.info("Location Type %s already exists.", loc_type)
            if not loc_type.parent:
                loc_type.parent = par_loc_type
                loc_type.validated_save()
                self.logger.info("Successfully added parent to %s Location Type.", loc_type)
        
        loc, created = Location.objects.get_or_create(
            name=LOCATION,
            status=active_status,
            location_type=loc_type,
            parent=par_loc
        )
        if created:
            loc.validated_save()
            self.logger.info("Successfully created %s Location.", loc)
        else:
            self.logger.info("Location %s already exists.", loc)

        # Create Manufacturer, Platform, Tenant, DeviceType, and Devices
        manufacturer, created = Manufacturer.objects.get_or_create(name="Citrix")
        if created:
            manufacturer.validated_save()
            self.logger.info("Successfully created %s Manufacturer.", manufacturer)
        else:
            self.logger.info("Manufacturer %s already exists.", manufacturer)
        
        platform, created = Platform.objects.get_or_create(
            name="citrix.adc",
            manufacturer=manufacturer,
            network_driver="citrix_netscaler",
            napalm_driver="netscaler"
        )
        if created:
            platform.validated_save()
            self.logger.info("Successfully created %s Platform.", platform)
        else:
            self.logger.info("Platform %s already exists.", platform)
        
        tenant, created = Tenant.objects.get_or_create(name=TENANT)
        if created:
            tenant.validated_save()
            self.logger.info("Successfully created %s Tenant.", tenant)
        else:
            self.logger.info("Tenant %s already exists.", tenant)
        
        device_type, created = DeviceType.objects.get_or_create(
            model="NetScaler ADC VPX",
            manufacturer=manufacturer,
            u_height=1,
            is_full_depth=True
        )
        if created:
            device_type.validated_save()
            self.logger.info("Successfully created %s Device Type.", device_type)
        else:
            self.logger.info("Device Type %s already exists.", device_type)
        
        # for dev in DEVICES:
        #     device, created = Device.objects.get_or_create(
        #         name=dev,
        #         device_type=device_type,
        #         platform=platform,
        #         location=loc,
        #         role=role,
        #         status=active_status,
        #         tenant=tenant
        #     )
        #     if created:
        #         device.validated_save()
        #         self.logger.info("Successfully created Device %s.", device)
        #     else:
        #         self.logger.info("Device %s already exists.", device)
        
        self.logger.info("Initial data creation process completed.")
        return "Initial data creation process completed."

