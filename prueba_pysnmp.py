# pysnmp 4.2.4 is needed to run this script
# pyasn1 0.1.9 is needed to run this script
from pysnmp.entity.rfc3413.oneliner import cmdgen

AGENT_ID = 'felix_agent'
DEFAULT_BULK_SIZE = 205
DEFAULT_TIMEOUT = 2
DEFAULT_RETRIES = 2
DEFAULT_PORT = 161

def get(host, community, oids, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    try:
        err_indication, err_status, err_index, var_binds = cmdgen.CommandGenerator().getCmd(cmdgen.CommunityData('my-agent', community),
                                                                                            cmdgen.UdpTransportTarget(
                                                                                                (host, port),
                                                                                                timeout=timeout,
                                                                                                retries=retries),
                                                                                            *oids)
    except Exception:
        print("La excepción")

if __name__ == '__main__':
    while True:
        get('192.168.5.14', 'alea2', '.')

