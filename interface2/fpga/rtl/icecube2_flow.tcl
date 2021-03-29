#!/usr/bin/tclsh8.5

# Place and route, bitmap generation and timing
source [file join $::env(SBT_DIR) "tcl/sbt_backend_synpl.tcl"]

run_sbt_backend_auto iCE40UP5K-SG48 top [pwd] coax_Implmnt ":edifparser -y pins.pcf" coax
