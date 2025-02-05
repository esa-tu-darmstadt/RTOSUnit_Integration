FROM ubuntu

RUN apt-get update && apt-get -y install pip verilator git && git clone https://github.com/esa-tu-darmstadt/BSVTools.git /opt/bsvtools && DEBIAN_FRONTEND=noninteractive apt-get install -y libtcl && pip install --break-system-packages cocotb && ln -s /usr/lib/x86_64-linux-gnu/libtcl8.6.so.0 /usr/lib/x86_64-linux-gnu/libtcl8.5.so