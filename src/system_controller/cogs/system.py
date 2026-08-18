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
        services = self.system_service.get_all() if hasattr(self.system_service, "get_all") else []
        choices = []
        
        for service in services:
            name = getattr(service, "name", None) or service.get("name")
            unit = getattr(service, "unit", "") or service.get("unit", "")
            
            if current.lower() in name.lower() or current.lower() in unit.lower():
                choices.append(app_commands.Choice(name=f"{name} {unit}", value=name))
                
        return choices[:25]
    
    @app_commands.command(name="start", description="啟動系統服務")
    @app_commands.describe(service="要啟動的服務")
    @app_commands.autocomplete(service=service_autocomplete)
    async def start(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        
        result = await self.system_service.start(service)
        if getattr(result, "success", False):
            await interaction.followup.send(f"{service} 啟動成功！\n```\n{result.message}\n```")
            
        else:
            msg = getattr(result, "message", result)
            await interaction.followup.send(f"{service} 啟動失敗：\n```\n{msg}\n```")
            
    @app_commands.command(name="status", description="查詢服務狀態")
    @app_commands.describe(service="要查詢的服務")
    @app_commands.autocomplete(service=service_autocomplete)
    async def status(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        
        result = await self.system_service.status(service)
        if getattr(result, "success", False):
            await interaction.followup.send(f"服務 `{service}` 狀態：\n```\n{result.message}\n```")
            
        else:
            msg = getattr(result, "message", result)
            await interaction.followup.send(f"無法取得服務 `{service}` 狀態：\n```\n{msg}\n```")
            
    @app_commands.command(name="list", description="列出所有服務")
    async def service_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        services = self.system_service.get_all() if hasattr(self.system_service, "get_all") else []
        if not services:
            await interaction.followup.send("目前尚未註冊任何服務。請使用 `/service add` 新增。")
            return
        
        formatted_list = []
        for service in services:
            name = getattr(service, "name", None) or service.get("name")
            unit = getattr(service, "unit", "") or service.get("unit", "")
            
            formatted_list.append(f"• **{name}**: `{unit}`")
            
        await interaction.followup.send(f"**可管理服務清單：**\n" + "\n".join(formatted_list))
        
    @app_commands.command(name="add", description="新增系統服務")
    @app_commands.describe(name="服務名稱", unit="systemd unit 檔名")
    async def add(self, interaction: discord.Interaction, name: str, unit: str):
        await interaction.response.defer(ephemeral=False)
        
        success = self.system_service.add(name, unit) if hasattr(self.system_service, "add") else False
        
        if success: await interaction.followup.send(f"成功新增服務：`{name}` (`{unit}`)")
        else: await interaction.followup.send(f"新增失敗：服務名稱 `{name}` 已存在或無法新增。")
        
    @app_commands.command(name="remove", description="移除已註冊的服務")
    @app_commands.describe(service="要移除的服務名稱")
    @app_commands.autocomplete(service=service_autocomplete)
    async def remove(self, interaction: discord.Interaction, service: str):
        await interaction.response.defer(ephemeral=False)
        
        success = self.system_service.remove(service) if hasattr(self.system_service, "remove") else False
        
        if success: await interaction.followup.send(f"已成功移除服務：`{service}`")
        else: await interaction.followup.send(f"移除失敗：找不到服務 `{service}`。")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))