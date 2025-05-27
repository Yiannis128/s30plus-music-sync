#!/usr/bin/env python3

from pathlib import Path
import datetime


def _encode_playlist_entry(file_path: str) -> bytes:
    # Encode the filename to bytes (e.g., UTF-8)
    filename_bytes = file_path.encode("utf-8")

    # Make sure it's not too long
    if len(filename_bytes) > 0x100:
        raise ValueError("Filename is too long to encode (max 256 bytes)")

    # Right-pad the filename to exactly 256 bytes
    padded_filename = filename_bytes.ljust(0x100, b"\x00")

    # Add a single byte for the length of the original filename
    length_byte = len(filename_bytes).to_bytes(1, "little")

    # Add 0x13 (19) bytes of null padding
    trailing_padding = b"\x00" * 0x13

    # Return the full encoded entry
    return padded_filename + length_byte + trailing_padding


def _write_listinfo(nokia_root: Path, playlists: dict) -> None:
    data_path: Path = nokia_root / "System" / "Mp3_res"
    listinfo_path: Path = data_path / "listinfo.data"
    assert data_path.exists()
    with open(listinfo_path, "wb") as file:
        # Write header
        file.write("MUSICARRAY SAVEFILE 01.00.0".encode("ascii"))
        # Add padding
        file.write(b"\x00" * 8)
        # Write playlists
        for playlist in playlists.keys():
            # Encode the filepath relative to the Nokia
            playlist_str: str = f"E:\\System\\Mp3_res\\{playlist}.lst"
            file.write(_encode_playlist_entry(playlist_str))


import struct


def _encode_music_entry(file_path: str, day: int, month: int, year: int) -> bytes:
    # Encode file path as UTF-16LE, truncate/pad to 0x100 chars = 512 bytes
    encoded_path = file_path.encode("utf-16le")
    encoded_path = encoded_path[:512]  # truncate if too long
    encoded_path += b"\x00" * (512 - len(encoded_path))  # pad if too short

    length = len(file_path)  # number of characters (not bytes)
    padding_1 = b"\x00"
    padding_2 = b"\x00"
    padding_3 = b"\x00"
    unknown = b"\x00" * 8  # default unknown value

    # Pack the values using little-endian format
    return (
        encoded_path
        + struct.pack("<B", length)  # u8 length
        + padding_1  # 1 byte padding
        + struct.pack("<B", day)  # u8 day
        + struct.pack("<B", month)  # u8 month
        + struct.pack("<H", year)  # u16 year
        + padding_2  # 1 byte padding
        + unknown  # 8 bytes unknown
        + padding_3  # 1 byte padding
    )


def _write_playlist(nokia_root: Path, playlist_name: str, playlist: dict) -> None:
    music_dest_dir: Path = nokia_root / "Music"
    data_path: Path = nokia_root / "System" / "Mp3_res" / (playlist_name + ".lst")
    with open(data_path, "wb") as f:
        # Write header
        f.write("MUSICARRAY SAVEFILE 01.00.0".encode("ascii"))

        # Write playlists
        for entry in playlist["entries"]:
            title: str = entry["title"]
            timestamp: int = entry["timestamp"]
            dt = datetime.datetime.utcfromtimestamp(timestamp)
            f.write(
                _encode_music_entry(
                    f"E:\\Music\\{title}.mp3", dt.day, dt.month, dt.year
                )
            )


def write_playlists(nokia_root: Path, music_path: Path, playlists: dict) -> None:
    assert nokia_root.exists() and nokia_root.is_dir()
    # if (nokia_root / "Music").exists():
    #     shutil.rmtree(nokia_root / "Music")

    # shutil.copytree(music_path, nokia_root / "Music")
    # Write the listinfo.data
    _write_listinfo(nokia_root, playlists)
    # Write the playlist data
    for playlist_name, playlist_data in playlists.items():
        _write_playlist(nokia_root, playlist_name, playlist_data)

    print("Finsihed")
