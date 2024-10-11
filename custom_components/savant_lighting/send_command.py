import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

async def send_tcp_command(host, port, data):
    """通过TCP发送命令并处理异常"""
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
        writer.write(data)
        await asyncio.wait_for(writer.drain(), timeout=5)

        # 读取响应，1024 表示最大读取字节数
        response = await asyncio.wait_for(reader.read(1024), timeout=5)
        writer.close()
        await writer.wait_closed()

        return response, True  # 返回响应和在线状态
    except asyncio.TimeoutError:
        _LOGGER.error(f"连接 {host}:{port} 超时")
        return None, False  # 设备超时，标记为离线
    except (ConnectionRefusedError, OSError) as e:
        _LOGGER.error(f"发送数据到 {host}:{port} 时出错 - {e}")
        return None, False  # 设备连接出错，标记为离线
    except Exception as e:
        _LOGGER.error(f"未知错误: {e}")
        return None, False  # 处理任何其他异常，标记为离线
    finally:
        if 'writer' in locals() and not writer.is_closing():
            writer.close()
            await writer.wait_closed()