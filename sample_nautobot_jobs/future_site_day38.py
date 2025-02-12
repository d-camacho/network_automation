
"""Job to create a new site of type POP with optional parent site support."""

from itertools import product
import re

from django.contrib.contenttypes.models import ContentType
import yaml

from nautobot.dcim.models import DeviceType, Manufacturer
from nautobot.dcim.models.device_component_templates import InterfaceTemplate
from nautobot.extras.models import Status
from nautobot.extras.models.roles import Role
from nautobot.ipam.models import Prefix, VLAN
from nautobot.tenancy.models import Tenant

####DAY36####
from nautobot.apps.jobs import Job, ObjectVar, register_jobs, StringVar
from nautobot.dcim.models.locations import Location, LocationType
from ipaddress import IPv4Network

####DAY38#####
from nautobot.dcim.models.racks import Rack

name = "Data Population Jobs Collection"


PREFIX_ROLES = ["p2p", "loopback", "server", "mgmt", "pop"]
####DAY36####
POP_PREFIX_SIZE = 16
####DAY37####
ROLE_PREFIX_SIZE = 18
TENANT_NAME = "Data Center"
ACTIVE_STATUS = Status.objects.get(name="Active")
# VLAN definitions: key is also used to look up the role.
VLAN_INFO = {
    "server": 1000,
    "mgmt": 99,
}

DEVICE_TYPES_YAML = [
    """
    manufacturer: Arista
    model: DCS-7280CR2-60
    part_number: DCS-7280CR2-60
    u_height: 1
    is_full_depth: false
    comments: '[Arista 7280R Data Sheet](https://www.arista.com/assets/data/pdf/Datasheets/7280R-DataSheet.pdf)'
    interfaces:
        - pattern: "Ethernet[1-60]/[1-4]"
          type: 100gbase-x-qsfp28
        - pattern: "Management1"
          type: 1000base-t
          mgmt_only: true
    """,
    """
    manufacturer: Arista
    model: DCS-7150S-24
    part_number: DCS-7150S-24
    u_height: 1
    is_full_depth: false
    comments: '[Arista 7150 Data Sheet](https://www.arista.com/assets/data/pdf/Datasheets/7150S_Datasheet.pdf)'
    interfaces:
        - pattern: "Ethernet[1-24]"
          type: 10gbase-x-sfpp
        - pattern: "Management1"
          type: 1000base-t
          mgmt_only: true
    """,
]

####DAY38####
ROLES = {
    "edge": {
        "nbr": 2,
        "device_type": "dcs-7280cr2-60",
        "platform": "arista_eos",
        "rack_elevation": 40,
        "color": "ff9800",
        "interfaces": [
            ("peer", 2),
            ("leaf", 12),
            ("external", 8),
        ],
    },
    "leaf": {
        "nbr": 6,
        "device_type": "dcs-7150s-24",
        "platform": "arista_eos",
        "rack_elevation": 44,
        "color": "3f51b5",
        "interfaces": [
            ("edge", 4),
            ("access", 20),
        ],
    },
}

RACK_HEIGHT = 48
RACK_TYPE = RackTypeChoices.TYPE_4POST

def create_prefix_roles(logger):
    """Create all Prefix Roles defined in PREFIX_ROLES and add content types for IPAM Prefix and VLAN."""

    # Retrieve the content type for Prefix and VLAN models.
    prefix_ct = ContentType.objects.get_for_model(Prefix)
    vlan_ct = ContentType.objects.get_for_model(VLAN)

    for role in PREFIX_ROLES:
        role_obj, created = Role.objects.get_or_create(name=role)
        # Add the Prefix and VLAN content types to the role.
        role_obj.content_types.add(prefix_ct, vlan_ct)
        role_obj.validated_save()
        logger.info(f"Successfully created role {role} with content types for Prefix and VLAN.")


def create_tenant(logger):
    """Create a tenant with the name defined in TENANT_NAME."""
    tenant_obj, _ = Tenant.objects.get_or_create(name=TENANT_NAME)
    tenant_obj.validated_save()
    logger.info(f"Successfully created Tenant {TENANT_NAME}.")


