# Divoom Ditoo Pro – Bluetooth protocol notes

What Ditoo Control uses, verified on a Ditoo Pro (firmware as of 2026) from Windows 11.
Builds on the reverse-engineering in
[andreas-mausch/divoom-ditoo-pro-controller](https://github.com/andreas-mausch/divoom-ditoo-pro-controller),
[d03n3rfr1tz3/hass-divoom](https://github.com/d03n3rfr1tz3/hass-divoom) and
[RomRider/node-divoom-timebox-evo](https://github.com/RomRider/node-divoom-timebox-evo/blob/master/PROTOCOL.md).

## Transport

- Classic Bluetooth **RFCOMM / SPP** on the device named `DitooPro-Audio` (the BLE radio `DitooPro-Light` uses a different, wrapped protocol).
- On Windows, SDP lists two RFCOMM services: Hands-Free (`0x111E`, held by Windows' audio stack) and Serial Port (`0x1101`). The control channel answered on **RFCOMM channel 2**; the app also tries 1 and 4.
- Python's standard `socket.AF_BLUETOOTH / BTPROTO_RFCOMM` works on Windows – no extra packages.
- **Only the first connected client is obeyed.** If a phone with the Divoom app is connected, writes succeed but are ignored. Disconnect the phone and power-cycle the Ditoo.

## Frame

```
01 | LL LL | CMD | ARGS … | CS CS | 02
```

- `LL LL` – little-endian `len(ARGS) + 3` (command byte + 2 checksum bytes)
- `CS CS` – little-endian 16-bit sum of every byte from `LL` through the last argument
- no escaping on Ditoo

Example – brightness 100: `01 04 00 74 64 dc 00 02`

## Commands used

| Cmd | Name | Args |
|---|---|---|
| `0x74` | brightness | `[0..100]` |
| `0x18` | set date & time | `[year%100, year/100, month, day, hour, min, sec, weekday]` |
| `0x2D` | 12/24 h | `[1 = 24 h]` |
| `0x45` | set view | clock: `[0x00, 24h, style, 0x01, weather, temp, calendar, R, G, B]` · light: `[0x01, R, G, B, brightness, 0, 1, 0, 0, 0, 0]` · visualizer: `[0x04, n]` |
| `0x44` | static image | `[0x00, 0x0A, 0x0A, 0x04] + FRAME` |
| `0x49` | animation chunk | `[total LL LL, chunk index] + up to 200 bytes of concatenated FRAMEs` |
| `0x46` | get view | – (the device answers, handy as a ping) |

## Image frame

```
AA | LL LL | TT TT | 00 | N | N × RGB | pixel indices
```

- `LL LL` – little-endian total frame length including the `AA` and the length itself
- `TT TT` – frame duration in ms (animations), `00 00` for a still image
- `N` – palette size (`0` means 256)
- pixels row by row from the top-left, as palette indices of `max(1, ceil(log2 N))` bits, packed **LSB-first** into a little-endian bit stream, last byte zero-padded

An animation is the concatenation of up to 60 frames (≤ 65 535 bytes), split into 200-byte chunks sent with `0x49`. The device loops it on its own.

## Practical notes

- Re-uploading an animation restarts it – live data (temperatures, FPS) is therefore sent as a still image and only when it changes.
- Keep palettes small (≤ 16–32 colours): upload time grows with bits per pixel.
- The device acknowledges few commands on SPP; don't wait for replies when streaming images.
