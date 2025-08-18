import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class UserStore:
    """Simple JSON-backed store for farmer profiles and phone mappings.

    Schema:
    {
      "farmers": {
         "farmer_123": {
             "farmer_id": "farmer_123",
             "name": "Ramesh",
             "phone_e164": "+919876543210",
             "created_at": "...",
             "updated_at": "...",
             "profile": { ... last submitted AdvisoryRequest.profile ... }
         },
         ...
      },
      "phone_to_farmer": {
         "+919876543210": "farmer_123"
      }
    }
    """

    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {"farmers": {}, "phone_to_farmer": {}}
        self._load()

    def _load(self) -> None:
        if self.data_path.exists():
            try:
                self._data = json.loads(self.data_path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {"farmers": {}, "phone_to_farmer": {}}

    def _save(self) -> None:
        tmp = self.data_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.data_path)

    def get_by_farmer_id(self, farmer_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get("farmers", {}).get(farmer_id)

    def get_farmer_id_by_phone(self, phone_e164: str) -> Optional[str]:
        return self._data.get("phone_to_farmer", {}).get(phone_e164)

    def upsert_farmer(self, farmer_id: str, name: Optional[str] = None, phone_e164: Optional[str] = None) -> Dict[str, Any]:
        farmers = self._data.setdefault("farmers", {})
        now = datetime.now().isoformat()
        rec = farmers.get(farmer_id) or {"farmer_id": farmer_id, "created_at": now}
        if name:
            rec["name"] = name
        if phone_e164:
            rec["phone_e164"] = phone_e164
            self._data.setdefault("phone_to_farmer", {})[phone_e164] = farmer_id
        rec["updated_at"] = now
        farmers[farmer_id] = rec
        self._save()
        return rec

    def bind_phone(self, farmer_id: str, phone_e164: str) -> None:
        farmers = self._data.setdefault("farmers", {})
        rec = farmers.get(farmer_id)
        if not rec:
            rec = {"farmer_id": farmer_id, "created_at": datetime.now().isoformat()}
        rec["phone_e164"] = phone_e164
        rec["updated_at"] = datetime.now().isoformat()
        farmers[farmer_id] = rec
        self._data.setdefault("phone_to_farmer", {})[phone_e164] = farmer_id
        self._save()

    def save_profile(self, farmer_id: str, profile: Dict[str, Any]) -> None:
        farmers = self._data.setdefault("farmers", {})
        rec = farmers.get(farmer_id)
        if not rec:
            rec = {"farmer_id": farmer_id, "created_at": datetime.now().isoformat()}
        rec["profile"] = profile
        rec["updated_at"] = datetime.now().isoformat()
        farmers[farmer_id] = rec
        self._save()


