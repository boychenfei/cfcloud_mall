import logging
import time
import multiprocessing
from multiprocessing import current_process
from cfcloud_mall.libs.loglib import handler
import logging.handlers
import logging.config



def print_logs(add_handler=False):

    target = logging.StreamHandler()
    target.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "{asctime} [{levelname}] [{name}] [{module}.{funcName}:{lineno:d}] {process:d} {thread:d} {message}", style='{')
    target.setFormatter(formatter)
    proxy_handler = None
    if add_handler:
        file_handler = logging.handlers.TimedRotatingFileHandler('D:\\applog\\test_handler.log', when='S', interval=5,
                                                                 backupCount=2)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        proxy_handler = handler.Logging2PynngProxyHandler(proxy_id="test_handler", handlers=(target, file_handler))
    else:
        proxy_handler = handler.Logging2PynngProxyHandler(proxy_id="test_handler")

    root_logger = logging.getLogger()
    root_logger.addHandler(proxy_handler)
    root_logger.setLevel(logging.DEBUG)
    for i in range(100):
        root_logger.info(f"hello world, 当前循环次数为: {i}")
        time.sleep(0.02)



if __name__ == '__main__':
    processes = []
    listener = handler.start_pynng_logging_listener()
    for _ in range(2):
        p = multiprocessing.Process(target=print_logs)
        processes.append(p)
        p.start()
    print_logs(True)
    for p in processes:
        p.join()
    print("all done=================")




