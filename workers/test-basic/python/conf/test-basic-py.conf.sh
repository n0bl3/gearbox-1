#!/bin/sh
cat <<EOF
{
    "component" : "testbasicpy",

    "daemons" : [{
        "name" : "worker",
        "logname": "%{component}",
        "command" : "$ROOT/bin/workerTestBasic.pl $ROOT/conf/gearbox/test-basic-py.conf",
        "count" : 1,
        "user" : "%{gearbox.user}"
    }]
}

EOF
