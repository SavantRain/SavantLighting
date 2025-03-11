# Savant Lighting Integration

Savant Lighting 是一个用于 Home Assistant 的智能家居集成，支持多种设备类型，包括灯光、开关、空调、风扇、窗帘、地暖、新风系统等。该集成通过 TCP 连接与设备进行通信，提供本地推送的物联网功能。

## 功能特性

- **灯光控制**：支持单色温、双色温（DALI-01、DALI-02）和 RGB 灯光的开关、亮度和色温调节。
- **开关控制**：支持普通开关、8 按钮开关、场景开关和带能量监控的开关。
- **气候控制**：支持空调、地暖和新风系统的模式和风速调节。
- **窗帘控制**：支持窗帘的开合和位置调节。
- **传感器监控**：支持电压、电流和功率传感器的能耗监控。

## 安装

1. 将 `custom_components/savant_lighting` 目录复制到 Home Assistant 的 `custom_components` 目录下。
2. 在 Home Assistant 的 `configuration.yaml` 文件中添加以下配置：
   ```yaml
   savant_lighting:
     host: "设备的IP地址"
     port: 6005
   ```
3. 重启 Home Assistant。

## 配置

通过 Home Assistant 的集成界面，添加 Savant Lighting 集成，并根据提示输入设备的 IP 地址和端口号。完成后，可以在设备列表中看到已添加的设备。

## 使用

- 在 Home Assistant 的仪表板中，可以看到所有已配置的 Savant 设备。
- 点击设备图标，可以进行开关、调节亮度、色温、风速等操作。
- 在自动化中，可以使用 Savant 设备的状态和属性来触发其他设备或服务。

## 支持的平台

- `light`：灯光
- `switch`：开关
- `climate`：气候设备（空调、地暖、新风）
- `fan`：风扇
- `cover`：窗帘
- `binary_sensor`：二进制传感器
- `sensor`：传感器

## 问题反馈

如有问题，请访问 [GitHub 问题追踪](https://github.com/SavantRain/SavantLightingk/issues) 提交反馈。

## 贡献

欢迎贡献代码和建议！请访问 [GitHub 仓库](https://github.com/SavantRain/SavantLighting) 了解更多信息。
