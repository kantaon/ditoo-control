"""Tiny gettext-style translation layer.

Source strings are English; ``CS`` maps them to Czech. Use ``_("Text {x}", x=1)``.
The UI has its own catalogue in ``ui/i18n.js``.
"""
import ctypes

LANG = "en"
SUPPORTED = ("en", "cs")

CS = {
    # modes & contexts
    "Automatic": "Automaticky", "Clock": "Hodiny", "PC monitor": "PC monitor", "Gaming": "Hraní",
    "Weather": "Počasí", "AI agents": "AI agenti", "Pomodoro": "Pomodoro", "Ambient": "Ambient",
    "Text": "Text", "Image / GIF": "Obrázek / GIF", "Visualizer": "Vizualizér", "Lamp": "Lampa", "Off": "Vypnuto",
    "Working with AI": "Práce s AI", "Idle": "Volno",
    # engine
    "Ditoo not found. Is it switched on, paired with this PC and disconnected from your phone?":
        "Ditoo nenalezeno. Je zapnuté, spárované s tímto PC a odpojené od telefonu?",
    "No Ditoo paired with this PC yet – pair it in Windows Bluetooth settings.":
        "S tímto PC zatím není spárované žádné Ditoo – spáruj ho v nastavení Bluetooth ve Windows.",
    "Transfer error: {err}": "Chyba přenosu: {err}",
    "Connection lost, retrying…": "Spojení přerušeno, zkouším znovu…",
    "Mode: {mode}": "Režim: {mode}",
    "Notification: {text}": "Oznámení: {text}",
    "Preview on Ditoo: {title}": "Ukázka na Ditoo: {title}",
    "Pomodoro started": "Pomodoro spuštěno",
    "Pomodoro stopped": "Pomodoro zastaveno",
    "Shortcut: back to automatic": "Zkratka: zpět na automatiku",
    "Shortcut: {screen} ({context})": "Zkratka: {screen} ({context})",
    "Shortcut: brightness {value} %": "Zkratka: jas {value} %",
    "Image can't be loaded: {err}": "Obrázek nejde načíst: {err}",
    "no game": "žádná hra",
    "Idle – rotating screens": "Klid – střídání obrazovek",
    "Idle – clock": "Klid – hodiny",
    "Warning: {part} {temp} °C": "Varování: {part} {temp} °C",
    "Careful: {part} is at {temp} °C": "Pozor: {part} má {temp} °C",
    "Incoming notification": "Příchozí oznámení",
    "Picked with a shortcut · context {context}": "Vybráno zkratkou · kontext {context}",
    "{agent} finished the task": "{agent} dokončil úlohu",
    "{agent} reports an error": "{agent} hlásí chybu",
    "Game started: {name}": "Spuštěna hra {name}",
    "Playing {name}": "Běží hra {name}",
    " · detected automatically": " · rozpoznáno automaticky",
    "Pomodoro running": "Běží pomodoro",
    "{agent} is waiting for your reply": "{agent} čeká na tvou odpověď",
    "{agent} is working on a task": "{agent} pracuje na úloze",
    "{agents} are working on a task": "{agents} pracují na úloze",
    "Gallery preview": "Ukázka z galerie",
    "Manually selected mode": "Ručně zvolený režim",
    "Ditoo Control started": "Ditoo Control spuštěno",
    "Game detected: {name}": "Detekována hra: {name}",
    "Game closed: {name}": "Hra ukončena: {name}",
    "Pomodoro: break": "Pomodoro: přestávka",
    "Pomodoro: focus": "Pomodoro: soustředění",
    "Internal error: {err}": "Interní chyba: {err}",
    "Hotkeys already used by another app: {keys}": "Zkratky obsazené jinou aplikací: {keys}",
    "Found {name} ({mac})": "Nalezeno {name} ({mac})",
    "You're away – display off to save the battery": "Nejsi u PC – displej zhasnut kvůli baterii",
    "Welcome back – display on": "Vítej zpět – displej svítí",
    "Ditoo not found. Is it switched on and charged, paired with this PC and disconnected from your phone?":
        "Ditoo nenalezeno. Je zapnuté a nabité, spárované s tímto PC a odpojené od telefonu?",
    "working": "pracuje", "done": "hotovo", "error": "chyba", "attention": "čeká na tebe", "idle": "nečinné",
    # tray
    "Open Ditoo Control": "Otevřít Ditoo Control", "Mode": "Režim", "Sounds": "Zvuky",
    "Reconnect Ditoo": "Znovu připojit Ditoo", "Quit": "Ukončit",
    # server / integrations / driver / sounds
    "Not a supported image file": "Soubor není podporovaný obrázek",
    "Can't read ~/.codex/config.toml: {err}": "~/.codex/config.toml nejde přečíst: {err}",
    "Connected to {mac} (channel {port})": "Připojeno k {mac} (kanál {port})",
    "Channel {port}: {err}": "Kanál {port}: {err}",
    "Connection to the device lost": "Spojení se zařízením přerušeno",
    "Ditoo is not reachable": "Ditoo není dostupné",
    "Done": "Hotovo", "Waiting for you": "Čeká na tebe", "Error": "Chyba", "Game start": "Start hry",
    "Overheating": "Přehřívání", "Notification": "Oznámení",
    "Sound: Ditoo is not connected as a speaker": "Zvuk: Ditoo není připojené jako reproduktor",
    "Sound could not be played: {err}": "Zvuk se nepodařilo přehrát: {err}",
    # scenes
    "PC monitor – temperatures and load": "PC monitor – teploty a vytížení",
    "Gaming – {name}": "Hraní – {name}",
    "Game started – {name}": "Spuštěna hra – {name}",
    "Weather – loading": "Počasí – načítám",
    "Weather – set your location in the app": "Počasí – nastav v aplikaci své město",
    "Tomorrow – {text}, high {t} °C": "Zítra – {text}, max {t} °C",
    "Weather – {city} – {text}, {t} °C": "Počasí – {city} – {text}, {t} °C",
    "Weather – {text}, {t} °C": "Počasí – {text}, {t} °C",
    "Clock {time}": "Hodiny {time}",
    "Native Divoom clock": "Nativní hodiny Divoom",
    "Music visualizer (reacts to sound played on the Ditoo)": "Vizualizér hudby (reaguje na zvuk hraný přes Ditoo)",
    "{agent} is working…": "{agent} pracuje…",
    "{agents} are working…": "{agents} pracují…",
    "AI – nothing running": "AI – nic neběží",
    "{agent} – error": "{agent} – chyba",
    "{agent} is waiting for you": "{agent} čeká na tebe",
    "Overheating {part}: {temp} °C": "Přehřívání {part}: {temp} °C",
    "Pomodoro ready – {min} min (start it in the app)": "Pomodoro připraveno – {min} min (spusť v aplikaci)",
    "Focus": "Soustředění", "Break": "Přestávka", " (paused)": " (pauza)",
    "Text: {text}": "Text: {text}",
    "Image – {name}": "Obrázek – {name}", "Animation – {name}": "Animace – {name}",
    "Ambient – {name}": "Ambient – {name}",
    "Plasma": "Plazma", "Fire": "Oheň", "Matrix": "Matrix", "Warp": "Warp", "Aurora": "Polární záře",
    "Game of Life": "Game of Life",
    # 3x5 pixel words on the device
    "BRK": "PAU", "T": "Z", "HELLO": "AHOJ",
    # gallery
    "Big digits, seconds fill the sides": "Velké číslice, vteřiny se plní po stranách",
    "CPU / GPU temperature and load, live": "Teplota a zátěž CPU / GPU, živě",
    "Gaming HUD": "Herní HUD",
    "FPS, CPU/GPU temperature and frame-time graph": "FPS, teploty CPU/GPU a graf latence snímků",
    "Animation when a game launches": "Animace při spuštění hry",
    "Weather – rain": "Počasí – déšť", "Drops falling at different speeds": "Kapky s různou rychlostí",
    "Weather – snow": "Počasí – sníh", "Drifting snowflakes": "Poletující vločky",
    "Clear night": "Jasná noc", "Moon and twinkling stars": "Měsíc a blikající hvězdy",
    "Tomorrow": "Zítra", "Tomorrow's forecast in the evening": "Večer předpověď na další den",
    "Claude is working": "Claude pracuje", "Orange spark, ring turns clockwise": "Oranžová jiskra, kruh po směru hodinek",
    "Codex / ChatGPT is working": "Codex / ChatGPT pracuje",
    "Teal >_ prompt, ring turns counter-clockwise": "Tyrkysový prompt >_, kruh proti směru hodinek",
    "Both are working": "Pracují oba", "Claude and Codex take turns": "Střídá se Claude a Codex",
    "AI done": "AI hotovo", "Task finished": "Úloha dokončena",
    "AI waiting": "AI čeká", "The agent needs your answer": "Agent potřebuje tvou odpověď",
    "Something went wrong": "Něco se pokazilo",
    "High temperature warning": "Varování při vysoké teplotě",
    "Focus countdown with a shrinking frame": "Odpočet soustředění s ubývajícím rámečkem",
    "Scrolling text": "Běžící text", "Your own message, rainbow too": "Vlastní zpráva, i duhově",
    "Messages from GitHub, tests, scripts": "Zprávy z GitHubu, testů, skriptů",
    "Reacts to music (built into Ditoo)": "Reaguje na hudbu (vestavěné v Ditoo)",
    "Ambient effect": "Ambientní efekt",
}

