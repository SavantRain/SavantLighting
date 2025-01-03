import asyncio
import logging
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

_LOGGER = logging.getLogger(__name__)

class TCPConnectionManager:
    """管理与设备的TCP连接"""
    def __init__(self, host, port, state_update_callback):
        self.host = host
        self.port = port
        self.hass = None
        self.reader = None
        self.writer = None
        self._is_connected = False
        # self.state_update_callback = state_update_callback  # 回调函数
        self.response_queue = asyncio.Queue()  # 用于缓存响应
        self.command_no = 0
        self._keep_alive_task = None  # 定时发送任务
        self._callbacks = {}

    def set_hass(self, hass):
        """设置 Home Assistant 的核心对象"""
        self.hass = hass
        
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
            
            if not self._keep_alive_task:
                self._keep_alive_task = asyncio.create_task(self._send_keep_alive())
            
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
                    response_str = bytes.fromhex(response.hex().strip())
                    response_dict = self._parse_response(response_str)
                    if response_dict['device_type'] in self._callbacks and response_dict['device']:
                        self._callbacks[response_dict['device_type']](response_dict)
                    else:
                        _LOGGER.warning(f"未识别的设备类型: {response_dict['device_type']}")
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

    async def _send_keep_alive(self):
        """定时发送 FF 字节保持心跳"""
        while self._is_connected:
            try:
                # 发送 FF 字节
                ff_bytes = b'\xFF'
                _LOGGER.info("发送心跳包: FF")
                await self.send_command(ff_bytes)
                await asyncio.sleep(60)  # 每 1 分钟发送一次
            except Exception as e:
                _LOGGER.error(f"发送心跳包失败: {e}")
                break
   
    async def get_response(self):
        """获取缓存中的响应,#暂时无调用"""
        try:
            response = await self.response_queue.get()
            return response
        except asyncio.QueueEmpty:
            return None

    def get_device_by_unique_id(self, device_type, unique_id):
        entity_registry = async_get_entity_registry(self.hass)
        entity_entry = None
        for entry in entity_registry.entities.values():
            if entry.unique_id == unique_id:
                entity_entry = entry
                break
        if entity_entry is None:
            _LOGGER.error(f"未找到 unique_id 为 {unique_id} 的设备")
            return None
        entity_id = entity_entry.entity_id
        
        device = self.hass.data[device_type].get_entity(entity_id)

        if device is None:
            _LOGGER.error(f"未找到 entity_id 为 {entity_id} 的设备实例")
            return None
        return device

    def register_callback(self, device_type, callback):
        """注册回调函数"""
        self._callbacks[device_type] = callback
        # self._callbacks.append(callback)
   
    def _parse_response(self, response_str):
        print(response_str)
        response_dict = {
            "response_str": response_str,
            "data1": response_str[8],
            "data2": response_str[9],
            "data3": response_str[10],
            "data4": response_str[11],
            "device_type":"",
            "sub_device_type":"",
            "module_address": response_str[4],
            "loop_address": response_str[5],
            "unique_id":"",
            "device":None
        }
        if response_dict["data2"] == 0x00 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x00:
            response_dict["device_type"] = "switch"

        elif response_dict["data3"] == 0x00 and response_dict["data4"] == 0x00:
            response_dict["device_type"] = "io08"

        elif response_dict["data4"] == 0x00:
            response_dict["device_type"] = "keypad"

        elif response_dict["data2"] == 0x00 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x11:
            response_dict["device_type"] = "light"
            response_dict["sub_device_type"] = "DALI-01"

        elif response_dict["data2"] == 0x00 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x12:
            response_dict["device_type"] = "light"
            response_dict["sub_device_type"] = "DALI-01"
            if response_dict["data4"] == 0x12:
                response_dict["loop_address"] = response_dict["loop_address"] - 1

        elif response_dict["data3"] == 0x00 and response_dict["data4"] == 0x15:
            response_dict["device_type"] = "light"
            response_dict["sub_device_type"] = "DALI-02"
        
        elif response_dict["data3"] == 0x00 and response_dict["data4"] == 0x00 and response_dict["data4"] == 0x10:
            response_dict["device_type"] = "light"
            response_dict["sub_device_type"] = "0603D"

        unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["device_type"]}"
        response_dict['device'] = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
        return response_dict
