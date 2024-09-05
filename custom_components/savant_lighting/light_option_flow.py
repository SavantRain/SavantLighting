from homeassistant import config_entries
import voluptuous as vol
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from .const import DOMAIN

class SavantLightingLightOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow for Savant Lighting Lights."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.selected_light = None  # 用于存储用户选择的灯光

    async def async_step_init(self, user_input=None):
        """Manage the options for lights: add, configure, or delete lights."""
        if user_input is not None:
            action = user_input["action"]
            if action == "add_light":
                return await self.async_step_add_light()
            elif action == "configure_light":
                return await self.async_step_select_light_config()
            elif action == "delete_light":
                return await self.async_step_select_light_delete()

        # 显示初始操作菜单
        return self.async_show_menu(
            step_id="init",
            menu_options={
                "add_light": "添加灯光",
                "configure_light": "配置灯光",
                "delete_light": "删除灯光",
            },
            description_placeholders={"desc": "选择操作来管理灯光设备"},
        )

    async def async_step_add_light(self, user_input=None):
        """Step to add a new light."""
        if user_input is not None:
            # 确保 'lights' 已初始化
            lights = self.hass.data[DOMAIN].setdefault("lights", [])

            light_data = {
                "type": "light",
                "name": user_input["name"],
                "identifier": user_input["identifier"]
            }
            lights.append(light_data)

            # 注册设备和实体
            await self._register_device_and_entity(light_data, device_type="light")

            return self.async_create_entry(title="Light Added", data={})

        # 添加灯光表单
        data_schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("identifier"): str,
        })
        return self.async_show_form(step_id="add_light", data_schema=data_schema)

    async def async_step_select_light_config(self, user_input=None):
        """Step to select a light to configure."""
        lights = self.hass.data[DOMAIN].get("lights", [])
        if not lights:
            return self.async_abort(reason="no_lights")

        if user_input is not None:
            self.selected_light = user_input["light"]
            return await self.async_step_edit_light()

        # 显示选择灯光菜单
        return self.async_show_menu(
            step_id="select_light_config",
            menu_options={light["name"]: light["name"] for light in lights},
            description_placeholders={"desc": "选择要配置的灯光"},
        )

    async def async_step_select_light_delete(self, user_input=None):
        """Step to select a light to delete."""
        lights = self.hass.data[DOMAIN].get("lights", [])
        if not lights:
            return self.async_abort(reason="no_lights")

        if user_input is not None:
            self.selected_light = user_input["light"]
            return await self.async_step_delete_light()

        # 显示选择灯光菜单
        return self.async_show_menu(
            step_id="select_light_delete",
            menu_options={light["name"]: light["name"] for light in lights},
            description_placeholders={"desc": "选择要删除的灯光"},
        )

    async def async_step_edit_light(self, user_input=None):
        """Step to edit an existing light."""
        if user_input is not None:
            # 更新灯光配置
            for light in self.hass.data[DOMAIN].get("lights", []):
                if light["name"] == self.selected_light:
                    light["name"] = user_input["name"]
                    light["identifier"] = user_input["identifier"]
            return self.async_create_entry(title="Light Updated", data={})

        # 编辑灯光表单，预填充现有的灯光配置
        for light in self.hass.data[DOMAIN].get("lights", []):
            if light["name"] == self.selected_light:
                data_schema = vol.Schema({
                    vol.Required("name", default=light["name"]): str,
                    vol.Required("identifier", default=light["identifier"]): str,
                })
                return self.async_show_form(step_id="edit_light", data_schema=data_schema)

    async def async_step_delete_light(self, user_input=None):
        """Step to delete an existing light."""
        if user_input is not None:
            # 删除选中的灯光
            self.hass.data[DOMAIN]["lights"] = [
                light for light in self.hass.data[DOMAIN]["lights"] if light["name"] != self.selected_light
            ]
            return self.async_create_entry(title="Light Deleted", data={})

        # 删除确认表单
        return self.async_show_form(
            step_id="delete_light",
            data_schema=vol.Schema({}),
            description_placeholders={"light": self.selected_light}
        )

    async def _register_device_and_entity(self, entity_data, device_type):
        """Register device and entity in Home Assistant."""
        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)

        # 注册设备
        device = device_registry.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers={(DOMAIN, entity_data["identifier"])},
            manufacturer="Savant",
            name=entity_data["name"],
            model=device_type.capitalize(),
            sw_version="1.0",
        )

        # 注册实体
        entity_registry.async_get_or_create(
            domain=device_type,  # "light"
            config_entry=self.config_entry,
            device_id=device.id,
            unique_id=f"{entity_data['identifier']}_{device_type}",
            suggested_object_id=entity_data["name"]
        )
