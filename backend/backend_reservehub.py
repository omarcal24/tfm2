# backend_reservehub.py
"""
Módulo para conectar con la API de ReserveHub (mock interno)
y verificar disponibilidad de restaurantes

VERSIÓN CORREGIDA: Evita deadlock HTTP con modo interno
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, date, time
from pydantic import BaseModel


class AvailabilityQuery(BaseModel):
    """Query para consultar disponibilidad"""
    venue_id: str
    reservation_date: date
    reservation_time: time
    party_size: int
    shift_id: Optional[str] = None


class ReservationRequest(BaseModel):
    """Request para crear una reserva"""
    venue_id: str
    reservation_date: date
    reservation_time: time
    party_size: int
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None
    shift_id: Optional[str] = None


class ReserveHubClient:
    """Cliente para interactuar con ReserveHub API"""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000", 
        api_key: str = "demo-api-key",
        use_internal_logic: bool = False  # ✅ NUEVO: Evita auto-llamadas HTTP
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.use_internal_logic = use_internal_logic  # ✅ NUEVO
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def check_venue_exists(self, venue_name: str) -> Optional[Dict]:
        """
        Verifica si un restaurante existe en ReserveHub
        Retorna el venue si existe, None si no
        """
        # ✅ NUEVO: Si usa modo interno, ejecutar mock sin HTTP
        if self.use_internal_logic:
            return self._mock_venue_lookup(venue_name)
        
        # Código HTTP original
        try:
            response = requests.get(
                f"{self.base_url}/api/venues",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            
            venues = response.json()
            # Buscar por nombre (case insensitive)
            for venue in venues:
                if venue["name"].lower() == venue_name.lower():
                    return venue
            return None
            
        except Exception as e:
            print(f"Error verificando venue: {e}")
            return None
    
    def get_venue_shifts(self, venue_id: str) -> List[Dict]:
        """Obtiene los turnos disponibles de un restaurante"""
        # ✅ NUEVO: Modo interno
        if self.use_internal_logic:
            return self._mock_shifts(venue_id)
        
        try:
            response = requests.get(
                f"{self.base_url}/api/venues/{venue_id}/shifts",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error obteniendo turnos: {e}")
            return []
    
    def check_availability(
        self,
        venue_id: str,
        reservation_date: date,
        party_size: int,
        shift_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Consulta disponibilidad de un restaurante
        Retorna lista de slots disponibles
        """
        # ✅ NUEVO: Modo interno
        if self.use_internal_logic:
            return self._mock_availability(venue_id, reservation_date, party_size)
        
        try:
            query = {
                "venue_id": venue_id,
                "reservation_date": reservation_date.isoformat(),
                "party_size": party_size,
                "shift_id": shift_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/availability",
                headers=self.headers,
                json=query,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error consultando disponibilidad: {e}")
            return []
    
    def create_reservation(
        self,
        venue_id: str,
        reservation_date: date,
        reservation_time: time,
        party_size: int,
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str] = None,
        notes: Optional[str] = None,
        shift_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Crea una reserva en ReserveHub"""
        # ✅ NUEVO: Modo interno
        if self.use_internal_logic:
            return self._mock_reservation(
                venue_id, reservation_date, reservation_time,
                party_size, customer_name, customer_phone
            )
        
        try:
            reservation_data = {
                "venue_id": venue_id,
                "reservation_date": reservation_date.isoformat(),
                "reservation_time": reservation_time.isoformat(),
                "party_size": party_size,
                "name": customer_name,
                "phone": customer_phone,
                "email": customer_email,
                "notes": notes,
                "shift_id": shift_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/reservations",
                headers=self.headers,
                json=reservation_data,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error creando reserva: {e}")
            return None
    
    # ============================================
    # ✅ NUEVOS MÉTODOS MOCK (SIN HTTP)
    # ============================================
    
    def _mock_venue_lookup(self, venue_name: str) -> Optional[Dict]:
        """
        Simula búsqueda de venue sin HTTP.
        30% de restaurantes tienen integración con ReserveHub.
        """
        import random
        
        # Generar resultado determinista basado en nombre
        random.seed(venue_name)
        has_integration = random.random() < 0.30
        
        if not has_integration:
            return None
        
        # Generar venue_id único
        venue_id = f"venue-{abs(hash(venue_name)) % 1000}"
        
        return {
            "id": venue_id,
            "name": venue_name,
            "slug": venue_name.lower().replace(" ", "-"),
            "timezone": "Europe/Madrid",
            "currency": "EUR"
        }
    
    def _mock_shifts(self, venue_id: str) -> List[Dict]:
        """Simula turnos de restaurante"""
        return [
            {
                "id": f"{venue_id}-lunch",
                "name": "Comida",
                "start_time": "13:00:00",
                "end_time": "16:00:00",
                "venue_id": venue_id
            },
            {
                "id": f"{venue_id}-dinner",
                "name": "Cena",
                "start_time": "20:00:00",
                "end_time": "23:00:00",
                "venue_id": venue_id
            }
        ]
    
    def _mock_availability(
        self,
        venue_id: str,
        reservation_date: date,
        party_size: int
    ) -> List[Dict]:
        """Simula disponibilidad sin HTTP"""
        import random
        from datetime import time as dt_time
        
        # Generar resultado determinista
        random.seed(f"{venue_id}{reservation_date}")
        
        available_slots = []
        
        # Generar 3 slots entre 20:00 y 22:00
        for i in range(3):
            hour = 20 + (i // 2)
            minutes = 0 if i % 2 == 0 else 30
            
            slot_time = dt_time(hour, minutes)
            available = random.random() > 0.3  # 70% probabilidad
            
            available_slots.append({
                "slot_time": slot_time.isoformat(),
                "available": available,
                "shift_id": f"{venue_id}-dinner"
            })
        
        # Garantizar al menos 1 slot disponible
        if not any(s["available"] for s in available_slots):
            available_slots[0]["available"] = True
        
        return available_slots
    
    def _mock_reservation(
        self,
        venue_id: str,
        reservation_date: date,
        reservation_time: time,
        party_size: int,
        customer_name: str,
        customer_phone: str
    ) -> Dict:
        """Simula creación de reserva"""
        import uuid
        
        return {
            "id": str(uuid.uuid4()),
            "venue_id": venue_id,
            "reservation_date": reservation_date.isoformat(),
            "reservation_time": reservation_time.isoformat(),
            "party_size": party_size,
            "status": "confirmed",
            "name": customer_name,
            "phone": customer_phone,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }


# Función auxiliar para enriquecer resultados de Google Places con disponibilidad
def enrich_with_availability(
    google_places_results: List[Dict],
    reservation_date: date,
    party_size: int,
    client: ReserveHubClient = None
) -> List[Dict]:
    """
    Enriquece los resultados de Google Places con datos de disponibilidad
    de ReserveHub si el restaurante existe en el sistema
    """
    if client is None:
        # ✅ NUEVO: Usar modo interno por defecto para evitar deadlock
        client = ReserveHubClient(use_internal_logic=True)
    
    enriched_results = []
    
    for place in google_places_results:
        result = place.copy()
        result["has_reservehub"] = False
        result["available_slots"] = []
        result["venue_id"] = None
        
        # Verificar si el restaurante está en ReserveHub
        venue = client.check_venue_exists(place.get("name", ""))
        
        if venue:
            result["has_reservehub"] = True
            result["venue_id"] = venue["id"]
            
            # Consultar disponibilidad
            slots = client.check_availability(
                venue_id=venue["id"],
                reservation_date=reservation_date,
                party_size=party_size
            )
            
            # Filtrar solo slots disponibles
            available = [s for s in slots if s.get("available", False)]
            result["available_slots"] = available
            
            # Agregar el primer slot disponible como sugerencia
            if available:
                result["suggested_time"] = available[0]["slot_time"]
            else:
                result["suggested_time"] = None
        
        enriched_results.append(result)
    
    return enriched_results
