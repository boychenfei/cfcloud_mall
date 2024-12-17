import copy
import signal
import threading
import asyncio
import queue
from multiprocessing.process import current_process

from cfcloud_mall.libs.concurrent import ThreadSafeDict
import pynng
import logging
import logging.config
import logging.handlers
from cfcloud_mall.libs.loglib.protocol import ProtocolCodec
import atexit




def _get_logger():
    """
    Get the logger instance
    :return: 
    """
    pynng_logger = logging.getLogger("pynng-logging")
    pynng_logger.propagate = False
    pynng_logger.level = logging.INFO
    if not pynng_logger.handlers:
        pynng_logger.addHandler(logging.StreamHandler())
    return pynng_logger

logger = _get_logger()


_TCP_ADDR_FMT = "tcp://{}:{}"


_HANDLER_HOLDER = ThreadSafeDict()
_LISTENER_HOLDER = ThreadSafeDict()
_PROXY_HOLDER = ThreadSafeDict()

class PynngLoggingHandler(logging.Handler):
    """
    PynngLoggingHandler 是一个自定义的日志处理类，继承自 logging.Handler。
    它通过网络发送日志消息到指定的地址。该处理器旨在与 asyncio 事件循环一起工作，
    以便非阻塞地发送日志消息。
    
    属性:
    - SENTINEL: 一个用于标记队列结束的特殊对象。
    """
    
    SENTINEL = object()

    def __new__(cls, *args, **kwargs):
        """
        重写 __new__ 方法以防止直接实例化。使用 get_instance 方法获取实例。
        
        参数:
        - *args, **kwargs: 传递给构造函数的参数。
        
        异常:
        - NotImplementedError: 如果尝试直接实例化，抛出此异常。
        """
        raise NotImplementedError("Cannot instantiate directly. Use get_instance() instead.")

    def __init__(self, host:str, port:int):
        """
        初始化 PynngLoggingHandler 实例。
        
        参数:
        - host: 日志服务器的主机名。
        - port: 日志服务器的端口号。
        """
        super().__init__()
        self._status_lock = threading.Lock()
        self._address = _TCP_ADDR_FMT.format(host, port)
        self._queue = queue.Queue(-1)
        self._thread = threading.Thread(target=self._log_event_loop, name='log-event-loop', daemon=True)
        self._thread.start()
        self._running = True

    @classmethod
    def get_instance(cls, host, port):
        """
        获取 PynngLoggingHandler 的单例实例。
        
        参数:
        - host: 日志服务器的主机名。
        - port: 日志服务器的端口号。
        
        返回:
        - PynngLoggingHandler 的实例。
        """
        address = _TCP_ADDR_FMT.format(host, port)
        def create_instance():
            new_instance = logging.Handler.__new__(cls)
            new_instance.__init__(host, port)
            return new_instance
        return _HANDLER_HOLDER.compute_if_absent(address, create_instance)

    def _log_event_loop(self):
        """
        日志事件循环，用于异步发送日志消息。
        """
        logger.info(f"=============================Log event loop for pid =[{current_process().pid}]=============================")
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._send_logs())
        finally:
            if loop:
                loop.stop()
                loop.close()

    async def _send_logs(self):
        """
        异步发送日志消息到指定地址。
        """
        with pynng.Pub0(dial=self._address, send_timeout=500) as socket:
            while self._running:
                try:
                    msg = self._queue.get()
                    self._queue.task_done()
                    if msg == self.SENTINEL:
                        return
                    encoded = ProtocolCodec.encode(msg)
                    await socket.asend(encoded)
                except Exception:
                    logger.exception("Error in send logs", exc_info=True)

    def prepare(self, record:logging.LogRecord):
        """
        准备 LogRecord，以便序列化。
        
        参数:
        - record: 要准备的日志记录。
        
        返回:
        - 准备好的日志记录。
        """
        msg = self.format(record)
        record = copy.copy(record)
        record.message = msg
        record.msg = msg
        record.args = None
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return record

    def emit(self, record):
        """
        发送日志记录到队列中以供异步发送。
        
        参数:
        - record: 要发送的日志记录。
        """
        try:
            rd = self.prepare(record)
            rdict = dict(rd.__dict__)
            self._queue.put_nowait(rdict)
        except Exception:
            logger.exception("Error in logging handler", exc_info=True)
            self.handleError(record)

    def start(self):
        """
        启动日志处理器。如果处理器已经在运行，则不执行任何操作。
        """
        if self._running:
            return
        self._status_lock.acquire()
        try:
            self._running = True
            self._thread.start()
        finally:
            self._status_lock.release()

    def stop(self):
        """
        停止日志处理器。如果处理器已经停止，则不执行任何操作。
        """
        if not self._running:
            return
        self._status_lock.acquire()
        self._running = False
        logger.info("**********************Stopping pynng logging handler=[{}] for pid={}**********************".format(self._address, current_process().pid))
        try:
            self._queue.put_nowait(self.SENTINEL)
            self._queue.join()
            if self._thread and self._thread.is_alive():
                self._thread.join()
        finally:
            self._status_lock.release()
        logger.info("**********************Stopped pynng logging handler=[{}] for pid={}**********************".format(self._address, current_process().pid))