WEATHER_CS = {
    "Clear": "Jasno", "Mostly clear": "Skoro jasno", "Partly cloudy": "Polojasno", "Overcast": "Zataženo",
    "Fog": "Mlha", "Rime fog": "Námraza", "Drizzle": "Mrholení", "Heavy drizzle": "Silné mrholení",
    "Freezing drizzle": "Mrznoucí mrholení", "Light rain": "Slabý déšť", "Rain": "Déšť", "Heavy rain": "Silný déšť",
    "Freezing rain": "Mrznoucí déšť", "Light snow": "Slabé sněžení", "Snow": "Sněžení", "Heavy snow": "Silné sněžení",
    "Snow grains": "Sněhová zrna", "Showers": "Přeháňky", "Heavy showers": "Silné přeháňky",
    "Snow showers": "Sněhové přeháňky", "Thunderstorm": "Bouřka", "Thunderstorm with hail": "Bouřka s kroupami",
}
CS.update(WEATHER_CS)


def _(msg, /, **kw):
    s = CS.get(msg, msg) if LANG == "cs" else msg
    return s.format(**kw) if kw else s


def detect():
    """Windows display language → 'cs' or 'en'."""
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return "cs" if (lang_id & 0x3FF) == 0x05 else "en"
    except Exception:
        return "en"


def set_lang(code):
    global LANG
    LANG = code if code in SUPPORTED else detect()
    return LANG
