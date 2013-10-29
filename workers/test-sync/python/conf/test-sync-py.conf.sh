#!/bin/sh
cat <<EOF
{
    "component" : "testsyncpy",

    "daemons" : [{
        "name" : "worker",
        "logname": "%{component}",
        "command" : "$ROOT/bin/workerTestSync.pl $ROOT/conf/gearbox/test-sync-py.conf",
        "count" : 1,
        "user" : "%{gearbox.user}"
    }]
}
EOF