class PynngLoggingListener:
    """
    该类用于监听和处理通过pynng传输的日志信息。
    它通过TCP协议接收日志信息，并将其分发到相应的处理程序。
    """

    def __new__(cls, *args, **kwargs):
        """
        禁止直接实例化该类。
        请使用get_instance()方法获取实例。
        """
        raise NotImplementedError("Cannot instantiate directly. Use get_instance() instead.")

    def __init__(self, host: str, port: int):
        """
        初始化PynngLoggingListener实例。

        参数:
        - host: 监听的主机地址。
        - port: 监听的端口。

        初始化内容包括:
        - 线程锁，用于同步操作。
        - 地址，按照指定格式组合host和port。
        - 运行状态标志。
        - 用于存储日志消息的队列。
        - 后台线程，用于接收日志消息。
        """
        self._lock = threading.Lock()
        self._address = _TCP_ADDR_FMT.format(host, port)
        self._running = False
        self._queue = asyncio.Queue(-1)
        self._thread = threading.Thread(target=self._recv_event_loop, daemon=True, name="pynng-logging")

    @classmethod
    def get_instance(cls, host, port):
        """
        获取PynngLoggingListener的实例。
        如果不存在，则创建一个新的实例。

        参数:
        - host: 监听的主机地址。
        - port: 监听的端口。

        返回:
        - PynngLoggingListener的实例。
        """
        address = _TCP_ADDR_FMT.format(host, port)

        def create_instance():
            new_instance = object.__new__(cls)
            new_instance.__init__(host, port)
            return new_instance

        return _LISTENER_HOLDER.compute_if_absent(address, create_instance)

    def start(self):
        """
        启动日志监听器。
        如果监听器已经在运行，则不执行任何操作。
        """
        if self._running:
            return
        with self._lock:
            self._running = True
            self._thread.start()

    def stop(self):
        """
        停止日志监听器。
        如果监听器已经停止，则不执行任何操作。
        """
        if not self._running:
            return
        with self._lock:
            logger.info("**********************Stopping pynng logging listener[{}] for pid={}**********************".format(self._address, current_process().pid))
            self._running = False
            if hasattr(self, "_thread") and self._thread.is_alive():
                self._thread.join()
        logger.info("**********************Stopped pynng logging listener[{}] for pid={}**********************".format(self._address, current_process().pid))

    @staticmethod
    def _handle(record):
        """
        处理接收到的日志记录。

        参数:
        - record: 日志记录，应包含proxy2pynng_id。

        该方法将日志记录分配给相应的代理处理程序。
        如果记录中没有proxy2pynng_id，则抛出运行时错误。
        """
        try:
            record = logging.makeLogRecord(record)
            if hasattr(record, "proxy2pynng_id"):
                proxy_id = record.proxy2pynng_id
                proxy_handlers = _PROXY_HOLDER.get(proxy_id)
                for handler in proxy_handlers:
                    if record.levelno >= handler.level:
                        handler.handle(record)
            else:
                raise RuntimeError("No proxy id found in record")
        except Exception:
            logger.exception("Error in logging handler", exc_info=True)

    def _recv_event_loop(self):
        """
        接收日志消息的事件循环。
        该方法在单独的线程中运行，负责接收和处理日志消息。
        """
        logger.info(f"=============================Recv event loop for pid =[{current_process().pid}]=============================")
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._listener())

        finally:
            if loop:
                loop.stop()
                loop.close()

    async def _listener(self):
        """
        异步监听方法，包含两个任务:
        - 接收日志消息。
        - 处理日志消息。
        """
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._recv_logs())
            tg.create_task(self._process_logs())

    async def _recv_logs(self):
        """
        接收日志消息的任务。
        该任务监听指定地址的日志消息，并将其放入队列中。
        """
        with pynng.Sub0(listen=self._address, recv_timeout=200, topics="") as server_socket:
            while self._running:
                try:
                    msg = await server_socket.arecv()
                    if msg:
                        await self._queue.put(msg)
                except pynng.Timeout:
                    pass
                except Exception as e:
                    logger.exception(f"pynng-logging handle error:{e}")

    async def _process_logs(self):
        """
        处理日志消息的任务。
        该任务从队列中获取日志消息，并将其分发到相应的处理程序。
        """
        codec = ProtocolCodec()
        while self._running:
            try:
                msg = await asyncio.wait_for(self._queue.get(), timeout=0.5)
                try:
                    data_list = codec.decode(msg)
                    for data in data_list:
                        self._handle(data)
                finally:
                    self._queue.task_done()
            except asyncio.TimeoutError:
                pass
            except Exception:
                logger.exception("Error in process logs", exc_info=True)


