FROM ubuntu

RUN apt-get update && apt-get -y install pip verilator git && git clone https://github.com/esa-tu-darmstadt/BSVTools.git /opt/bsvtools && DEBIAN_FRONTEND=noninteractive apt-get install -y libtcl && pip install --break-system-packages cocotb && ln -s /usr/lib/x86_64-linux-gnu/libtcl8.6.so.0 /usr/lib/x86_64-linux-gnu/libtcl8.5.so

RUN apt-get -y install autoconf automake autotools-dev curl python3 python3-pip python3-tomli libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev && git clone https://github.com/riscv/riscv-gnu-toolchain && cd riscv-gnu-toolchain && mkdir /opt/riscv && ./configure --prefix=/opt/riscv --with-arch=rv32i --with-abi=ilp32 && make -j 16 && cd .. && rm -rf riscv-gnu-toolchain 
RUN git clone https://github.com/riscv/riscv-gnu-toolchain && cd riscv-gnu-toolchain && mkdir /opt/riscv_e && ./configure --disable-gdb --prefix=/opt/riscv_e --with-arch=rv32em_zicsr --with-abi=ilp32e && make -j 16 && cd .. && rm -rf riscv-gnu-toolchain
RUN pip install --break-system-packages cocotb_bus cocotbext-axi pandas matplotlib seaborn