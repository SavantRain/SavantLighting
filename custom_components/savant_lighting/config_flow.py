from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from .const import DOMAIN
from .option_flow import SavantLightingOptionsFlowHandler


class SavantLightingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Savant Lighting."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user sets up the gateway."""
        if user_input is not None:
            # 初始化 hass.data[DOMAIN] 以存储网关配置
            if DOMAIN not in self.hass.data:
                self.hass.data[DOMAIN] = {}

            # 保存网关配置
            self.hass.data[DOMAIN]["host"] = user_input["host"]
            self.hass.data[DOMAIN]["port"] = user_input["port"]

            # 创建网关条目
            return self.async_create_entry(title="Savant Gateway", data={
                "type": "gateway",
                "name": "Savant Gateway",
                "host": user_input["host"],
                "port": user_input["port"],
                "devices":[]
            })

        # 定义表单数据结构
        data_schema = vol.Schema({
            vol.Required("host"): str,
            vol.Required("port", default=6005): int,
        })

        # 显示网关配置表单
        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler for this config entry."""
        return SavantLightingOptionsFlowHandler(config_entry)