from hier_config import WorkflowRemediation, get_hconfig
from hier_config.utils import hconfig_v2_os_v3_platform_mapper, load_hconfig_v2_options

# try:
#         remediation_setting_obj = RemediationSetting.objects.get(platform=obj.rule.platform)
#     except Exception as err:  # pylint: disable=broad-except:
#         raise ValidationError(f"Platform {obj.device.platform.name} has no Remediation Settings defined.") from err

with open("actual.txt", "r") as f:
    actual = f.read()
with open("intended.txt", "r") as f:
    intended = f.read()
hierconfig_os = "ios"

try:
    
    hierconfig_os = hconfig_v2_os_v3_platform_mapper(hierconfig_os)

    hierconfig_running_config = get_hconfig(hierconfig_os, actual)
    hierconfig_intended_config = get_hconfig(hierconfig_os, intended)
    hierconfig_wfr = WorkflowRemediation(
        hierconfig_running_config,
        hierconfig_intended_config,
    )

except Exception as err:  # pylint: disable=broad-except:
    raise Exception(  # pylint: disable=broad-exception-raised
        f"Cannot instantiate HierConfig on DEVICE, check Device, Platform and Hier Options. Original error: {err}"
    ) from err

hierconfig_wfr.remediation_config  # pylint: disable=pointless-statement
remediation_config = hierconfig_wfr.remediation_config_filtered_text(include_tags={}, exclude_tags={})

print(remediation_config)
