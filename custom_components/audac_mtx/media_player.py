from __future__ import annotations
import logging
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.components.media_player.const import MediaPlayerState
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, SUPPORTED_SOURCES, FRIENDLY_TO_INDEX

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    hub = hass.data[DOMAIN][entry.entry_id]
    zones = entry.data["zones"]
    async_add_entities([AudacZoneEntity(hub, z) for z in range(1, zones + 1)])

class AudacZoneEntity(MediaPlayerEntity):
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, hub, zone: int):
        self.hub = hub
        self.zone = zone
        self._attr_name = f"AUDAC Zone {zone}"
        self._attr_state = MediaPlayerState.ON
        self._volume = 0.5       # 0..1
        self._muted = False
        self._source_list = list(SUPPORTED_SOURCES.values())
        self._source = SUPPORTED_SOURCES.get(3, self._source_list[0])  # Line 3 par défaut

    @property
    def unique_id(self):
        return f"audac_mtx_zone_{self.zone}"

    @property
    def volume_level(self) -> float | None:
        return self._volume

    @property
    def is_volume_muted(self) -> bool | None:
        return self._muted

    @property
    def source_list(self):
        return self._source_list

    @property
    def source(self):
        return self._source

    async def async_set_volume_level(self, volume: float):
        vol_pct = int(round(max(0.0, min(1.0, volume)) * 100))
        await self.hub.set_volume(self.zone, vol_pct)
        self._volume = vol_pct / 100.0
        self.async_write_ha_state()

    async def async_mute_volume(self, mute: bool):
        await self.hub.set_mute(self.zone, mute)
        self._muted = mute
        self.async_write_ha_state()

    async def async_select_source(self, source: str):
        idx = FRIENDLY_TO_INDEX.get(source)
        if not idx:
            _LOGGER.warning("Unknown source %s", source)
            return
        await self.hub.set_source(self.zone, idx)
        self._source = source
        self.async_write_ha_state()

    async def async_update(self):
        info = await self.hub.get_zone_info(self.zone)
        if not info:
            return
        if "volume_db" in info:
            vdb = info["volume_db"]
            percent = round((70 - vdb) * 100 / 70)  # 0..70 -> 0..100%
            self._volume = max(0, min(100, percent)) / 100.0
        if "mute" in info:
            self._muted = bool(info["mute"])
        if "source_idx" in info and info["source_idx"] in SUPPORTED_SOURCES:
            self._source = SUPPORTED_SOURCES[info["source_idx"]]