def create_vlans(logger):
    """Create predefined VLANs defined in VLAN_INFO, and assign the appropriate role."""
    # Get the active status from the database.

    for vlan_name, vlan_id in VLAN_INFO.items():
        # Retrieve the appropriate role based on the VLAN name.
        try:
            role_obj = Role.objects.get(name=vlan_name)
        except Role.DoesNotExist:
            logger.error(f"Role '{vlan_name}' not found. VLAN will be created without a role.")
            role_obj = None

        defaults = {"name": vlan_name, "status": ACTIVE_STATUS}
        if role_obj:
            defaults["role"] = role_obj

        vlan_obj, created = VLAN.objects.get_or_create(
            vid=vlan_id,
            defaults=defaults,
        )
        if created:
            vlan_obj.validated_save()
            logger.info(f"Successfully created VLAN '{vlan_name}' with ID {vlan_id}.")
        else:
            logger.info(f"VLAN '{vlan_name}' with ID {vlan_id} already exists.")


def create_device_types(logger):
    """
    Create DeviceType objects from YAML definitions and add interfaces using InterfaceTemplate.
    """

    for device_yaml in DEVICE_TYPES_YAML:
        data = yaml.safe_load(device_yaml)

        manufacturer_name = data.pop("manufacturer", None)
        if not manufacturer_name:
            logger.error("Manufacturer not provided in YAML definition.")
            continue
        manufacturer_obj, _ = Manufacturer.objects.get_or_create(name=manufacturer_name)

        model_name = data.pop("model", None)
        if not model_name:
            logger.error("Model not provided in YAML for manufacturer %s", manufacturer_name)
            continue

        # Create DeviceType
        device_type_defaults = {
            k: data[k] for k in ["part_number", "u_height", "is_full_depth", "comments"] if k in data
        }
        device_type_obj, created = DeviceType.objects.get_or_create(
            manufacturer=manufacturer_obj,
            model=model_name,
            defaults=device_type_defaults,
        )

        if created:
            device_type_obj.validated_save()
            logger.info(f"DeviceType created: {device_type_obj}")
        else:
            logger.info(f"DeviceType already exists: {device_type_obj}")

        # Add interfaces using InterfaceTemplate
        for iface in data.get("interfaces", []):
            pattern = iface.get("pattern")
            iface_type = iface.get("type")
            mgmt_only = iface.get("mgmt_only", False)

            if not pattern or not iface_type:
                logger.error(f"Invalid interface definition in {model_name}: {iface}")
                continue

            # Generate interfaces from range patterns
            interface_names = expand_interface_pattern(pattern)
            for iface_name in interface_names:
                interface_template, created = InterfaceTemplate.objects.get_or_create(
                    device_type=device_type_obj,
                    name=iface_name,
                    defaults={
                        "type": iface_type,
                        "mgmt_only": mgmt_only,
                    },
                )
                if created:
                    logger.info(f"Added interface {iface_name} ({iface_type}) to {model_name}")


def expand_interface_pattern(pattern):
    """
    Expands an interface pattern like 'Ethernet[1-60]/[1-4]' into actual names.
    Supports:
      - Single range: Ethernet[1-24] -> Ethernet1, Ethernet2, ..., Ethernet24
      - Nested range: Ethernet[1-60]/[1-4] -> Ethernet1/1, Ethernet1/2, ..., Ethernet60/4
    """
    match = re.findall(r"\[([0-9]+)-([0-9]+)\]", pattern)
    if not match:
        return [pattern]  # No expansion needed, return as-is.

    # Convert to lists of numbers
    ranges = [list(range(int(start), int(end) + 1)) for start, end in match]

    # Generate names using cartesian product
    expanded_names = []
    base_name = re.sub(r"\[[0-9]+-[0-9]+\]", "{}", pattern)

    for numbers in product(*ranges):
        expanded_names.append(base_name.format(*numbers))

    return expanded_names


