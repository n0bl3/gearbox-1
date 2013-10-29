#!/bin/sh
cat <<EOF
{
    "component" : "testdelaypy",

    "daemons" : [{
        "name" : "worker",
        "logname": "%{component}",
        "command" : "$ROOT/bin/workerTestDelay.pl $ROOT/conf/gearbox/test-delay-py.conf",
        "count" : 3,
        "user" : "%{gearbox.user}"
    }]
}

EOF
