#!/bin/sh

cat <<EOF
{
    "component" : "testagentspy",

    "daemons" : [{
        "name" : "worker",
        "logname": "%{component}",
        "command" : "$ROOT/bin/workerTestAgents.pl $ROOT/conf/gearbox/test-agents-py.conf",
        "count" : 6,
        "user" : "%{gearbox.user}"
    }]
}

EOF
