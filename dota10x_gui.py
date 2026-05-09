#!/usr/bin/env python3
r"""dota10x_gui.py
==============================================================
Tiny Tkinter front-end for the dota10x-lowspec toolkit.

Lets you point-and-click pick a particle preset, an asset-strip
bundle, and which visual mods to apply, then runs the underlying
CLI scripts in the right order with --merge:

    1) kill_particles_pak66.py --preset <preset>
    2) strip_assets_pak66.py   --categories <bundle> --merge
    3) apply_mods.py           --mods <list>          --merge
    4) set_launch_option.py    --locale <locale>

A "Build pak66" button kicks off the whole pipeline. Output of
each step is streamed live into a log pane. An "Uninstall" button
runs ``apply_mods.py --uninstall`` (which is the canonical
uninstaller -- it just deletes ``<dota>/game/dota_<locale>/``).

Requires nothing beyond stdlib Tkinter + the same Python deps
the CLI scripts already need (``vpk``, ``vdf``).

USAGE:
    python dota10x_gui.py
or double-click dota10x_gui.bat on Windows.
"""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

REPO = Path(__file__).resolve().parent
KILL_PARTICLES_PY = REPO / "5_pak66_builder" / "kill_particles_pak66.py"
STRIP_ASSETS_PY = REPO / "5_pak66_builder" / "strip_assets_pak66.py"
APPLY_MODS_PY = REPO / "6_minify_mods" / "apply_mods.py"
SET_LAUNCH_PY = REPO / "5_pak66_builder" / "set_launch_option.py"
MODS_ROOT = REPO / "vendor" / "dota2-minify" / "mods"

PARTICLE_PRESETS = [
    ("off",         "Off  (skip particle stubbing)"),
    ("safe",        "Safe  (~19,700 \u2014 heroes / items / spells)"),
    ("aggressive",  "Aggressive  (~30,400 \u2014 + cosmetics, weather, ambient)"),
    ("total",       "Total  (~80,700 \u2014 every .vpcf_c in the VPK)"),
]

STRIP_BUNDLES = [
    ("off",            "Off  (skip asset stripping)"),
    ("all-safe",       "all-safe       (8 cat, ~7.6 GB stubbed)"),
    ("all-aggressive", "all-aggressive (19 cat, ~37.6 GB stubbed)"),
    ("all-extreme",    "all-extreme    (23 cat, ~55.6 GB stubbed)"),
    ("all-nuclear",    "all-nuclear    (32 cat, ~57.1 GB stubbed)"),
    ("all-suicide",    "all-suicide    (42 cat, ~58.3 GB \u2014 may break events)"),
]


def list_mods() -> list[str]:
    if not MODS_ROOT.is_dir():
        return []
    return sorted(p.name for p in MODS_ROOT.iterdir() if p.is_dir())


