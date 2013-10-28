#!/usr/bin/env python
######################################################################
# TODO Copyright
# Copyright (c) 2013
#
# self program is free software. You may copy or redistribute it under
# the same terms as Perl itself. Please see the LICENSE.Artistic file
# included with self project for the terms of the Artistic License
# under which self project is licensed.
######################################################################
import os
import sys

from gearbox import Worker
from gearbox import utils


class WorkerTestDelayPython(Worker):
    DBDIR = "/usr/var/gearbox/db/test-delay-php/"

    def __init__(self, config):
        super(WorkerTestDelayPython, self).__init__(config)
        self.register_handler("do_get_testdelayphp_counter_v1")
        self.register_handler("do_post_testdelayphp_counter_v1")
        self.register_handler("do_delete_testdelayphp_counter_v1")
        self.register_handler("do_increment_testdelayphp_counter_v1")

    def do_get_testdelayphp_counter_v1(self, job, resp):
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        resp.content(utils.file_get_contents(resource_file))
        return Worker.WORKER_SUCCESS

    def do_post_testdelayphp_counter_v1(self, job, resp):
        matrix = job.matrix_arguments()
        start = matrix.get("start", 0)

        resource_file = os.path.join(self.DBDIR, job.resource_name())
        utils.file_put_contents(resource_file, start)

        seconds = matrix.get("delay", 1)

        self.afterwards(job, "do_increment_testdelayphp_counter_v1",
                        eval(seconds))
        return Worker.WORKER_CONTINUE

    def do_delete_testdelayphp_counter_v1(self, job, resp):
        args = self.arguments()
        os.unlink(os.path.join(self.DBDIR, args[0]))
        return Worker.WORKER_SUCCESS

    def do_increment_testdelayphp_counter_v1(self, job, resp):
        resource_file = os.path.join(self.DBDIR, job.resource_name())
        newval = 1 + utils.file_get_contents(resource_file)
        utils.file_put_contents(resource_file, newval)
        matrix = job.matrix_arguments()
        start = matrix.get("start", 0)
        end = matrix.get("end", 10)

        resp.status().add_message("set to %s" % newval)
        if newval == end:
            return Worker.WORKER_SUCCESS
        else:
            resp.status().progress(resp.status().progress() + (end - start))

        matrix = job.matrix_arguments()
        seconds = matrix.get("delay", 1)

        if "retry" in matrix and matrix["retry"]:
            msg = "retry attempt number %s" % (resp.status().failures()+1)
            resp.status().add_message(msg)
            return Worker.WORKER_RETRY
        else:
            self.afterwards(job, eval(seconds))

        return Worker.WORKER_CONTINUE


if __name__ == "__main__":
    worker = WorkerTestDelayPhp(sys.argv[1])
    worker.run()
