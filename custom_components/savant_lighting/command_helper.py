

class LightCommand():
    
    def __init__(self, host, module_address, loop_address):
        self.host_hex = f"AC{int(host.split('.')[-1]):02X}0010"
        self.module_hex = f"{int(module_address):02X}"
        self.loop_hex = f"{int(loop_address):02X}"
        self.host_bytes = bytes.fromhex(self.host_hex)
        self.module_bytes = bytes.fromhex(self.module_hex)
        self.loop_bytes = bytes.fromhex(self.loop_hex)
            
    def query_state(self):
        command_bytes = bytes.fromhex('01000108CA')
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
        
    def turnonoff(self, command):
        if command == "on":
            command_hex = f'{self.loop_hex}000401000001CA'   #状态开启
        elif command == "off":
            command_hex = f'{self.loop_hex}000400000001CA'   #状态关闭
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
    
    def brightness(self, brightness_percentage):
        brightness_hex = f"{int(brightness_percentage):02X}" if self.brightness_percentage is not None else '00'
        command_hex = f'{self.loop_hex}0004{brightness_hex}00FF10CA'
        command_bytes = bytes.fromhex(command_hex)
        command = self.host_bytes + self.module_bytes + command_bytes
        return command
        
    def dali01_brightness(self, brightness_percentage):
        brightness_hex = f"{int(brightness_percentage):02X}" if brightness_percentage is not None else '00'
        command_hex = f'{self.loop_hex}0004{brightness_hex}000010CA'
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
        brightness_hex = f"{int(brightness_percentage):02X}" if self.brightness_percentage is not None else '00'
        command_hex = f'{self.loop_hex}0004{brightness_hex}00FF10CA'
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
    
    def query_state(self):
        command_bytes = bytes.fromhex('01000108CA')
        command = self.host_bytes + self.module_bytes + command_bytes
        return command