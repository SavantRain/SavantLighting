import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Savant Light entities from a config entry."""
    config = hass.data[DOMAIN].get(entry.entry_id, {}).get("devices", [])
    
    # 创建所有已配置的灯光实体并添加到 Home Assistant
    switchs = [
        SavantSwitch(
            name=device["name"],
            module_address=device["module_address"],
            loop_address=device["loop_address"],
            host=device["host"],
            port=device["port"],
        )
        for device in config if device["type"] == "switch"
    ]
    async_add_entities(switchs, update_before_add=True)

class SavantSwitch(SwitchEntity):
    """Representation of a Savant Switch."""

    def __init__(self, name, module_address, loop_address, host, port):
        """Initialize the switch."""
        self._attr_name = name
        self._module_address = module_address
        self._loop_address = loop_address
        self._host = host
        self._port = port
        self._attr_unique_id = f"{module_address}_{loop_address}_switch"
        self._state = False

    @property
    def unique_id(self):
        """Return a unique ID for this light."""
        return f"{self._module_address}_{self._loop_address}_switch"
    
    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def device_info(self):
        """Return device information to link this entity with the device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self._module_address}_{self._loop_address}")}
        }
    

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._state = True
        await self._send_state_to_device("on")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        self._state = False
        await self._send_state_to_device("off")
        self.async_write_ha_state()

    async def _send_state_to_device(self, command):
        """Send the current state to the actual device."""
        # 在这里实现与实际硬件设备通信的逻辑
        # 这可以是通过 REST API 调用、MQTT 消息或其他协议
        hex_command = self._convert_to_hex(command)
        self._send_tcp_command(hex_command)
        pass
    
    async def async_update(self):
        """Fetch new state data for this switch."""
        # 从实际设备获取新的状态数据
        # 例如，调用 REST API 端点或读取 MQTT 主题
        response = await self._get_state_from_device()

        if response:
            self._state = self._parse_device_state(response)  # 更新为实际状态
            self._async_write_ha_state()

    async def _get_state_from_device(self):
        command = self._query_to_hex("get_state")
        return self._send_tcp_command(command)

    def _parse_device_state(self, response):
        try:
            if len(response) >= 12:
                relay_state = response[8]

                if relay_state == 0x01:
                    return True
                elif relay_state == 0x00:
                    return False
                else:
                    _LOGGER.warning("无法解析继电器状态：{relay_state}")
            else:
                _LOGGER.error("无效的设备回复长度：{len(response)}")
        except Exception as e:
            _LOGGER.error("解析设备状态出错：{e}")

        return self._state
    
    def _query_to_hex(self, command):
        #查询指令
        host_hex = f"AC{int(self._host.split('.')[-1]):02X}"
        module_hex = f"{int(self._module_address):02X}00B0"
        command_hex = '01000108CA'
        host_bytes = bytes.fromhex(host_hex)
        module_bytes = bytes.fromhex(module_hex)
        command_bytes = bytes.fromhex(command_hex)
        command = host_bytes + module_bytes + command_bytes
        print(command)
        return command

    def _convert_to_hex(self, command):
        """将'开'和'关'的命令转换为十六进制格式"""
        #指令第二个字节为IP的最后一位，如192.168.1.230，将230转化为十六进制E6在指令中进行传输
        #最后一个字节AC为校验位，校验方式：和校验
        host_hex = f"AC{int(self._host.split('.')[-1]):02X}0010"
        module_hex = f"{int(self._module_address):02X}"
        loop_hex = f"{int(self._loop_address):02X}"
        if command == "on":
            command_hex = '000401000000CA'
        elif command == "off":
            command_hex = '000400000000CA'
        else:
            command_hex = ''
        host_bytes = bytes.fromhex(host_hex)
        module_bytes = bytes.fromhex(module_hex)
        loop_bytes = bytes.fromhex(loop_hex)
        command_bytes = bytes.fromhex(command_hex)
        command = host_bytes + module_bytes + loop_bytes + command_bytes
        print(command)
        return command

    def _send_tcp_command(self, data):
        import socket
        """通过TCP发送命令"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self._host, self._port))
                s.sendall(data)
#                response = s.recv(1024)
#                return response
        except socket.error as e:
            _LOGGER.error(f"Error sending data to {self._host}:{self._port} - {e}")
            