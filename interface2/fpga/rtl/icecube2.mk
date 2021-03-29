# See https://github.com/halfmanhalftaco/fpga-docker/tree/master/Lattice_iCEcube2
ICECUBE2_WRAPPER = docker run -it --rm --volume $(RTL):/data --workdir /data --mac-address=$(shell cat .mac_address) icecube2:latest ./icecube2_env.sh

RTL = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
IMPLMNT = coax_Implmnt

all: top.bin

$(IMPLMNT)/coax.edf: coax_syn.prj *.v third_party/*.v clocks.sdc
	$(ICECUBE2_WRAPPER) synpwrap -prj coax_syn.prj

top.bin: $(IMPLMNT)/coax.edf pins.pcf
	rm -f top.bin
	$(ICECUBE2_WRAPPER) ./icecube2_flow.tcl
	cp $(IMPLMNT)/sbt/outputs/bitmap/top_bitmap.bin top.bin

clean:
	rm -rf $(IMPLMNT) synlog.tcl *.bin *.log *.log.bak

.PHONY: all clean
