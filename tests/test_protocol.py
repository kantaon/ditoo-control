"""Divoom serial protocol: framing, checksums, image encoding, animation chunking."""
import math

from ditoo_control import ditoo


def hexbytes(s):
    return bytes.fromhex(s.replace(" ", ""))


def test_brightness_frame_matches_known_capture():
    assert ditoo.build_message(0x74, [100]) == hexbytes("01 04 00 74 64 dc 00 02")


def test_alarm_frame_matches_published_vector():
    args = [0x00, 0x00, 0x0D, 0x25, 0x00, 0x00, 0x00, 0x00, 0x00, 0x64]
    assert ditoo.build_message(0x43, args) == hexbytes("01 0d 00 43 00 00 0d 25 00 00 00 00 00 64 e6 00 02")


def test_checksum_wraps_at_16_bits():
    msg = ditoo.build_message(0x49, [0xFF] * 300)
    length = msg[1] | msg[2] << 8
    assert length == 303
    assert (msg[-3] | msg[-2] << 8) == sum(msg[1:-3]) & 0xFFFF


def test_single_colour_frame_uses_one_bit_per_pixel():
    frame = ditoo.encode_frame([(10, 20, 30)] * 256)
    assert frame[0] == 0xAA
    assert frame[1] | frame[2] << 8 == len(frame)
    assert frame[6] == 1                      # palette size
    assert frame[7:10] == bytes([10, 20, 30])
    assert len(frame) == 7 + 3 + 32           # 256 px * 1 bit


def test_pixels_are_packed_lsb_first():
    px = [(0, 0, 0)] * 256                    # black is seen first → palette index 0
    px[1] = px[9] = (255, 0, 0)               # red → index 1
    frame = ditoo.encode_frame(px)
    data = frame[7 + 6:]                      # two palette colours
    assert data[0] == 0b0000_0010             # pixel 1 → bit 1 of byte 0
    assert data[1] == 0b0000_0010             # pixel 9 → bit 1 of byte 1


def test_bits_per_pixel_grows_with_palette():
    for colours in (2, 3, 5, 16, 17, 200):
        px = [(i % colours, 0, 0) for i in range(256)]
        frame = ditoo.encode_frame(px)
        bpp = max(1, math.ceil(math.log2(colours)))
        assert len(frame) == 7 + 3 * colours + math.ceil(256 * bpp / 8)


def test_palette_is_reduced_to_256_colours():
    px = [(i, 255 - i, (i * 7) % 256) for i in range(256)]
    px[0] = (1, 2, 3)
    assert len(set(ditoo._reduce_palette(px))) <= 256


class FakeSocket:
    def __init__(self):
        self.sent = []

    def sendall(self, data):
        self.sent.append(bytes(data))


def connected(dev):
    dev.sock = FakeSocket()
    return dev.sock


def test_animation_is_chunked_in_200_byte_pieces():
    dev = ditoo.Ditoo("AA:BB:CC:DD:EE:FF")
    sock = connected(dev)
    frames = [[(f * 10, 0, 0) if (x + f) % 3 else (0, 0, 0) for x in range(256)] for f in range(10)]
    dev.animation([(f, 100) for f in frames])
    total = sum(len(ditoo.encode_frame(f, 100)) for f in frames)
    assert len(sock.sent) == math.ceil(total / 200)
    for i, msg in enumerate(sock.sent):
        assert msg[3] == 0x49
        assert msg[4] | msg[5] << 8 == total
        assert msg[6] == i


def test_identical_image_is_not_resent():
    dev = ditoo.Ditoo("AA:BB:CC:DD:EE:FF")
    sock = connected(dev)
    px = [(1, 2, 3)] * 256
    dev.image(px)
    dev.image(px)
    assert len(sock.sent) == 1
    dev.image(px, force=True)
    assert len(sock.sent) == 2
