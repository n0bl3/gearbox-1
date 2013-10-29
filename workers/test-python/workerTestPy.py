import sys

import gearbox
from gearbox import Job
from gearbox import Status
from gearbox import Worker


class PyWorker(Worker):
    def __init__(self, config):
        super(PyWorker, self).__init__(config)
        self.register_handler("do_get_testpy_example_v1")
        self.register_handler("do_post_testpy_example_v1")

    def do_post_testpy_example_v1(self, job, resp):
        status = Status(resp.status())
        status.add_message("self is a status message!")
        raise gearbox.ERR_INTERNAL_SERVER_ERROR("uh oh")
        return Worker.WORKER_SUCCESS

    def do_get_testpy_example_v1(self, job, resp):
        print "content:", job.content()
        print "serialize:", job.serialize()
        i = 0
        for arg in job.arguments():
            print "Arg", i, ":", arg
            i += 1

        for key, value in job.matrix_arguments().items():
            print "Matrix Arg:", key, "=>", value

        for key, value in job.query_params().items():
            print "Query Param:", key, "=>", value

        for key, value in job.headers().items():
            print "Header:", key, "=>", value

        for key, value in job.environ().items():
            print "ENV:", key, "=>", value

        print "status:", job.status()
        print "name:", job.name()
        print "base_uri:", job.base_uri()

        job_types = {Job.JOB_UNKNOWN: "UNKNOWN",
                     Job.JOB_ASYNC: "ASYNC",
                     Job.JOB_SYNC: "SYNC"}

        print "type:", job_types[job.type()]

        print "api_version:", job.api_version()
        print "operation:", job.operation()
        print "component:", job.component()
        print "resource_type:", job.resource_type()
        print "resource_name:", job.resource_name()
        print "resource_uri:", job.resource_uri()
        print "remote_ip:", job.remote_ip()
        print "remote_user:", job.remote_user()
        print "timeout:", job.timeout()

        print "resp code:", resp.code()

        status = resp.status()
        status.add_message("self is a status message!")
        print "status name:", status.name()
        print "status resource_uri:", status.resource_uri()
        print "status operation:", status.operation()

        resp.content('{"hello": "world"}')
        print "Done"
        return Worker.WORKER_SUCCESS


if __name__ == "__main__":
    worker = PyWorker(sys.argv[1])
    worker.run()
