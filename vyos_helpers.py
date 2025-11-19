#!/usr/bin/env python3

import time
import syslog

from vyos.utils.process import cmd
from vyos.utils.process import rc_cmd
from vyos.utils.process import run

def ntfy(message, url):
    """
    Send a notification via an ntfy.sh endpoint.
    More info: https://ntfy.sh/

    Args:
        message (str): Message body to send.
        url (str): Full ntfy endpoint URL.

    Notes:
        Caller should ensure the URL points to the correct topic and
        that ntfy.sh is reachable.
    """    
    run(f'curl -d "{message}" {url}')

def log_message(message, process, level=syslog.LOG_INFO):
    """
    Send a syslog message with a custom process name.

    Args:
        message (str): The text to log.
        process (str): The syslog identifier to tag the message with.
        level (int, optional): Syslog severity level.
            Defaults to syslog.LOG_INFO.

    Notes:
        This is useful when multiple components or scripts need to log
        separately within VyOS or systemd-journald.
    """    
    syslog.openlog(process, syslog.LOG_PID)
    syslog.syslog(level, message)    
    syslog.closelog()

def configure(commands):
    """
    Output VyOS configuration commands in a format suitable for execution
    by a vbash wrapper script.

    Args:
        commands (iterable[str]): A list or iterable of VyOS configuration
            commands (e.g., "set interfaces ethernet eth0 address dhcp").

    Behavior:
        Prints:
            - 'configure' to enter configuration mode
            - each command on its own line
            - 'commit' to apply the configuration

    Notes:
        This function is designed to be used in conjunction with a vbash wrapper
        such as:

            #!/bin/vbash
            if [ "$(id -g -n)" != 'vyattacfg' ]; then
                exec sg vyattacfg -c "/bin/vbash $(readlink -f $0) $@"
            fi

            source /opt/vyatta/etc/functions/script-template
            source <(/config/scripts/ispcheck.py)

        When the Python script prints these commands, the wrapper script
        evaluates them directly inside a real VyOS configuration session.
        No commands are executed by Python itself — only emitted.
    """
    print('configure')
    for command in commands:
        print(command)
    print('commit')

def ping_test(addresses, retries=3, interval=5):
    """
    Test reachability of one or more targets using ping.

    Args:
        addresses (list[str]): IP addresses or hostnames to ping.
        retries (int, optional): How many total ping rounds to attempt.
        interval (int, optional): Seconds to wait between retry rounds.

    Returns:
        bool: True if any address responds during any attempt,
              False if all attempts fail.

    Notes:
        Uses single ICMP echo requests with a short timeout to keep
        checks fast. Intended for ISP failover, link-health checks,
        or route-validation logic.
    """    
    for attempt in range(retries):
        if any(run(f"ping {addr} -c 1 -W 0.5") == 0 for addr in addresses):
            return True
        if attempt < retries - 1:
            time.sleep(interval)
    return False

def dns_test(servers, query, retries=3, interval=5):
    """
    Test whether a DNS record exists by querying one or more DNS servers.

    Args:
        servers (list[str]): DNS server IPs to query.
        record (str): Domain name (or FQDN) to check.
        retries (int, optional): Total retry rounds. Defaults to 3.
        interval (int, optional): Seconds between retries. Defaults to 5.

    Returns:
        bool: True if any server returns a non-empty ANSWER section during
              any attempt, False if all attempts fail.
    """
    for attempt in range(retries):
        for server in servers:
            output = cmd(f"dig @{server} {query} +time=1 +tries=1 +retry=0 +noall +answer")
            if output and output.strip():
                return True

        if attempt < retries - 1:
            time.sleep(interval)

    return False

def http_test(urls, retries=3, timeout=2):
    """
    Test whether any HTTP/HTTPS URL in a list is reachable.

    Args:
        urls (list[str]): List of URLs to test.
        retries (int, optional): Total attempts. Defaults to 3.
        timeout (int, optional): Curl timeout in seconds. Defaults to 2.

    Returns:
        bool: True if any URL returns a 2xx or 3xx status code during any
              attempt, False if all attempts fail.
    """
    for attempt in range(retries):
        for url in urls:
            # curl prints only the HTTP status code
            rc, status = rc_cmd(
                f"curl -s -o /dev/null -w '%{{http_code}}' --max-time {timeout} '{url}'"
            )

            # rc != 0 means curl failed (DNS, TLS, timeout, connection refused, etc.)
            # so we only evaluate status when we got output
            if status:
                code = status.strip()
                if code and code[0] in ("2", "3"):
                    return True

    return False
