# See https://github.com/halfmanhalftaco/fpga-docker/tree/master/Lattice_iCEcube2
ICECUBE2_WRAPPER = docker run -t --rm --volume $(RTL):/data --workdir /data --mac-address=$(or $(ICECUBE2_MAC_ADDRESS),$(shell cat .mac_address)) $(or $(ICECUBE2_IMAGE),icecube2:latest) ./icecube2_env.sh

RTL = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
IMPLMNT = coax_Implmnt

all: top.bin top_timing_report.txt

$(IMPLMNT)/coax.edf: coax_syn.prj *.v third_party/*.v clocks.sdc
	$(ICECUBE2_WRAPPER) synpwrap -prj coax_syn.prj

$(IMPLMNT)/sbt/outputs/bitmap/top_bitmap.bin $(IMPLMNT)/sbt/outputs/router/top_timing.rpt: $(IMPLMNT)/coax.edf pins.pcf
	$(ICECUBE2_WRAPPER) ./icecube2_flow.tcl

top.bin: $(IMPLMNT)/sbt/outputs/bitmap/top_bitmap.bin
	rm -f $@
	cp $< $@

top_timing_report.txt: $(IMPLMNT)/sbt/outputs/router/top_timing.rpt
	rm -f $@
	cp $< $@

clean:
	rm -rf $(IMPLMNT) synlog.tcl *.bin *_report.txt *.log *.log.bak

.PHONY: all clean
