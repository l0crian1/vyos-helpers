#!/usr/bin/env python3

import json

from vyos_helpers import log_message
from vyos_helpers import ntfy
from vyos_helpers import configure
from vyos_helpers import ping_test
from vyos_helpers import ping_targets

from vyos.utils.process import cmd
from vyos.utils.dict import dict_search_args

# Variables
addresses = [*ping_targets["cloudflare"], *ping_targets["google"], *ping_targets["quad9"]]
peer = "172.16.0.2"

bgp_data = json.loads(cmd(f"vtysh -c 'show ip bgp neighbor {peer} json'"))
def_sent = dict_search_args(bgp_data, peer, 'addressFamilyInfo', 'ipv4Unicast', 'defaultSent')

pingcheck = ping_test(addresses)

if pingcheck:
    #log_message("DEBUG: At least one address is reachable. No action needed.", "ispcheck.py")
    if not def_sent:
        log_message(f"Service restored. Restoring default route to {peer}...", "ispcheck.py")    
        ntfy(f"ISP checks passed. Restoring default route to peer {peer}", "http://10.0.95.80/bgp")
        configure([f'set protocols bgp neighbor {peer} address-family ipv4-unicast default-originate'])
else:
    if def_sent:
        log_message(f"All addresses failed to respond. Withdrawing default route to {peer}...", "ispcheck.py")
        ntfy(f"ISP checks failed. Withdrawing default route to peer {peer}", "http://10.0.95.80/bgp")
        configure([f'delete protocols bgp neighbor {peer} address-family ipv4-unicast default-originate'])
        
