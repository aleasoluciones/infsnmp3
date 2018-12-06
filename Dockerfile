FROM ubuntu:trusty
MAINTAINER bifer@alea-soluciones.com

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        apt-utils python-pip gcc libc6-dev\
    && rm -rf /var/lib/apt/lists/*

RUN pip install snmpsim==0.1.5

EXPOSE 1161/udp

CMD python $(which snmpsimd.py) --v2c-arch --agent-udpv4-endpoint=0.0.0.0:1161 --device-dir=/simulated_data/ --validate-device-data
