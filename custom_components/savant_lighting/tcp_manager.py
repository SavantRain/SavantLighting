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

    async def send_command_list(self, data_list):
        if not await self.check_connection():
            _LOGGER.warning("连接未建立，无法发送命令")
            return None, False
        """通过TCP发送命令"""
        for data in data_list:
            self.command_no = self.command_no + 1
            print(f"发送第{self.command_no}个命令:{str(data).replace('\\x', '')}")
            try:
                self.writer.write(data)
                await self.writer.drain()
            except Exception as e:
                _LOGGER.error(f"发送命令时出错: {e}")
                self._is_connected = False  # 出错后标记为断开连接
        return True, True
    
    
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
        hvac_off = [0x01, 0x0A, 0x13, 0x1C, 0x25, 0x2E, 0x37, 0x40, 0x49, 0x52, 0x5B, 0x64, 0x6D, 0x76, 0x7F, 0x88]
        hvac_mode = [0x02, 0x0B, 0x14, 0x1D, 0x26, 0x2F, 0x38, 0x41, 0x4A, 0x53, 0x5C, 0x65, 0x6E, 0x77, 0x80, 0x89]
        hvac_fan = [0x03, 0x0C, 0x15, 0x1E, 0x27, 0x30, 0x39, 0x42, 0x4B, 0x54, 0x5D, 0x66, 0x6F, 0x78, 0x81, 0x8A]
        hvac_current_set_point = [0x04, 0x0D, 0x16, 0x1F, 0x28, 0x31, 0x3A, 0x43, 0x4C, 0x55, 0x5E, 0x67, 0x70, 0x79, 0x82, 0x8B]
        hvac_5 = [0x05, 0x0E, 0x17, 0x20, 0x29, 0x32, 0x3B, 0x44, 0x4D, 0x56, 0x5F, 0x68, 0x71, 0x7A, 0x83, 0x8C]
        hvac_6 = [0x06, 0x0F, 0x18, 0x21, 0x2A, 0x33, 0x3C, 0x45, 0x4E, 0x57, 0x60, 0x69, 0x72, 0x7B, 0x84, 0x8D]
        hvac_7 = [0x07, 0x10, 0x19, 0x22, 0x2B, 0x34, 0x3D, 0x46, 0x4F, 0x58, 0x61, 0x6A, 0x73, 0x7C, 0x85, 0x8E]
        hvac_8 = [0x08, 0x11, 0x1A, 0x23, 0x2C, 0x35, 0x3E, 0x47, 0x50, 0x59, 0x62, 0x6B, 0x74, 0x7D, 0x86, 0x8F]
        hvac_current_temperature = [0x09, 0x12, 0x1B, 0x24, 0x2D, 0x36, 0x3F, 0x48, 0x51, 0x5A, 0x63, 0x6C, 0x75, 0x7E, 0x87, 0x90]
        response_dict = {
            "response_str": response_str,
            "data1": response_str[8],
            "data2": response_str[9],
            "data3": response_str[10],
            "data4": response_str[11],
            "device_type":"",
            "sub_device_type":"",
            "hvac_type": "",
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
        
        elif response_dict["data2"] == 0x00 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x10:
            response_dict["device_type"] = "light"
            response_dict["sub_device_type"] = "0603D"
        
        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x20 and response_dict["loop_address"] in hvac_off:
            response_dict["device_type"] = "climate"
            # response_dict["loop_address"] = (response_dict["loop_address"] + 287) // 9
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_01"
        
        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x20 and response_dict["loop_address"] in hvac_mode:
            response_dict["device_type"] = "climate"
            # response_dict["loop_address"] = (response_dict["loop_address"] + 286) // 9
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_02"

        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x20 and response_dict["loop_address"] in hvac_fan:
            response_dict["device_type"] = "climate"
            # response_dict["loop_address"] = (response_dict["loop_address"] + 285) // 9
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_03"
        
        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x20 and response_dict["loop_address"] in hvac_current_set_point:
            response_dict["device_type"] = "climate"
            # response_dict["loop_address"] = (response_dict["loop_address"] + 284) // 9
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_04"
        
        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x20 and response_dict["loop_address"] in hvac_current_temperature:
            response_dict["device_type"] = "climate"
            # response_dict["loop_address"] = (response_dict["loop_address"] + 279) // 9
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_09"

        unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["device_type"]}"
        response_dict['device'] = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
        return response_dict
