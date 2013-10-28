#!/usr/bin/env python
######################################################################
# TODO copyright
# Copyright (c) 2013
#
# This program is free software. You may copy or redistribute it under
# the same terms as Perl itself. Please see the LICENSE.Artistic filename
# included with this project for the terms of the Artistic License
# under which this project is licensed.
######################################################################

import glob
import json
import os
import utils

from gearbox import Worker
from gearbox import Scoreboard
from gearbox import StopWatch


class WorkerTestBasicPython(Worker):
    DBDIR = "/usr/var/gearbox/db/test-basic-python/"

    def __init__(self):
        super(WorkerTestBasicPython, self).__init__()

        self.register_handler("do_get_testbasicpy_thing_v1")
        self.register_handler("do_put_testbasicpy_thing_v1")
        self.register_handler("do_post_testbasicpy_thing_v1")
        self.register_handler("do_delete_testbasicpy_thing_v1")

    def do_get_testbasicpy_thing_v1(self, job, resp):
        if "TestBasic" in job.environ():
            env = job.environ()["TestBasic"]
            resp.add_header("TestBasic", env["TestBasic"])

        args = job.arguments()

        if not args:  # index GET
            files = glob.glob(self.DBDIR + "*")
            out = {}
            out["things"] = {}
            limit = len(files)

            if "_count" in job.query_params():
                cgi = job.query_params()
                limit = eval(cgi["_count"])

            for i in xrange(limit):
                matrix = job.matrix_arguments()
                if "_expand" in matrix and matrix["_expand"] == "1":
                    contents = utils.file_get_contents(files[i])
                    out["things"].append(json.loads(contents))
                else:
                    out["things"].append(os.path.basename(files[i]))
        else:
            name = args[0]
            file_path = os.path.join(self.DBDIR, name)
            if os.path.exists(file_path):
                resp.content(utils.file_get_contents(file_path))
            else:
                raise ERR_NOT_FOUND("thing %(name)s not found" % locals())

        return Worker.WORKER_SUCCESS

    def do_put_testbasicpy_thing_v1(self, job, resp):
        # async message, so update status to let user know we are processing
        resp.status().progress(10)
        resp.status().add_message("processing")
        args = job.arguments()
        if not args:
            raise ERR_BAD_REQUEST("missing required resource name")

        job_content = json.loads(job.content())
        if not "id" in job_content:
            raise ERR_BAD_REQUEST("missing required \"id\" field")

        filename = os.path.join(self.DBDIR, args[0])
        utils.file_put_contents(filename, job.content())
        resp.status().add_message("done")

        return Worker.WORKER_SUCCESS

    def do_post_testbasicphp_thing_v1(self, job, resp):
        resp.status().progress(10)
        resp.status().add_message("processing")

        # test SWIG wapper for scoreboarding
        Scoreboard.initialize(resp.status().component())
        sb = Scoreboard.get_scoreboard()
        sb.increment_counter("status", "testbasicphp")

        sw = StopWatch()
        sw.start()
        sw.stop()

        sb.update_duration_hours("status", "testbasicphp",
                                 "duration_success", sw)

        if job.operation() == "create":
            # post-create where the resource id is created for user
            # (instead of a PUT where the user specifies the name)

            # get the generated id
            job_content = json.loads(job.content())
            job_content["id"] = job.resource_name()

            filename = os.path.join(self.DBDIR, job.resource_name())
            utils.file_put_contents(filename, json.dumps(job_content))
        else:
            args = job.arguments()
            # post update
            filename = os.path.join(self.DBDIR, args[0])
            if os.path.exists(filename):
                job_content = json.loads(job.content())
                out = json.loads(utils.file_get_contents(filename))
                out["stuff"] = job_content["stuff"]
                utils.file_put_contents(filename, json.dumps(out))
            else:
                raise ERR_NOT_FOUND("thing \"%s\" not found" % args[0])
        resp.status().add_message("done")
        return Worker.WORKER_SUCCESS

    def do_delete_testbasicphp_thing_v1(self, job, resp):
        resp.status().progress(10)
        resp.status().add_message("processing")

        # don't actually delete if fake-out header is set
        headers = job.headers()
        if "fake-out" in headers and eval(headers["fake-out"]):
            resp.status().add_message("ignoring delete due to fake-out header")
            return Worker.WORKER_SUCCESS

        args = job.arguments()
        if not args:
            raise ERR_BAD_REQUEST("missing required resource name")

        filename = os.path.join(self.DBDIR, args[0])
        if os.path.exists(filename) and os.path.isfile(filename):
            os.unlink(filename)
        else:
            raise ERR_NOT_FOUND("thing \"%s\" not found" % args[0])

        resp.status().add_message("done")
        return Worker.WORKER_SUCCESS


if __name__ == "__main__":
    worker = WorkerTestBasicPhp(sys.argv[1])
    worker.run()
