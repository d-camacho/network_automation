"""Job to create a new POP site"""

from nautobot.apps.jobs import Job, ObjectVar, register_jobs, StringVar
from nautobot.dcim.models.locations import Location, LocationType
from nautobot.extras.models import Status
from nautobot.extras.models.roles import Role
from nautobot.ipam.models import Prefix

###DAY3###
from ipaddress import IPv4Network


name = "Data Population Jobs Collection"


PREFIX_ROLES = ["p2p", "loopback", "server", "mgmt", "pop"]
POP_PREFIX_SIZE = 16

###DAY3###
ROLE_PREFIX_SIZE = 18
P2P_PREFIX_SIZE = 31

def create_prefix_roles():
    """Create all Prefix Roles defined in PREFIX_ROLES."""
    for role in PREFIX_ROLES:
        Role.objects.get_or_create(name=role)
        

class CreatePop(Job):
    """Job to create a new site of type POP."""
    
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
        label="Parent Site",
    )

    class Meta:
        """Metadata for CreatePop."""

        name = "Create a Point of Presence"
        description = """
        Create a new Site of Type POP with 2 Edge Routers and N leaf switches.
        A new /16 will automatically be allocated from the 'POP Global Pool' Prefix.
        """
        field_order = ["parent_site", "location_type", "site_name", "site_facility"]

    def run(self, location_type, site_name, site_facility, parent_site=None):
        """Main function to create a site."""

        # ----------------------------------------------------------------------------
        # Initialize the database with all required objects
        # We will build on this in coming days
        # ----------------------------------------------------------------------------
        
        create_prefix_roles()
        self.logger.info(f"Successfully created roles.")
        

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
                message = f"Site '{site_name}' successfully nested under '{parent_site.name}'."
            self.logger.info(message)

            # ----------------------------------------------------------------------------
            # Allocate Prefix for this POP
            # ----------------------------------------------------------------------------
            # Search if there is already a POP prefix associated with this side
            # if not search the Top Level Prefix and create a new one

            pop_role = Role.objects.get(name="pop")
            self.logger.info(f"Assigning '{site_name}' as '{pop_role}' role.")

            # Find an available /16 prefix that isn't assigned to a site yet
            pop_prefix = Prefix.objects.filter(
                type="container",  # Ensure it's a top-level subnet assigned as a container
                prefix_length=POP_PREFIX_SIZE,
                status__name="Active",
                location__isnull=True  # Ensure it's not already assigned to another site
            ).first()

            if pop_prefix:
                # Assign the prefix to the new site
                pop_prefix.location = self.site
                pop_prefix.validated_save()
                self.logger.info(f"Assigned {pop_prefix} to {self.site.name}.")
            else:
                self.logger.warning("No available /16 prefixes found!")

        else:
            self.logger.warning(f"Site '{site_name}' already exists.")
        
        
        ###DAY3###
        # ----------------------------------------------------------------------------
        # Allocate Subnets for the POP
        # ----------------------------------------------------------------------------
        
        site = Location.objects.get(name=site_name)    
        # Check if site has prefix assigned
        assigned_prefix = site.prefixes.first()
        if assigned_prefix:
            self.logger.info(f"'{site_name}' has prefix of '{assigned_prefix}'.")
        else:
            print(f"No prefix found for site: {site_name}")
        
        site_subnets = IPv4Network(str(site.prefixes.first())).subnets(new_prefix=ROLE_PREFIX_SIZE)

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
            status = active_status,
            location = self.site
        )
        self.logger.info(f"'{server_prefix}' assigned to '{server_role}'.")

        mgmt_role = Role.objects.get(name="mgmt")
        mgmt_prefix, created = Prefix.objects.get_or_create(
            prefix = str(mgmt_subnet),
            type = "network", 
            role = mgmt_role,
            parent = pop_prefix,
            status = active_status
        )
        self.logger.info(f"'{mgmt_prefix}' assigned to '{mgmt_role}'.")

        loopback_role = Role.objects.get(name="loopback")
        loopback_prefix, created = Prefix.objects.get_or_create(
            prefix = str(loopback_subnet),
            type = "network", 
            role = loopback_role,
            parent = pop_prefix,
            status = active_status
        )
        self.logger.info(f"'{loopback_prefix}' assigned to '{loopback_role}'.")

        p2p_role = Role.objects.get(name="p2p")
        p2p_prefix, created = Prefix.objects.get_or_create(
            prefix = str(p2p_subnet),
            type = "network",
            location = self.site,
            role = p2p_role,
            parent = pop_prefix,
            status = active_status
        )
        self.logger.info(f"'{p2p_prefix}' assigned to '{p2p_role}'.")

register_jobs(
    CreatePop
)