create_clock -period 25.00 -name {clk} [get_ports {clk}]
create_clock -period 100.00 -name {spi_sck} [get_ports {spi_sck}]
