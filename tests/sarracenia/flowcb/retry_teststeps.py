import pytest
from pytest_steps import test_steps
from unittest.mock import patch

import os, types

#useful for debugging tests
#import pprint
#pretty = pprint.PrettyPrinter(indent=2, width=200).pprint

#from sarracenia.flowcb import FlowCB
from sarracenia.flowcb.retry import Retry

import fakeredis

class Options:
    retry_driver = 'disk'
    redisqueue_serverurl = ''
    no = 1
    retry_ttl = 0
    batch = 8
    logLevel = "DEBUG"
    queueName = "TEST_QUEUE_NAME"
    component = "sarra"
    config = "foobar.conf"
    pid_filename = "NotARealPath"
    housekeeping = float(0)
    def add_option(self, option, type, default = None):
        if not hasattr(self, option):
            setattr(self, option, default)



WorkList = types.SimpleNamespace()
WorkList.ok = []
WorkList.incoming = []
WorkList.rejected = []
WorkList.failed = []
WorkList.directories_ok = []

message = {
    "pubTime": "20180118151049.356378078",
    "topic": "v02.post.sent_by_tsource2send",
    "headers": {
        "atime": "20180118151049.356378078", 
        "from_cluster": "localhost",
        "mode": "644",
        "mtime": "20180118151048",
        "parts": "1,69,1,0,0",
        "source": "tsource",
        "sum": "d,c35f14e247931c3185d5dc69c5cd543e",
        "to_clusters": "localhost"
    },
    "baseUrl": "https://NotARealURL",
    "relPath": "ThisIsAPath/To/A/File.txt",
    "notice": "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"
}

@pytest.mark.bug("DiskQueue.py doesn't cleanup properly")
@test_steps('disk', 'redis')
def test_cleanup(test_step, tmp_path):
    # Execute the step according to name
    if test_step == 'disk':
        cleanup__disk(tmp_path)
    elif test_step == 'redis':
        cleanup__redis()

def cleanup__disk(tmp_path):
    BaseOptions = Options()
    # -- DiskQueue
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    retry.download_retry.put([message, message, message])
    retry.post_retry.put([message, message, message])

    assert len(retry.download_retry) == 3
    assert len(retry.post_retry) == 3

    retry.cleanup()

    #These should both return 0, but with the current DiskQueue, cleanup doesn't work properly.
    assert len(retry.download_retry) == 0
    assert len(retry.post_retry) == 0

def cleanup__redis():
    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_cleanup"
        retry = Retry(BaseOptions)

        retry.download_retry.put([message, message, message])
        retry.post_retry.put([message, message, message])

        #assert os.path.exists(retry.download_retry.queue_file) == True
        assert len(retry.download_retry) == 3
        assert len(retry.post_retry) == 3

        retry.cleanup()

        assert len(retry.download_retry) == 0
        assert len(retry.post_retry) == 0


@test_steps('disk', 'redis')
def test_metricsReport(test_step, tmp_path):
    # Execute the step according to name
    if test_step == 'disk':
        metricsReport__disk(tmp_path)
    elif test_step == 'redis':
        metricsReport__redis()

