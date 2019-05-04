# -*- coding:utf-8 -*-

import time
import threading
import Queue

from const import ThreadParameter

'''
    线程池类
'''
class ThreadPool(object):
    def __init__(self, thread_num):
        self.thread_num = thread_num
        self.work_queue = Queue.Queue()
        self.threads = []

    # 向线程池中添加任务
    def add_job(self, func, time_seq, **kwargs):
        self.work_queue.put((func, time_seq, kwargs))

    # 开始
    def start(self):
        for i in xrange(self.thread_num):
            self.threads.append(Thread(self.work_queue))
        self.wait_all_complete()

    # 等待全部线程执行完毕
    def wait_all_complete(self):
        for item in self.threads:
            if item.isActive():
                item.join()

'''
    线程类
'''
class Thread(threading.Thread):
    def __init__(self, work_queue):
        super(Thread,self).__init__()
        self.work_queue = work_queue
        self.start()

    def run(self):
        st = time.time()
        while(True):
            try:
                func, time_seq, kwargs = self.work_queue.get(block=False)
                now = time.time()
                while now - st < time_seq:
                    time.sleep(ThreadParameter.thread_sleep_time)
                    now = time.time()
                func(kwargs)
                self.work_queue.task_done()
            except:
                break



