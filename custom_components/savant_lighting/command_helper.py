

class LightCommand():
    
    def __init__(self, host, module_address, loop_address, gradient_time):
        self.host_hex = f"AC{int(host.split('.')[-1]):02X}0010"
        self.module_hex = f"{int(module_address):02X}"
        self.loop_hex = f"{int(loop_address):02X}"
        self.time_hex = f"{int(gradient_time):02X}"

        self.host_bytes = bytes.fromhex(self.host_hex)
        self.module_bytes = bytes.fromhex(self.module_hex)
        self.loop_bytes = bytes.fromhex(self.loop_hex)
            
    # def query_state(self):
    #     command_bytes = bytes.fromhex('01000108CA')
    #     command = self.host_bytes + self.module_bytes + command_bytes
    #     return command
        
    def turnonoff(self, command):
        if command == "on":
            command_hex = f'{self.loop_hex}000401000001CA'   #状态开启
        elif command == "off":
            command_hex = f'{self.loop_hex}000400000001CA'   #状态关闭
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command

    def brightness(self, brightness_percentage):
        brightness_hex = f"{int(brightness_percentage):02X}" if brightness_percentage is not None else '00'
        command_hex = f'{self.loop_hex}0004{brightness_hex}{self.time_hex}FF10CA'
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
        
    def dali01_brightness(self, brightness_percentage):
        brightness_hex = f"{int(brightness_percentage):02X}" if brightness_percentage is not None else '00'
        command_hex = f'{self.loop_hex}0004{brightness_hex}{self.time_hex}0010CA'
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
        
    def dali01_color_temp(self, color_temp_kelvin_value):
        loop_hex_value = int(self.loop_hex, 16)
        loop_hex_value += 1
        loop_hex_original = f"{loop_hex_value:02X}"
        color_temp_hex = f"{int(color_temp_kelvin_value):02X}" if color_temp_kelvin_value is not None else '00'
        command_hex = f'{loop_hex_original}0004{color_temp_hex}000000CA'
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
    
    def dali02_brightness(self, brightness_percentage):
        brightness_hex = f"{int(brightness_percentage):02X}" if brightness_percentage is not None else '00'
        command_hex = f'{self.loop_hex}0004{brightness_hex}{self.time_hex}FF10CA'
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command

    def dali02_color_temp(self, color_temp_kelvin_value):
        color_temp_hex = f"{int(color_temp_kelvin_value):02X}" if color_temp_kelvin_value is not None else '00'
        command_hex = f'{self.loop_hex}0004FF00{color_temp_hex}10CA'
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
        
    def rgb_color_temp(self, color_temp_kelvin_value):
        color_temp_hex = f"{int(color_temp_kelvin_value):02X}" if color_temp_kelvin_value is not None else '00'
        command_hex = f'{self.loop_hex}0004FF00{color_temp_hex}10CA'
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
    
    def rgb_color(self, color_rgb_hex):
        # 以下代码需要实现颜色指令的转换，请重构
        color_rgb_hex = f"{int(color_rgb_hex):02X}" if color_rgb_hex is not None else '00'
        command_hex = f'{self.loop_hex}0004FF00{color_rgb_hex}10CA'
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command

    def query_0603d_state(self):
        command_01_bytes = bytes.fromhex('B0')
        command_bytes = bytes.fromhex('01000106CA')
        command = self.host_bytes + command_01_bytes + self.module_bytes + command_bytes
        return command
    def query_dali01_01_state(self):
        command_01_bytes = bytes.fromhex('B0')
        command_bytes = bytes.fromhex('01000120CA')
        command = self.host_bytes + command_01_bytes + self.module_bytes + command_bytes
        return command
    def query_dali01_02_state(self):
        command_01_bytes = bytes.fromhex('B0')
        command_bytes = bytes.fromhex('21000120CA')
        command = self.host_bytes + command_01_bytes + self.module_bytes + command_bytes
        return command
    
    def query_dali02_01_state(self):
        command_01_bytes = bytes.fromhex('B0')
        command_bytes = bytes.fromhex('01000110CA')
        command = self.host_bytes + command_01_bytes + self.module_bytes + command_bytes
        return command
    
    def query_dali02_02_state(self):
        command_01_bytes = bytes.fromhex('B0')
        command_bytes = bytes.fromhex('11000120CA')
        command = self.host_bytes + command_01_bytes + self.module_bytes + command_bytes
        return command
    
    def query_dali02_03_state(self):
        command_01_bytes = bytes.fromhex('B0')
        command_bytes = bytes.fromhex('21000120CA')
        command = self.host_bytes + command_01_bytes + self.module_bytes + command_bytes
        return command
    
    def query_dali02_04_state(self):
        command_01_bytes = bytes.fromhex('B0')
        command_bytes = bytes.fromhex('31000120CA')
        command = self.host_bytes + command_01_bytes + self.module_bytes + command_bytes
        return command
    
