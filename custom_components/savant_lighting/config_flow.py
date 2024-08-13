import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.data_entry_flow import FlowResult

from custom_components.savant_lighting import DOMAIN  # 常量，表示你的组件域名

# 定义用户需要提供的配置字段
CONFIG_SCHEMA = vol.Schema({
    vol.Required("ip_address"): str,
    vol.Optional("port", default=80): int,
    vol.Optional("username"): str,
    vol.Optional("password"): str,
})

class SavantLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理 Savant Light 集成的配置流程。"""

    VERSION = 1  # 配置流的版本号
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """第一次用户配置输入步骤。"""
        errors = {}

        if user_input is not None:
            # 在这里可以添加验证逻辑
            ip_address = user_input.get("ip_address")
            port = user_input.get("port")
            
            # 验证IP地址的有效性或尝试连接设备
            if not await self._test_connection(ip_address, port):
                errors["base"] = "cannot_connect"
            else:
                # 保存配置数据
                return self.async_create_entry(title="Savant Light", data=user_input)

        # 显示输入表单
        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
        )

    async def _test_connection(self, ip_address, port):
        """测试与设备的连接（此处仅为示例，可以根据需要调整）。"""
        try:
            # 进行实际的连接测试，如通过 HTTP 请求验证设备
            # session = async_get_clientsession(self.hass)
            # async with session.get(f"http://{ip_address}:{port}") as response:
            #     return response.status == 200
            
            # 简单示例，假设连接成功
            return True
        except Exception:
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """返回配置流的选项流处理器（可选）。"""
        return SavantLightOptionsFlowHandler(config_entry)


class SavantLightOptionsFlowHandler(config_entries.OptionsFlow):
    """处理集成的选项流（可选）。"""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """管理集成的选项配置。"""
        # 如果需要用户调整已经配置的参数，可以在这里实现
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """选项流用户输入处理。"""
        if user_input is not None:
            # 更新配置条目
            return self.async_create_entry(title="", data=user_input)

        # 显示选项表单
        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
        )
