"""Minimal VPK v1/v2 directory reader + content extractor.

Used by the particle killer to:
  1) Read pak01_dir.vpk and enumerate every file inside the VPK chain
  2) Pull bytes out of the right pak01_NNN.vpk for any given entry
"""
from __future__ import annotations

import struct
from pathlib import Path


def _read_cstring(buf: bytes, off: int) -> tuple[str, int]:
    end = buf.index(b"\x00", off)
    return buf[off:end].decode("utf-8", errors="replace"), end + 1


def parse_vpk_dir(path: Path) -> tuple[int, list[dict]]:
    data = path.read_bytes()
    sig, version, tree_size = struct.unpack_from("<III", data, 0)
    if sig != 0x55AA1234:
        raise ValueError(f"Not a VPK file: {path} (bad magic {sig:#x})")
    if version == 1:
        header = 12
    elif version == 2:
        header = 12 + 16
    else:
        raise ValueError(f"Unsupported VPK version {version}")

    pos = header
    tree_end = header + tree_size
    entries: list[dict] = []
    while pos < tree_end:
        ext, pos = _read_cstring(data, pos)
        if ext == "":
            break
        while True:
            dir_path, pos = _read_cstring(data, pos)
            if dir_path == "":
                break
            while True:
                fname, pos = _read_cstring(data, pos)
                if fname == "":
                    break
                crc32, preload, archive_index, entry_offset, entry_length, _term = (
                    struct.unpack_from("<IHHIIH", data, pos)
                )
                pos += 18
                preload_data = data[pos : pos + preload]
                pos += preload
                if dir_path:
                    full = f"{dir_path}/{fname}.{ext}"
                else:
                    full = f"{fname}.{ext}"
                entries.append(
                    {
                        "ext": ext,
                        "path": dir_path,
                        "name": fname,
                        "full": full,
                        "archive_index": archive_index,
                        "entry_offset": entry_offset,
                        "entry_length": entry_length,
                        "preload": preload_data,
                        "crc32": crc32,
                    }
                )
    return version, entries


def read_entry_bytes(entry: dict, dir_vpk_path: Path) -> bytes:
    """Read the full bytes of a VPK entry. archive_index 0x7FFF means data is
    embedded in the dir.vpk after the tree. Otherwise read from pak01_NNN.vpk."""
    base = dir_vpk_path.with_name(dir_vpk_path.name.replace("_dir.vpk", ""))
    archive_index = entry["archive_index"]
    if archive_index == 0x7FFF:
        # Embedded inside _dir.vpk after the tree; the offset is from end of tree.
        with open(dir_vpk_path, "rb") as f:
            sig, version, tree_size = struct.unpack("<III", f.read(12))
            header = 12 if version == 1 else 28
            f.seek(header + tree_size + entry["entry_offset"])
            data = f.read(entry["entry_length"])
    else:
        archive_path = base.with_name(f"{base.name}_{archive_index:03d}.vpk")
        with open(archive_path, "rb") as f:
            f.seek(entry["entry_offset"])
            data = f.read(entry["entry_length"])
    return entry["preload"] + data


def find_dota_install() -> Path | None:
    """Best-effort: try common Steam paths."""
    candidates = [
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta"),
        Path(r"C:\Program Files\Steam\steamapps\common\dota 2 beta"),
        Path(r"D:\Steam\steamapps\common\dota 2 beta"),
        Path(r"D:\SteamLibrary\steamapps\common\dota 2 beta"),
        Path(r"E:\Steam\steamapps\common\dota 2 beta"),
        Path(r"E:\SteamLibrary\steamapps\common\dota 2 beta"),
        Path(r"F:\Steam\steamapps\common\dota 2 beta"),
        Path(r"F:\SteamLibrary\steamapps\common\dota 2 beta"),
        Path.home() / ".steam/steam/steamapps/common/dota 2 beta",
        Path.home() / ".local/share/Steam/steamapps/common/dota 2 beta",
    ]
    for c in candidates:
        if (c / "game" / "dota" / "pak01_dir.vpk").exists():
            return c
    return None
