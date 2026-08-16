import json
from pathlib import Path

from system_controller.models.service import Service

class ServiceRepository:
    def __init__(self, path: str | Path = "database/service.json"):
        self.path = Path(path)
        self.services: dict[str, Service] = {}
        
        self._load()
        
    def _load(self) -> None:
        if not self.path.exists(): return
        
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                
        except(json.JSONDecodeError, OSError): return
        
        if not isinstance(data, dict): return
        
        self.services = {
            name: Service(name=name, unit=unit)
            for name, unit in data.items()
            if isinstance(name, str) and isinstance(unit, str)
        }
        
    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            service.name: service.unit
            for service in self.services.values()
        }
        
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
            
    def get(self, name: str) -> Service | None:
        return self.services.get(name)
    
    def get_all(self) -> list[Service]:
        return list(self.services.values())
    
    def add(self, service: Service) -> bool:
        if service.name in self.services: return False
        
        self.services[service.name] = service
        self._save()
        
        return True
    
    def remove(self, name: str) -> bool:
        if name not in self.services: return False
        
        del self.services[name]
        self._save()
        
        return True