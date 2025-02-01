"""Job to create a new site of type POP."""
import logging
# from nautobot.extras.jobs import *
from nautobot.apps.jobs import Job, ObjectVar, register_jobs, StringVar, IntegerVar

from nautobot.dcim.models.locations import Location, LocationType
from nautobot.dcim.models.devices import Device, DeviceType, Platform

from nautobot.extras.models import Status
from nautobot.tenancy.models import Tenant

logger = logging.getLogger(__name__)

name = "Data Population Jobs Collection"


class CreatePop1(Job):
    """Job to create a new site of type POP."""

    location_type = StringVar(description="Type of Location", label="Location Type")

    site_name = StringVar(description="Name of the new site", label="Site Name")

    # site_code = StringVar(description="Slug of the new site", label="Site Code")

    # site_facility = StringVar(description="Facility of the new site", label="Site Facility")

    # leaf_count = IntegerVar(description="Number of Leaf Switch", label="Leaf switches count", min_value=1, max_value=12)

    class Meta:
        """Meta class for CreatePop."""

        name = "Create a POP"
        description = """
        Create a new Site of Type POP with 2 Edge Routers and N leaf switches.
        A new /16 will automatically be allocated from the 'POP Global Pool' Prefix
        """
        label = "POP"
        field_order = [
            "location_typesite_name",
            "site_code",
            "site_facility",
        ]

    def create_location_type(location_type):
        location_type_site = LocationType.objects.get_or_create(name=location_type)
        return location_type_site

    def run(self, location_type, site_name):
        """Main function for CreatePop."""

        # ----------------------------------------------------------------------------
        # Initialize the database with all required objects
        # ----------------------------------------------------------------------------
        # create_custom_fields()
        # create_relationships()
        # create_prefix_roles()

        location_type_site = LocationType.objects.get_or_create(name=location_type)
        self.site_name = site_name
        # self.site_facility = site_facility
        # self.site_code = site_code
        # self.location = data["location"]
        # self.tenant = data["tenant"]
        self.status = Status.objects.get(name="Active")
        self.site, created = Location.objects.get_or_create(
            name=self.site_name,
            # location=self.location,
            location_type=LocationType.objects.get(name=location_type),
            status=self.status,
            # facility=self.site_facility,
            # tenant=self.tenant,
        )
        # self.site.custom_field_data["site_type"] = "POP"
        logger.success(self.site, f"Site {name} successfully created")
# Location Type
# Location
# Role
# Manufacturer


# Device Type
# Prefixes