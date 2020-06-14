IVERILOG ?= iverilog
VVP ?= vvp

RTL = ../rtl

all: 

clean:
	rm -f *_tb *.vcd

%_tb:
	$(IVERILOG) -o $@ $^

%_tb.vcd: %_tb
	$(VVP) -N $< -lxt2

.PHONY: all, clean
