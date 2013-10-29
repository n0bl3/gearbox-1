#!/usr/bin/env python
######################################################################
# TODO copytright
# Copyright (c) 2013
#
# self program is free software. You may copy or redistribute it under
# the same terms as python itself. Please see the LICENSE.Artistic file
# included with self project for the terms of the Artistic License
# under which self project is licensed.
######################################################################

import glob
import json
import os
import sys

import gearbox
from gearbox import Worker
from gearbox import utils


class WorkerTestSyncPy(Worker):
    DBDIR = "/usr/var/gearbox/db/test-sync-py/"

    def __init__(self, config):
        super(WorkerTestSyncPy, self).__init__(config)

        self.register_handler("do_get_testsyncpy_thing_v1")
        self.register_handler("do_put_testsyncpy_thing_v1")
        self.register_handler("do_post_testsyncpy_thing_v1")
        self.register_handler("do_delete_testsyncpy_thing_v1")

    def do_get_testsyncpy_thing_v1(self, job, resp):
        if "TestSync" in job.environ():
            env = job.environ()
            resp.add_header("TestSync", env["TestSync"])

        args = job.arguments()
        if not args:
            files = glob.glob(self.DBDIR + "*")
            out = {}

            # set things to an empty array in case our glob did not match
            # anything
            out["things"] = []
            limit = len(files)

            if "_count" in job.query_params():
                cgi = job.query_params()
                limit = eval(cgi["_count"])

            for i in xrange(limit):
                matrix = job.matrix_arguments()
                if "_expand" in matrix and matrix["_expand"] == "1":
                    file_contents = utils.file_get_contents(files[i])
                    out["things"].append(json.dumps(file_contents))
                else:
                    out["things"].append(os.path.basename(files[i]))

            # set the output content
            resp.content(json.loads(out))
        else:
            name = args[0]
            file_name = os.path.join(self.DBDIR, name)
            if os.path.exists(file_name):
                resp.content(utils.file_get_contents(file_name))
            else:
                raise gearbox.ERR_NOT_FOUND("thing \"%s\" not found" % name)

        return Worker.WORKER_SUCCESS

    def do_put_testsyncpy_thing_v1(self, job, resp):
        args = job.arguments()
        if not args:
            raise gearbox.ERR_BAD_REQUEST("missing required resource name")

        job_content = json.dumps(job.content())
        if not "id" in job_content:
            raise gearbox.ERR_BAD_REQUEST("missing required \"id\" field")

        utils.file_put_contents(os.path.join(self.DBDIR, args[0]),
                                job.content())

        resp.content(job.content())
        return Worker.WORKER_SUCCESS

    def do_post_testsyncpy_thing_v1(self, job, resp):
        if job.operation() == "create":
            # post-create where the resource id is created for user
            # (instead of a PUT where the user specifies the name)

            # get the generated id
            job_content = json.dumps(job.content())
            job_content["id"] = job.resource_name()

            content = json.loads(job_content)
            resource_file = os.path.join(self.DBDIR, job.resource_name())
            utils.file_put_contents(resource_file, content)
            resp.content(content)
        else:
            args = job.arguments()
            # post update
            file_name = os.path.join(self.DBDIR, args[0])
            if os.path.exists(file_name):
                job_content = json.dumps(job.content())
                out = json.dumps(utils.file_get_contents(file_name))
                out["stuff"] = job_content["stuff"]
                content = json.loads(out)
                utils.file_put_contents(file_name, content)
                resp.content(content)
            else:
                raise gearbox.ERR_NOT_FOUND("thing \"%s\" not found" % args[0])

        return Worker.WORKER_SUCCESS

    def do_delete_testsyncpy_thing_v1(self, job, resp):
        # don't actually delete if fake-out header is set
        headers = job.headers()
        if "fake-out" in headers and eval(headers["fake-out"]):
            return Worker.WORKER_SUCCESS

        args = job.arguments()
        if not args:
            raise gearbox.ERR_BAD_REQUEST("missing required resource name")

        file_name = os.path.join(self.DBDIR, args[0])
        if os.path.exists(file_name) and os.path.isfile(file_name):
            os.unlink(file_name)
        else:
            raise gearbox.ERR_NOT_FOUND("thing \"%s\" not found" % args[0])

        return Worker.WORKER_SUCCESS


if __name__ == "__main__":
    worker = WorkerTestSyncPy(sys.argv[1])
    worker.run()
