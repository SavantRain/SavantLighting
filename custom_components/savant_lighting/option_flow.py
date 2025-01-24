from homeassistant import config_entries
import voluptuous as vol
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, entity_registry as er, selector
from .const import DOMAIN
from homeassistant.components.light import ColorMode

class SavantLightingOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow for Savant Lighting."""

    def __init__(self, config_entry):
        """Initialize options flow."""  
        self.config_entry = config_entry
        self.host = config_entry.data.get("host")
        self.port = config_entry.data.get("port")
        self.device_type = None  # 用于存储当前正在配置的设备类型
        self.sub_device_type = None # 用于存储当前正在配置的设备子类型
        
    async def async_step_init(self, user_input=None):
        """Manage the options for devices: add or manage devices."""
        if user_input is not None:
            if user_input == "light_menu":
                self.device_type = "light"
                return await self.async_step_light_menu()
            elif user_input == "light_006_menu":
                self.device_type = "light"
                return await self.async_step_light_006_menu()
            elif user_input == "light_dali_001_menu":
                self.device_type = "light"
                return await self.async_step_light_dali_001_menu()
            elif user_input == "light_dali_002_menu":
                self.device_type = "light"
                return await self.async_step_light_dali_002_menu()
            elif user_input == "light_rgb_menu":
                self.device_type = "light"
                return await self.async_step_light_rgb_menu()
            elif user_input == "switch_menu":
                self.device_type = "switch"
                return await self.async_step_switch_menu()
            elif user_input == "climate_menu":
                self.device_type = "climate"
                return await self.async_step_climate_menu()
            elif user_input == "curtain_menu":
                self.device_type = "cover"
                return await self.async_step_curtain_menu()
            
        # 显示初始操作菜单，确保选项键与步骤方法一致
        # async_step_{step}  键名={step}方法名
        return self.async_show_menu(
            step_id="init",
            menu_options={
                "switch_menu": "管理继电器",
                "light_006_menu": "管理六路调光",
                "light_menu": "管理【单色温】灯光",
                "light_dali_001_menu": "管理【双色温DALI-01】灯光",
                "light_dali_002_menu": "管理【双色温DALI-02】灯光",
                "light_rgb_menu": "管理【DALI-RGB】灯光",
                "climate_menu": "管理空调",
                "floor_heating_menu": "管理地暖",
                "fresh_air_menu": "管理新风设备",
                "8button_menu": "管理8键开关",
                "curtain_menu": "管理窗帘",
                "person_sensor_menu": "管理人体传感器",
                "scene_switch_menu": "管理场景开关",
            },
            description_placeholders={"desc": "选择操作来管理子设备"},
        )
        
    async def async_step_light_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="light",user_input=user_input, sub_device_type="single")
    
    async def async_step_light_006_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="light",user_input=user_input, sub_device_type="0603D")

    async def async_step_light_rgb_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="light",user_input=user_input, sub_device_type="rgb")

    async def async_step_light_dali_001_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="light",user_input=user_input, sub_device_type="DALI-01")

    async def async_step_light_dali_002_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="light",user_input=user_input, sub_device_type="DALI-02")

    async def async_step_switch_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="switch", user_input=user_input)

    async def async_step_climate_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="climate", user_input=user_input)
        
    async def async_step_floor_heating_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="floor_heating", user_input=user_input)
    
    async def async_step_fresh_air_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="fresh_air", user_input=user_input)

    async def async_step_8button_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="8button", user_input=user_input)
    
    async def async_step_curtain_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="curtain", user_input=user_input) 
    
    async def async_step_person_sensor_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="person_sensor", user_input=user_input)
    
    async def async_step_scene_switch_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="scene_switch", user_input=user_input)
    
    async def async_step_device_menu(self, user_input=None, device_type=None, sub_device_type=None):
        """Second level menu: Add, configure, or delete devices."""
        self.device_type = device_type
        self.sub_device_type = sub_device_type
        if user_input is not None:
            if user_input == "add":
                return await self.async_step_add()
            elif user_input == "configure":
                return await self.async_step_configure()
            elif user_input == "delete":
                return await self.async_step_delete()

        # 显示第二级菜单，选择管理操作（添加、配置或删除）
        return self.async_show_menu(
            step_id="device_menu",
            menu_options={
                "add": f"添加{self.device_type.capitalize()}",
                "configure": f"配置{self.device_type.capitalize()}",
                "delete": f"删除{self.device_type.capitalize()}",
            },
            description_placeholders={"desc": f"选择操作来管理{self.device_type.capitalize()}设备"},
        )
        
    async def async_step_add(self, user_input=None):
        """Step to add a new device."""
        host = self.config_entry.data.get("host")
        port = self.config_entry.data.get("port")
        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
            if not entry:
                raise ValueError("Configuration entry not found")
            devices = entry.data.get("devices", [])
            
             # 检查是否有重复的 module_address 和 loop_address
            for exist_device in devices:
                if (exist_device["module_address"] == user_input["module_address"] and
                    exist_device["loop_address"] == user_input["loop_address"]):
                    # 发现重复，返回提示信息
                    return self.async_abort(
                        reason=f"已存在相同地址的设备({exist_device['type']}：{exist_device['name']})",
                    )
            
            device_data = {
                "type": self.device_type,
                "sub_device_type": self.sub_device_type,
                "name": user_input["name"],
                "module_address": user_input["module_address"],
                "loop_address": user_input["loop_address"],
                "host": host,
                "port": port
            }
            if self.device_type == 'light':
                device_data["gradient_time"] = user_input["gradient_time"]
            if self.device_type == '8button':
                device_data["selected_buttons"] = user_input["selected_buttons"]
                
            devices.append(device_data)

            self.hass.config_entries.async_update_entry(
                self.config_entry, data={"devices": devices, "host": host, "port": port}
            )
            await self._register_device_and_entity(device_data, device_type=self.device_type)
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            result = self.async_create_entry(title=f"{self.device_type.capitalize()} Added",data=device_data)
            return result

        # 添加设备表单，包含名称字段
        if self.device_type == 'light':
            data_schema = vol.Schema({
                vol.Required("name", default=""): str,
                vol.Required("module_address", default=""): int,
                vol.Required("loop_address", default=""): int,
                vol.Required("gradient_time"):int,
            })
        elif self.device_type == '8button':
            button_options = [str(i) for i in range(1, 9)]
            data_schema = vol.Schema({
                vol.Required("name", default=""): str,
                vol.Required("module_address", default=""): int,
                vol.Required("loop_address", default=""): int,
                vol.Required("selected_buttons"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=button_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            })
        else:
            data_schema = vol.Schema({
                vol.Required("name", default=""): str,
                vol.Required("module_address", default=""): int,
                vol.Required("loop_address", default=""): int,
            })
        return self.async_show_form(step_id="add", data_schema=data_schema)
    
    async def async_step_configure(self, user_input=None):
        """Step to configure an existing device."""
        devices = self._get_devices_of_type(self.device_type)
        
        # 如果没有设备可以配置，显示一条错误信息
        if not devices:
            return self.async_abort(reason="没有找到设备")

        if user_input is not None:
            # 用户选择了某个设备，进入配置流程
            self.selected_device = user_input["selected_device"]
            return await self.async_step_edit_device()

        # 显示设备选择菜单
        data_schema = vol.Schema({
            vol.Required("selected_device"): vol.In(
                {f"{device['name']}|{device['module_address']}|{device['loop_address']}": f"{device['name']} (模块地址：{device['module_address']}, 回路地址：{device['loop_address']})" for device in devices}
            )
        })

        return self.async_show_form(
            step_id="configure",
            data_schema=data_schema,
            description_placeholders={"desc": f"选择要配置的{self.device_type.capitalize()}设备"}
        )
        
    async def async_step_delete(self, user_input=None):
        """Step to delete an existing device."""
        # 获取当前类型的设备列表
        devices = self._get_devices_of_type(self.device_type)
        
        # 如果没有设备可删除，显示一条错误信息
        if not devices:
            return self.async_abort(reason="no_devices_to_delete")

        if user_input is not None:
            # 用户选择了某个设备，执行删除操作
            selected_device = user_input["selected_device"]
            await self._delete_device(selected_device)
            return self.async_create_entry(title="Device Deleted", data={})

        # 显示设备选择菜单
        data_schema = vol.Schema({
            vol.Required("selected_device"): vol.In(
                {f"{device['name']}|{device['module_address']}|{device['loop_address']}": f"{device['name']} (模块地址：{device['module_address']}, 回路地址：{device['loop_address']})" for device in devices}
            )
        })

        return self.async_show_form(
            step_id="delete",
            data_schema=data_schema,
            description_placeholders={"desc": f"选择要删除的{self.device_type.capitalize()}设备"}
        )

    async def async_step_edit_device(self, user_input=None):
        """Step to edit the selected device's configuration."""
        # 根据用户选择的设备名称找到设备数据
        selected_device_data = self._get_device_by_name(self.selected_device)
        
        if user_input is not None:
            # 更新设备配置数据
            updated_device_data = {
                "type": self.device_type,
                "sub_device_type": self.sub_device_type,
                "name": user_input["name"],
                "module_address": selected_device_data["module_address"],
                "loop_address": selected_device_data["loop_address"],
                "host": self.host,
                "port": self.port
            }
            if self.device_type == 'light':
                updated_device_data["gradient_time"] = user_input["gradient_time"]
            if self.device_type == '8button':
                updated_device_data["selected_buttons"] = user_input["selected_buttons"]
            # 更新设备数据到配置条目中
            await self._update_device_config(selected_device_data, updated_device_data)
            return self.async_create_entry(title="Device Configured", data={})

        # 预填充当前设备数据
        if self.device_type == "light":
            data_schema = vol.Schema({
                vol.Required("name", default=selected_device_data["name"]): str,
                # vol.Required("module_address", default=selected_device_data["module_address"]): str,
                # vol.Required("loop_address", default=selected_device_data["loop_address"]): str,
                vol.Required("gradient_time", default=selected_device_data["gradient_time"]):int,
            })
        elif self.device_type == '8button':
            button_options = [str(i) for i in range(1, 9)]
            data_schema = vol.Schema({
                vol.Required("name", default=selected_device_data["name"]): str,
                vol.Required("selected_buttons",default=selected_device_data.get("selected_buttons", [])): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=button_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            })
        else:
            data_schema = vol.Schema({
                vol.Required("name", default=selected_device_data["name"]): str,
                # vol.Required("module_address", default=selected_device_data["module_address"]): str,
                # vol.Required("loop_address", default=selected_device_data["loop_address"]): str,
            })
        description_placeholders = {
            "desc": f"配置{self.selected_device}",
            "module_address": selected_device_data["module_address"],
            "loop_address": selected_device_data["loop_address"]
        }
        return self.async_show_form(
            step_id="edit_device",
            data_schema=data_schema,
            description_placeholders=description_placeholders
        )
        
    async def _register_device_and_entity(self, device_data, device_type):
        """Register device in Home Assistant's device registry."""
        device_registry = dr.async_get(self.hass)
        if not isinstance(device_type, str) or device_type not in ["light", "switch","climate","floor_heating","fresh_air","8button","curtain","person_sensor","scene_switch"]:
            raise ValueError(f"Invalid device type provided: {device_type}")
        model_name = device_type.capitalize()
        device_registry.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers={(DOMAIN, f"{device_data['module_address']}_{device_data['loop_address']}")},
            manufacturer="Savant",
            name=device_data["name"],
            model=model_name,
            sw_version="1.0",
        )

    async def _update_device_config(self, old_device_data, new_device_data):
        """Update the configuration of an existing device."""
        entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
        if not entry:
            raise ValueError("Configuration entry not found")
        devices = entry.data.get("devices", [])
        for index, device in enumerate(devices):
            if (
                device["type"] == new_device_data["type"] and
                device["sub_device_type"] == new_device_data["sub_device_type"] and
                device["module_address"] == new_device_data["module_address"] and
                device["loop_address"] == new_device_data["loop_address"]
            ):
                updated_device = {**device, **new_device_data}
                updated_device["name"] = new_device_data.get("name", device["name"])
                if device["type"] == "light":
                    updated_device["gradient_time"] = new_device_data.get("gradient_time", device["gradient_time"])
                if device["type"] == "8button":
                    old_selected_buttons = old_device_data.get("selected_buttons", [])
                    new_selected_buttons = new_device_data.get("selected_buttons", old_selected_buttons)
                    buttons_to_add = set(new_selected_buttons) - set(old_selected_buttons)
                    buttons_to_remove = set(old_selected_buttons) - set(new_selected_buttons)
                    updated_device['selected_buttons'] = new_selected_buttons
                devices[index] = updated_device
                
        updated_data = {**entry.data, "devices": devices}
        self.hass.config_entries.async_update_entry(entry, data=updated_data)
        await self.hass.config_entries.async_reload(entry.entry_id)
        print("Updated device config")

    async def _delete_device(self, device_param):
        """Delete a device and its entities from the config entry and registries."""
        # 获取当前配置条目
        entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
        if not entry:
            raise ValueError("Configuration entry not found")

        # 获取设备列表
        devices = entry.data.get("devices", [])

        # 找到要删除的设备
        device_to_delete = None
        for device in devices:
            if f"{device['name']}|{device['module_address']}|{device['loop_address']}" == device_param:
                device_to_delete = device
                break

        if not device_to_delete:
            return

        # 从设备注册表中获取设备
        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)

        # 删除设备及其关联的实体
        device_id = None
        for device_entry in device_registry.devices.values():
            if (DOMAIN, f"{device_to_delete['module_address']}_{device_to_delete['loop_address']}") in device_entry.identifiers:
                device_id = device_entry.id
                # 删除实体
                for entity_entry in entity_registry.entities.values():
                    if entity_entry.device_id == device_id:
                        entity_registry.async_remove(entity_entry.entity_id)
                        break
                # 删除设备
                device_registry.async_remove_device(device_id)
                break

        # 更新配置条目中的设备列表（删除条目）
        updated_devices = [device for device in devices if f"{device['name']}|{device['module_address']}|{device['loop_address']}" != device_param]
        updated_data = {**entry.data, "devices": updated_devices}
        self.hass.config_entries.async_update_entry(entry, data=updated_data)
        
    def _get_devices_of_type(self, device_type):
        """Retrieve devices of a specific type from the config entry."""
        entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
        if not entry:
            return []
        # 从配置条目中获取设备列表
        devices = entry.data.get("devices", [])
        # 根据设备类型筛选设备
        filtered_devices = [device for device in devices if device["type"] == device_type]
        if self.sub_device_type is not None:
            filtered_devices = [device for device in devices if device["sub_device_type"] == self.sub_device_type]
        return filtered_devices
    
    def _get_device_by_name(self, device_param):
        """Retrieve a device by its name from the config entry."""
        entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
        if not entry:
            return None
        devices = entry.data.get("devices", [])
        for device in devices:
            if f"{device['name']}|{device['module_address']}|{device['loop_address']}" == device_param:
                return device
        return None
