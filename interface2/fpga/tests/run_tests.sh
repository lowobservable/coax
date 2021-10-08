#!/bin/bash

VVP=vvp

set -o pipefail

ANY_FAILURES=0

for TB in *_tb; do
    echo "Running $TB"

    ${VVP} -n $TB | awk "BEGIN{f=0} /^\[FAIL:/{f=1} 1; END{exit(f)}"

    if [ $? != 0 ]; then
        ANY_FAILURES=1
    fi
done

exit $ANY_FAILURES
