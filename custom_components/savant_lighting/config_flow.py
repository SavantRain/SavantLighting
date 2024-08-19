"""Config flow for Savant Lighting integration."""
from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class SavantLightingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Savant Lighting."""

    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user selects the device type."""
        if user_input is not None:
            # Store the selected type and proceed to the next step
            self.selected_type = user_input["device_type"]
            if self.selected_type == "light":
                return await self.async_step_light_config()
            elif self.selected_type == "switch":
                return await self.async_step_switch_config()
            elif self.selected_type == "gateway":
                return await self.async_step_gateway_config()
            
        # Define the schema for the first step
        data_schema = vol.Schema({
            vol.Required("device_type", default="light"): vol.In(["light", "switch"]),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema
        )

    async def async_step_gateway_config(self, user_input=None):
        """Handle the configuration for a gateway device."""
        if user_input is not None:
            # User has completed the gateway config step, create the entry
            return self.async_create_entry(title=user_input["name"], data={
                "type": "gateway",
                "name": user_input["name"],
                "host": user_input["host"],
                "port": user_input["port"]
            })

        # Define the schema for the gateway configuration step
        data_schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("host"): str,
            vol.Required("port"): int,
        })

        return self.async_show_form(
            step_id="gateway_config",
            data_schema=data_schema
        )

    async def async_step_light_config(self, user_input=None):
        """Handle the configuration for a light device."""
        if user_input is not None:
            # User has completed the light config step, create the entry
            return self.async_create_entry(title=user_input["name"], data={
                "type": "light",
                "name": user_input["name"],
                "host": user_input["host"],
                "port": user_input["port"]
            })

        # Define the schema for the light configuration step
        data_schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("host"): str,
            vol.Required("port"): int,
        })

        return self.async_show_form(
            step_id="light_config",
            data_schema=data_schema
        )

    async def async_step_switch_config(self, user_input=None):
        """Handle the configuration for a switch device."""
        if user_input is not None:
            # User has completed the switch config step, create the entry
            return self.async_create_entry(title=user_input["name"], data={
                "type": "switch",
                "name": user_input["name"],
                "host": user_input["host"],
                "port": user_input["port"],
                "identifier": user_input["identifier"]
            })

        # Define the schema for the switch configuration step
        data_schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required("host"): str,
            vol.Required("port"): int,
            vol.Required("identifier"): int,
        })

        return self.async_show_form(
            step_id="switch_config",
            data_schema=data_schema
        )
