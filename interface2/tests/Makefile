IVERILOG ?= iverilog
VVP ?= vvp

RTL = ../rtl

all: coax_bit_timer_tb.vcd coax_tx_tb.vcd hello_world_tb.vcd

coax_bit_timer_tb: coax_bit_timer_tb.v $(RTL)/coax_bit_timer.v
coax_tx_tb: coax_tx_tb.v $(RTL)/coax_bit_timer.v $(RTL)/coax_tx.v
hello_world_tb: hello_world_tb.v $(RTL)/hello_world.v $(RTL)/coax_bit_timer.v $(RTL)/coax_tx.v

clean:
	rm -f *_tb *.vcd

%_tb:
	$(IVERILOG) -o $@ $^

%_tb.vcd: %_tb
	$(VVP) -N $< -lxt2

.PHONY: all, clean
