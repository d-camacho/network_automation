"""Job to create a new site of type POP with optional parent site support."""

from nautobot.apps.jobs import Job, ObjectVar, register_jobs, StringVar
from nautobot.dcim.models.locations import Location, LocationType
from nautobot.extras.models import Status


name = "Data Population Jobs Collection"


class CreatePop1(Job):
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
        field_order = ["parent_site", "location_type", "site_name", "site_facility"]

    def run(self, location_type, site_name, site_facility, parent_site=None):
        """Main function to create a site."""

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

register_jobs(
    CreatePop1
)

