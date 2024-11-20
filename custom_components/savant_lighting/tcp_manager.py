import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class TCPConnectionManager:
    """管理与设备的TCP连接"""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self._is_connected = False

    async def connect(self):
        """建立TCP连接"""
        if self._is_connected:
            _LOGGER.debug("连接已存在，复用现有连接")
            return True
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self._is_connected = True
            _LOGGER.info(f"成功连接到 {self.host}:{self.port}")
            return True
        except Exception as e:
            _LOGGER.error(f"连接到 {self.host}:{self.port} 失败: {e}")
            self._is_connected = False
            return False

    async def send_command(self, data):
        """通过TCP发送命令"""
        if not await self.check_connection():
            print("The connect is not connected.")
            if not await self.connect():
                return None, False  # 连接失败，返回离线状态

        try:
            self.writer.write(data)
            await self.writer.drain()

            # 读取响应
            response = await asyncio.wait_for(self.reader.read(1024), timeout=5)
            return response, True
        except asyncio.TimeoutError:
            _LOGGER.error(f"发送命令到 {self.host}:{self.port} 超时")
            self._is_connected = False  # 超时后标记为断开连接
            return None, False
        except Exception as e:
            _LOGGER.error(f"发送命令到 {self.host}:{self.port} 时出错: {e}")
            self._is_connected = False  # 出错后标记为断开连接
            return None, False

    async def close(self):
        """关闭TCP连接"""
        if self.writer and not self.writer.is_closing():
            self.writer.close()
            await self.writer.wait_closed()
            _LOGGER.info(f"连接到 {self.host}:{self.port} 已关闭")
        self._is_connected = False


    async def check_connection(self):
        """检查连接是否有效"""
        if self.writer is None or self.writer.is_closing():
            self._is_connected = False
            _LOGGER.warning(f"连接到 {self.host}:{self.port} 无效，需要重新建立连接")
            return False
        return True