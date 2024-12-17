import abc
import json
import logging
import pickle
import zlib
import struct

logger=logging.getLogger()

# 序列化类型
serialize_json = 0
serialize_pickle = 1
# 序列化器字典
_serializers = {}

def register_serializer(serialize_type:int):
    """
    定义一个装饰器，用于注册序列化器
    :param serialize_type: 序列化器类型
    :return:
    """
    def decorator(cls):
        if serialize_type in _serializers:
            raise KeyError('Serializer type already registered')
        _serializers[serialize_type] = cls()
        return cls
    return decorator

class Serializer(abc.ABC):
    """
    序列化器基类
    """
    @abc.abstractmethod
    def serialize(self, data):
        raise NotImplementedError

    @abc.abstractmethod
    def deserialize(self, data_bytes):
        raise NotImplementedError

class CommonJsonEncoder(json.JSONEncoder):
    @staticmethod
    def has_method(obj, name):
        return hasattr(obj, name) and callable(getattr(obj, name))
    def default(self, o):
        if self.has_method(o, 'to_dict'):
            return o.to_dict()
        if self.has_method(o, 'to_json'):
            return o.to_json()
        return str(o)

# 注册JSON序列化器
@register_serializer(serialize_json)
class JsonSerializer(Serializer):

    def serialize(self, data):
        return json.dumps(data, cls=CommonJsonEncoder).encode('utf-8')

    def deserialize(self, data_bytes):
        data = data_bytes.decode('utf-8')
        return json.loads(data)
# 注册Pickle序列化器
@register_serializer(serialize_pickle)
class PickleSerializer(Serializer):
    def serialize(self, data):
        return pickle.dumps(data)

    def deserialize(self, data_bytes):
        return pickle.loads(data_bytes)

class ProtocolCodec:
    """
    自定义协议编解码器：header + body
    _HEADER_FMT 4字节魔数 + body长度 + 序化类型 + 压缩标识
    _MAGIC_NUMBER 魔数
    """
    _HEADER_FMT = "!4s2i?"
    _HEADER_LEN = struct.calcsize(_HEADER_FMT)
    _MAGIC_NUMBER = b'\x1A\x2B\x3C\x4D'

    def __init__(self):
        self._buffer = bytearray()

    def decode(self, data):
        """
        解码给定的数据并将其添加到缓冲区中

        参数:
        data (bytes): 接收的字节数据

        返回:
        解码后的结果列表
        """
        self._buffer.extend(data)
        return self._decode_buffered()

    def _decode_buffered(self):
        results = []
        memory_view = memoryview(self._buffer)
        current_offset = 0
        while len(self._buffer) >= current_offset + self._HEADER_LEN:
            try:
                # 解码header
                magic, data_len, serial_type, compress = struct.unpack_from(self._HEADER_FMT,
                                                                       memory_view, current_offset)
                # 校验魔数
                if magic != self._MAGIC_NUMBER:
                    logger.error(f'Invalid magic number:{magic}, then skip it ...')
                    current_offset = self._find_next_header_index(current_offset)
                    continue
            except Exception as e:
                logger.error(f'Decode header error, try to find next header:{e}')
                current_offset = self._find_next_header_index(current_offset)
                continue
            body_start = current_offset + self._HEADER_LEN
            body_end = body_start + data_len
            if len(self._buffer) < body_end:
                break
            # 解码body
            body = memory_view[body_start:body_end]
            current_offset = body_end
            try:
                if compress:
                    body = zlib.decompress(body)
                serializer = _serializers[serial_type]
                results.append(serializer.deserialize(body))
            except Exception as e:
                logger.error(f'Decode body error, then skip:{e}')
        if current_offset > 0:
            self._buffer = self._buffer[current_offset:]
        memory_view.release()
        return results

    @staticmethod
    def encode(data, serialize_type=serialize_json, compress=True):
        """
        编码数据
        :param data: 要编码的数据
        :param serialize_type: 序列化类型
        :param compress: 是否压缩
        :return: 编码后的数据
        """
        serializer = _serializers[serialize_type]
        body = serializer.serialize(data)
        if compress:
            body = zlib.compress(body)
        data_len = len(body)
        header = struct.pack(ProtocolCodec._HEADER_FMT, ProtocolCodec._MAGIC_NUMBER, data_len, serialize_type, compress)
        return header + body

    def _find_next_header_index(self, current_offset):
        """
        查找下一个有效的header
        :return: 下一个有效的header的起始索引，如果没有找到，则返回buffer的长度
        """
        magic_len = len(self._MAGIC_NUMBER)
        buffer_len = len(self._buffer)
        if buffer_len > magic_len + current_offset :
            index = self._buffer.find(self._MAGIC_NUMBER, current_offset + 1)
            if index != -1:
                return index
            return buffer_len - magic_len + 1










