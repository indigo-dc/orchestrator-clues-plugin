import unittest
import os
import mock
import condor
from clueslib.node import NodeInfo
from clueslib.request import Request
from mock import MagicMock, Mock, patch, call
import htcondor
import classad


def open_file(file_name):
    tests_path = os.path.dirname(os.path.abspath(__file__))
    abs_file_path = os.path.join(tests_path, file_name)
    return open(abs_file_path, 'r')


def get_jobs_scheduled_attributes(maxrange):
    list_jobs_scheduled_attr = []
    # gather scheduled jobs from respective file job$n.txt
    # files are generated by generate_job_sched.py
    for i in range(0, maxrange):
        filename = 'test-files/job' + str(i) + '.txt'
        tmpfile_1line = open_file(filename)
        tmpobj = classad.parse(tmpfile_1line)
        list_jobs_scheduled_attr.append(tmpobj)
        tmpfile_1line.close()
    return list_jobs_scheduled_attr


def get_schedulers(filename):
    list_schedulers = []
    tmpfile_1sched = open_file(filename)
    sched = classad.parse(tmpfile_1sched)
    list_schedulers.append(sched)
    tmpfile_1sched.close()
    return list_schedulers


def get_worker_nodes(filename):
    worker_nodes = []
    tmpfile_wn = open_file(filename)
    wn = classad.parse(tmpfile_wn)
    worker_nodes.append(wn)
    tmpfile_wn.close()
    return worker_nodes


class TestCondorPlugin(unittest.TestCase):

    print '\n'
    print "==============================================================="
    print "---------- starting test ----class TestCondorPlugin------------"
    print "==============================================================="
    print '\n'

    def test_run_command(self):
        assert condor.run_command("echo test".split(" ")) == 'test\n'

    @mock.patch('subprocess.Popen.communicate')
    def test_run_command_subprocess_error(self, mock_subprocess):
        mock_subprocess.return_value = ('test', 'error')
        with self.assertRaises(Exception):
            condor.run_command("echo test".split(" "))

    # Condor job states: 1-Idle, 2-Running, 3-Removed, 4-Completed, 5-Held, 6-Transferring Output, 7-Suspended
    # CLUES2 job states: ATTENDED o PENDING

    def test_infer_chronos_state_idle(self):
        assert condor.infer_clues_job_state(1) == Request.PENDING

    def test_infer_chronos_state_running(self):
        assert condor.infer_clues_job_state(2) == Request.ATTENDED

    def test_infer_chronos_state_removed(self):
        assert condor.infer_clues_job_state(3) == Request.ATTENDED

    def test_infer_chronos_state_completed(self):
        assert condor.infer_clues_job_state(4) == Request.ATTENDED

    def test_infer_chronos_state_held(self):
        assert condor.infer_clues_job_state(5) == Request.ATTENDED

    def test_infer_chronos_state_transferout(self):
        assert condor.infer_clues_job_state(6) == Request.ATTENDED

    def test_infer_chronos_state_suspended(self):
        assert condor.infer_clues_job_state(7) == Request.ATTENDED

    def test_init_lrms_empty(self):
        lrms = condor.lrms()
        assert lrms._server_ip == 'htcondoreserver'

    def test_init_lrms(self):
        lrms = condor.lrms('test_ip')
        assert lrms._server_ip == 'test_ip'

    @mock.patch('htcondor.Schedd.query')
    @mock.patch('htcondor.Collector.locateAll')
    def test_get_jobinfolist(self, locateAll, query):
        print '   Now testing with --> test_get_jobinfolist'
        test_numjobs = 2
        locateAll.return_value = get_schedulers('test-files/schedulers.txt')
        query.return_value = get_jobs_scheduled_attributes(test_numjobs)
        job_info_list = condor.lrms(MagicMock(condor.lrms)).get_jobinfolist()
        lenj = len(job_info_list)
        assert lenj == test_numjobs

    @mock.patch('htcondor.Schedd.query')
    @mock.patch('condor.get_schedulers_list_from_Schedd')
    @mock.patch('condor.get_worker_nodes_list_from_Startd')
    def test_get_nodeinfolist(self, get_worker_nodes_list, get_schedulers_list, query):
        print '   Now testing with --> test_get_nodeinfolist'
        get_worker_nodes_list.return_value = get_worker_nodes(
            'test-files/workernodes.txt')
        get_schedulers_list.return_value = get_schedulers(
            'test-files/schedulers.txt')
        query.return_value = get_jobs_scheduled_attributes(2)

        node_info_list = condor.lrms(MagicMock(condor.lrms)).get_nodeinfolist()
        if node_info_list:
            result = '[NODE "wn1.condor.vagrant"] state: used, 1/1 (free slots), 457/457 (mem)'
            assert str(node_info_list['wn1.condor.vagrant']) == result
        else:
            print 'No node_info_list'


if __name__ == '__main__':
    unittest.main()
