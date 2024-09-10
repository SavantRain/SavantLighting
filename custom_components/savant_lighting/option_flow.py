from homeassistant import config_entries
import voluptuous as vol
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .light import SavantLight
from .switch import SavantSwitch
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

    async def async_step_init(self, user_input=None):
        """Manage the options for devices: add or manage devices."""
        if user_input is not None:
            if user_input == "light_menu":
                self.device_type = "light"
                return await self.async_step_light_menu()
            elif user_input == "switch_menu":
                self.device_type = "switch"
                return await self.async_step_switch_menu()

        # 显示初始操作菜单，确保选项键与步骤方法一致
        # async_step_{step}  键名={step}方法名
        return self.async_show_menu(
            step_id="init",
            menu_options={
                "light_menu": "管理灯光",
                "switch_menu": "管理开关",
            },
            description_placeholders={"desc": "选择操作来管理子设备"},
        )
        
    async def async_step_light_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="light",user_input=user_input)

    async def async_step_switch_menu(self, user_input=None):
        return await self.async_step_device_menu(device_type="switch", user_input=user_input)
    
    async def async_step_device_menu(self, user_input=None, device_type=None):
        """Second level menu: Add, configure, or delete devices."""
        self.device_type = device_type
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
        if user_input is not None:
            # 确保 'devices' 已初始化
            devices = self.hass.data[DOMAIN].setdefault("devices", [])
            device_data = {
                "type": self.device_type,
                "name": user_input["name"],
                "module_address": user_input["module_address"],
                "loop_address": user_input["loop_address"],
                "host": self.host,
                "port": self.port
            }
            devices.append(device_data)

            # Update the config entry with the modified 'devices' list
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={"devices": devices}
            )

            # 注册设备和实体
            await self._register_device_and_entity(device_data, device_type=self.device_type)
            
            # Reload the config entry to add the new entity dynamically
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            
            return self.async_create_entry(title=f"{self.device_type.capitalize()} Added",data=device_data)

        # 添加设备表单，包含名称字段
        data_schema = vol.Schema({
            vol.Required("name", default="设备名称"): str,
            vol.Required("module_address", default="模块地址: 1-64"): str,
            vol.Required("loop_address", default="回路地址: 1-8"): str,
        })
        return self.async_show_form(step_id="add", data_schema=data_schema)
    
    async def async_step_configure(self, user_input=None):
        """Step to configure an existing device."""
        devices = self._get_devices_of_type(self.device_type)
        
        # 如果没有设备可以配置，显示一条错误信息
        if not devices:
            return self.async_abort(reason="no_devices_to_configure")

        if user_input is not None:
            # 用户选择了某个设备，进入配置流程
            self.selected_device = user_input["selected_device"]
            return await self.async_step_edit_device()

        # 显示设备选择菜单
        data_schema = vol.Schema({
            vol.Required("selected_device"): vol.In(
                {device["name"]: f"{device['name']} ({device['module_address']}, {device['loop_address']})" for device in devices}
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
                {device["name"]: f"{device['name']} ({device['module_address']}, {device['loop_address']})" for device in devices}
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
                "name": user_input["name"],
                "module_address": user_input["module_address"],
                "loop_address": user_input["loop_address"],
                "host": self.host,
                "port": self.port
            }
            
            # 更新设备数据到配置条目中
            await self._update_device_config(selected_device_data, updated_device_data)
            
            return self.async_create_entry(title="Device Configured", data={})

        # 预填充当前设备数据
        data_schema = vol.Schema({
            vol.Required("name", default=selected_device_data["name"]): str,
            vol.Required("module_address", default=selected_device_data["module_address"]): str,
            vol.Required("loop_address", default=selected_device_data["loop_address"]): str,
        })

        return self.async_show_form(
            step_id="edit_device",
            data_schema=data_schema,
            description_placeholders={"desc": f"配置{self.selected_device}"}
        )
        
    async def _register_device_and_entity(self, device_data, device_type):
        """Register device in Home Assistant's device registry."""
        # 获取设备注册表
        device_registry = dr.async_get(self.hass)

        # 确保 device_type 是有效的字符串
        if not isinstance(device_type, str) or device_type not in ["light", "switch"]:
            raise ValueError(f"Invalid device type provided: {device_type}")

        # 格式化设备的 model 名称
        model_name = device_type.capitalize()

        # 创建或获取设备
        device_registry.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers={(DOMAIN, f"{device_data['module_address']}_{device_data['loop_address']}")},
            manufacturer="Savant",
            name=device_data["name"],  # 设备名称
            model=model_name,
            sw_version="1.0",
        )

    async def _update_device_config(self, old_device_data, new_device_data):
        """Update the configuration of an existing device."""
        # 获取当前配置条目
        entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
        if not entry:
            raise ValueError("Configuration entry not found")

        # 从配置条目中获取设备列表
        devices = entry.data.get("devices", [])

        # 查找并更新目标设备的配置
        updated_devices = []
        for device in devices:
            if device["name"] == old_device_data["name"] and device["module_address"] == old_device_data["module_address"]:
                # 用新的设备数据替换旧的
                updated_devices.append(new_device_data)
            else:
                # 保持其他设备数据不变
                updated_devices.append(device)
        
        # 更新配置条目中的设备列表
        updated_data = {**entry.data, "devices": updated_devices}
        
        # 将更新后的数据持久化到配置条目中
        self.hass.config_entries.async_update_entry(entry, data=updated_data)

    async def _delete_device(self, device_name):
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
            if device["name"] == device_name:
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
        updated_devices = [device for device in devices if device["name"] != device_name]
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
            
        return filtered_devices
    
    def _get_device_by_name(self, device_name):
        """Retrieve a device by its name from the config entry."""
        # 获取当前配置条目
        entry = self.hass.config_entries.async_get_entry(self.config_entry.entry_id)
        if not entry:
            return None

        # 从配置条目中获取设备列表
        devices = entry.data.get("devices", [])

        # 根据名称查找设备
        for device in devices:
            if device["name"] == device_name:
                return device

        # 如果找不到设备，返回 None
        return None
    