r"""set_launch_option.py
==============================================================
Adds (or removes) ``-language <locale>`` to/from your Steam
"Dota 2 launch options" by editing ``localconfig.vdf`` for every
Steam account that has Dota 2 data.

Why this exists
---------------
The pak66_dir.vpk built by ``apply_mods.py`` /
``kill_particles_pak66.py`` is written to
``<dota>/game/dota_<locale>/`` (mirroring dota2-minify's design).
Dota 2 only mounts that folder when Steam launches the game with
``-language <locale>``. This helper writes that flag automatically
instead of asking you to dig through Steam's UI.

This is the same routine dota2-minify performs in its
``core/steam.py``.

USAGE
-----
::

    # Add `-language minify` to Dota 2 launch options for every Steam
    # account that has Dota 2 data on this machine.
    python set_launch_option.py --locale minify

    # Remove `-language <locale>` (and only that one).
    python set_launch_option.py --locale minify --remove

    # See what would change without writing.
    python set_launch_option.py --locale minify --dry-run

WARNINGS
--------
* You MUST close Steam first. Steam writes ``localconfig.vdf`` on
  exit and will overwrite our edit otherwise. The script refuses
  to run if a process named ``steam`` (or ``steam.exe``) is alive.
* A timestamped ``.bak`` backup of every modified ``localconfig.vdf``
  is created next to the original. Restore by copying the backup
  back over the file.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    import vdf
except ImportError:
    print("ERROR: 'vdf' Python package not installed.")
    print("       Install it with:   pip install vdf")
    sys.exit(1)


DOTA_2_APPID = "570"


# ---------------------------------------------------------------------------
# Steam discovery
# ---------------------------------------------------------------------------


def find_steam_root() -> Path | None:
    """Find the Steam root directory.

    On Windows, prefer the registry. On Linux/Mac fall back to known paths."""
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as k:
                steam_path = winreg.QueryValueEx(k, "InstallPath")[0]
                p = Path(steam_path)
                if p.exists():
                    return p
        except OSError:
            pass

        # Fallback to default locations
        for default in [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
        ]:
            p = Path(default)
            if p.exists():
                return p

    elif sys.platform == "darwin":
        p = Path.home() / "Library" / "Application Support" / "Steam"
        if p.exists():
            return p

    else:  # Linux
        for default in [
            Path.home() / ".local" / "share" / "Steam",
            Path.home() / ".steam" / "steam",
        ]:
            if default.exists():
                return default

    return None


def find_user_localconfigs(steam_root: Path) -> list[Path]:
    """Return every localconfig.vdf that has a Dota 2 entry."""
    userdata = steam_root / "userdata"
    if not userdata.is_dir():
        return []

    matches: list[Path] = []
    for entry in sorted(userdata.iterdir()):
        if not entry.is_dir() or not entry.name.isdigit():
            continue
        cfg = entry / "config" / "localconfig.vdf"
        if not cfg.is_file():
            continue
        # Only touch accounts that actually have Dota 2 data
        dota_dir = entry / DOTA_2_APPID
        if not dota_dir.is_dir():
            continue
        matches.append(cfg)
    return matches


def is_steam_running() -> bool:
    """Refuse to edit localconfig.vdf while Steam is running."""
    name = "steam.exe" if sys.platform == "win32" else "steam"
    try:
        if sys.platform == "win32":
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", "replace")
            return name.lower() in out.lower()
        else:
            out = subprocess.check_output(["pgrep", "-x", name], stderr=subprocess.DEVNULL)
            return bool(out.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ---------------------------------------------------------------------------
# launchoption mutation
# ---------------------------------------------------------------------------


def split_args(s: str) -> list[str]:
    return s.split() if s else []


def remove_language_arg(tokens: list[str], locale: str | None = None) -> list[str]:
    """Drop a single ``-language <X>`` pair (any X if locale is None,
    else only the matching one). Other args preserved."""
    out: list[str] = []
    skip = False
    for i, tok in enumerate(tokens):
        if skip:
            skip = False
            continue
        if tok == "-language" and i + 1 < len(tokens) and not tokens[i + 1].startswith(("-", "+")):
            if locale is None or tokens[i + 1] == locale:
                skip = True
                continue
        out.append(tok)
    return out


def set_language_arg(tokens: list[str], locale: str) -> list[str]:
    """Strip any existing -language pair, then prepend ``-language <locale>``."""
    cleaned = remove_language_arg(tokens, locale=None)
    return ["-language", locale] + cleaned


def update_vdf(
    cfg_path: Path,
    locale: str,
    *,
    remove: bool,
    dry_run: bool,
) -> tuple[bool, str, str]:
    """Edit one localconfig.vdf. Returns (changed, before, after)."""
    with cfg_path.open("r", encoding="utf-8", errors="replace") as f:
        data = vdf.load(f)

    apps = (
        data.get("UserLocalConfigStore", {})
        .get("Software", {})
        .get("Valve", {})
        .get("Steam", {})
        .get("apps", {})
    )
    if DOTA_2_APPID not in apps:
        return False, "", ""

    dota_node = apps[DOTA_2_APPID]
    before = dota_node.get("LaunchOptions", "")
    tokens = split_args(before)

    if remove:
        new_tokens = remove_language_arg(tokens, locale)
    else:
        new_tokens = set_language_arg(tokens, locale)

    after = " ".join(new_tokens)
    if before == after:
        return False, before, after

    if dry_run:
        return True, before, after

    backup = cfg_path.with_suffix(cfg_path.suffix + f".bak.{int(time.time())}")
    shutil.copy2(cfg_path, backup)

    dota_node["LaunchOptions"] = after
    with cfg_path.open("w", encoding="utf-8") as f:
        vdf.dump(data, f, pretty=True)
    return True, before, after


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--locale", default="minify",
                    help="Locale folder name; e.g. 'minify' or 'russian'. Default: 'minify'.")
    ap.add_argument("--remove", action="store_true",
                    help="Remove '-language <locale>' instead of adding it.")
    ap.add_argument("--steam-root", type=Path, default=None,
                    help="Override autodetected Steam root.")
    ap.add_argument("--dry-run", action="store_true", help="Print changes, don't write.")
    ap.add_argument("--force", action="store_true",
                    help="Edit localconfig.vdf even if Steam looks like it's running. "
                         "Steam will overwrite your edits on exit if this is on.")
    args = ap.parse_args()

    if not args.locale or "/" in args.locale or "\\" in args.locale:
        print("ERROR: --locale must be a single token (no slashes)")
        return 1

    if is_steam_running() and not args.force:
        print("ERROR: Steam appears to be running. Close Steam first")
        print("       (otherwise Steam overwrites localconfig.vdf on exit and "
              "your -language change disappears).")
        print("       To skip this check pass --force.")
        return 1

    steam_root = args.steam_root or find_steam_root()
    if not steam_root or not steam_root.exists():
        print("ERROR: Could not find Steam root. Pass --steam-root <path>.")
        return 1
    print(f"[+] Steam root: {steam_root}")

    cfgs = find_user_localconfigs(steam_root)
    if not cfgs:
        print(f"[!] No Steam accounts with Dota 2 (appid {DOTA_2_APPID}) data found under {steam_root / 'userdata'}.")
        return 1

    print(f"[+] Found {len(cfgs)} Steam account(s) with Dota 2 data:")
    for c in cfgs:
        print(f"    - {c.parent.parent.name}  ({c})")

    changed = 0
    for cfg in cfgs:
        try:
            did, before, after = update_vdf(cfg, args.locale, remove=args.remove, dry_run=args.dry_run)
        except Exception as e:
            print(f"[!] Failed to update {cfg}: {e}")
            continue
        action = "DRY-RUN" if args.dry_run else "WROTE"
        if did:
            changed += 1
            print(f"[+] {action} {cfg}")
            print(f"      before: {before!r}")
            print(f"      after:  {after!r}")
        else:
            print(f"[+] (no change) {cfg}")
            print(f"      keeps: {before!r}")

    print()
    if args.dry_run:
        print(f"DRY RUN done. {changed} of {len(cfgs)} would change.")
    else:
        print(f"Done. {changed} of {len(cfgs)} updated.")
        if changed and not args.remove:
            print(f"Now restart Steam and Dota 2. The game will mount dota_{args.locale}/ overlays.")
        elif changed and args.remove:
            print("Now restart Steam. Overrides are off.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