class SwitchCommand:
    def __init__(self, host, module_address, loop_address):
        self.host_hex = f"AC{int(host.split('.')[-1]):02X}0010"
        self.module_hex = f"{int(module_address):02X}"
        self.loop_hex = f"{int(loop_address):02X}"
        self.host_bytes = bytes.fromhex(self.host_hex)
        self.module_bytes = bytes.fromhex(self.module_hex)
        self.loop_bytes = bytes.fromhex(self.loop_hex)
    
    def turnonoff(self, command):
        if command == "on":
            command_hex = f'000401000000CA'   #状态开启
        elif command == "off":
            command_hex = f'000400000000CA'   #状态关闭
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + self.loop_bytes + command_bytes
        return command
    
    # 在HA添加了模块地址回路  再下发此模块查询
    def query_state(self):
        command_bytes = bytes.fromhex('01000108CA')
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
    
class ClimateCommand:
    def __init__(self, host, module_address, loop_address):
        self.host_hex = f"AC{int(host.split('.')[-1]):02X}0010"
        self.module_hex = f"{int(module_address):02X}"
        self.loop_hex = f"{int(loop_address):02X}"
        self.host_bytes = bytes.fromhex(self.host_hex)
        self.module_bytes = bytes.fromhex(self.module_hex)
        
    def hvac_mode(self, command):
        from homeassistant.components.climate.const import (
            HVAC_MODE_OFF,HVAC_MODE_COOL,HVAC_MODE_HEAT,HVAC_MODE_AUTO,HVAC_MODE_DRY)
        loop_hex_value = int(self.loop_hex, 16)
        command_list = []
        if command == HVAC_MODE_OFF:
            loop_hex_modeaddress = loop_hex_value * 9 - 287
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_list.append(f"{loop_hex_original}000400002020CA")
        elif command == HVAC_MODE_COOL:
            command_list.append(f"{loop_hex_value * 9 - 287:02X}000401000000CA")
            command_list.append(f"{loop_hex_value * 9 - 286:02X}000405000000CA")
        elif command == HVAC_MODE_HEAT:
            command_list.append(f"{loop_hex_value * 9 - 287:02X}000401000000CA")
            command_list.append(f"{loop_hex_value * 9 - 286:02X}000408002020CA")
        elif command == HVAC_MODE_AUTO:
            command_list.append(f"{loop_hex_value * 9 - 287:02X}000401000000CA")
            command_list.append(f"{loop_hex_value * 9 - 286:02X}000404000000CA")
        elif command == HVAC_MODE_DRY:
            command_list.append(f"{loop_hex_value * 9 - 287:02X}000401000000CA")
            command_list.append(f"{loop_hex_value * 9 - 286:02X}000402000000CA")
        return [self.host_bytes + self.module_bytes + bytes.fromhex(cmd) for cmd in command_list]

    def temperature(self, temperature):
        if temperature.startswith("temp:"):
            temperature_str = temperature.split(":")[1]
            temperature_hex = f"{int(float(temperature_str)):02X}"
            command_hex = f"{int(self.loop_hex, 16) * 9 - 284:02X}0004{temperature_hex}000000CA"
            return self.host_bytes + self.module_bytes + bytes.fromhex(command_hex)

    def fan_mode(self, command):
        fan_speed_map = {"low": "04", "medium": "02", "high": "01", "auto": "00"}
        command_hex = f"{int(self.loop_hex, 16) * 9 - 285:02X}0004{fan_speed_map[command]}000000CA"
        return self.host_bytes + self.module_bytes + bytes.fromhex(command_hex)
    
    def floor_heat_mode(self, command):
        from homeassistant.components.climate.const import (
            HVAC_MODE_OFF,HVAC_MODE_COOL,HVAC_MODE_HEAT,HVAC_MODE_AUTO,HVAC_MODE_DRY)
        loop_hex_value = int(self.loop_hex, 16)
        command_list = []
        if command == HVAC_MODE_OFF:
            loop_hex_modeaddress = loop_hex_value * 9 - 283
            loop_hex_original = f"{loop_hex_modeaddress:02X}"
            command_list.append(f"{loop_hex_original}000400002020CA")
        elif command == HVAC_MODE_HEAT:
            command_list.append(f"{loop_hex_value * 9 - 283:02X}000401000000CA")
        return [self.host_bytes + self.module_bytes + bytes.fromhex(cmd) for cmd in command_list]
    
    def floor_heat_temperature(self, temperature):
        if temperature.startswith("temp:"):
            temperature_str = temperature.split(":")[1]
            temperature_hex = f"{int(float(temperature_str)):02X}"
            command_hex = f"{int(self.loop_hex, 16) * 9 - 282:02X}0004{temperature_hex}000000CA"
            return self.host_bytes + self.module_bytes + bytes.fromhex(command_hex)

    def _command_to_bytes(self, command_hex):
        return bytes.fromhex(command_hex)
    
    
