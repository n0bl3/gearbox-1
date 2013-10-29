#!/bin/sh
cat <<EOF
{
    "component" : "testcancelpy",

    "daemons" : [{
        "name" : "worker",
        "logname": "%{component}",
        "command" : "$ROOT/bin/workerTestCancel.pl $ROOT/conf/gearbox/test-cancel-py.conf",
        "count" : 1,
        "user" : "%{gearbox.user}"
    }]
}

EOF
