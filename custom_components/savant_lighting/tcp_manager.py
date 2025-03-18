import asyncio
import logging
from .const import DOMAIN
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from custom_components.savant_lighting import sensor

_LOGGER = logging.getLogger(__name__)

class TCPConnectionManager:
    """管理与设备的TCP连接"""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.hass = None
        self.reader = None
        self.writer = None
        self._is_connected = False
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
        _LOGGER.debug(f"发送第{self.command_no}个命令:{str(data).replace('\\x', '')}")
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
            _LOGGER.debug(f"发送第{self.command_no}个命令:{str(data).replace('\\x', '')}")
            try:
                self.writer.write(data)
                await self.writer.drain()
                await asyncio.sleep(1)
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

                    if len(response_str)> 13:
                        response_dict_array = self._parse_response_array(response_str)
                        for response_dict in response_dict_array:
                            if response_dict['device_type'] in self._callbacks and response_dict['device']:
                                self._callbacks[response_dict['device_type']](response_dict)
                            elif not response_dict['device']:
                                _LOGGER.warning(f"未识别的设备类型: {response_dict['unique_id']} {response_dict['device_type']}")
                            else:
                                _LOGGER.warning(f"响应处理失败: {response_dict['unique_id']} {response_dict['device']} {response_dict['device_type']}")
                    continue

                    response_dict = self._parse_response(response_str)
                    if response_dict['device_type'] in self._callbacks and response_dict['device']:
                        self._callbacks[response_dict['device_type']](response_dict)
                        if ('redirect_type' in response_dict):
                            response_dict['device_type'] = response_dict['redirect_type']
                            unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["device_type"]}"
                            device = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
                            if device:
                                response_dict['device'] = device
                                self._callbacks[response_dict['device_type']](response_dict)
                            # response_dict['device'] = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
                            # self._callbacks[response_dict['device_type']](response_dict)
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
                switch_with_energy_devices = []
                # Iterate over all devices in the DOMAIN data
                for key, data in self.hass.data[DOMAIN].items():
                    if 'devices' not in data:
                        break
                    devices = data.get("devices", [])
                    for device in devices:
                        if device["type"] == "switch_with_energy":
                            switch_with_energy_devices.append(device)

                if switch_with_energy_devices:
                    _LOGGER.debug("存在 switch_with_energy 设备，执行状态查询")
                    await self.update_all_device_state_switch(switch_with_energy_devices)
                else:
                    _LOGGER.debug("发送保持连接的心跳包")
                    ff_bytes = b'\xFF'
                    await self.send_command(ff_bytes)
                await asyncio.sleep(60)
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
            _LOGGER.warning(f"未找到 unique_id 为 {unique_id} 的设备")
            return None
        entity_id = entity_entry.entity_id

        if device_type in self.hass.data:
            device = self.hass.data[device_type].get_entity(entity_id)
        elif device_type == 'floor_heating':
            device = self.hass.data['climate'].get_entity(entity_id)
        elif device_type == 'fresh_air':
            device = self.hass.data['fan'].get_entity(entity_id)
        elif device_type == 'curtain':
            device = self.hass.data['cover'].get_entity(entity_id)
        elif device_type == 'switch':
            device = self.hass.data['switch'].get_entity(entity_id)
        elif device_type == 'scene_switch':
            device = self.hass.data['switch'].get_entity(entity_id)
        elif device_type == 'person_sensor':
            device = self.hass.data['binary_sensor'].get_entity(entity_id)
        elif device_type == '8button':
            device = self.hass.data['switch'].get_entity(entity_id)
        elif device_type == 'switch_with_energy':
            device = self.hass.data['switch'].get_entity(entity_id)

        if device is None:
            _LOGGER.warning(f"未找到 entity_id 为 {entity_id} 的设备实例")
            return None
        return device

    def register_callback(self, device_type, callback):
        """注册回调函数"""
        self._callbacks[device_type] = callback
        # self._callbacks.append(callback)

    def _parse_response(self, response_str):
        _LOGGER.debug(f"接收响应：{str(response_str).replace('\\x', '')}")
        hvac_off = [0x01, 0x0A, 0x13, 0x1C, 0x25, 0x2E, 0x37, 0x40, 0x49, 0x52, 0x5B, 0x64, 0x6D, 0x76, 0x7F, 0x88]
        hvac_mode = [0x02, 0x0B, 0x14, 0x1D, 0x26, 0x2F, 0x38, 0x41, 0x4A, 0x53, 0x5C, 0x65, 0x6E, 0x77, 0x80, 0x89]
        hvac_fan = [0x03, 0x0C, 0x15, 0x1E, 0x27, 0x30, 0x39, 0x42, 0x4B, 0x54, 0x5D, 0x66, 0x6F, 0x78, 0x81, 0x8A]
        hvac_current_set_point = [0x04, 0x0D, 0x16, 0x1F, 0x28, 0x31, 0x3A, 0x43, 0x4C, 0x55, 0x5E, 0x67, 0x70, 0x79, 0x82, 0x8B]
        floor_heat_mode = [0x05, 0x0E, 0x17, 0x20, 0x29, 0x32, 0x3B, 0x44, 0x4D, 0x56, 0x5F, 0x68, 0x71, 0x7A, 0x83, 0x8C]
        floor_heat_temperature = [0x06, 0x0F, 0x18, 0x21, 0x2A, 0x33, 0x3C, 0x45, 0x4E, 0x57, 0x60, 0x69, 0x72, 0x7B, 0x84, 0x8D]
        hvac_fan_mode = [0x07, 0x10, 0x19, 0x22, 0x2B, 0x34, 0x3D, 0x46, 0x4F, 0x58, 0x61, 0x6A, 0x73, 0x7C, 0x85, 0x8E]
        hvac_fan_speed = [0x08, 0x11, 0x1A, 0x23, 0x2C, 0x35, 0x3E, 0x47, 0x50, 0x59, 0x62, 0x6B, 0x74, 0x7D, 0x86, 0x8F]
        hvac_current_temperature = [0x09, 0x12, 0x1B, 0x24, 0x2D, 0x36, 0x3F, 0x48, 0x51, 0x5A, 0x63, 0x6C, 0x75, 0x7E, 0x87, 0x90]
        shade_address = [0x14, 0x17, 0x1A, 0x1D, 0x20, 0x23, 0x26, 0x29, 0x2C, 0x2F, 0x32, 0x35, 0x38, 0x3B, 0x3E]
        response_dict = {
            "response_str": response_str,
            "data1": response_str[8],
            "data2": response_str[9],
            "data3": response_str[10],
            "data4": response_str[11],
            "device_type":"",
            "sub_device_type":"",
            "hvac_type": "",
            "switch_type":"",
            "module_address": response_str[4],
            "loop_address": response_str[5],
            "unique_id":"",
            "button_index":"",
            "device":None

        }
        if response_dict["data2"] == 0x00 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x00:
            response_dict["device_type"] = "switch"
            response_dict["switch_type"] = "num0"
            response_dict["redirect_type"] = "switch_with_energy"

        elif response_dict["data2"] == 0x04 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x00 and response_dict["loop_address"] in shade_address:
            response_dict["loop_address"] = (response_dict["loop_address"] - 17) // 3
            response_dict["device_type"] = "curtain"

        elif response_dict["loop_address"] == 0x00 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x00:
            response_dict["loop_address"] = response_str[9]
            response_dict["device_type"] = "person_sensor"

        elif response_dict["loop_address"] == 0x00 and response_dict["data4"] == 0x00:
            response_dict["button_index"] = response_str[9]
            response_dict["loop_address"] = response_str[10]
            response_dict["device_type"] = "8button"

        elif response_dict["data2"] == 0x00 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x11:
            response_dict["device_type"] = "light"
            response_dict["sub_device_type"] = "DALI-01"

        elif response_dict["data2"] == 0x00 and response_dict["data3"] == 0x00 and response_dict["data4"] == 0x12:
            response_dict["device_type"] = "light"
            response_dict["sub_device_type"] = "DALI-01"
            if response_dict["data4"] == 0x12:
                response_dict["loop_address"] = response_dict["loop_address"] - 1

        elif response_dict["data4"] == 0x15:
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
            # hvac_fhs = ["climate", "floor_heating"]
            # for hvac_fh in hvac_fhs:
            #     response_dict["device_type"] = hvac_fh
            response_dict["device_type"] = "climate"
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_09"
            response_dict["redirect_type"] = "floor_heating"

        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x21 and response_dict["loop_address"] in floor_heat_mode:
            response_dict["device_type"] = "floor_heating"
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_05"

        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x21 and response_dict["loop_address"] in floor_heat_temperature:
            response_dict["device_type"] = "floor_heating"
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_06"

        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x22 and response_dict["loop_address"] in hvac_fan_mode:
            response_dict["device_type"] = "fresh_air"
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_07"

        elif response_dict["data2"] == 0x00 and response_dict["data4"] == 0x22 and response_dict["loop_address"] in hvac_fan_speed:
            response_dict["device_type"] = "fresh_air"
            response_dict["loop_address"] = response_dict["data3"]
            response_dict["hvac_type"] = "hvac_08"

        # todo: switch_with_energy 类型判断
        elif response_dict["device_type"] == "switch_with_energy":
            response_dict["device_type"] = "switch_with_energy"
            unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_switch_with_energy"

        if response_dict["device_type"] == "8button":
            unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["button_index"]}_{response_dict["device_type"]}"
        else:
            unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["device_type"]}"

        response_dict['device'] = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
        return response_dict

    def _parse_response_array(self, response_str):
        _LOGGER.debug(f"接收响应：{str(response_str).replace('\\x', '')}")
        response_dict_array = []
        module_address = response_str[4]
        response_start = response_str[5]
        response_length = response_str[7]

        if response_length == 0x20:
            response_array = [response_str[i:i+4] for i in range(8, len(response_str), 4)]
            for idx,response in enumerate(response_array):
                if idx == 8:
                    break
                response_dict = {
                    "response_str": response_str,
                    "data1": response[0],
                    "data2": response[1],
                    "data3": response[2],
                    "data4": response[3],
                    "device_type":"switch",
                    "sub_device_type":"",
                    "switch_type": "num0",
                    "module_address": module_address,
                    "loop_address": idx +1,
                    "unique_id":"",
                    "button_index":"",
                    "device":None
                }
                unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["device_type"]}"
                response_dict['device'] = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
                if response_dict['device']:
                    response_dict_array.append(response_dict)

        elif response_length == 0x40:
            response_array = [response_str[i:i+4] for i in range(8, len(response_str), 4)]
            for idx,response in enumerate(response_array):
                if idx == 16:
                    break
                # response_start = 1
                if response_start == 0x01:
                    response_start = 1
                elif response_start == 0x11:
                    response_start = 17
                elif response_start == 0x21:
                    response_start = 33
                elif response_start == 0x31:
                    response_start = 49
                # len = 9 if response_start == 0x21 else 1
                response_dict = {
                    "response_str": response_str,
                    "data1": response[0],
                    "data2": response[1],
                    "data3": response[2],
                    "data4": response[3],
                    "device_type":"light",
                    "sub_device_type":"DALI-02",
                    "hvac_type": "",
                    "module_address": module_address,
                    "loop_address": str(idx+response_start),
                    "unique_id":"",
                    "button_index":"",
                    "device":None
                }
                unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["device_type"]}"
                response_dict['device'] = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
                response_dict_array.append(response_dict)

        elif response_length == 0x24:
            response_array = [response_str[i:i+4] for i in range(8, len(response_str), 4)]
            hvac1_state = response_str[8]
            hvac2_state = response_str[24]
            hvac3_state = response_str[32]
            for idx,response in enumerate(response_array):
                if idx == 9:
                    break
                response_dict = {
                    "response_str": response_str,
                    "data1": response[0],
                    "data2": response[1],
                    "data3": response[2],
                    "data4": response[3],
                    "device_type":"",
                    "sub_device_type":"",
                    "hvac_type": "",
                    "module_address": module_address,
                    "loop_address": str(idx+response_start),
                    "unique_id":"",
                    "button_index":"",
                    "device":None
                }
                if response_dict["data4"] == 0x20 and idx == 0:
                    response_dict["device_type"] = "climate"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_01"
                elif response_dict["data4"] == 0x20 and idx == 1 and hvac1_state != 0x00:
                    response_dict["device_type"] = "climate"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_02"
                elif response_dict["data4"] == 0x20 and idx == 2 and hvac1_state != 0x00:
                    response_dict["device_type"] = "climate"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_03"
                elif response_dict["data4"] == 0x20 and idx == 3 and hvac1_state != 0x00:
                    response_dict["device_type"] = "climate"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_04"
                elif response_dict["data4"] == 0x21 and idx == 4:
                    response_dict["device_type"] = "floor_heating"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_05"
                elif response_dict["data4"] == 0x21 and idx == 5  and hvac2_state != 0x00:
                    response_dict["device_type"] = "floor_heating"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_06"
                elif response_dict["data4"] == 0x22 and idx == 6:
                    response_dict["device_type"] = "fresh_air"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_07"
                elif response_dict["data4"] == 0x22 and idx == 7 and hvac3_state != 0x00:
                    response_dict["device_type"] = "fresh_air"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_08"
                elif response_dict["data4"] == 0x20 and idx == 8:
                    response_dict["device_type"] = "climate"
                    response_dict["loop_address"] = response_dict["data3"]
                    response_dict["hvac_type"] = "hvac_09"
                    response_dict["redirect_type"] = "floor_heating"
                else:
                    continue
                unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["device_type"]}"
                response_dict['device'] = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
                response_dict_array.append(response_dict)

        elif response_length == 0x50:
            response_array = [response_str[i:i+4] for i in range(8, len(response_str), 4)]
            response_start = response_str[5]
            device_dict = {}
            for idx,response in enumerate(response_array):
                if idx == 20:
                    break
                response_dict = {
                    "response_str": response_str,
                    "data1": response[0],
                    "data2": response[1],
                    "data3": response[2],
                    "data4": response[3],
                    "device_type":"switch_with_energy",
                    "sub_device_type":"",
                    "switch_type": "",
                    "module_address": module_address,
                    "loop_address": "",
                    "unique_id":"",
                    "button_index":"",
                    "device":None
                }
                if idx < 4 and idx >=0:
                    response_dict["loop_address"] = idx + response_start
                    response_dict["switch_type"] = "num1"
                    unique_id = f"{response_dict["module_address"]}_{response_dict["loop_address"]}_{response_dict["device_type"]}"
                    response_dict['unique_id'] = unique_id
                    response_dict['device'] = self.get_device_by_unique_id(response_dict["device_type"],unique_id)
                    device_dict[response_dict["loop_address"]] = response_dict['device']

                if idx < 8 and idx >=4 and device_dict[idx - 3]:
                    response_dict["loop_address"] = idx - 3
                    response_dict["switch_type"] = "num2"
                    response_dict['device'] = device_dict[idx - 3]

                elif idx < 12 and idx >=8 and device_dict[idx - 7]:
                    response_dict["loop_address"] = idx - 7
                    response_dict["switch_type"] = "num3"
                    response_dict['device'] = device_dict[idx - 7]
                elif idx < 16 and idx >=12 and device_dict[idx - 11]:

                    response_dict["loop_address"] = idx - 11
                    response_dict["switch_type"] = "num4"
                    response_dict['device'] = device_dict[idx - 11]

                elif idx < 20 and idx >=16 and device_dict[idx - 15]:
                    response_dict["loop_address"] = idx - 15
                    response_dict["switch_type"] = "num5"
                    response_dict['device'] = device_dict[idx - 15]

                if response_dict['device']:
                    response_dict_array.append(response_dict)

        return response_dict_array

    async def update_all_device_state(self, devices):
        command_list = []
        processed_types = ["light","switch","climate"]
        queryed_device = []
        for device in devices:
            device_type = device.get("type")
            sub_device_type = device.get("sub_device_type")
            host = device.get("host")
            module_address = device.get('module_address')
            loop_address = device.get('loop_address')

            if device_type not in processed_types:
                continue
            if module_address in queryed_device:
                continue
            queryed_device.append(module_address)

            self.host_hex = f"AC{int(host.split('.')[-1]):02X}00B0"
            self.module_hex = f"{int(module_address):02X}"
            self.loop_hex = f"{int(loop_address):02X}"
            self.host_bytes = bytes.fromhex(self.host_hex)
            self.module_bytes = bytes.fromhex(self.module_hex)
            self.loop_bytes = bytes.fromhex(self.loop_hex)
            if device_type == "light" and sub_device_type == "DALI-02":
                for cmd in [
                    f"{self.module_hex}01000110CA",
                    f"{self.module_hex}11000110CA",
                    f"{self.module_hex}21000110CA",
                    f"{self.module_hex}31000110CA"
                ]:
                    command_bytes = bytes.fromhex(cmd)
                    command_list.append(self.host_bytes + command_bytes)
            elif device_type == "light" and sub_device_type == "0603D":
                command_hex = f'{self.module_hex}01000106CA'
                command_bytes = bytes.fromhex(command_hex)
                command_list.append(self.host_bytes + command_bytes)
            elif device_type == "switch":
                command_hex = f'{self.module_hex}01000108CA'
                command_bytes = bytes.fromhex(command_hex)
                command_list.append(self.host_bytes + command_bytes)
            elif device_type == "climate":
                command_hex = f'{self.module_hex}01000109CA'
                command_bytes = bytes.fromhex(command_hex)
                command_list.append(self.host_bytes + command_bytes)
            elif device_type == "switch_with_energy":
                command_hex = f'{self.module_hex}01000114CA'
                command_bytes = bytes.fromhex(command_hex)
                command_list.append(self.host_bytes + command_bytes)

        await self.send_command_list(command_list)
        _LOGGER.debug("已查询所有设备状态")

    async def update_all_device_state_switch(self, devices):
        command_list = []
        processed_types = ["switch_with_energy"]
        for device in devices:
            device_type = device.get("type")
            sub_device_type = device.get("sub_device_type")
            host = device.get("host")
            module_address = device.get('module_address')
            loop_address = device.get('loop_address')

            if device_type not in processed_types:
                continue

            host_hex = f"AC{int(host.split('.')[-1]):02X}00B0"
            module_hex = f"{int(module_address):02X}"
            loop_hex = f"{int(loop_address):02X}"
            host_bytes = bytes.fromhex(host_hex)
            module_bytes = bytes.fromhex(module_hex)
            loop_bytes = bytes.fromhex(loop_hex)

            if device_type == "switch_with_energy":
                command_hex = f'{module_hex}01000114CA'
                command_bytes = bytes.fromhex(command_hex)
                command_list.append(host_bytes + command_bytes)

        await self.send_command_list(command_list)