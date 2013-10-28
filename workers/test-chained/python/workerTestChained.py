#!/usr/bin/env python
######################################################################
# TODO copyright
# Copyright (c) 2013
#
# self program is free software. You may copy or redistribute it under
# the same terms as  itself. Please see the LICENSE.Artistic file
# included with self project for the terms of the Artistic License
# under which self project is licensed.
######################################################################

import json
import os
import sys
import time

from gearbox import HttpClient
from gearbox import Job
from gearbox import Worker
from gearbox import utils


class WorkerTestChainedPython(Worker):
    DBDIR = "/usr/var/gearbox/db/test-chained-py/"

    def __init__(self, config):
        super(WorkerTestChainedPython, self).__init__(config)

        self.register_handler("do_get_testchainedpy_hello_v1")
        self.register_handler("do_get_internalpy_hello1_v1")
        self.register_handler("do_post_testchainedpy_hello2_v1")

        self.register_handler("do_get_testchainedpy_goodbye_v1")
        self.register_handler("do_post_testchainedpy_goodbye_v1")
        self.register_handler("do_append_internalpy_goodbye1_v1")
        self.register_handler("do_append_internalpy_goodbye2_v1")

        self.register_handler("do_get_testchainedpy_thing_v1")
        self.register_handler("do_post_testchainedpy_thing_v1")
        self.register_handler("do_reg_internalpy_service1_v1")
        self.register_handler("do_post_testchainedpy_service2_v1")

        self.register_handler("do_delete_testchainedpy_thing_v1")
        self.register_handler("do_unreg_internalpy_service1_v1")
        self.register_handler("do_delete_testchainedpy_service2_v1")

    # I am not sure why we would want to do a chained syncronous get, but
    # you can chain a bunch of sync jobs together
    def do_get_testchainedpy_hello_v1(self, job, resp):
        content = json.loads("Hello from job")

        # do internal hello1 which just appends it name to our content
        j = Job(job)
        j.name("do_get_internalpy_hello1_v1")
        j.type(Job.JOB_SYNC)
        j.content(content)
        r = j.run()

        # create sync http rest job back to localhost which takes
        # the output from previous job and adds its own name.
        j = self.job_manager().job(HttpClient.METHOD_POST,
                                   job.base_uri() + "/hello2")
        j.content(r.content())
        j.headers(r.headers())
        r = j.run()

        resp.content(r.content())
        resp.headers(r.headers())
        return Worker.WORKER_SUCCESS

    def do_get_internalpy_hello1_v1(self, job, resp):
        job_content = json.dumps(job.content())
        job_content = job_content + " and job1"
        resp.add_header("job1-header", "1")
        resp.content(json.loads(job_content))
        return Worker.WORKER_SUCCESS

    # self is a SYNC post call configured via the httpd-test-chained.conf
    def do_post_testchainedpy_hello2_v1(self, job, resp):
        job_content = json.dumps(job.content())
        job_content = job_content + " and job2"
        resp.headers(job.headers())
        resp.add_header("job2-header", "1")
        resp.content(json.loads(job_content))
        return Worker.WORKER_SUCCESS

    def do_get_testchainedpy_goodbye_v1(self, job, resp):
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        resp.content(utils.file_get_contents(resource_file))
        return Worker.WORKER_SUCCESS

    def do_post_testchainedpy_goodbye_v1(self, job, resp):
        resp.status().add_message("processing from %s" % job.name())
        content = json.loads("Goodbye from job")
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        utils.file_put_contents(resource_file, content)

        # do internal goodbye1 which just appends its name to our content
        self.afterwards(job, "do_append_internalpy_goodbye1_v1")
        # don't finalize the status, are going to keep going
        return Worker.WORKER_CONTINUE

    def do_append_internalpy_goodbye1_v1(self, job, resp):
        resp.status().add_message("processing from %s" % job.name())
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        content = json.dumps(utils.file_get_contents(resource_file))
        content = content + " and job1"
        utils.file_put_contents(resource_file, json.loads(content))

        # do internal goodbey2 which just appends it name to our content
        self.afterwards(job, "do_append_internalpy_goodbye2_v1")
        # don't finalize the status, are going to keep going
        return Worker.WORKER_CONTINUE

    def do_append_internalpy_goodbye2_v1(self, job, resp):
        resp.status().add_message("processing from %s" % job.name())
        os.path.join(self.DBDIR, job.resource_name())
        content = json.dumps(utils.file_get_contents())
        content = content + " and job2"
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        utils.file_put_contents(resource_file, json.loads(content))

        # finally done so dont continue
        return Worker.WORKER_SUCCESS

    def do_get_testchainedpy_thing_v1(self, job, resp):
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        resp.content(utils.file_get_contents(resource_file))
        return Worker.WORKER_SUCCESS

    def do_post_testchainedpy_thing_v1(self, job, resp):
        resp.status().add_message("processing from %s" % job.name())
        out = {}
        out["id"] = job.resource_name()
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        utils.file_put_contents(resource_file, json.loads(out))

        # our new thing needs to be registered with 2 fancy
        # services. They can both be registered at the same
        # time in parallel.
        jm = self.job_manager()

        responses = []

        # service 1 is registered via async local worker
        service_job = jm.job("do_reg_internalpy_service1_v1")
        responses.append(service_job.content(json.loads(out)).run())
        responses.append(jm.job(HttpClient.METHOD_POST,
                         (job.base_uri() + "/service2").
                         content(json.loads(out)).run()))

        while not responses:
            s = responses[0].status()

            sm = self.status_manager()
            sm.fetch(s.uri())

            s.sync()
            if s.has_completed():
                if s.is_success():
                    responses.pop()
                else:
                    err_class = eval("ERR_CODE_" + s.code())
                    msgs = s.messages()
                    raise err_class(msgs[0])

                # pause between polling again
                time.sleep(1)

        return Worker.WORKER_SUCCESS

    def do_reg_internalpy_service1_v1(self, job, resp):
        resp.status().add_message("service1 registered")
        return Worker.WORKER_SUCCESS

    def do_post_testchainedpy_service2_v1(self, job, resp):
        resp.status().add_message("service2 registered")
        return Worker.WORKER_SUCCESS

    def do_delete_testchainedpy_thing_v1(self, job, resp):
        # our new thing needs to be unregistered with 2 fancy
        # services.  service 1 must be unregistered before service 2

        resource_file = os.path.join(self.DBDIR, job.resource_name())
        content = utils.file_get_contents(resource_file)

        jm = self.job_manager()

        jobs = []

        # first gen jobs only has service1, unregister happens via local worker
        jobs.append(jm.job("do_unreg_internalpy_service1_v1"))

        # second gen jobs only has service 2, unregister happens via DELETE
        # http call on remote worker
        jobs.append(jm.job(HttpClient.METHOD_DELETE,
                           job.base_uri() + "/service2"))

        jm.job_queue_apply(jobs, "content", content)

        jm.job_queue_run(jobs)
        return Worker.WORKER_SUCCESS

    def do_unreg_internalpy_service1_v1(self, job, resp):
        resp.status().add_message("service1 unregistered")
        return Worker.WORKER_SUCCESS

    def do_delete_testchainedpy_service2_v1(self, job, resp):
        resp.status().add_message("service2 unregistered")
        return Worker.WORKER_SUCCESS


if __name__ == "__main__":
    worker = WorkerTestChainedPython(sys.argv[1])
    worker.run()
