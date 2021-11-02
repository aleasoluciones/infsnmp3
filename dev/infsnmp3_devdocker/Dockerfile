FROM python:3.7-slim
LABEL maintainer="bifer@alea-soluciones.com"

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m pip install --upgrade pip && python -m pip install snmpsim==0.1.5

EXPOSE 1161/udp

ENTRYPOINT python $(which snmpsimd.py) --v2c-arch --agent-udpv4-endpoint=0.0.0.0:1161 --device-dir=/simulated_data/ --validate-device-data
