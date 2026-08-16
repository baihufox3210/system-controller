from dataclasses import dataclass

from system_controller.adapters.systemd import SystemdAdapter
from system_controller.models.service import Service
from system_controller.repositories.repository import ServiceRepository


@dataclass(slots=True)
class ServiceOperationResult:
    success: bool
    service: Service | None = None
    message: str = ""


@dataclass(slots=True)
class ServiceStatus:
    service: Service
    active: str
    enabled: str


@dataclass(slots=True)
class ServiceLogs:
    service: Service
    content: str


class SystemService:
    def __init__(self, repository: ServiceRepository | None = None, systemd: SystemdAdapter | None = None):
        self.repository = repository or ServiceRepository()
        self.systemd = systemd or SystemdAdapter()

    def get(self, name: str) -> Service | None:
        return self.repository.get(name)

    def get_all(self) -> list[Service]:
        return self.repository.get_all()

    async def _execute(self, name: str, operation, success_message: str,) -> ServiceOperationResult:
        service = self.repository.get(name)

        if service is None:
            return ServiceOperationResult(
                success=False,
                message=f"Unknown service: {name}"
            )

        result = await operation(service.unit)

        if not result.success:
            return ServiceOperationResult(
                success=False,
                service=service,
                message=result.stderr.strip() or "Operation failed"
            )

        return ServiceOperationResult(
            success=True,
            service=service,
            message=success_message
        )

    async def start(self, name: str) -> ServiceOperationResult:
        return await self._execute(
            name,
            self.systemd.start,
            "Service started successfully."
        )

    async def stop(self, name: str) -> ServiceOperationResult:
        return await self._execute(
            name,
            self.systemd.stop,
            "Service stopped successfully."
        )

    async def restart(self, name: str) -> ServiceOperationResult:
        return await self._execute(
            name,
            self.systemd.restart,
            "Service restarted successfully."
        )

    async def enable(self, name: str) -> ServiceOperationResult:
        return await self._execute(
            name,
            self.systemd.enable,
            "Service enabled successfully."
        )

    async def disable(self, name: str) -> ServiceOperationResult:
        return await self._execute(
            name,
            self.systemd.disable,
            "Service disabled successfully."
        )

    async def status(self, name: str) -> ServiceStatus | None:
        service = self.repository.get(name)

        if service is None:
            return None

        active = await self.systemd.is_active(service.unit)
        enabled = await self.systemd.is_enabled(service.unit)

        return ServiceStatus(
            service=service,
            active=active.stdout.strip(),
            enabled=enabled.stdout.strip(),
        )

    async def logs(self, name: str, lines: int = 50) -> ServiceLogs | None:
        service = self.repository.get(name)

        if service is None: return None

        result = await self.systemd.logs(service.unit, lines)

        if not result.success:
            return ServiceLogs(
                service=service,
                content=result.stderr.strip() or "Failed to retrieve logs."
            )

        return ServiceLogs(
            service=service,
            content=result.stdout.strip()
        )

    def add(self, name: str, unit: str) -> bool:
        service = Service(
            name=name,
            unit=unit
        )

        return self.repository.add(service)

    def remove(self, name: str) -> bool:
        return self.repository.remove(name)