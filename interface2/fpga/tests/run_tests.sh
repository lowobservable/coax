#!/bin/bash

VVP=vvp

set -o pipefail

if [ $# -eq 0 ]; then
    TESTS=(*_tb)
else
    TESTS=$@
fi

ANY_FAILURES=0

for TEST in ${TESTS[@]}; do
    echo "Running $TEST"

    ${VVP} -n $TEST | awk "BEGIN{f=0} /^\[FAIL:/{f=1} 1; END{exit(f)}"

    if [ $? != 0 ]; then
        ANY_FAILURES=1
    fi
done

exit $ANY_FAILURES