def metricsReport__disk(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    retry.download_retry.put([message, message, message])
    retry.post_retry.put([message, message, message])

    metrics = retry.metricsReport()

    assert metrics['msgs_in_download_retry'] == 3
    assert metrics['msgs_in_post_retry'] == 3

def metricsReport__redis():
    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_metricsReport"
        retry = Retry(BaseOptions)

        retry.download_retry.put([message, message, message])
        retry.post_retry.put([message, message, message])

        metrics = retry.metricsReport()

        assert metrics['msgs_in_download_retry'] == 3
        assert metrics['msgs_in_post_retry'] == 3


@test_steps('disk', 'redis')
def test_after_post(test_step, tmp_path):
    # Execute the step according to name
    if test_step == 'disk':
        after_post__disk(tmp_path)
    elif test_step == 'redis':
        after_post__redis()

def after_post__disk(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_post_worklist = WorkList
    after_post_worklist.failed = [message, message, message]

    retry.after_post(after_post_worklist)

    assert len(retry.post_retry) == 3

def after_post__redis():
    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_post"
        retry = Retry(BaseOptions)

        after_post_worklist = WorkList
        after_post_worklist.failed = [message, message, message]

        retry.after_post(after_post_worklist)

        assert len(retry.post_retry) == 3


@test_steps('disk', 'redis')
def test_after_work__WLFailed(test_step, tmp_path):
    # Execute the step according to name
    if test_step == 'disk':
        after_work__WLFailed__disk(tmp_path)
    elif test_step == 'redis':
        after_work__WLFailed__redis()

def after_work__WLFailed__disk(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_work_worklist = WorkList
    after_work_worklist.failed = [message, message, message]

    retry.after_work(after_work_worklist)

    assert len(retry.download_retry) == 3
    assert len(after_work_worklist.failed) == 0

def after_work__WLFailed__redis():
    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_work__WLFailed"
        retry = Retry(BaseOptions)

        after_work_worklist = WorkList
        after_work_worklist.failed = [message, message, message]

        retry.after_work(after_work_worklist)

        assert len(retry.download_retry) == 3
        assert len(after_work_worklist.failed) == 0



@test_steps('disk', 'redis')
def test_after_work__SmallQty(test_step, tmp_path):
    # Execute the step according to name
    if test_step == 'disk':
        after_work__SmallQty__disk(tmp_path)
    elif test_step == 'redis':
        after_work__SmallQty__redis()

def after_work__SmallQty__disk(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.batch = 2
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_work_worklist = WorkList
    after_work_worklist.ok = [message, message, message]

    retry.after_work(after_work_worklist)

    assert len(retry.download_retry) == 0
    assert len(after_work_worklist.ok) == 3

def after_work__SmallQty__redis():
    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.batch = 2
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_work__SmallQty"
        retry = Retry(BaseOptions)

        after_work_worklist = WorkList
        after_work_worklist.ok = [message, message, message]

        retry.after_work(after_work_worklist)

        assert len(retry.download_retry) == 0
        assert len(after_work_worklist.ok) == 3


@test_steps('disk', 'redis')
def test_after_work(test_step, tmp_path):
    # Execute the step according to name
    if test_step == 'disk':
        after_work__disk(tmp_path)
    elif test_step == 'redis':
        after_work__redis()

def after_work__disk(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_work_worklist = WorkList
    after_work_worklist.ok = [message, message, message]
    retry.post_retry.put([message, message, message])
    retry.on_housekeeping()

    retry.after_work(after_work_worklist)

    assert len(retry.download_retry) == 0
    assert len(after_work_worklist.ok) == 4

def after_work__redis():
    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_work"
        retry = Retry(BaseOptions)

        after_work_worklist = WorkList
        after_work_worklist.ok = [message, message, message]
        retry.post_retry.put([message, message, message])
        retry.on_housekeeping()

        retry.after_work(after_work_worklist)

        assert len(retry.download_retry) == 0
        assert len(after_work_worklist.ok) == 4


@test_steps('disk', 'redis')
def test_after_accept__SmallQty(test_step, tmp_path):
    # Execute the step according to name
    if test_step == 'disk':
        after_accept__SmallQty__disk(tmp_path)
    elif test_step == 'redis':
        after_accept__SmallQty__redis()

def after_accept__SmallQty__disk(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.batch = 2
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_accept_worklist = WorkList
    after_accept_worklist.incoming = [message, message, message]

    retry.after_accept(after_accept_worklist)

    assert len(retry.download_retry) == 0
    assert len(after_accept_worklist.incoming) == 3

def after_accept__SmallQty__redis():
    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.batch = 2
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_accept__SmallQty"
        retry = Retry(BaseOptions)

        after_accept_worklist = WorkList
        after_accept_worklist.incoming = [message, message, message]

        retry.after_accept(after_accept_worklist)

        assert len(retry.download_retry) == 0
        assert len(after_accept_worklist.incoming) == 3
        yield


@test_steps('disk', 'redis')
def test_after_accept(test_step, tmp_path):
    # Execute the step according to name
    if test_step == 'disk':
        after_accept__disk(tmp_path)
    elif test_step == 'redis':
        after_accept__redis()

def after_accept__disk(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    retry.download_retry.put([message, message, message])
    retry.on_housekeeping()

    after_accept_worklist = WorkList
    after_accept_worklist.incoming = [message, message, message]

    retry.after_accept(after_accept_worklist)

    assert len(retry.download_retry) == 0
    assert len(after_accept_worklist.incoming) == 4

def after_accept__redis():
    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_accept"
        retry = Retry(BaseOptions)

        after_accept_worklist = WorkList
        after_accept_worklist.incoming = [message, message, message]
        retry.download_retry.put([message, message, message])
        retry.on_housekeeping()

        retry.after_accept(after_accept_worklist)

        assert len(retry.download_retry) == 0
        assert len(after_accept_worklist.incoming) == 4


@test_steps('disk', 'redis')
def test_on_housekeeping(test_step, tmp_path, caplog):
    # Execute the step according to name
    if test_step == 'disk':
        on_housekeeping__disk(tmp_path, caplog)
    elif test_step == 'redis':
        on_housekeeping__redis(caplog)

def on_housekeeping__disk(tmp_path, caplog):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    retry.download_retry.put([message, message, message])
    retry.post_retry.put([message, message, message])

    assert len(retry.download_retry) == 3
    assert len(retry.post_retry) == 3

    retry.on_housekeeping()

    log_found_hk_elapse = False
    for record in caplog.records:
        if "on_housekeeping elapse" in record.message:
            log_found_hk_elapse = True

    assert log_found_hk_elapse == True

def on_housekeeping__redis(caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_on_housekeeping"
        retry = Retry(BaseOptions)

        #server_test_on_housekeeping = fakeredis.FakeServer()
        #retry.download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_on_housekeeping)
        #retry.post_retry.redis = fakeredis.FakeStrictRedis(server=server_test_on_housekeeping)

        retry.download_retry.put([message, message, message])
        retry.post_retry.put([message, message, message])

        assert len(retry.download_retry) == 3
        assert len(retry.post_retry) == 3

        retry.on_housekeeping()

        log_found_hk_elapse = False
        for record in caplog.records:
            if "on_housekeeping elapse" in record.message:
                log_found_hk_elapse = True

        assert log_found_hk_elapse == True
