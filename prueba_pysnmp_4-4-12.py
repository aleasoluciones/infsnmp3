# pysnmp 4.4.12 is needed to run this script
# pyasn1 0.4.8 is needed to run this script
from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget

AGENT_ID = 'felix_agent'
DEFAULT_BULK_SIZE = 205
DEFAULT_TIMEOUT = 2
DEFAULT_RETRIES = 2
DEFAULT_PORT = 161

def get(host, community, oids, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    try:
        iterator = getCmd(SnmpEngine(),
            CommunityData('my-agent', community),
            UdpTransportTarget(
                (host, port),
                timeout=timeout,
                retries=retries),
            *oids)
        err_indication, err_status, err_index, var_binds = next(iterator)
    except Exception:
        print("La excepción")

if __name__ == '__main__':
    while True:
        get('192.168.5.14', 'alea2', '.')

