

class LightCommand():
    
    def __init__(self, host, module_address, loop_address):
        self.host_hex = f"AC{int(host.split('.')[-1]):02X}0010"
        self.module_hex = f"{int(module_address):02X}"
        self.loop_hex = f"{int(loop_address):02X}"
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

    # 可控硅6路调光
    # 回路控制设备发送  AC E6 00 10 06（设备地址） 02（回路号1-6） 00 04（字节长度） 64（亮度0-100） 02(渐变时间) 00 10 CA
    # 设备回复          AC E6 00 11 06（设备地址） 02（回路号1-6） 00 04（字节长度） 64（亮度0-100） 00 00 10（可控硅调光标识符） CA
    #----------------------------------------------
    # 查询指令发送  AC E6 00 B0 06（设备地址）01 00 01 06 CA
    # 设备回复      AC E6 00 B1 06（设备地址） 01 00 18（字节长度） 64（亮度） 00 00 10（回路1数据） 64（亮度） 00 00 10 （回路2数据）
    #               64（亮度） 00 00 10（回路3数据） 64（亮度） 00 00 10（回路4数据） 64（亮度） 00 00 10（回路5数据） 64（亮度） 00 00 10（回路6数据） CA
    def query_0603d_state(self):
        command_01_bytes = bytes.fromhex('B0')
        command_bytes = bytes.fromhex('01000106CA')
        command = self.host_bytes + command_01_bytes + self.module_bytes + command_bytes
        return command
    
    # DALI-B类控制
    # DALI组（亮度、色温）
    #    组1（1、2）；组2（5、6）；组3（9、10）；组4（13、14）；组5（17、18）；组6（21、22）；组7（25、26）；组8（29、30）；
    #    组9（33、34）；组10（37、38）；组11（41、42）；组12（45、46）；组13（49、50）；组14（53、54）；组15（57、58）；组16（61、62）；
    # 亮度控制
    # 回路控制设备发送  AC E6 00 10 06（设备地址） 13（组4） 00 04（字节长度） 64（亮度0-100） 02(渐变时间) 00 10 CA
    # 设备回复          AC E6 00 11 06（设备地址） 13（组4） 00 04（字节长度） 64（亮度0-100） 00 00 11（DALI-B亮度标识符） CA
    # 色温控制
    # 回路控制设备发送  AC E6 00 10 06（设备地址） 14（组4） 00 04（字节长度） 41（色温15-65） 00 00 00 CA
    # 设备回复          AC E6 00 11 06（设备地址） 14（组4） 00 04（字节长度） 41（色温15-65） 00 00 12（DALI-B色温标识符） CA
    #----------------------------------------------
    # 由于查询指令设备回复数据量比较多 分两次查询
    # 1-8组查询指令： AC E6 00 B0 06（设备地址）01 00 01 20 CA
    #设备回复         AC E6 00 B1 06 01 00 80(数据长度) 
    #                2F（亮度0-100） 00 00 11（亮度数据） 00（色温15-65） 00 00 12（色温数据） 00（R） 00（G） 00（B） 13（RGB数据） 00 00 00 14（WA数据暂不处理）  组1数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14        组2数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14        组3数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14        组4数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14        组5数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14        组6数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14        组7数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14        组8数据   49 （校验位）
    # 9-16组查询指令： AC E6 00 B0 06（设备地址）21 00 01 20 CA
    #设备回复         AC E6 00 B1 06 21 00 80(数据长度) 
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14      组9数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14      组10数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14      组11数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14      组12数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14      组13数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14      组14数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14      组15数据
    #                00 00 00 11 00 00 00 12 00 00 00 13 00 00 00 14      组16数据      3A

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
    
    #  DALI-C类控制
    # DALI组地址1-64
    # 亮度控制
    # 回路控制设备发送  AC E6 00 10 06（设备地址） 06（组6） 00 04（字节长度） 64（亮度0-100） 02(渐变时间) FF 10 CA
    # 设备回复          AC E6 00 11 06（设备地址） 06（组6） 00 04（字节长度） 64（亮度0-100） 0F（色温15-65） 00 15（DALI-C标识符） CA
    # 色温控制
    # 回路控制设备发送  AC E6 00 10 06（设备地址） 06（组6） 00 04（字节长度） FF 02(渐变时间) 41 10 CA
    # 设备回复          AC E6 00 11 06（设备地址） 06（组6） 00 04（字节长度） 64（亮度0-100） 41（色温15-65） 00 15（DALI-C标识符） CA
    #----------------------------------------------
    # 由于查询指令设备回复数据量比较多 分四次查询
    #1-16组查询     AC E6 00 B0 06（设备地址） 01（起始字节） 00 01 10（查询组长度） CA
    #设备回复         AC E6 00 B1 06 21 00 40(数据长度) 
    #                64(亮度值) 41（色温值） 00 15    组1数据   64(亮度值) 41（色温值） 00 15    组2数据
    #                64(亮度值) 41（色温值） 00 15    组3数据   64(亮度值) 41（色温值） 00 15    组4数据     
    #                64(亮度值) 41（色温值） 00 15    组5数据   64(亮度值) 41（色温值） 00 15    组6数据
    #                64(亮度值) 41（色温值） 00 15    组7数据   64(亮度值) 41（色温值） 00 15    组8数据
    #                64(亮度值) 41（色温值） 00 15    组9数据   64(亮度值) 41（色温值） 00 15    组10数据
    #                64(亮度值) 41（色温值） 00 15    组11数据   64(亮度值) 41（色温值） 00 15    组12数据     
    #                64(亮度值) 41（色温值） 00 15    组13数据   64(亮度值) 41（色温值） 00 15    组14数据
    #                64(亮度值) 41（色温值） 00 15    组15数据   64(亮度值) 41（色温值） 00 15    组16数据      CA（和校验位）
    #17-32组查询     AC E6 00 B0 06（设备地址） 11 00 01 10 CA
    #设备回复         AC E6 00 B1 06 21 00 40(数据长度) 
    #                64(亮度值) 41（色温值） 00 15    组17数据   64(亮度值) 41（色温值） 00 15    组8数据
    #                64(亮度值) 41（色温值） 00 15    组19数据   64(亮度值) 41（色温值） 00 15    组20数据     
    #                64(亮度值) 41（色温值） 00 15    组21数据   64(亮度值) 41（色温值） 00 15    组22数据
    #                64(亮度值) 41（色温值） 00 15    组23数据   64(亮度值) 41（色温值） 00 15    组24数据
    #                64(亮度值) 41（色温值） 00 15    组25数据   64(亮度值) 41（色温值） 00 15    组26数据
    #                64(亮度值) 41（色温值） 00 15    组27数据   64(亮度值) 41（色温值） 00 15    组28数据                                                               
    #                64(亮度值) 41（色温值） 00 15    组29数据   64(亮度值) 41（色温值） 00 15    组30数据
    #                64(亮度值) 41（色温值） 00 15    组31数据   64(亮度值) 41（色温值） 00 15    组32数据      CA（和校验位）
    #33-48组查询     AC E6 00 B0 06（设备地址） 21 00 01 10 CA
    # #设备回复         AC E6 00 B1 06 21 00 40(数据长度) 
    #                64(亮度值) 41（色温值） 00 15    组33数据   64(亮度值) 41（色温值） 00 15    组34数据
    #                64(亮度值) 41（色温值） 00 15    组35数据   64(亮度值) 41（色温值） 00 15    组36数据     
    #                64(亮度值) 41（色温值） 00 15    组37数据   64(亮度值) 41（色温值） 00 15    组38数据
    #                64(亮度值) 41（色温值） 00 15    组39数据   64(亮度值) 41（色温值） 00 15    组40数据
    #                64(亮度值) 41（色温值） 00 15    组41数据   64(亮度值) 41（色温值） 00 15    组42数据
    #                64(亮度值) 41（色温值） 00 15    组43数据   64(亮度值) 41（色温值） 00 15    组44数据     
    #                64(亮度值) 41（色温值） 00 15    组45数据   64(亮度值) 41（色温值） 00 15    组46数据
    #                64(亮度值) 41（色温值） 00 15    组47数据   64(亮度值) 41（色温值） 00 15    组58数据      CA（和校验位） 
    #49-64组查询     AC E6 00 B0 06（设备地址） 31 00 01 10 CA
    #设备回复         AC E6 00 B1 06 21 00 40(数据长度) 
    #                64(亮度值) 41（色温值） 00 15    组49数据   64(亮度值) 41（色温值） 00 15    组50数据
    #                64(亮度值) 41（色温值） 00 15    组51数据   64(亮度值) 41（色温值） 00 15    组52数据     
    #                64(亮度值) 41（色温值） 00 15    组53数据   64(亮度值) 41（色温值） 00 15    组54数据
    #                64(亮度值) 41（色温值） 00 15    组55数据   64(亮度值) 41（色温值） 00 15    组56数据
    #                64(亮度值) 41（色温值） 00 15    组57数据   64(亮度值) 41（色温值） 00 15    组58数据
    #                64(亮度值) 41（色温值） 00 15    组59数据   64(亮度值) 41（色温值） 00 15    组60数据     
    #                64(亮度值) 41（色温值） 00 15    组61数据   64(亮度值) 41（色温值） 00 15    组62数据
    #                64(亮度值) 41（色温值） 00 15    组63数据   64(亮度值) 41（色温值） 00 15    组64数据      CA（和校验位）
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