import io
import discord
from discord import app_commands
from discord.ext import commands

from system_controller.services.system_service import SystemService


class Services(commands.GroupCog, group_name="service"):
    def __init__(self, bot: commands.Bot, system_service: SystemService = None):
        self.bot = bot
        self.system_service = system_service or SystemService()
        super().__init__()

    async def service_autocomplete(self, interaction: discord.Interaction, current: str):
        services = (
            self.system_service.get_all()
            if hasattr(self.system_service, "get_all") else []
        )
        
        choices = []

        for service in services:
            name = getattr(service, "name", None) or service.get("name")
            unit = getattr(service, "unit", "") or service.get("unit", "")

            if current.lower() in name.lower() or current.lower() in unit.lower():
                choices.append(app_commands.Choice(name=f"{name} ({unit})", value=name))

        return choices[:25]

    # --- 服務狀態控制指令 ---

    @app_commands.command(name="start", description="啟動系統服務")
    @app_commands.describe(service="要啟動的服務名稱")
    @app_commands.autocomplete(service=service_autocomplete)
    async def start(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        result = await self.system_service.start(service)

        if result.success:
            await interaction.followup.send(f"`{service}` 啟動成功！\n```\n{result.message}\n```")
        else:
            await interaction.followup.send(f"`{service}` 啟動失敗：\n```\n{result.message}\n```")

    @app_commands.command(name="stop", description="關閉系統服務")
    @app_commands.describe(service="要關閉的服務名稱")
    @app_commands.autocomplete(service=service_autocomplete)
    async def stop(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        result = await self.system_service.stop(service)

        if result.success:
            await interaction.followup.send(f"`{service}` 關閉成功！\n```\n{result.message}\n```")
        else:
            await interaction.followup.send(f"`{service}` 關閉失敗：\n```\n{result.message}\n```")

    @app_commands.command(name="restart", description="重啟系統服務")
    @app_commands.describe(service="要重啟的服務名稱")
    @app_commands.autocomplete(service=service_autocomplete)
    async def restart(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        result = await self.system_service.restart(service)

        if result.success:
            await interaction.followup.send(f"`{service}` 重啟成功！\n```\n{result.message}\n```")
        else:
            await interaction.followup.send(f"`{service}` 重啟失敗：\n```\n{result.message}\n```")

    @app_commands.command(name="enable", description="設定服務開機自動啟動")
    @app_commands.describe(service="要設定的服務名稱")
    @app_commands.autocomplete(service=service_autocomplete)
    async def enable(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        result = await self.system_service.enable(service)

        if result.success:
            await interaction.followup.send(f"`{service}` 已設定為開機自動啟動！")
        else:
            await interaction.followup.send(f"設定開機自動啟動失敗：\n```\n{result.message}\n```")

    @app_commands.command(name="disable", description="取消服務開機自動啟動")
    @app_commands.describe(service="要取消的服務名稱")
    @app_commands.autocomplete(service=service_autocomplete)
    async def disable(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        result = await self.system_service.disable(service)

        if result.success:
            await interaction.followup.send(f"`{service}` 已取消開機自動啟動！")
        else:
            await interaction.followup.send(f"取消開機自動啟動失敗：\n```\n{result.message}\n```")

    # --- 查詢與資訊指令 ---

    @app_commands.command(name="status", description="查詢服務狀態")
    @app_commands.describe(service="要查詢的服務名稱")
    @app_commands.autocomplete(service=service_autocomplete)
    async def status(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        status_info = await self.system_service.status(service)

        if status_info is not None:
            await interaction.followup.send(
                f"📊 **服務 `{service}` 狀態：**\n"
                f"• Active State: `{status_info.active}`\n"
                f"• Enabled State: `{status_info.enabled}`\n"
                f"• Unit: `{status_info.service.unit}`"
            )
        else:
            await interaction.followup.send(f"找不到服務 `{service}` 或無法讀取狀態。")

    @app_commands.command(name="logs", description="查詢服務日誌")
    @app_commands.describe(service="要調閱的服務名稱", lines="讀取行數 (預設 50 行)")
    @app_commands.autocomplete(service=service_autocomplete)
    async def logs(self, interaction: discord.Interaction, service: str, lines: int = 50):
        await interaction.response.defer(ephemeral=False)
        log_info = await self.system_service.logs(service, lines=lines)

        if log_info is None:
            await interaction.followup.send(f"找不到服務 `{service}`。")
            return

        content = log_info.content
        if len(content) <= 1800:
            await interaction.followup.send(f"服務 `{service}` 日誌 ({lines} 行)：\n```\n{content}\n```")
        else:
            log_file = discord.File(
                fp=io.BytesIO(content.encode("utf-8")), filename=f"{service}_logs.txt",
            )
            await interaction.followup.send(
                f"服務 `{service}` 的日誌過長，已改以文字檔傳送：", file=log_file,
            )

    @app_commands.command(name="list", description="列出所有服務")
    async def service_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        services = self.system_service.get_all()

        if not services:
            await interaction.followup.send("目前尚未註冊任何服務。請使用 `/service add` 新增。")
            return

        formatted_list = [f"• **{s.name}**: `{s.unit}`" for s in services]
        await interaction.followup.send(f"**可管理服務清單：**\n" + "\n".join(formatted_list))

    # --- 管理維護指令 ---

    @app_commands.command(name="add", description="新增系統服務")
    @app_commands.describe(name="服務名稱", unit="systemd unit 檔名")
    async def add(self, interaction: discord.Interaction, name: str, unit: str):
        await interaction.response.defer(ephemeral=False)
        success = self.system_service.add(name, unit)

        if success:
            await interaction.followup.send(f"成功新增服務：`{name}` (`{unit}`)")
        else:
            await interaction.followup.send(f"新增失敗：服務名稱 `{name}` 已存在。")

    @app_commands.command(name="remove", description="移除已註冊的服務")
    @app_commands.describe(service="要移除的服務名稱")
    @app_commands.autocomplete(service=service_autocomplete)
    async def remove(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        success = self.system_service.remove(service)

        if success:
            await interaction.followup.send(f"🗑️ 已成功移除服務：`{service}`")
        else:
            await interaction.followup.send(f"移除失敗：找不到服務 `{service}`。")


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))