class CreatePop(Job):
    """Job to create a new site of type POP."""
    ####DAY36####
    # Receive input from user about site iformation
    location_type = ObjectVar(
    model=LocationType,
    description = "Select location type for new site."
    )
    site_name = StringVar(description="Name of the new site", label="Site Name")
    site_facility = StringVar(description="Facility of the new site", label="Site Facility")
    parent_site = ObjectVar(
        model=Location,
        required=False,
        description="Select an existing site to nest this site under. Site will be created as a Region if left blank.",
        label="Parent Site"
    )
    site_code = StringVar(description="Enter Site Code as 2-letter state and 2-digit site number e.g. NY01 for New York Store #01")
    tenant = ObjectVar(model=Tenant)


    class Meta:
        """Metadata for CreatePop."""

        name = "Create a Point of Presence"
        description = """
        Create a new POP Site.
        A new /16 will automatically be allocated from the 'POP Global Pool' Prefix.
        """
        
        ####DAY36####
        field_order = ["location_type", "parent_site", "site_name", "site_facility"]
        
        
    ####DAY36PassNewParameters####
    def run(self, location_type, site_name, site_facility, tenant, site_code, parent_site=None):
        """Main function to create a site."""

        # ----------------------------------------------------------------------------
        # Initialize the database with all required objects.
        # We will build on this in the coming days.
        # ----------------------------------------------------------------------------
        create_prefix_roles(self.logger)
        create_tenant(self.logger)
        create_vlans(self.logger)
        create_device_types(self.logger)

        # ----------------------------------------------------------------------------
        # Create Site
        # ----------------------------------------------------------------------------
        location_type_site, _ = LocationType.objects.get_or_create(name=location_type)
        self.site_name = site_name
        self.site_facility = site_facility
        self.site, created = Location.objects.get_or_create(
            name = site_name,
            location_type = LocationType.objects.get(name=location_type),
            facility = site_facility,
            status = ACTIVE_STATUS,
            parent = parent_site,  # Will be None if not provided
            tenant = tenant
        )
        
        if created:
            message = f"Site '{site_name}' created as a top level Region."
            if parent_site:
                message = f"Site '{site_name}' successfully nested under '{parent_site.name}'."
            self.site.validated_save()
            self.logger.info(message)

            # ----------------------------------------------------------------------------
            # Allocate Prefix for this POP
            # ----------------------------------------------------------------------------
            # Search if there is already a POP prefix associated with this side
            # if not search the Top Level Prefix and create a new one
            pop_role = Role.objects.get(name="pop")
            self.logger.info(f"Assigning '{site_name}' as '{pop_role}' role.")

            # Find the first available /16 prefix that isn't assigned to a site yet
            pop_prefix = Prefix.objects.filter(
                type="container",  # Ensure it's a top-level subnet assigned as a container
                prefix_length = POP_PREFIX_SIZE,
                status = ACTIVE_STATUS,
                location__isnull = True  # Ensure it's not already assigned to another site
            ).first()

            if pop_prefix:
                # Assign the prefix to the new site 
                pop_prefix.location = self.site
                pop_prefix.validated_save()
                self.logger.info(f"Assigned {pop_prefix} to {site_name}.")
            else:                 
                self.logger.warning("No available /16 prefixes found. Creating a new /16.")
                
                # Search for top-level /8 prefixes
                top_level_prefix = Prefix.objects.filter(
                    type = "container",  
                    status = ACTIVE_STATUS,
                    prefix_length = 8
                ).first()

                # Get the first available prefix within the /8
                first_avail = top_level_prefix.get_first_available_prefix()

                if not first_avail:
                    raise Exception("No available subnets found within the /8 prefix.")

                # Iterate over all possible /16 subnets within the /8 and find the first unassigned one
                for candidate_prefix in IPv4Network(str(first_avail)).subnets(new_prefix=POP_PREFIX_SIZE):
                    if not Prefix.objects.filter(prefix=str(candidate_prefix)).exists():
                        pop_prefix, created = Prefix.objects.get_or_create(
                            prefix=str(candidate_prefix),
                            type="container",
                            location=self.site,
                            status=ACTIVE_STATUS,
                            role=pop_role
                        )
                        pop_prefix.validated_save()
                        self.logger.info(f"Allocated new'{pop_prefix}' for site '{site_name}'.")
                        break
                else:
                    raise Exception("No available /16 prefixes found within the /8 range.")        
        
        else:
            self.logger.warning(f"Site '{site_name}' already exists.") 


        # ----------------------------------------------------------------------------
        # Create and assign prefixes to roles in POP
        # ----------------------------------------------------------------------------
        
        site_subnets = IPv4Network(str(pop_prefix)).subnets(new_prefix=ROLE_PREFIX_SIZE)

        # Divide POP Prefix into blocks of of /18
        server_subnet = next(site_subnets)    
        mgmt_subnet = next(site_subnets)    
        loopback_subnet = next(site_subnets)     
        p2p_subnet = next(site_subnets) 

        # Assign new subnets to roles
        server_role = Role.objects.get(name="server")
        server_prefix, created = Prefix.objects.get_or_create(
            prefix = str(server_subnet), 
            type = "network",
            role = server_role,
            parent = pop_prefix,
            status = ACTIVE_STATUS,
            location = self.site,
            tenant = tenant
        )
        self.logger.info(f"'{server_prefix}' assigned to '{server_role}'.")

        mgmt_role = Role.objects.get(name="mgmt")
        mgmt_prefix, created = Prefix.objects.get_or_create(
            prefix = str(mgmt_subnet),
            type = "network", 
            role = mgmt_role,
            parent = pop_prefix,
            status = ACTIVE_STATUS,
            location = self.site,
            tenant = tenant
        )
        self.logger.info(f"'{mgmt_prefix}' assigned to '{mgmt_role}'.")

        loopback_role = Role.objects.get(name="loopback")
        loopback_prefix, created = Prefix.objects.get_or_create(
            prefix = str(loopback_subnet),
            type = "network", 
            role = loopback_role,
            parent = pop_prefix,
            status = ACTIVE_STATUS,
            location = self.site,
            tenant = tenant
        )
        self.logger.info(f"'{loopback_prefix}' assigned to '{loopback_role}'.")

        p2p_role = Role.objects.get(name="p2p")
        p2p_prefix, created = Prefix.objects.get_or_create(
            prefix = str(p2p_subnet),
            type = "network",
            location = self.site,
            role = p2p_role,
            parent = pop_prefix,
            status = ACTIVE_STATUS,
            location = self.site,
            tenant = tenant
        )
        self.logger.info(f"'{p2p_prefix}' assigned to '{p2p_role}'.") 

        # ----------------------------------------------------------------------------
        # Create Racks
        # ----------------------------------------------------------------------------
        rack_status = Status.objects.get_for_model(Rack).get(status="active") ####might have to change to ACTIVE_STATUS
        for i in range(1, ROLES["leaf"]["nbr"] + 1): ####Provide explanation
            rack_name = f"{site_code}-{100 + i}"
            rack = Rack.objects.get_or_create(
                name=rack_name,
                location=self.site,
                u_height=RACK_HEIGHT,
                type=RACK_TYPE,
                status=rack_status,
                tenant=self.tenant,
            )

        # ----------------------------------------------------------------------------
        # Create Devices
        # ----------------------------------------------------------------------------
        ip_status = Status.objects.get_for_model(IPAddress).get(slug="active")
        vlan_status = Status.objects.get_for_model(VLAN).get(slug="active")
        for role, data in ROLES.items():
            for i in range(1, data.get("nbr", 2) + 1):

                rack_name = f"{site_code}-{100 + i}"
                rack = Rack.objects.filter(name=rack_name, site=self.site).first()
                platform = Platform.objects.filter(slug=data["platform"]).first()

                device_name = f"{site_code}-{role}-{i:02}"

                device = Device.objects.filter(name=device_name).first()
                if device:
                    self.devices[device_name] = device
                    if not device.platform and platform:
                        device.platform = platform
                        device.validated_save()

                    self.log_success(obj=device, message=f"Device {device_name} already present")
                    continue

                device_status = Status.objects.get_for_model(Device).get(slug="active")
                device_role, _ = DeviceRole.objects.get_or_create(
                    name=role, slug=slugify(role), color=ROLES[role]["color"]
                )
                device = Device.objects.create(
                    device_type=DeviceType.objects.get(slug=data.get("device_type")),
                    name=device_name,
                    site=self.site,
                    status=device_status,
                    device_role=device_role,
                    rack=rack,
                    platform=platform,
                    position=data.get("rack_elevation"),
                    face="front",
                    tenant=self.tenant,
                )

                device.clean()
                device.validated_save()
                self.devices[device_name] = device
                self.log_success(device, f"Device {device_name} successfully created")

                # Generate Loopback interface and assign Loopback
                loopback_intf = Interface.objects.create(
                    name="Loopback0", type=InterfaceTypeChoices.TYPE_VIRTUAL, device=device
                )

                loopback_prefix = Prefix.objects.get(
                    site=self.site,
                    role__name="loopback",
                )

                available_ips = loopback_prefix.get_available_ips()
                address = list(available_ips)[0]
                loopback_ip = IPAddress.objects.create(
                    address=str(address),
                    assigned_object=loopback_intf,
                    status=ip_status,
                    tenant=self.tenant,
                    dns_name=f"{role}-{i:02}.{site_code}.{self.tenant.description}",
                )
                device.primary_ip4 = loopback_ip
                device.clean()
                device.validated_save()

                # Assign Role to Interfaces
                intfs = iter(Interface.objects.filter(device=device))
                for int_role, cnt in data["interfaces"]:
                    for i in range(0, cnt):
                        intf = next(intfs)
                        intf._custom_field_data = {"role": int_role}
                        intf.validated_save()

                if role == "leaf":
                    for vlan_name, vlan_data in VLANS.items():
                        prefix_role = Role.objects.get(slug=vlan_name)
                        vlan = VLAN.objects.create(
                            vid=vlan_data["vlan_id"],
                            name=f"{rack_name}-{vlan_name}",
                            site=self.site,
                            role=prefix_role,
                            status=vlan_status,
                            tenant=self.tenant,
                        )
                        vlan_block = Prefix.objects.filter(
                            site=self.site, status=container_status, role=prefix_role
                        ).first()

                        # Find Next available Network
                        first_avail = vlan_block.get_first_available_prefix()
                        subnet = list(first_avail.subnet(24))[0]
                        vlan_prefix = Prefix.objects.create(
                            prefix=str(subnet),
                            vlan=vlan,
                            status=prefix_status,
                            role=prefix_role,
                            site=self.site,
                            tenant=self.tenant,
                        )
                        vlan_prefix.validated_save()

                        intf_name = f"vlan{vlan_data['vlan_id']}"
                        intf = Interface.objects.create(
                            name=intf_name, device=device, type=InterfaceTypeChoices.TYPE_VIRTUAL
                        )

                        # Create IP Addresses on both sides
                        vlan_ip = IPAddress.objects.create(
                            address=str(subnet[0]),
                            assigned_object=intf,
                            status=ip_status,
                            tenant=self.tenant,
                            dns_name=f"ip-{str(subnet[0]).replace('.', '-')}.{vlan_name}.{site_code}.{self.tenant.description}",
                        )

                        RelationshipAssociation.objects.create(
                            relationship=rel_device_vlan,
                            source_type=rel_device_vlan.source_type,
                            source_id=device.id,
                            destination_type=rel_device_vlan.destination_type,
                            destination_id=vlan.id,
                        )

                        RelationshipAssociation.objects.create(
                            relationship=rel_rack_vlan,
                            source_type=rel_rack_vlan.source_type,
                            source_id=rack.id,
                            destination_type=rel_rack_vlan.destination_type,
                            destination_id=vlan.id,
                        )
        
        

register_jobs(CreatePop)
