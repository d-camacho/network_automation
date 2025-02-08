
"""Job to create a new site of type POP with optional parent site support."""

from nautobot.apps.jobs import Job, ObjectVar, register_jobs, StringVar
from nautobot.dcim.models.locations import Location, LocationType
from nautobot.extras.models import Status
from nautobot.extras.models.roles import Role
from nautobot.ipam.models import Prefix


name = "Data Population Jobs Collection"


PREFIX_ROLES = ["p2p", "loopback", "server", "mgmt", "pop"]
POP_PREFIX_SIZE = 16

def create_prefix_roles():
    """Create all Prefix Roles defined in PREFIX_ROLES."""
    for role in PREFIX_ROLES:
        role_obj, _ = Role.objects.get_or_create(name=role)
        role_obj.validated_save()

        

class CreatePop1(Job):
    """Job to create a new site of type POP."""

    # location_type = StringVar(description="Type of Location", label="Location Type")
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
        else:
            self.logger.warning(f"Site '{site_name}' already exists.")

        # ----------------------------------------------------------------------------
        # Allocate Prefixes for this POP
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


# register_jobs(
#     CreatePop1
# )
