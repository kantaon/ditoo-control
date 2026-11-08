"use strict";
/* UI translations. Source strings are English; add a language by adding a catalogue. */

const CATALOGS = {
  cs: {
    // navigation & pages
    "Overview": "Přehled", "Scene gallery": "Galerie scén", "Automation": "Automatika", "Games": "Hry", "Content": "Obsah",
    "Sounds": "Zvuky", "Integrations": "Integrace", "Settings": "Nastavení", "Help": "Nápověda",
    "What Ditoo shows right now and why": "Co právě Ditoo ukazuje a proč",
    "Everything your Ditoo Pro can do": "Co všechno umí tvoje Ditoo Pro",
    "How Ditoo decides on its own": "Jak se Ditoo samo rozhoduje",
    "Gaming HUD and game detection": "Herní HUD a rozpoznávání her",
    "Images, text, effects, clock and lamp": "Obrázky, text, efekty, hodiny a lampa",
    "Notifications from the Ditoo speaker": "Notifikace z reproduktoru Ditoo",
    "Claude Code, Codex, start with Windows and API": "Claude Code, Codex, spouštění s Windows a API",
    "Connection, location and language": "Připojení, místo a jazyk",
    "What everything on the display means and how it all works": "Co na displeji znamená co a jak to celé funguje",
    "for Divoom Ditoo Pro": "pro Divoom Ditoo Pro", "Main navigation": "Hlavní navigace",
    // connection
    "Connecting…": "Připojuji…", "Reconnect": "Znovu připojit", "Fix connection": "Opravit připojení",
    "Connected": "Připojeno", "Not reachable": "Nedostupné", "Disconnected": "Odpojeno",
    "Connected · channel {port}": "Připojeno · kanál {port}",
    "Ditoo isn't connected": "Ditoo není připojené", "Help me connect": "Pomoz mi připojit",
    "Ditoo is disconnected": "Ditoo je odpojené", "The app is not sending anything to the display.": "Aplikace na displej nic neposílá.",
    "Connect": "Připojit", "The app isn't responding": "Aplikace neodpovídá",
    // overview
    "Ditoo display preview": "Náhled displeje Ditoo", "What the display shows": "Co ukazuje displej",
    "Display brightness": "Jas displeje", "Start": "Spustit", "Pause": "Pozastavit", "Resume": "Pokračovat",
    "Skip phase": "Přeskočit fázi", "Stop and turn the timer off": "Zastavit a vypnout časovač",
    "Mode": "Režim", "Display mode": "Režim displeje", "AI agents": "AI agenti", "Activity": "Aktivita", "idle": "nečinné",
    "Ctrl + Shift + Alt + ": "Ctrl + Shift + Alt + ", "switches by context": "přepíná podle kontextu",
    "Automatic = the app picks the screen based on what you are doing. Any other mode locks the display to that one thing until you pick another.":
      "Automaticky = aplikace sama vybírá obrazovku podle toho, co děláš. Ostatní režimy displej zamknou na jednu věc, dokud nevybereš jinou.",
    "Status of Claude Code and Codex, reported by their hooks (see Integrations). Working = solving a task, Waiting for you = needs approval or an answer, Done = finished.":
      "Stav Claude Code a Codexu, hlášený jejich hooky (viz Integrace). Pracuje = řeší úlohu, Čeká na tebe = potřebuje schválení nebo odpověď, Hotovo = dokončil.",
    "Latest app events: connection, mode changes, detected games, agent signals.": "Poslední události aplikace: připojení, změny režimu, detekce her, signály agentů.",
    "CPU temperature": "Teplota CPU", "GPU temperature": "Teplota GPU", "CPU load": "Zátěž CPU", "GPU load": "Zátěž GPU",
    "ms/frame": "ms/snímek", "Temperatures unavailable": "Teploty nejsou k dispozici",
    "Start MSI Afterburner (with RivaTuner) – temperatures, load and FPS are read from it.": "Spusť MSI Afterburner (s RivaTunerem) – teploty, zátěž i FPS se čtou z něj.",
    "Get MSI Afterburner": "Stáhnout MSI Afterburner",
    "Context: {name}": "Kontext: {name}", "Night brightness": "Noční jas", "night": "noc",
    "No signal yet. Turn on the Claude Code or Codex integration on the Integrations page.": "Zatím žádný signál. Zapni integraci s Claude Code nebo Codexem v sekci Integrace.",
    "Working": "Pracuje", "Done": "Hotovo", "Error": "Chyba", "Waiting for you": "Čeká na tebe", "Idle": "Volno",
    "Ready · {min} min focus": "Připraveno · {min} min soustředění", "Focus": "Soustředění", "Break": "Přestávka",
    "paused": "pozastaveno", "round {n}": "kolo {n}",
    "What you see": "Co právě vidím", "Explanation": "Vysvětlení",
    // modes
    "Automatic": "Automaticky", "Clock": "Hodiny", "PC monitor": "PC monitor", "Gaming": "Hraní", "Weather": "Počasí",
    "Pomodoro": "Pomodoro", "Ambient": "Ambient", "Text": "Text", "Image / GIF": "Obrázek / GIF", "Visualizer": "Vizualizér",
    "Lamp": "Lampa", "Off": "Vypnuto",
    "Reacts to games, AI agents, temperatures and time of day": "Reaguje na hry, AI agenty, teploty a denní dobu",
    "Animated, with seconds": "Animované, s vteřinami", "CPU / GPU temperature and load": "Teplota a zátěž CPU / GPU",
    "FPS and temperatures while playing": "FPS a teploty během hry", "Animated, with forecast": "Animované, s předpovědí",
    "Claude Code and Codex": "Claude Code a Codex", "Focus timer": "Časovač soustředění", "Plasma, fire, Matrix…": "Plazma, oheň, Matrix…",
    "Your own scrolling message": "Vlastní běžící zpráva", "Your pixel art": "Tvůj pixel art", "Reacts to music": "Reaguje na hudbu",
    "Night light": "Noční světlo", "Blank display": "Černý displej", "LEDs off": "Diody vypnuté", "Animated": "Animované",
    // gallery
    "Every scene below is rendered live from the app. Try one on your Ditoo for 12 seconds, or make it the current mode.":
      "Každá scéna níže se vykresluje živě z aplikace. Vyzkoušej ji na Ditoo na 12 sekund, nebo ji nastav jako aktuální režim.",
    "Try it": "Vyzkoušet", "Use": "Nastavit", "{title} – showing on Ditoo for 12 s": "{title} – ukázka na Ditoo na 12 s", "Mode: {mode}": "Režim: {mode}",
    // rules
    "Automation priorities": "Priority automatiky", "Top to bottom – the first one that applies wins": "Shora dolů – vyhrává první, která platí",
    "In Automatic mode the rules are checked from top to bottom every second. The display shows the first rule that applies – it is highlighted.":
      "V režimu Automaticky se pravidla každou sekundu vyhodnocují shora dolů. Displej ukazuje první pravidlo, které platí – to je zvýrazněné.",
    "When nothing is happening": "Když se nic neděje", "Seconds on screen, 0 = off": "Sekundy na displeji, 0 = vypnuto",
    "When no game, agent or pomodoro is running, the display cycles through these screens. After 5 pm the weather also shows tomorrow's forecast.":
      "Když neběží hra, agent ani pomodoro, displej střídá tyto obrazovky. Po 17. hodině počasí ukáže i předpověď na zítřek.",
    "Night mode": "Noční režim", "From": "Od", "To": "Do",
    "Dims the display at night so it doesn't light up the room. Sounds can be silenced at night on the Sounds page.":
      "V noci ztlumí displej, aby nesvítil do pokoje. Zvuky v noci ztišíš na stránce Zvuky.",
    "Temperature limits": "Teplotní limity",
    "Warning = the number on the display turns orange. Critical = Automatic switches to a blinking warning and plays a sound. Up to 15 °C below the warning the number is green, in between yellow.":
      "Varování = číslo na displeji zoranžoví. Kritická = Automatika přepne na blikající varování a zazní zvuk. Do 15 °C pod varováním je číslo zelené, mezi tím žluté.",
    "Keyboard shortcuts": "Klávesové zkratky",
    "Work anywhere in Windows, even in games. A/D steps through the screens that fit what you are doing (context), S returns to Automatic, W toggles brightness.":
      "Fungují kdekoli ve Windows, i ve hrách. A/D listuje obrazovkami vhodnými pro to, co právě děláš (kontext), S vrátí Automatiku, W přepíná jas.",
    "Ctrl + Alt acts as AltGr on many European keyboards, so the shortcuts use Ctrl + Shift + Alt. Changes apply after restarting the app.":
      "Ctrl + Alt se na mnoha evropských klávesnicích chová jako AltGr, proto zkratky používají Ctrl + Shift + Alt. Změny se projeví po restartu aplikace.",
    "Overheating": "Přehřívání", "Blinking warning when the CPU or GPU passes the critical temperature": "Blikající varování, když CPU nebo GPU překročí kritickou teplotu",
    "Notifications": "Oznámení", "Messages from your scripts and webhooks (always on)": "Zprávy z tvých skriptů a webhooků (vždy aktivní)",
    "Picked with a shortcut": "Vybráno zkratkou", "Ctrl+Shift+Alt+A/D – stays until the context changes": "Ctrl+Shift+Alt+A/D – platí, dokud se nezmění kontext",
    "AI finished / error": "AI dokončilo / chyba", "Short confirmation when Claude or Codex finishes": "Krátké potvrzení, když Claude nebo Codex skončí",
    "Gaming HUD with FPS and temperatures": "Herní HUD s FPS a teplotami", "Countdown while the timer runs": "Odpočet, když běží časovač",
    "AI working / waiting": "AI pracuje / čeká", "Animation while an agent works or waits for your answer": "Animace, dokud agent pracuje nebo čeká na tvou odpověď",
    "Cycles clock, weather, monitor and effects": "Střídání hodin, počasí, monitoru a efektů",
    "Even while gaming": "I během hry", "even while gaming": "i během hry", "Game start animation": "Úvodní animace hry", "intro": "intro", "always": "vždy", "off": "vyp.",
    "CPU warning °C": "CPU varování °C", "CPU critical °C": "CPU kritická °C", "GPU warning °C": "GPU varování °C", "GPU critical °C": "GPU kritická °C",
    "Previous screen": "Předchozí obrazovka", "Next screen": "Další obrazovka", "Back to Automatic": "Zpět na Automatiku", "Toggle brightness": "Přepnout jas",
    "Working with AI": "Práce s AI",
    "HUD → monitor → clock → weather": "HUD → monitor → hodiny → počasí",
    "AI → pomodoro → clock → monitor → weather → ambient": "AI → pomodoro → hodiny → monitor → počasí → ambient",
    "clock → weather → monitor → ambient → AI → pomodoro → visualizer": "hodiny → počasí → monitor → ambient → AI → pomodoro → vizualizér",
    // games
    "My games": "Moje hry", "game.exe": "hra.exe", "Name (optional)": "Název (volitelné)", "Executable file": "Spustitelný soubor", "Game name": "Název hry", "Add": "Přidat",
    "When one of these programs is running, Ditoo switches to the gaming HUD. The name is only for display – the .exe file name is what counts.":
      "Když běží některý z těchto programů, Ditoo přepne na herní HUD. Název je jen pro zobrazení – rozhoduje název .exe souboru.",
    "Automatic detection": "Automatické rozpoznání", "Automatic game detection": "Automatické rozpoznání her",
    "Detects games that are not on your list: a full-screen window that RivaTuner measures FPS for. Adding the game to the list is more reliable.":
      "Pozná i hry mimo seznam: okno přes celou obrazovku, u kterého RivaTuner měří FPS. Spolehlivější je hru přidat do seznamu.",
    "Below are the apps RivaTuner is tracking right now – add any of them with one click.": "Níže jsou aplikace, které RivaTuner právě sleduje – přidáš je jedním klikem.",
    "Ignored apps": "Ignorované aplikace", "app.exe": "aplikace.exe", "Ignored app": "Ignorovaná aplikace",
    "Apps RivaTuner tracks that are not games (browsers, Discord…). Automatic detection skips them.":
      "Aplikace, které RivaTuner sleduje, ale nejsou to hry (prohlížeče, Discord…). Automatické rozpoznání je přeskočí.",
    "{n} games": "{n} her", "Remove {name}": "Odebrat {name}", "This game is already on the list": "Tahle hra už v seznamu je", "Added: {name}": "Přidáno: {name}",
    "No game running": "Žádná hra neběží", "detected automatically": "rozpoznáno automaticky", "from your list": "ze seznamu", "since {time}": "od {time}",
    "As soon as you start a game, Ditoo switches to the gaming HUD": "Jakmile spustíš hru, Ditoo přepne na herní HUD",
    "full screen": "na celé obrazovce", "RivaTuner isn't tracking any 3D app right now": "RivaTuner teď nesleduje žádnou 3D aplikaci",
    // content
    "Images and GIFs": "Obrázky a GIFy",
    "The image is cropped to a square and scaled to 16×16 px. Pixel art that is already 16×16 looks best. A GIF can have up to 60 frames.":
      "Obrázek se ořízne na čtverec a zmenší na 16×16 px. Nejlépe vypadá pixel art, který už 16×16 je. GIF může mít až 60 snímků.",
    "Drop an image or GIF here": "Přetáhni sem obrázek nebo GIF", "or click to choose · cropped to a 16 × 16 square · up to 60 frames": "nebo klikni a vyber · ořízne se na čtverec 16 × 16 · max 60 snímků",
    "Ambient effect": "Ambientní efekt",
    "Decorative animations without information – for the background, music or the night. Click one to select and show it.":
      "Dekorativní animace bez informací – do pozadí, k hudbě nebo na noc. Kliknutím efekt vybereš a zobrazíš.",
    "Scrolling text": "Běžící text",
    "Show = the text stays on the display as a mode. Notify = the text scrolls once with a coloured frame, then the display returns to what it was showing.":
      "Zobrazit = text zůstane na displeji jako režim. Oznámení = text jednou proběhne s barevným rámečkem a displej se pak vrátí k předchozímu obsahu.",
    "Type a message": "Napiš zprávu", "Display text": "Text na displej", "Text colour": "Barva textu", "Rainbow colours": "Duhové barvy", "Rainbow text": "Duhový text",
    "Show": "Zobrazit", "Send as notification": "Poslat jako oznámení",
    "Animated = big digits from this app, seconds fill the sides. Native = Ditoo's built-in clock (keeps running without the PC).":
      "Animované = velké číslice z této aplikace, vteřiny se plní po stranách. Nativní = vestavěné hodiny Ditoo (běží i bez PC).",
    "Clock type": "Typ hodin", "Native Divoom": "Nativní Divoom", "Colour": "Barva", "Clock colour": "Barva hodin",
    "The whole display glows in one colour – a night light or desk backlight.": "Celý displej svítí jednou barvou – noční světlo nebo podsvícení stolu.",
    "Custom colour": "Vlastní barva", "Lamp colour": "Barva lampy",
    "A focus technique: 25 min of work, 5 min break, repeat. The timer only starts with Start, and Stop turns it off completely.":
      "Technika soustředění: 25 min práce, 5 min pauza, dokola. Časovač se spustí jen tlačítkem Spustit a Zastavit ho úplně vypne.",
    "Focus (min)": "Soustředění (min)", "Break (min)": "Přestávka (min)", "Start pomodoro": "Spustit pomodoro",
    "Showing {name}": "Zobrazuji {name}", "Delete {name}": "Smazat {name}", "The file is too big (max 20 MB)": "Soubor je moc velký (max 20 MB)",
    "Uploaded and shown on Ditoo": "Nahráno a zobrazeno na Ditoo", "The text is on the display": "Text je na displeji",
    "Type a message first": "Nejdřív napiš zprávu", "Notification sent": "Oznámení odesláno", "Pomodoro is running – focus!": "Pomodoro běží – soustřeď se!",
    // sound
    "Sounds from Ditoo": "Zvuky z Ditoo",
    "Sound plays only through the Ditoo speaker, not your PC speakers. Ditoo must be connected in Windows as an audio device (DitooPro-Audio).":
      "Zvuk hraje jen z reproduktoru Ditoo, ne z reproduktorů PC. Ditoo musí být ve Windows připojené jako zvukové zařízení (DitooPro-Audio).",
    "Short 8-bit jingles play straight from the Ditoo speaker. Your default audio output (PC speakers) stays untouched.":
      "Krátké 8bitové znělky hrají přímo z reproduktoru Ditoo. Tvůj výchozí zvukový výstup (reproduktory u PC) zůstává beze změny.",
    "Volume": "Hlasitost", "Silent while gaming": "Během hraní ticho", "Silent at night": "V noci ticho", "Windows sound settings": "Nastavení zvuku ve Windows",
    "Events": "Události", "Which events play a jingle. Press Play to hear it now.": "Při kterých událostech zazní znělka. Tlačítkem Přehrát si ji poslechneš hned.",
    "Play": "Přehrát",
    // integrations
    "Your own scripts and webhooks": "Vlastní skripty a webhooky", "Local API on 127.0.0.1": "Lokální API na 127.0.0.1",
    "The app only listens on this PC (127.0.0.1). Any script can send text to the display or set an agent's status.":
      "Aplikace poslouchá jen na tomto PC (127.0.0.1). Jakýkoli skript může poslat text na displej nebo nastavit stav agenta.",
    "Anything on your PC can send a notification or a status – tests, builds, GitHub Actions via": "Cokoli na tvém PC může poslat oznámení nebo stav – testy, buildy, GitHub Actions přes",
    ", anything.": ", cokoliv.",
    "hooks in ~/.claude/settings.json": "hooky v ~/.claude/settings.json", "notify in ~/.codex/config.toml": "notify v ~/.codex/config.toml",
    "Ditoo shows when Claude is working, waiting for your approval or has finished.": "Ditoo ukáže, když Claude pracuje, čeká na tvé schválení nebo dokončil úlohu.",
    "working: after you send a prompt": "pracuje: po odeslání promptu", "waiting for you: permission request": "čeká na tebe: žádost o povolení",
    "done: end of the answer + jingle": "hotovo: konec odpovědi + znělka", "restart Claude Code after turning it on": "po zapnutí restartuj Claude Code",
    "After every Codex turn Ditoo shows a check mark and plays a jingle.": "Po každém tahu Codexu Ditoo ukáže fajfku a zahraje znělku.",
    "done: end of the agent's turn": "hotovo: konec tahu agenta", "keeps the Codex app's own notify working": "vlastní notify aplikace Codex dál funguje",
    "restart the Codex app after turning it on": "po zapnutí restartuj aplikaci Codex",
    "Start with Windows": "Spouštět s Windows", "shortcut in the Startup folder": "zástupce ve složce Po spuštění",
    "Ditoo Control starts in the tray after you sign in and reacts right away.": "Ditoo Control po přihlášení naběhne do lišty a hned začne reagovat.",
    "starts hidden in the tray": "startuje skrytě v oznamovací oblasti", "low priority, easy on performance": "nízká priorita, šetrné k výkonu",
    "Start menu shortcut": "Zástupce v nabídce Start", "find it by typing \"Ditoo\"": "najdeš ho napsáním „Ditoo“",
    "Adds Ditoo Control to the Start menu so you can open it like any other app.": "Přidá Ditoo Control do nabídky Start, takže ho otevřeš jako každou jinou aplikaci.",
    "opens the window": "otevře okno", "uninstall by turning it off": "odebereš vypnutím",
    "Turn on": "Zapnout", "Turn off": "Vypnout", "Not installed": "Není nainstalováno", "On": "Zapnuto",
    "{name} turned on": "{name} zapnuto", "{name} turned off": "{name} vypnuto",
    "Text on the display": "Text na displej", "Your own agent's status": "Stav vlastního agenta", "Agent finished": "Agent dokončil", "From any script": "Z libovolného skriptu",
    "Copy": "Kopírovat", "Copied": "Zkopírováno",
    // settings
    "Bluetooth": "Bluetooth",
    "Ditoo is controlled over its Bluetooth serial channel (RFCOMM). The address and channel are found automatically – change them only for a different Ditoo.":
      "Ditoo se ovládá přes sériový Bluetooth kanál (RFCOMM). Adresa i kanál se najdou automaticky – měň je jen u jiného kusu Ditoo.",
    "MAC address": "MAC adresa", "RFCOMM channel": "Kanál RFCOMM", "automatic": "automaticky", "Save and connect": "Uložit a připojit", "Disconnect": "Odpojit",
    "Find automatically": "Najít automaticky", "Display not reacting?": "Displej nereaguje?",
    "Ditoo Pro only listens to the first device that connects. Disconnect it from your phone (turn off Bluetooth on the phone or close the Divoom app) and restart Ditoo.":
      "Ditoo Pro poslouchá jen první zařízení, které se připojí. Odpoj ho od telefonu (vypni Bluetooth v mobilu nebo zavři aplikaci Divoom) a Ditoo restartuj.",
    "Weather location": "Místo pro počasí", "Free weather from Open-Meteo, refreshed every 15 minutes for the chosen city.": "Počasí zdarma z Open-Meteo, obnovuje se každých 15 minut pro zvolené město.",
    "Search for a city": "Hledat město", "City": "Město", "Search": "Hledat", "not set": "nenastaveno",
    "App": "Aplikace", "Language": "Jazyk", "Run setup again": "Spustit průvodce znovu", "Open settings folder": "Otevřít složku s nastavením", "Report a problem": "Nahlásit problém",
    "Log": "Protokol", "Detailed event log – useful when troubleshooting the connection.": "Podrobný záznam událostí – hodí se při řešení problémů s připojením.",
    "That isn't a valid MAC address (e.g. AA:BB:CC:DD:EE:FF)": "To není platná MAC adresa (např. AA:BB:CC:DD:EE:FF)",
    "Looking for a paired Ditoo…": "Hledám spárované Ditoo…", "Weather for {city}": "Počasí: {city}",
    "Nothing found – try another spelling": "Nic nenalezeno – zkus jiný zápis", "Search failed – are you online?": "Hledání selhalo – jsi online?",
    "Couldn't save: {err}": "Nepodařilo se uložit: {err}",
    // help
    "How to read the display": "Jak číst displej", "Every screen explained": "Každá obrazovka s vysvětlivkami", "Colours": "Barvy",
    "How Automatic works": "Jak funguje Automaticky", "Modes": "Režimy", "Troubleshooting": "Řešení problémů",
    "Temperatures": "Teploty", "green up to (warning − 15 °C) · yellow · orange from the warning · red from critical (limits under Automation)":
      "zelená do (varování − 15 °C) · žlutá · oranžová od varování · červená od kritické (limity v Automatice)",
    "Load": "Zátěž", "blue = low, purple = medium, red = full": "modrá = málo, fialová = středně, červená = naplno",
    "green from 60 · yellow 30–59 · red below 30": "zelené od 60 · žluté 30–59 · červené pod 30",
    "Frame time": "Latence snímků", "green up to 17.5 ms (60+ FPS) · yellow up to 34 ms · red = stutter": "zelená do 17,5 ms (60+ FPS) · žlutá do 34 ms · červená = zásek",
    "orange": "oranžová", "teal": "tyrkysová", "Codex / ChatGPT": "Codex / ChatGPT",
    "CPU or GPU overheating – blinking warning and a sound": "Přehřívání CPU nebo GPU – blikající varování a zvuk",
    "Notifications from scripts and webhooks": "Oznámení ze skriptů a webhooků",
    "The screen you picked with a shortcut (until the context changes)": "Obrazovka vybraná zkratkou (do změny kontextu)",
    "An agent just finished its task or reports an error (briefly)": "Agent právě dokončil úlohu nebo hlásí chybu (krátce)",
    "A game is running – gaming HUD": "Běží hra – herní HUD", "Pomodoro is running": "Běží pomodoro",
    "An agent is working or waiting for your answer": "Agent pracuje nebo čeká na tvou odpověď",
    "None of the above – clock, weather, monitor and effects take turns": "Nic z toho – střídají se hodiny, počasí, monitor a efekty",
    "previous screen": "předchozí obrazovka", "next screen": "další obrazovka", "back to Automatic": "zpět na Automatiku", "toggle brightness": "přepnout jas",
    "Screens follow the context: while gaming HUD → monitor → clock → weather, while working with AI agent → pomodoro → clock…, otherwise clock → weather → monitor → effects. Works inside games too.":
      "Obrazovky se listují podle kontextu: při hraní HUD → monitor → hodiny → počasí, při práci s AI agent → pomodoro → hodiny…, jinak hodiny → počasí → monitor → efekty. Funguje to i ve hře.",
    "The display doesn't react although the app says connected": "Displej nereaguje, i když aplikace hlásí připojeno",
    "Ditoo Pro only listens to the first device that connects. Turn off Bluetooth on your phone (or close the Divoom app), then switch Ditoo off and on.":
      "Ditoo Pro poslouchá jen první zařízení, které se připojí. Vypni Bluetooth na telefonu (nebo zavři aplikaci Divoom) a Ditoo vypni a zapni.",
    "I don't see temperatures or FPS": "Nevidím teploty ani FPS",
    "MSI Afterburner with RivaTuner has to be running. Temperatures come from Afterburner, FPS from RivaTuner.": "Musí běžet MSI Afterburner s RivaTunerem. Teploty jdou z Afterburneru, FPS z RivaTuneru.",
    "My game wasn't detected": "Hra se nerozpoznala",
    "Add its .exe on the Games page – or add it with one click from the list of apps RivaTuner is tracking.": "Přidej její .exe na stránce Hry – nebo ji přidej jedním klikem ze seznamu aplikací, které RivaTuner sleduje.",
    "No sounds": "Nehrají zvuky",
    "Ditoo has to be connected in Windows as an audio device too (DitooPro-Audio). Sounds are muted on purpose while gaming and at night.":
      "Ditoo musí být ve Windows připojené i jako zvukové zařízení (DitooPro-Audio). Během hry a v noci jsou zvuky záměrně ztlumené.",
    "Claude / Codex doesn't show up": "Claude / Codex se neukazuje",
    "Turn the integration on under Integrations and restart Claude Code / the Codex app – they only read their settings at start.":
      "Zapni integraci v sekci Integrace a restartuj Claude Code / aplikaci Codex – nastavení čtou jen při startu.",
    "How do I turn pomodoro off completely": "Jak úplně vypnout pomodoro",
    "The square Stop button under the display preview stops the timer and returns the display to Automatic.": "Čtvercové tlačítko Zastavit pod náhledem displeje časovač vypne a vrátí displej do Automatiky.",
    "Does the HUD show input latency or ping?": "Je v HUDu latence vstupu nebo ping?",
    "No. The bottom graph is frame time (how long one frame takes to draw) – the part of input latency you can influence. Real mouse-to-screen latency is only measured by NVIDIA Reflex in its overlay, and only the game knows its ping; neither is available to other apps.":
      "Ne. Spodní graf je latence snímků (jak dlouho trvá vykreslit jeden snímek) – část latence vstupu, kterou ovlivníš. Skutečnou latenci od myši po obraz měří jen NVIDIA Reflex ve svém overlayi a ping zná jen hra; ani jedno není dostupné jiným aplikacím.",
    "Shortcuts don't work": "Zkratky nefungují",
    "Another app may use the same combination. Change the letters under Automation → Keyboard shortcuts and restart the app.":
      "Jiná aplikace může mít stejnou kombinaci. Změň písmena v Automatice → Klávesové zkratky a restartuj aplikaci.",
    // legends
    "C + number": "C + číslo", "processor temperature (°C)": "teplota procesoru (°C)", "G + number": "G + číslo",
    "graphics card temperature (°C)": "teplota grafické karty (°C)", "Bar under the number": "Pruh pod číslem",
    "load 0–100 % (blue = low, red = high)": "vytížení 0–100 % (modrá = málo, červená = hodně)", "Number colour": "Barva čísla",
    "green fine · yellow warm · orange warning · red critical": "zelená v pohodě · žlutá teplá · oranžová varování · červená kritická",
    "Big number on top": "Velké číslo nahoře", "FPS – green ≥ 60, yellow ≥ 30, red below 30": "FPS – zelené ≥ 60, žluté ≥ 30, červené pod 30",
    "Left number + orange line": "Číslo vlevo + oranžová linka", "Right number + green line": "Číslo vpravo + zelená linka", "graphics temperature (°C)": "teplota grafiky (°C)",
    "Bottom row": "Spodní řádek",
    "frame time over the last 16 s – green smooth, yellow slower, red / taller bar = stutter. Not ping or mouse latency – only NVIDIA Reflex measures that":
      "latence snímků za posledních 16 s – zelená plynulé, žlutá pomalejší, červená / vyšší sloupek = zásek. Není to ping ani latence myši – tu měří jen NVIDIA Reflex",
    "Controller instead of FPS": "Ovladač místo FPS", "a game runs but RivaTuner isn't measuring FPS yet": "hra běží, ale RivaTuner zatím neměří FPS",
    "Controller + name": "Ovladač + jméno", "a game just started, the gaming HUD follows in a moment": "právě se spustila hra, za chvíli naskočí herní HUD",
    "Top number": "Horní číslo", "hours": "hodiny", "Bottom number": "Dolní číslo", "minutes": "minuty",
    "Blinking dots in the middle": "Blikající tečky uprostřed", "tick every second": "tikají každou sekundu",
    "Side columns": "Boční sloupce", "fill up during the minute – full = end of the minute": "plní se během minuty – plné = konec minuty",
    "Divoom clock": "Hodiny Divoom", "Ditoo's built-in clock face, runs even without the PC": "vestavěný ciferník Ditoo, běží i bez PC",
    "Big number": "Velké číslo", "minutes left (seconds in the last minute)": "zbývající minuty (v poslední minutě sekundy)",
    "MIN / BRK / II": "MIN / PAU / II", "focus / break / paused": "soustředění / přestávka / pozastaveno", "Frame": "Rámeček",
    "time left – switches off bit by bit": "zbývající čas – postupně zhasíná", "Green colour": "Zelená barva", "break": "přestávka",
    "Dimmed number": "Tlumené číslo", "focus length – the timer isn't running, start it with Start": "délka soustředění – časovač neběží, spustíš ho tlačítkem Spustit",
    "Picture": "Obrázek", "current weather (animated rain, snow, sun, storm, fog)": "aktuální počasí (animovaný déšť, sníh, slunce, bouřka, mlha)",
    "Number": "Číslo", "outside temperature – blue freezing, light blue chilly, yellow pleasant, orange hot": "teplota venku – modrá mráz, světle modrá chladno, žlutá příjemně, oranžová horko",
    "T bottom left": "Z vlevo dole", "tomorrow's forecast (high)": "předpověď na zítřek (maximum)",
    "Three dots": "Tři tečky", "downloading the forecast": "stahuji předpověď", "Pin": "Špendlík", "choose your city in Settings to see the weather": "vyber v Nastavení své město, ať vidíš počasí",
    "Orange spark": "Oranžová jiskra", "Claude is working (ring turns clockwise)": "pracuje Claude (kruh obíhá po směru hodinek)",
    "Teal >_": "Tyrkysový >_", "Codex / ChatGPT is working (ring turns counter-clockwise)": "pracuje Codex / ChatGPT (kruh obíhá proti směru hodinek)",
    "Taking turns": "Střídání", "both agents are working at once": "pracují oba agenti najednou",
    "Exclamation mark": "Vykřičník", "the agent needs your approval or answer": "agent potřebuje schválení nebo odpověď",
    "Corner mark": "Značka v rohu", "colour says who: orange Claude, teal Codex": "barva říká kdo: oranžová Claude, tyrkysová Codex",
    "Check mark": "Fajfka", "the agent finished its task": "agent dokončil úlohu", "who finished (orange Claude, teal Codex)": "kdo skončil (oranžová Claude, tyrkysová Codex)",
    "Cross": "Křížek", "the agent reports an error": "agent hlásí chybu", "which agent": "u kterého agenta",
    "Dimmed frame": "Tlumený rámeček", "no agent is working right now": "žádný agent teď nepracuje",
    "Thermometer + number": "Teploměr + číslo", "the temperature passed the critical limit": "teplota přesáhla kritický limit",
    "CPU / GPU": "CPU / GPU", "which part is overheating": "která součástka se přehřívá",
    "Animation": "Animace", "decoration without information – choose it on the Content page": "dekorace bez informací – vybíráš ji na stránce Obsah",
    "your message (Content page)": "tvoje zpráva (stránka Obsah)", "Frame + text": "Rámeček + text",
    "a message from a script or webhook, disappears after one pass": "zpráva ze skriptu nebo webhooku, po přeběhnutí zmizí",
    "your uploaded image or animation": "tvůj nahraný obrázek nebo animace", "Empty frame": "Prázdný rámeček", "upload an image on the Content page": "nahraj obrázek na stránce Obsah",
    "Bars": "Sloupce", "react to sound playing through the Ditoo": "reagují na zvuk hraný přes Ditoo",
    "Colour ": "Barva ", "the display glows like a lamp": "displej svítí jako lampa", "nothing is shown": "nic se nezobrazuje",
    "Rainbow frame + check": "Duhový rámeček + fajfka", "test pattern from the setup": "zkušební obrazec z průvodce",
    // without Afterburner
    "Optional: CPU temperature and FPS": "Volitelně: teplota CPU a FPS",
    "Load and GPU readings come straight from Windows. CPU temperature and FPS need the free MSI Afterburner – until then the display shows CPU load instead.":
      "Vytížení a údaje o GPU jdou přímo z Windows. Teplota CPU a FPS potřebují bezplatný MSI Afterburner – do té doby displej ukazuje místo teploty vytížení CPU.",
    "PC readings": "Údaje z PC", "What the app can read on this PC right now. Nothing here is required.": "Co teď aplikace na tomto PC umí přečíst. Nic z toho není povinné.",
    "needs MSI Afterburner": "potřebuje MSI Afterburner", "FPS in games": "FPS ve hrách", "ready": "připraveno",
    "Want CPU temperature and FPS too?": "Chceš i teplotu CPU a FPS?",
    "Install the free MSI Afterburner (it brings RivaTuner for FPS) and keep it running. In Afterburner → Settings → Monitoring tick \"CPU temperature\". You can do this any time later.":
      "Nainstaluj bezplatný MSI Afterburner (přinese i RivaTuner pro FPS) a nech ho běžet. V Afterburneru → Nastavení → Monitorování zaškrtni „CPU temperature“. Můžeš to udělat kdykoli později.",
    "Number without the ° mark": "Číslo bez značky °",
    "load in % – shown when the temperature isn't available (CPU temperature needs MSI Afterburner)": "vytížení v % – ukáže se, když teplota není k dispozici (teplota CPU potřebuje MSI Afterburner)",
    "I don't see the CPU temperature or FPS": "Nevidím teplotu CPU ani FPS",
    "CPU and GPU load (and GPU temperature on NVIDIA cards) work out of the box. CPU temperature and FPS need the free MSI Afterburner with RivaTuner running – Windows doesn't offer them to normal apps. Until then the display shows CPU load instead.":
      "Vytížení CPU a GPU (a u karet NVIDIA i teplota GPU) fungují hned. Teplota CPU a FPS potřebují běžící bezplatný MSI Afterburner s RivaTunerem – Windows je běžným aplikacím neposkytují. Do té doby displej ukazuje vytížení CPU.",
    "Do I need MSI Afterburner?": "Potřebuji MSI Afterburner?",
    "No. It only adds CPU temperature and FPS. Clock, weather, AI status, effects, games detection from your list and everything else work without it.":
      "Ne. Přidává jen teplotu CPU a FPS. Hodiny, počasí, stav AI, efekty, rozpoznávání her ze seznamu a všechno ostatní funguje i bez něj.",
    "Made by": "Vytvořil",
    "When you're away": "Když nejsi u PC", "Display off when you're away": "Zhasnout displej, když nejsi u PC",
    "Switches the LEDs completely off when you leave the PC, which saves the Ditoo's battery the most. It lights up again as soon as you touch the mouse or keyboard. Never happens while a game is running.":
      "Když odejdeš od PC, úplně zhasne diody – to šetří baterii Ditoo nejvíc. Rozsvítí se hned, jak sáhneš na myš nebo klávesnici. Během hry se to nikdy nestane.",
    "After": "Po", "Minutes without input": "Minuty bez aktivity", "{n} min": "{n} min",
    "Right away when the PC is locked (Win+L)": "Hned při zamčení PC (Win+L)", "Display off when the PC is locked": "Zhasnout displej při zamčení PC",
    "display off": "displej vypnutý", "off – you're away": "vypnuto – nejsi u PC", "Display off – you're away": "Displej vypnutý – nejsi u PC",
    "What happens when the Ditoo battery runs out?": "Co když se Ditoo vybije?",
    "Ditoo doesn't report its battery level over Bluetooth, so the app can't show a percentage. When it switches off, the app shows a message and reconnects by itself once you charge it and switch it on. It also works while charging over USB-C – at a desk, just leave it plugged in.":
      "Ditoo přes Bluetooth nehlásí stav baterie, takže aplikace procenta ukázat neumí. Když se vypne, aplikace ukáže hlášku a sama se znovu připojí, jakmile ho nabiješ a zapneš. Funguje i během nabíjení přes USB-C – u stolu ho klidně nech v nabíječce.",
    "Can I switch the display off completely?": "Jde displej úplně vypnout?",
    "Yes. The Off mode turns the LEDs off (brightness 0). Under Automation the display also switches off when you're away from the PC or lock it, and night brightness can go down to 0.":
      "Ano. Režim Vypnuto zhasne diody (jas 0). V Automatice se displej vypne i když odejdeš od PC nebo ho zamkneš, a noční jas jde nastavit až na 0.", "Author": "Autor", "Source code": "Zdrojový kód",
    // wizard
    "Welcome": "Vítej", "Test": "Test", "Sensors": "Senzory", "Finish": "Hotovo", "Continue": "Pokračovat", "Back": "Zpět", "Skip setup": "Přeskočit průvodce",
    "Welcome to Ditoo Control": "Vítej v Ditoo Control",
    "Let's get your Ditoo Pro reacting to your PC. It takes about a minute.": "Nastavíme, aby tvoje Ditoo Pro reagovalo na PC. Zabere to asi minutu.",
    "Connect your Ditoo": "Připoj své Ditoo",
    "The app talks to Ditoo over Bluetooth. If it doesn't connect on its own, go through these steps.": "Aplikace s Ditoo mluví přes Bluetooth. Pokud se nepřipojí samo, projdi tyto kroky.",
    "Connected to {mac}": "Připojeno k {mac}", "Not connected yet": "Zatím nepřipojeno", "Looking for your Ditoo…": "Hledám tvoje Ditoo…",
    "1. Switch Ditoo on": "1. Zapni Ditoo", "Wait until the display lights up.": "Počkej, až se rozsvítí displej.",
    "2. Pair it with this PC": "2. Spáruj ho s tímto PC",
    "Windows Settings → Bluetooth → Add device → choose \"DitooPro-Audio\".": "Nastavení Windows → Bluetooth → Přidat zařízení → vyber „DitooPro-Audio“.",
    "Open Bluetooth settings": "Otevřít nastavení Bluetooth",
    "3. Disconnect your phone": "3. Odpoj telefon",
    "Ditoo only obeys the first device. Turn off Bluetooth on your phone or close the Divoom app, then switch Ditoo off and on.":
      "Ditoo poslouchá jen první zařízení. Vypni Bluetooth na telefonu nebo zavři aplikaci Divoom a Ditoo vypni a zapni.",
    "4. Try again": "4. Zkus to znovu", "Connect now": "Připojit teď",
    "Let's test it": "Vyzkoušíme to",
    "Press the button and look at your Ditoo. You should see a rainbow frame with a big check mark.": "Stiskni tlačítko a podívej se na Ditoo. Měl bys vidět duhový rámeček s velkou fajfkou.",
    "Show test pattern": "Ukázat zkušební obrazec", "Do you see it?": "Vidíš ho?", "Yes, I see it": "Ano, vidím", "No": "Ne", "Almost there.": "Už jen kousek.",
    "The phone is usually the culprit: turn its Bluetooth off, switch Ditoo off and on, then press Show test pattern again. Still nothing? Go back one step and press Connect now.":
      "Většinou za to může telefon: vypni na něm Bluetooth, Ditoo vypni a zapni a znovu stiskni Ukázat zkušební obrazec. Pořád nic? Vrať se o krok zpět a stiskni Připojit teď.",
    "Temperatures and FPS (optional)": "Teploty a FPS (volitelné)",
    "For the PC monitor and the gaming HUD the app reads data from MSI Afterburner – a free tool many gamers already have.":
      "Pro PC monitor a herní HUD čte aplikace data z MSI Afterburneru – bezplatného nástroje, který má spousta hráčů.",
    "MSI Afterburner is running – temperatures: CPU {c} °C, GPU {g} °C": "MSI Afterburner běží – teploty: CPU {c} °C, GPU {g} °C",
    "MSI Afterburner isn't running": "MSI Afterburner neběží",
    "1. Install MSI Afterburner": "1. Nainstaluj MSI Afterburner", "It installs RivaTuner (FPS) with it. Keep both running.": "Nainstaluje s ním i RivaTuner (FPS). Nech oba běžet.",
    "2. Enable CPU temperature": "2. Zapni teplotu CPU",
    "Afterburner → Settings → Monitoring → tick \"CPU temperature\" and \"CPU usage\".": "Afterburner → Nastavení → Monitorování → zaškrtni „CPU temperature“ a „CPU usage“.",
    "You can skip this": "Tohle můžeš přeskočit", "Everything else works without it.": "Všechno ostatní funguje i bez toho.",
    "Where are you?": "Kde jsi?", "For the animated weather. Only the city is used, nothing else leaves your PC.": "Pro animované počasí. Použije se jen město, nic dalšího tvé PC neopustí.",
    "All set!": "Hotovo!", "Ditoo now runs in Automatic mode. A few handy extras:": "Ditoo teď běží v režimu Automaticky. Pár užitečných doplňků:",
    "Add to the Start menu": "Přidat do nabídky Start", "Show Claude Code status": "Ukazovat stav Claude Code", "Show Codex status": "Ukazovat stav Codexu",
    "You can change everything later. Closing the window keeps the app running in the tray next to the clock.":
      "Všechno můžeš později změnit. Zavřením okna aplikace dál běží v oznamovací oblasti u hodin.",
  },
};

let LANG = "en";
function setLang(code) {
  LANG = CATALOGS[code] ? code : "en";
  document.documentElement.lang = LANG;
}
function t(s, vars) {
  let out = (LANG !== "en" && CATALOGS[LANG][s]) || s;
  if (vars) for (const [k, v] of Object.entries(vars)) out = out.split(`{${k}}`).join(String(v));
  return out;
}
/* Translate static HTML: text nodes and the attributes people read. */
function translatePage(root = document.body) {
  if (LANG === "en") return;
  const cat = CATALOGS[LANG];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const raw = n.nodeValue, key = raw.trim();
    if (key && cat[key]) n.nodeValue = raw.replace(key, cat[key]);
  }
  for (const attr of ["placeholder", "aria-label", "title", "data-help"]) {
    root.querySelectorAll(`[${attr}]`).forEach((el) => { const v = el.getAttribute(attr); if (cat[v]) el.setAttribute(attr, cat[v]); });
  }
}
