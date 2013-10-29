#!/bin/sh
bindir=/usr/bin

cat <<EOF
{
    "component" : "testpy",

    "daemons" : [{
        "name" : "worker",
        "logname": "%{component}",
        "command" : "/usr/bin/python $bindir/workerTestPy.py $ROOT/conf/gearbox/test-py.conf",
        "count" : 1,
        "user" : "%{gearbox.user}"
    }]
}

EOF
