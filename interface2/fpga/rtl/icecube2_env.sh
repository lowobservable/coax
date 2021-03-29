#!/bin/sh

export ICECUBE_DIR="/opt/icecube2"
export SBT_DIR="$ICECUBE_DIR/sbt_backend"

export FOUNDRY="$ICECUBE_DIR/LSE"
export SYNPLIFY_PATH="$ICECUBE_DIR/synpbase"
export LM_LICENSE_FILE="$ICECUBE_DIR/license.dat"

export LD_LIBRARY_PATH="$LD_LIBRARY_PATH${LD_LIBRARY_PATH:+:}$SBT_DIR/bin/linux/opt:$SBT_DIR/bin/linux/opt/synpwrap:$SBT_DIR/lib/linux/opt:$FOUNDRY/bin/lin64"

# Give precedence to iCEcube2 tools.
export PATH="$SBT_DIR/bin/linux/opt:$SBT_DIR/bin/linux/opt/synpwrap${PATH:+:}$PATH"

$*
