#!/usr/bin/env python
######################################################################
# TODO copyright
# Copyright (c) 2013 ???
#
# This program is free software. You may copy or redistribute it under
# the same terms as Python itself. Please see the LICENSE.Artistic file
# included with this project for the terms of the Artistic License
# under which this project is licensed.
######################################################################

import json
import os
import sys
import time

from gearbox import Worker
from gearbox import utils


class WorkerTestAgentsPython(Worker):
    DBDIR = "/var/gearbox/db/test-agents-py/"

    def __init__(self):
        super(WorkerTestAgentsPython, self).__init__()

        self.register_handler("do_get_testagentsperl_thing_v1",
                              self.thing_handler)
        self.register_handler("do_post_testagentsperl_thing_v1",
                              self.thing_handler)
        self.register_handler("do_delete_testagentsperl_thing_v1",
                              self.thing_handler)

        for resource in ['A', 'B', 'C', 'D']:
            for operation in ['reg', 'unreg']:
                handler_name = ("do_%(operation)s_testagentspy_%(resource)s_v1"
                                % locals())
                self.register_handler(handler_name, self.dummy_handler)

    def thing_handler(self, job, resp):
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        if os.path.exists(resource_file):
            content = json.loads(resource_file)

        if job.operation() == "get":
            resp.content(json.dumps(content))
            return Worker.WORKER_SUCCESS

        py_agents_conf = "/etc/gearbox/test-agents-py-agents.conf"
        agents = json.loads(utils.file_get_contents(py_agents_conf))

        resp.status().add_message("calling agents")

        if job.operation() == "create":
            content['id'] = job.resource_name()
            utils.file_put_contents(resource_file, json.dumps(content))
            run_agents_job = self.job_manager.job("do_run_global_agents_v1")
            agents_content = {}
            agents_content['agents'] = agents['register']
            agents_content['content'] = json.loads(content)
            run_agents_job.content(json.loads(agents_content))
            run_agents = run_agents_job.run()
            run_status = run_agents.status()
            # poll for agents to be done
            while True:
                time.sleep(1)
                run_status.sync()
                if run_status.has_completed():
                    break
            if not run_status.is_success():
                err_code_class_name = "ERR_CODE_" + run_status.code()
                err_code_class = __import__('gearbox',
                                            fromlist=[err_code_class_name])
                raise err_code_class(run_status.message())
        else:
            # operation == delete
            job_manager = self.job_manager()
            queue = job_manager.job_queue(agents['unregister'])
            # TODO check
            job_manager.job_queue_apply(queue, "content", json.loads(content))
            job_manager.job_queue_run(queue)
            os.unlink(resource_file)
        resp.status().add_message("done")
        return Worker.WORKER_SUCCESS

    def dummy_handler(self, job, resp):
        contents = json.loads(job.content())
        operation = job.operation()
        resource_type = job.resource_type()
        operation = "registered" if operation == "reg" else "unregistered"
        content_id = contents['id']

        msg = "%(resource_type)s %(operation)s for %(content_id)s" % locals()
        resp.status().add_message(msg)

        # give us time from smoke tests to verify the progress of the
        # agents job
        if job.operation == "reg":
            time.sleep(10)

        resp.status().meta(resp.status().name(), content_id)
        return Worker.WORKER_SUCCESS


if __name__ == "__main__":
    worker = WorkerTestAgentsPython(sys.argv[1])
    worker.run()
