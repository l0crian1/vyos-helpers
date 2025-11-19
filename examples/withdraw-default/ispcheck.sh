#!/bin/vbash

# Set ID to vyattacfg for proper updates
if [ "$(id -g -n)" != 'vyattacfg' ] ; then
    exec sg vyattacfg -c "/bin/vbash $(readlink -f $0) $@"
fi

source /opt/vyatta/etc/functions/script-template
source <(/config/scripts/ispcheck.py)
