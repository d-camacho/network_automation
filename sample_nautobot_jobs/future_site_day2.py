"""Job to create a new site of type POP with optional parent site support."""
import re
from django.utils.text import slugify

from nautobot.apps.jobs import Job, ObjectVar, StringVar, IntegerVar, register_jobs
from nautobot.dcim.models.locations import Location, LocationType
from nautobot.extras.models import Status

from nautobot.extras.models.roles import Role
from nautobot.dcim.models.device_components import Interface
from nautobot.ipam.models import Prefix
from nautobot.tenancy.models import Tenant
from ipaddress import IPv4Network

name = "Data Population Jobs Collection"


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


TOP_LEVEL_PREFIX_ROLE = "POP Global Pool"
PREFIX_ROLES = ["point-to-point", "loopback", "server", "mgmt", "pop"]

P2P_PREFIX_SIZE = 31
SITE_PREFIX_SIZE = 16

def create_prefix_roles():
    """Create all Prefix Roles defined in PREFIX_ROLES."""
    for role in PREFIX_ROLES:
        Role.objects.get_or_create(name=role)

class CreatePop2(Job):
    """Job to create a new site of type POP."""


    location_type = StringVar(description="Type of Location", label="Location Type")

    site_name = StringVar(description="Name of the new site", label="Site Name")

    site_facility = StringVar(description="Facility of the new site", label="Site Facility")

    parent_site = ObjectVar(
        model=Location,
        required=False,
        description="Select an existing site to nest this site under. Site will be created as a Region if left blank.",
        label="Parent Site",
    )

    class Meta:
        """Metadata for CreatePop."""

        name = "Create a Point of Presence"
        description = """
        Create a new Site of Type POP with 2 Edge Routers and N leaf switches.
        A new /16 will automatically be allocated from the 'POP Global Pool' Prefix.
        """
        field_order = ["parent_site", "location_type", "site_name", "site_facility", "leaf_count"]

    def run(self, location_type, site_name, site_facility, leaf_count, parent_site=None):
        """Main function to create a site."""

        # ----------------------------------------------------------------------------
        # Initialize the database with all required objects
        # We'll build on this in coming days
        # ----------------------------------------------------------------------------
        
        create_prefix_roles()

        # ----------------------------------------------------------------------------
        # Find or Create Site
        # ----------------------------------------------------------------------------

        location_type_site, _ = LocationType.objects.get_or_create(name=location_type)
        active_status = Status.objects.get(name="Active")
        self.site_name = site_name
        self.site_facility = site_facility
        self.site, created = Location.objects.get_or_create(
            name=site_name,
            location_type=LocationType.objects.get(name=location_type),
            facility=site_facility,
            status=active_status,
            parent=parent_site,  # Will be None if not provided
        )

        if created:
            message = f"Site '{site_name}' created as a top level Region."
            if parent_site:
                message = f"Site '{site_facility}' successfully nested under '{parent_site.name}'."
            self.logger.info(message)
        else:
            self.logger.warning(f"Site '{site_name}' already exists.")

        
        # ----------------------------------------------------------------------------
        # Allocate Prefixes for this POP
        # ----------------------------------------------------------------------------
        # Search if there is already a POP prefix associated with this side
        # if not search the Top Level Prefix and create a new one
        # # ROLES["leaf"]["nbr"] = leaf_count
        
        # pop_role, _ = Role.objects.get_or_create(name="pop")
        # container_status = Status.objects.get_for_model(Prefix).get(name="container")
        # p2p_status = Status.objects.get_for_model(Prefix).get(name="point-to-point")
        # prefix_status = Status.objects.get_for_model(Prefix).get(status="Active")
        # pop_prefix = Prefix.objects.filter(site=self.site, status=container_status, role=pop_role).first()

        # if not pop_prefix:
        #     top_level_prefix = Prefix.objects.filter(
        #         role__slug=slugify(TOP_LEVEL_PREFIX_ROLE), status=container_status
        #     ).first()

        #     if not top_level_prefix:
        #         raise Exception("Unable to find the top level prefix to allocate a Network for this site")

        #     first_avail = top_level_prefix.get_first_available_prefix()
        #     if not first_avail:
        #         raise Exception("No available /16 prefix in the POP Global Pool.")
        #     prefix = list(first_avail.subnet(SITE_PREFIX_SIZE))[0]
        #     pop_prefix = Prefix.objects.create(
        #         prefix=prefix, site=self.site, status=container_status, role=pop_role
        #     )

        # iter_subnet = IPv4Network(str(pop_prefix.prefix)).subnets(new_prefix=18)

        # # Allocate the subnet by block of /18
        # server_block = next(iter_subnet)
        # mgmt_block = next(iter_subnet)
        # loopback_subnet = next(iter_subnet)
        # p2p_subnet = next(iter_subnet)

        # # Create Server & Mgmt Block
        # server_role, _ = Role.objects.get_or_create(name="server")
        # Prefix.objects.get_or_create(
        #     prefix=str(server_block), site=self.site, role=server_role, status=container_status
        # )

        # mgmt_role, _ = Role.objects.get_or_create(name="mgmt")
        # Prefix.objects.get_or_create(
        #     prefix=str(mgmt_block), site=self.site, role=mgmt_role, status=container_status
        # )

        # loopback_role, _ = Role.objects.get_or_create(name="loopback")
        # Prefix.objects.get_or_create(
        #     prefix=str(loopback_subnet),
        #     site=self.site,
        #     role=loopback_role,
        #     status=container_status
        # )

        # p2p_role, _ = Role.objects.get_or_create(name="point-to-point")
        # Prefix.objects.get_or_create(
        #     prefix=str(p2p_subnet),
        #     site=self.site,
        #     role=p2p_role,
        #     status=container_status
        # )

        


register_jobs(
    CreatePop2
)

