from dataclasses import dataclass

from system_controller.adapters.systemd import CommandResult, SystemdAdapter
from system_controller.models.service import Service
from system_controller.repositories.repository import ServiceRepository

@dataclass(slots=True)
class ServiceOperationResult:
    success: bool
    service: Service | None = None
    result: CommandResult | None = None
    message: str = ""
    
class SystemService:
    def __init__(self, repository: ServiceRepository | None = None, systemd: SystemdAdapter | None = None):
        self.repository = repository or ServiceRepository()
        self.systemd = systemd or SystemdAdapter()
        
    def get(self, name: str) -> Service | None:
        return self.repository.get(name)
    
    def get_all(self) -> list[Service]:
        return self.repository.get_all()
    
    async def _execute(self, name: str, operation) -> ServiceOperationResult:
        service = self.repository.get(name)
        
        if service is None:
            return ServiceOperationResult(
                success=False, message=f"Unknown service: {name}"
            )
            
        result = await operation(service.unit)
        
        if not result.success:
            return ServiceOperationResult(
                success=False, service=service, result=result,
                message=result.stderr.strip() or "Operation failed"
            )
        
        return ServiceOperationResult(
            success=True, service=service, result=result
        )
        
    async def start(self, name: str):
        return await self._execute(name, self.systemd.start)
    
    async def stop(self, name: str):
        return await self._execute(name, self.systemd.stop)

    async def restart(self, name: str):
        return await self._execute(name, self.systemd.restart)

    async def enable(self, name: str):
        return await self._execute(name, self.systemd.enable)

    async def disable(self, name: str):
        return await self._execute(name, self.systemd.disable)
    
    async def status(self, name: str):
        service = self.repository.get(name)
        
        if service is None:
            return ServiceOperationResult(
                success=False, message=f"Unknown service: {name}"
            )
            
        active = await self.systemd.is_active(service.unit)
        enable = await self.systemd.is_enabled(service.unit)
        
        return ServiceOperationResult(
            success=True, service=service, result=active,
            message=enable.stdout.strip()
        )
        
    async def logs(self, name: str, lines: int = 50):
        service = self.repository.get(name)
        
        if service is None:
            return ServiceOperationResult(
                success=False, message=f"Unknown service: {name}"
            )
            
        result = await self.systemd.logs(service.unit, lines)
        
        return ServiceOperationResult(
            success=result.success, service=service, result=result, message=result.stderr.strip()
        )
        
    def add(self, name: str, unit: str) -> bool:
        return self.repository.add(
            Service(name=name, unit=unit)
        )
        
    def remove(self, name: str) -> bool:
        return self.repository.remove(name)