from __future__ import annotations
import asyncio
import logging
from typing import Optional
from .const import TIMEOUT, RECV_EOL, SEND_EOL

_LOGGER = logging.getLogger(__name__)

class AudacProtocolError(Exception):
    pass

class AudacHub:
    def __init__(self, host: str, port: int, zones: int, device_id: str, source_id: str):
        self.host = host
        self.port = port
        self.zones = zones
        self.device_id = device_id   # ex: X001 (fixe)
        self.source_id = source_id   # ex: HA (≤ 4 chars)
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()

    async def async_connect(self):
        _LOGGER.info("Connecting to AUDAC MTX at %s:%s", self.host, self.port)
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), TIMEOUT
        )

    async def async_close(self):
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as exc:
                _LOGGER.debug("Close error: %s", exc)
        self._reader = self._writer = None

    def _build(self, command: str, *args: str) -> str:
        # #|{dest}|{src}|{cmd}|{args...}|U|<CR><LF>
        parts = ["#", self.device_id, self.source_id, command]
        parts += [f"{a}" for a in args]
        return "|".join(parts) + "|U|" + SEND_EOL

    async def _send_recv(self, payload: str) -> str:
        if not self._writer or not self._reader:
            await self.async_connect()
        async with self._lock:
            _LOGGER.debug("TX: %s", payload.strip())
            self._writer.write(payload.encode())
            await self._writer.drain()
            data = await asyncio.wait_for(self._reader.readuntil(RECV_EOL), TIMEOUT)
            text = data.decode(errors="ignore").strip()
            _LOGGER.debug("RX: %s", text)
            return text

    # ---------- Commandes selon manuel ----------
    async def set_volume(self, zone: int, percent_value: int):
        """UI 0..100% -> protocole 0..70 (0 = volume max, 70 = min) → SVx.
        Mapping: 100% -> 0 ; 0% -> 70"""
        p = max(0, min(100, int(percent_value)))
        db = round((100 - p) * 70 / 100)  # inversé car 0=fort, 70=faible
        cmd = self._build(f"SV{zone}", str(db))  # SVx (x sans zéro)
        return await self._send_recv(cmd)

    async def set_mute(self, zone: int, muted: bool):
        # SM0x (x avec zéro), arg 0/1 (0=unmute, 1=mute)
        cmd = self._build(f"SM{zone:02d}", "1" if muted else "0")
        return await self._send_recv(cmd)

    async def set_source(self, zone: int, source_index: int):
        # SRx (x sans zéro), arg 0..8 (0 = none, 1..8 = Input list)
        idx = max(0, min(8, int(source_index)))
        cmd = self._build(f"SR{zone}", str(idx))
        return await self._send_recv(cmd)

    async def get_zone_info(self, zone: int) -> dict:
        # GZI0x|0 → "ZIxx|vol^route^mute^bass^treble"
        cmd = self._build(f"GZI{zone:02d}", "0")
        resp = await self._send_recv(cmd)
        return self._parse_gzi(resp)

    def _parse_gzi(self, text: str) -> dict:
        """Parse "…|ZIxx|vol^route^mute^bass^treble|…"
        vol=0..70 (0=max), route=0..8, mute=0/1, bass=00..14, treble=00..14"""
        try:
            parts = text.strip("|\r\n").split("|")
            idx = next(i for i, p in enumerate(parts) if p.startswith("ZI"))
            payload = parts[idx + 1]
        except Exception:
            return {}

        try:
            vol_s, route_s, mute_s, bass_s, treble_s = payload.split("^")
            vol = int(vol_s)
            route = int(route_s)
            mute = int(mute_s)
            bass = int(bass_s)
            treble = int(treble_s)
        except Exception:
            return {}

        return {
            "volume_db": max(0, min(70, vol)),
            "source_idx": max(0, min(8, route)),
            "mute": bool(mute),
            "bass": bass,
            "treble": treble,
        }
