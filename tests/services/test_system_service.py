from unittest.mock import AsyncMock, Mock

import pytest

from system_controller.adapters.systemd import CommandResult
from system_controller.models.service import Service
from system_controller.services.system_service import (
    ServiceLogs,
    ServiceOperationResult,
    ServiceStatus,
    SystemService,
)


@pytest.fixture
def repository():
    return Mock()


@pytest.fixture
def systemd():
    return Mock()


@pytest.fixture
def service():
    return Service(
        name="test",
        unit="system-controller-test.service",
    )


@pytest.fixture
def system_service(repository, systemd):
    return SystemService(
        repository=repository,
        systemd=systemd,
    )


def command_result(
    *,
    code: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> CommandResult:
    return CommandResult(
        code=code,
        stdout=stdout,
        stderr=stderr,
    )


# ----------------------------------------------------------------------
# get
# ----------------------------------------------------------------------


def test_get_returns_registered_service(
    system_service,
    repository,
    service,
):
    repository.get.return_value = service

    result = system_service.get("test")

    assert result is service
    repository.get.assert_called_once_with("test")


def test_get_returns_none_for_unknown_service(
    system_service,
    repository,
):
    repository.get.return_value = None

    result = system_service.get("unknown")

    assert result is None
    repository.get.assert_called_once_with("unknown")


# ----------------------------------------------------------------------
# get_all
# ----------------------------------------------------------------------


def test_get_all_returns_registered_services(
    system_service,
    repository,
    service,
):
    services = [
        service,
        Service(
            name="another",
            unit="another.service",
        ),
    ]

    repository.get_all.return_value = services

    result = system_service.get_all()

    assert result == services
    repository.get_all.assert_called_once_with()


# ----------------------------------------------------------------------
# start
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_success(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service
    systemd.start = AsyncMock(
        return_value=command_result()
    )

    result = await system_service.start("test")

    assert isinstance(result, ServiceOperationResult)
    assert result.success is True
    assert result.service is service
    assert result.message == "Service started successfully."

    systemd.start.assert_awaited_once_with(
        "system-controller-test.service"
    )


@pytest.mark.asyncio
async def test_start_unknown_service(
    system_service,
    repository,
    systemd,
):
    repository.get.return_value = None

    result = await system_service.start("unknown")

    assert result.success is False
    assert result.service is None
    assert result.message == "Unknown service: unknown"

    systemd.start.assert_not_called()


@pytest.mark.asyncio
async def test_start_failure(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service

    systemd.start = AsyncMock(
        return_value=command_result(
            code=1,
            stderr="Failed to start service.",
        )
    )

    result = await system_service.start("test")

    assert result.success is False
    assert result.service is service
    assert result.message == "Failed to start service."

    systemd.start.assert_awaited_once_with(
        "system-controller-test.service"
    )


# ----------------------------------------------------------------------
# stop
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_success(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service
    systemd.stop = AsyncMock(
        return_value=command_result()
    )

    result = await system_service.stop("test")

    assert result.success is True
    assert result.service is service
    assert result.message == "Service stopped successfully."

    systemd.stop.assert_awaited_once_with(
        service.unit
    )


# ----------------------------------------------------------------------
# restart
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_restart_success(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service
    systemd.restart = AsyncMock(
        return_value=command_result()
    )

    result = await system_service.restart("test")

    assert result.success is True
    assert result.service is service
    assert result.message == "Service restarted successfully."

    systemd.restart.assert_awaited_once_with(
        service.unit
    )


# ----------------------------------------------------------------------
# enable
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enable_success(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service
    systemd.enable = AsyncMock(
        return_value=command_result()
    )

    result = await system_service.enable("test")

    assert result.success is True
    assert result.service is service
    assert result.message == "Service enabled successfully."

    systemd.enable.assert_awaited_once_with(
        service.unit
    )


# ----------------------------------------------------------------------
# disable
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_disable_success(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service
    systemd.disable = AsyncMock(
        return_value=command_result()
    )

    result = await system_service.disable("test")

    assert result.success is True
    assert result.service is service
    assert result.message == "Service disabled successfully."

    systemd.disable.assert_awaited_once_with(
        service.unit
    )


# ----------------------------------------------------------------------
# status
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_status_success(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service

    systemd.is_active = AsyncMock(
        return_value=command_result(
            stdout="active\n"
        )
    )

    systemd.is_enabled = AsyncMock(
        return_value=command_result(
            stdout="enabled\n"
        )
    )

    result = await system_service.status("test")

    assert isinstance(result, ServiceStatus)
    assert result.service is service
    assert result.active == "active"
    assert result.enabled == "enabled"

    systemd.is_active.assert_awaited_once_with(
        service.unit
    )

    systemd.is_enabled.assert_awaited_once_with(
        service.unit
    )


@pytest.mark.asyncio
async def test_status_unknown_service(
    system_service,
    repository,
    systemd,
):
    repository.get.return_value = None

    result = await system_service.status("unknown")

    assert result is None

    systemd.is_active.assert_not_called()
    systemd.is_enabled.assert_not_called()


# ----------------------------------------------------------------------
# logs
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logs_success(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service

    systemd.logs = AsyncMock(
        return_value=command_result(
            stdout="line 1\nline 2\nline 3\n"
        )
    )

    result = await system_service.logs("test", lines=50)

    assert isinstance(result, ServiceLogs)
    assert result.service is service
    assert result.content == "line 1\nline 2\nline 3"

    systemd.logs.assert_awaited_once_with(
        service.unit,
        50,
    )


@pytest.mark.asyncio
async def test_logs_failure(
    system_service,
    repository,
    systemd,
    service,
):
    repository.get.return_value = service

    systemd.logs = AsyncMock(
        return_value=command_result(
            code=1,
            stderr="journalctl failed",
        )
    )

    result = await system_service.logs("test")

    assert isinstance(result, ServiceLogs)
    assert result.service is service
    assert result.content == "journalctl failed"


@pytest.mark.asyncio
async def test_logs_unknown_service(
    system_service,
    repository,
    systemd,
):
    repository.get.return_value = None

    result = await system_service.logs("unknown")

    assert result is None

    systemd.logs.assert_not_called()


# ----------------------------------------------------------------------
# add
# ----------------------------------------------------------------------


def test_add_service(
    system_service,
    repository,
):
    repository.add.return_value = True

    result = system_service.add(
        name="test",
        unit="system-controller-test.service",
    )

    assert result is True

    repository.add.assert_called_once()

    added_service = repository.add.call_args.args[0]

    assert isinstance(added_service, Service)
    assert added_service.name == "test"
    assert added_service.unit == "system-controller-test.service"


# ----------------------------------------------------------------------
# remove
# ----------------------------------------------------------------------


def test_remove_service(
    system_service,
    repository,
):
    repository.remove.return_value = True

    result = system_service.remove("test")

    assert result is True

    repository.remove.assert_called_once_with("test")