class Logging2PynngProxyHandler(logging.Handler):
    """
    一个日志处理类，用于将日志从一个应用代理到另一个应用。
    
    参数:
    - proxy_id: 代理的唯一标识符。
    - level: 日志级别，默认为DEBUG。
    - host: 目标主机地址，默认为本地地址。
    - port: 目标主机端口，默认为23888。
    - handlers: 初始时要设置的处理器列表。
    """
    def __init__(self, proxy_id, level=logging.DEBUG,  host='127.0.0.1', port=23888, handlers = None):
        super().__init__(level)
        self._proxy_id = proxy_id
        self._proxy_handler = PynngLoggingHandler.get_instance(host, port)
        if handlers:
            _PROXY_HOLDER.setdefault(proxy_id, list(handlers))

    @classmethod
    def get_proxy(cls, proxy_id, listen_handler_names=None, level=logging.DEBUG, host='127.0.0.1', port=23888):
        """
        获取一个代理实例。
        
        参数:
        - proxy_id: 代理的唯一标识符。
        - listen_handler_names: 要监听的处理器名称列表。
        - level: 日志级别，默认为DEBUG。
        - host: 目标主机地址，默认为本地地址。
        - port: 目标主机端口，默认为23888。
        
        返回:
        一个Logging2PynngProxyHandler实例。
        """
        if listen_handler_names:
            name_set = frozenset(listen_handler_names)
            handlers = []
            for handler_name in name_set:
                handler = logging.getHandlerByName(handler_name)
                if not handler:
                    raise ValueError("handler name [{}] not found".format(handler_name))
                handlers.append(handler)
            return cls(proxy_id,level,host, port, handlers)
        return cls(proxy_id,level,host, port)

    def handle(self, record):
        """
        处理日志记录，将其代理到pynng处理器。
        
        参数:
        - record: 要处理的日志记录。
        """
        try:
            # 代理发送至 pynng
            record.proxy2pynng_id = self._proxy_id
            self._proxy_handler.handle(record)
        except Exception:
            logger.exception("Error in logging handler", exc_info=True)

    def flush(self):
        """
        刷新所有关联的处理器。
        """
        for handler in _PROXY_HOLDER.get(self._proxy_id, []):
            handler.flush()
            
    def close(self):
        """
        关闭所有关联的处理器。
        """
        for handler in _PROXY_HOLDER.get(self._proxy_id, []):
            handler.close()

def start_pynng_logging_listener(host='127.0.0.1', port=23888):
    """
    启动一个pynng日志监听器。
    
    参数:
    - host: 监听器主机地址，默认为本地地址。
    - port: 监听器端口，默认为23888。
    
    返回:
    一个PynngLoggingListener实例。
    """
    listener = PynngLoggingListener.get_instance(host, port)
    listener.start()
    return listener

def cleanup():
    """
    清理所有存在的处理器和监听器。
    """
    for exists_handler in _HANDLER_HOLDER.values():
        exists_handler.stop()
    for exists_listener in _LISTENER_HOLDER.values():
        exists_listener.stop()

def signal_cleanup(signum, frame):
    """
    当接收到特定信号时进行清理。
    
    参数:
    - signum: 信号编号。
    - frame: 当前的帧对象。
    """
    cleanup()

# 注册清理函数，以确保程序退出时进行清理
atexit.register(cleanup)
# 注册信号处理函数，以确保接收到中断或终止信号时进行清理
signal.signal(signal.SIGINT, signal_cleanup)
signal.signal(signal.SIGTERM, signal_cleanup)
























