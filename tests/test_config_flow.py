import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from custom_components.savant_lighting.config_flow import SavantLightConfigFlow
from light.const import DOMAIN

@pytest.fixture
def hass():
    return HomeAssistant()

async def test_show_form(hass):
    """测试配置流程的初始表单显示。"""
    flow = MokaLightConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user(user_input=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

async def test_create_entry(hass):
    """测试配置流程的创建配置项。"""
    flow = MokaLightConfigFlow()
    flow.hass = hass

    user_input = {
        "ip_address": "192.168.1.100",
        "port": 80,
    }
    result = await flow.async_step_user(user_input=user_input)

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "Moka Light"
    assert result["data"] == user_input
