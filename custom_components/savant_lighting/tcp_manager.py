import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class TCPConnectionManager:
    """管理与设备的TCP连接"""
    def __init__(self, host, port, state_update_callback):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self._is_connected = False
        self.state_update_callback = state_update_callback  # 回调函数
        self.response_queue = asyncio.Queue()  # 用于缓存响应
        self.command_no = 0
        
    async def connect(self):
        """建立TCP连接"""
        if self._is_connected:
            _LOGGER.debug("连接已存在，复用现有连接")
            return True
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self._is_connected = True
            _LOGGER.info(f"成功连接到 {self.host}:{self.port}")
            # 启动后台任务来监听响应
            asyncio.create_task(self._listen_for_responses())
            return True
        except Exception as e:
            _LOGGER.error(f"连接到 {self.host}:{self.port} 失败: {e}")
            self._is_connected = False
            return False

    async def send_command(self, data):
        """通过TCP发送命令"""
        self.command_no = self.command_no + 1
        print(f"发送第{self.command_no}个命令:{str(data).replace('\\x', '')}")
        if not await self.check_connection():
            _LOGGER.warning("连接未建立，无法发送命令")
            return None, False
        try:
            self.writer.write(data)
            await self.writer.drain()
            return True, True
        except Exception as e:
            _LOGGER.error(f"发送命令时出错: {e}")
            self._is_connected = False  # 出错后标记为断开连接

    async def _listen_for_responses(self):
        """后台任务：监听响应并处理"""
        while self._is_connected:
            try:
                # 等待并读取响应，假设每次响应不超过 1024 字节
                response = await asyncio.wait_for(self.reader.read(1024), timeout=5)
                if response:
                    # 将收到的响应放入队列
                    self.response_queue.put_nowait(response)
                    self.state_update_callback(response)
                else:
                    _LOGGER.warning(f"连接到 {self.host}:{self.port} 关闭或断开")
                    self._is_connected = False  # 连接关闭时标记为断开
            except asyncio.TimeoutError:
                # 超时后继续尝试读取
                continue
            except Exception as e:
                _LOGGER.error(f"监听响应时出错: {e}")
                self._is_connected = False  # 出错后标记为断开连接
                break
            
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
    
    async def get_response(self):
        """获取缓存中的响应"""
        try:
            response = await self.response_queue.get()
            return response
        except asyncio.QueueEmpty:
            return None