# Mods that the CLI cannot fully apply (need Workshop Tools to compile .vcss_c).
# We still show them but disabled.
WORKSHOP_TOOLS_REQUIRED = {
    "Remove Hero Renders",
    "Remove Showcases",
    "Remove Main Menu Background",
}


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("dota10x-lowspec :: Builder")
        self.geometry("820x800")
        self.minsize(740, 720)

        # ---- shared state ----
        self.proc: subprocess.Popen | None = None
        self.proc_lock = threading.Lock()
        self.log_queue: queue.Queue[str | None] = queue.Queue()

        self.locale_var = tk.StringVar(value="minify")
        self.particle_var = tk.StringVar(value="total")
        self.bundle_var = tk.StringVar(value="all-extreme")
        self.mod_all_var = tk.BooleanVar(value=True)
        self.set_launch_var = tk.BooleanVar(value=True)

        # Per-mod checkboxes (only used when "all" is unchecked)
        self.mod_vars: dict[str, tk.BooleanVar] = {}
        self.mod_checks: dict[str, ttk.Checkbutton] = {}

        self._build_ui()
        self._poll_log_queue()

    # -----------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------
    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}

        # Top: locale
        top = ttk.Frame(self)
        top.pack(fill="x", **pad)
        ttk.Label(top, text="Locale folder:").pack(side="left")
        e = ttk.Entry(top, textvariable=self.locale_var, width=14)
        e.pack(side="left", padx=(6, 0))
        ttk.Label(
            top,
            text="(VPK goes into game/dota_<locale>/, Steam needs -language <locale>)",
            foreground="#666",
        ).pack(side="left", padx=(8, 0))

        # ---- Step 1: particles ----
        f1 = ttk.LabelFrame(self, text="Step 1: Particles  (kill_particles_pak66)")
        f1.pack(fill="x", **pad)
        for value, label in PARTICLE_PRESETS:
            ttk.Radiobutton(
                f1, text=label, value=value, variable=self.particle_var
            ).pack(anchor="w", padx=12, pady=1)

        # ---- Step 2: asset bundles ----
        f2 = ttk.LabelFrame(self, text="Step 2: Asset stripping  (strip_assets_pak66)")
        f2.pack(fill="x", **pad)
        for value, label in STRIP_BUNDLES:
            ttk.Radiobutton(
                f2, text=label, value=value, variable=self.bundle_var
            ).pack(anchor="w", padx=12, pady=1)

        # ---- Step 3: mods ----
        f3 = ttk.LabelFrame(self, text="Step 3: Visual mods  (apply_mods)")
        f3.pack(fill="x", **pad)
        ttk.Checkbutton(
            f3,
            text="Apply all available mods (recommended)",
            variable=self.mod_all_var,
            command=self._on_mod_all_toggle,
        ).pack(anchor="w", padx=12, pady=2)

        ttk.Label(
            f3, text="\u2014 or pick individually \u2014", foreground="#666"
        ).pack(anchor="w", padx=12)

        grid = ttk.Frame(f3)
        grid.pack(fill="x", padx=12, pady=(0, 6))

        all_mods = list_mods()
        cols = 2
        for i, m in enumerate(all_mods):
            v = tk.BooleanVar(value=False)
            self.mod_vars[m] = v
            disabled = m in WORKSHOP_TOOLS_REQUIRED
            text = m + ("  (needs Workshop Tools - skipped)" if disabled else "")
            cb = ttk.Checkbutton(grid, text=text, variable=v)
            if disabled:
                cb.state(["disabled"])
            cb.grid(row=i // cols, column=i % cols, sticky="w", padx=2, pady=1)
            self.mod_checks[m] = cb
        # Initially "Apply all" is on, so individual checkboxes are disabled.
        self._on_mod_all_toggle()

        # ---- Step 4: launch option ----
        f4 = ttk.LabelFrame(self, text="Step 4: Steam launch flag  (set_launch_option)")
        f4.pack(fill="x", **pad)
        ttk.Checkbutton(
            f4,
            text="Auto-add  -language <locale>  to Dota 2 launch options",
            variable=self.set_launch_var,
        ).pack(anchor="w", padx=12, pady=2)
        ttk.Label(
            f4,
            text="(Steam must be CLOSED. Edits are made to localconfig.vdf, .bak written.)",
            foreground="#666",
        ).pack(anchor="w", padx=12)

        # ---- buttons ----
        bf = ttk.Frame(self)
        bf.pack(fill="x", **pad)
        self.build_btn = ttk.Button(bf, text="Build pak66", command=self.on_build)
        self.build_btn.pack(side="left", padx=(0, 6))
        self.uninstall_btn = ttk.Button(
            bf, text="Uninstall", command=self.on_uninstall
        )
        self.uninstall_btn.pack(side="left", padx=6)
        self.cancel_btn = ttk.Button(
            bf, text="Cancel", command=self.on_cancel, state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=6)
        ttk.Button(bf, text="Clear log", command=self._clear_log).pack(
            side="right"
        )

        # ---- log ----
        f5 = ttk.LabelFrame(self, text="Output log")
        f5.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(
            f5, wrap="word", height=18, state="disabled",
            font=("Consolas", 9),
        )
        self.log.pack(fill="both", expand=True, padx=4, pady=4)
        self.log.tag_config("err", foreground="#c0392b")
        self.log.tag_config("ok",  foreground="#27ae60")

        # status
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status, foreground="#666").pack(
            anchor="w", padx=10, pady=(0, 6)
        )

    def _on_mod_all_toggle(self) -> None:
        all_on = self.mod_all_var.get()
        for m, cb in self.mod_checks.items():
            if m in WORKSHOP_TOOLS_REQUIRED:
                continue
            cb.state(["disabled"] if all_on else ["!disabled"])

    # -----------------------------------------------------------------
    # logging
    # -----------------------------------------------------------------
    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _append_log(self, line: str, tag: str | None = None) -> None:
        self.log.configure(state="normal")
        if tag:
            self.log.insert("end", line, (tag,))
        else:
            self.log.insert("end", line)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll_log_queue(self) -> None:
        try:
            while True:
                item = self.log_queue.get_nowait()
                if item is None:
                    self._on_proc_done()
                else:
                    self._append_log(item)
        except queue.Empty:
            pass
        self.after(80, self._poll_log_queue)

    # -----------------------------------------------------------------
    # commands
    # -----------------------------------------------------------------
    def _validate_locale(self) -> str | None:
        loc = self.locale_var.get().strip()
        if not loc or "/" in loc or "\\" in loc:
            messagebox.showerror(
                "Bad locale", "Locale must be a single folder name (no slashes)."
            )
            return None
        return loc

    def _selected_mods_arg(self) -> str:
        if self.mod_all_var.get():
            return "all"
        picked = [m for m, v in self.mod_vars.items() if v.get()]
        return ",".join(picked)

    def on_build(self) -> None:
        loc = self._validate_locale()
        if loc is None:
            return

        particle = self.particle_var.get()
        bundle = self.bundle_var.get()
        mods_arg = self._selected_mods_arg()

        steps: list[tuple[str, list[str]]] = []
        # The first non-off step writes a fresh pak66; subsequent ones merge.
        merged = False

        def py(*args: str) -> list[str]:
            return [sys.executable, "-u", *args]

        if particle != "off":
            steps.append((
                f"Step 1: kill_particles_pak66 --preset {particle}",
                py(
                    str(KILL_PARTICLES_PY),
                    "--preset", particle,
                    "--locale", loc,
                ),
            ))
            merged = True

        if bundle != "off":
            cmd = py(
                str(STRIP_ASSETS_PY),
                "--categories", bundle,
                "--locale", loc,
            )
            if merged:
                cmd.append("--merge")
            steps.append((
                f"Step 2: strip_assets_pak66 --categories {bundle}"
                + ("  (merge)" if merged else ""),
                cmd,
            ))
            merged = True

        if mods_arg:
            cmd = py(
                str(APPLY_MODS_PY),
                "--mods", mods_arg,
                "--locale", loc,
            )
            if merged:
                cmd.append("--merge")
            steps.append((
                f"Step 3: apply_mods --mods {mods_arg!r}"
                + ("  (merge)" if merged else ""),
                cmd,
            ))
            merged = True

        if self.set_launch_var.get():
            steps.append((
                f"Step 4: set_launch_option --locale {loc}",
                py(str(SET_LAUNCH_PY), "--locale", loc),
            ))

        if not steps:
            messagebox.showinfo(
                "Nothing to do",
                "All four steps are off and no mods are selected. Pick at least one.",
            )
            return

        if not messagebox.askokcancel(
            "Confirm",
            f"About to run {len(steps)} step(s).\n\n"
            "Steam must be CLOSED (otherwise it overwrites the launch flag\n"
            "edit on exit and corrupts pak66 mounting).\n\n"
            "Proceed?",
        ):
            return

        self._set_running(True)
        self._append_log(
            "\n" + "=" * 60 + "\n"
            f"  Starting build: {len(steps)} step(s)\n"
            + "=" * 60 + "\n"
        )
        self.status.set(f"Running step 1 of {len(steps)}...")
        threading.Thread(
            target=self._run_pipeline, args=(steps,), daemon=True
        ).start()

    def on_uninstall(self) -> None:
        loc = self._validate_locale()
        if loc is None:
            return
        if not messagebox.askokcancel(
            "Confirm uninstall",
            f"This will:\n"
            f"  1. Delete <dota>/game/dota_{loc}/ (the entire override folder)\n"
            f"  2. Remove '-language {loc}' from Steam launch options\n"
            "\nSteam must be CLOSED. Proceed?",
        ):
            return

        steps: list[tuple[str, list[str]]] = [
            (
                f"Removing dota_{loc}/",
                [sys.executable, "-u", str(APPLY_MODS_PY),
                 "--uninstall", "--locale", loc],
            ),
            (
                f"Removing '-language {loc}' from Steam launch options",
                [sys.executable, "-u", str(SET_LAUNCH_PY),
                 "--locale", loc, "--remove"],
            ),
        ]
        self._set_running(True)
        self._append_log(
            "\n" + "=" * 60 + "\n  Uninstalling...\n" + "=" * 60 + "\n"
        )
        self.status.set("Uninstalling...")
        threading.Thread(
            target=self._run_pipeline, args=(steps,), daemon=True
        ).start()

    def on_cancel(self) -> None:
        with self.proc_lock:
            if self.proc and self.proc.poll() is None:
                try:
                    self.proc.terminate()
                except OSError:
                    pass
                self.status.set("Cancel requested...")

    # -----------------------------------------------------------------
    # subprocess pipeline (background thread)
    # -----------------------------------------------------------------
    def _run_pipeline(self, steps: list[tuple[str, list[str]]]) -> None:
        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(
                subprocess, "CREATE_NO_WINDOW", 0x08000000
            )

        had_err = False
        for i, (title, cmd) in enumerate(steps, start=1):
            self.log_queue.put(f"\n[{i}/{len(steps)}] {title}\n")
            self.log_queue.put(f"      $ {' '.join(cmd)}\n\n")
            try:
                with self.proc_lock:
                    self.proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        creationflags=creationflags,
                        cwd=str(REPO),
                    )
                assert self.proc.stdout is not None
                for line in self.proc.stdout:
                    self.log_queue.put(line)
                rc = self.proc.wait()
            except Exception as e:
                self.log_queue.put(f"\n[!] Failed to start: {e}\n")
                had_err = True
                break
            finally:
                with self.proc_lock:
                    self.proc = None

            if rc != 0:
                self.log_queue.put(
                    f"\n[!] Step {i} exited with code {rc}. Stopping pipeline.\n"
                )
                had_err = True
                break

        if not had_err:
            self.log_queue.put(
                "\n" + "=" * 60 + "\n"
                "  Done. Restart Steam + Dota 2 for changes to take effect.\n"
                + "=" * 60 + "\n"
            )
        self.log_queue.put(None)  # sentinel = pipeline finished

    def _on_proc_done(self) -> None:
        self._set_running(False)
        self.status.set("Ready.")

    def _set_running(self, running: bool) -> None:
        state = ["disabled"] if running else ["!disabled"]
        for btn in (self.build_btn, self.uninstall_btn):
            btn.state(state)
        self.cancel_btn.state(["!disabled"] if running else ["disabled"])


def main() -> int:
    if not REPO.is_dir():
        print(f"ERROR: repo root not found: {REPO}", file=sys.stderr)
        return 1
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
