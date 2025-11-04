DOMAIN = "audac_mtx"
DEFAULT_PORT = 5001
DEFAULT_HOST = "192.168.1.100"
DEFAULT_ZONES = 4  # MTX48

# Protocole AUDAC : destination fixe X001, source = identifiant client (≤ 4 chars)
DEFAULT_DEVICE_ID = "X001"
DEFAULT_SOURCE_ID = "HA"

TIMEOUT = 3.0
RECV_EOL = b"\r\n"
SEND_EOL = "\r\n"

# Liste des entrées (1..8)
SUPPORTED_SOURCES = {
    1: "Mic 1",
    2: "Mic 2",
    3: "Line 3",
    4: "Line 4",
    5: "Line 5",
    6: "Line 6",
    7: "WLI/MWX65",
    8: "WMI",
}

# Mapping inverse pratique pour la sélection par nom
FRIENDLY_TO_INDEX = {v: k for k, v in SUPPORTED_SOURCES.items()}
