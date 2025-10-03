from jinja2 import Environment, FileSystemLoader, StrictUndefined
import yaml
from yaml import Loader

# TEMPLATEDIR = "video-config-templates/cisco_nxos"
TEMPLATEDIR = "video-config-templates/cisco_xr"

# TEMPLATE = "aaa.j2"
# TEMPLATE = "snmp.j2"
# TEMPLATE = "ntp.j2"
# TEMPLATE = "mgmt.j2"
TEMPLATE = "logging.j2"
# TEMPLATE = "acl.j2"

## IOSXR ##
# VARIABLES_FILE = "video-config-variables/config_contexts/video_iosxr_aaa.yml"
# VARIABLES_FILE = "video-config-variables/config_contexts/video_iosxr_snmp.yml"
# VARIABLES_FILE = "video-config-variables/config_contexts/video_iosxr_ntp.yml"
# VARIABLES_FILE = "video-config-variables/config_contexts/video_iosxr_mgmt.yml"
VARIABLES_FILE = "video-config-variables/config_contexts/video_iosxr_logging.yml"
# VARIABLES_FILE = "video-config-variables/config_contexts/video_iosxr_acl.yml"

## NXOS ##
# VARIABLES_FILE = "video-config-variables/config_contexts/video_nxos_snmp.yml"
# VARIABLES_FILE = "video-config-variables/config_contexts/video_nxos_ntp.yml"
# VARIABLES_FILE = "video-config-variables/config_contexts/video_nxos_logging.yml"
# VARIABLES_FILE = "video-config-variables/config_contexts/video_nxos_mgmt.yml"

OUTPUT_FILE = "output-mytest.txt"

with open(VARIABLES_FILE, "r") as fin:
    _variables = yaml.load(fin.read(), Loader=Loader)
VARIABLES = {"config_context": _variables, "hostname": "CHANGE_ME", "device": {}}
# print(VARIABLES)

env = Environment(
    loader=FileSystemLoader(TEMPLATEDIR), trim_blocks=True, lstrip_blocks=True, undefined=StrictUndefined,#, keep_trailing_newline=True
)
template = env.get_template(TEMPLATE)

data = template.render(**VARIABLES)

# print(data)
with open(OUTPUT_FILE, "w") as fout:
    fout.write(data)