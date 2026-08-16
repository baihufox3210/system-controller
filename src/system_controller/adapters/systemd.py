import asyncio
from dataclasses import dataclass

@dataclass(slots=True)
class CommandResult:
    code: int
    stdout: str
    stderr: str
    
    @property
    def success(self) -> bool:
        return self.code == 0
    
class SystemdAdapter:
    def __init__(self, sudo_path: str = "/usr/bin/sudo", systemctl_path: str = "/usr/bin/systemctl"):
        self.sudo_path = sudo_path
        self.systemctl_path = systemctl_path
        
    async def _run(self, *args: str, timeout: float = 15) -> CommandResult:
        try:
            process = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            
            return CommandResult(
                code=process.returncode or 0,
                stdout=stdout.decode(errors="replace"),
                stderr=stderr.decode(errors="replace")
            )
        
        except asyncio.TimeoutError:
            return CommandResult(
                code=-1, stdout="", stderr="Command timed out."
            )
        
        except OSError as e:
            return CommandResult(
                code=-1, stdout="", stderr=str(e)
            )
            
    async def _systemctl(self, action: str, unit: str, *, timeout: float = 15) -> CommandResult:
        return await self._run(
            self.sudo_path, "-n", self.systemctl_path, action, unit, timeout=timeout
        )
    
    async def start(self, unit: str) -> CommandResult:
        return await self._systemctl("start", unit)

    async def stop(self, unit: str) -> CommandResult:
        return await self._systemctl("stop", unit)

    async def restart(self, unit: str) -> CommandResult:
        return await self._systemctl("restart", unit)

    async def enable(self, unit: str) -> CommandResult:
        return await self._systemctl("enable", unit)

    async def disable(self, unit: str) -> CommandResult:
        return await self._systemctl("disable", unit)

    async def is_active(self, unit: str) -> CommandResult:
        return await self._systemctl("is-active", unit)

    async def is_enabled(self, unit: str) -> CommandResult:
        return await self._systemctl("is-enabled", unit)
    
    async def logs(self, unit: str, lines: int = 50) -> CommandResult:
        return await self._run(
            "journalctl", "-u", unit, "-n", str(lines), "--no-pager",timeout=10
        )