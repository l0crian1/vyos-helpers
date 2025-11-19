This example withdraws a default route when the upstream connectivity fails. This is useful for when the internet connection is static or learned via DHCP. It will withdraw a default route into a LAN environment to allow less preferred default routes learned via other routers to be used until connectivity is restored.

`vyos_helpers.py` must be placed on the same folder as the shell script and configuration script. Recommended `/config/scripts/`

The scripts must be made executable:
```
chmod +x /config/scripts/ispcheck.sh
chmod +x /config/scripts/ispcheck.py
```

The shell script must be added to the task scheduler:
```
set system task-scheduler task ISP_CHECK executable path '/config/scripts/ispcheck.sh'
set system task-scheduler task ISP_CHECK interval '1m'
```