class FreshAirCommand:
    def __init__(self, host, module_address, loop_address):
        self.host_hex = f"AC{int(host.split('.')[-1]):02X}0010"
        self.module_hex = f"{int(module_address):02X}"
        self.loop_hex = f"{int(loop_address):02X}"
        self.host_bytes = bytes.fromhex(self.host_hex)
        self.module_bytes = bytes.fromhex(self.module_hex)
        
        
class CurtainCommand:
    def __init__(self, host, module_address, loop_address):
        self.host_hex = f"AC{int(host.split('.')[-1]):02X}0010"
        self.module_hex = f"{int(module_address):02X}"
        self.loop_hex = f"{int(loop_address):02X}"
        self.host_bytes = bytes.fromhex(self.host_hex)
        self.module_bytes = bytes.fromhex(self.module_hex)
        
class SwitchSceneCommand:
    def __init__(self, host, scene_number):
        self.host_hex = f"AC{int(host.split('.')[-1]):02X}101000"
        self.host_bytes = bytes.fromhex(self.host_hex)
        self.scene_hex = f"{int(scene_number):02X}"
        self.scene_bytes = bytes.fromhex(self.scene_hex)
    # def __init__(self, host, module_address, loop_address):
    #     self.host_hex = f"AC{int(host.split('.')[-1]):02X}0010"
    #     self.module_hex = f"{int(module_address):02X}"
    #     self.loop_hex = f"{int(loop_address):02X}"
    #     self.host_bytes = bytes.fromhex(self.host_hex)
    #     self.module_bytes = bytes.fromhex(self.module_hex)
    #     self.loop_bytes = bytes.fromhex(self.loop_hex)
    
    def turnonoff(self, command):
        if command == "on":
            command_hex = f'000401000000CA'   #状态开启
        elif command == "off":
            command_hex = f'000401000000CA'   #状态关闭
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.scene_bytes + command_bytes
        return command