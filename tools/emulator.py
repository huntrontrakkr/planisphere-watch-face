"""Run the face in an isolated QEMU Pebble. Never a real watch.

    <pebble-tool-python> tools/emulator.py <emery|gabbro> shots [--time ...] [--shots 0,2,4] [--gdb expr ...]
    <pebble-tool-python> tools/emulator.py <emery|gabbro> profile [--fn frame update ...]

shots    boots with the clock at --time (UTC), installs watchface/build/watchface.pbw
         (or --pbw), starts it, saves a screendump (PNG) at each listed second.
         --update PBW --update-at T installs another package over the running
         face as the phone does when the store has a newer version.
         --icount N runs the CPU at a fixed 2^N ns an instruction (3: 125 MIPS)
         instead of as fast as the PC can, for a real watch's pace.
         The watch's own log (system and app) goes to <out>/<platform>-serial.log.
profile  counts the Thumb instructions executed by one call of each named
         app function (QEMU block traces; instructions, not cycles), by
         function: fw: the firmware, app: main.c, plan: the renderer's code.

Needs the SDL/pulse libraries: staged in /tmp/dymaxion-runtime (Radiant notes), else ~/.local/lib/pebble-emulator.
"""
import argparse, bz2, json, os, re, socket, subprocess, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "watchface"
SDK = Path.home() / ".local/share/pebble-sdk/SDKs/current"
TOOLS = SDK / "toolchain/arm-none-eabi/bin"
RUNTIME = "/tmp/dymaxion-runtime/usr/lib/x86_64-linux-gnu"
if not Path(RUNTIME).is_dir():                     # (the staged copy is gone after a restart: the kept one)
    RUNTIME = str(Path.home() / ".local/lib/pebble-emulator")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Monitor:
    def __init__(self, port):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=60)
        self.read()

    def read(self):
        data = b""
        while b"(qemu)" not in data:
            block = self.s.recv(65536)
            if not block:
                break
            data += block
        return data.decode(errors="replace")

    def cmd(self, c):
        self.s.sendall((c + "\n").encode())
        return self.read()


class Emu:
    def __init__(self, plat, when, out, trace=None, icount=None, events=(), exec_filter=None, utc_offset=0):
        self.utc_offset = utc_offset           # minutes the watch's local time runs ahead of UTC
        self.exec_filter = exec_filter
        self.plat, self.out, self.when = plat, out, when
        self.ports = {k: free_port() for k in ["app", "serial", "gdb", "monitor"]}
        flash = out / f"{plat}-spi-flash.bin"
        flash.write_bytes(bz2.decompress((SDK / f"sdk-core/pebble/{plat}/qemu/qemu_spi_flash.bin.bz2").read_bytes()))
        p = self.ports
        args = [str(SDK / "toolchain/bin/qemu-pebble"), "-machine", f"pebble-{plat}", "-cpu", "cortex-m33",
                "-rtc", f"base={when}",
                "-serial", "null", "-serial", f"tcp:127.0.0.1:{p['app']},server=on,wait=off",
                "-serial", f"tcp:127.0.0.1:{p['serial']},server=on,wait=off",
                "-kernel", str(SDK / f"sdk-core/pebble/{plat}/qemu/qemu_micro_flash.bin"),
                "-drive", f"if=mtd,format=raw,file={flash}",
                "-gdb", f"tcp:127.0.0.1:{p['gdb']},server=on,wait=off",
                "-monitor", f"tcp:127.0.0.1:{p['monitor']},server=on,wait=off",
                "-audio", "driver=none,id=audio0", "-display", "none"]
        if trace:
            args += ["-d", "in_asm,nochain", "-D", str(trace)]
        if getattr(self, "exec_filter", None):              # every run of the blocks at these addresses
            args += ["-d", "exec,nochain", "-dfilter", self.exec_filter[0], "-D", str(self.exec_filter[1])]
        for ev in events:                                  # QEMU trace events, into the QEMU log
            args += ["-trace", ev]
        if icount is not None:
            args += ["-icount", f"shift={icount},sleep=on"]
            args[args.index("-rtc") + 1] += ",clock=vm"     # the watch's clock keeps the CPU's time
        env = dict(os.environ, LD_LIBRARY_PATH=f"{RUNTIME}:{RUNTIME}/pulseaudio")
        self.log = open(out / f"{plat}-qemu.log", "wb")
        self.q = subprocess.Popen(args, env=env, stdout=self.log, stderr=self.log, start_new_session=True)
        self.mon = None
        self.add = None

    def serial_log(self):
        """The firmware's debug serial (its log) into a file, in the background."""
        import threading
        path = self.out / f"{self.plat}-serial.log"
        def pump():
            try:
                s = socket.create_connection(("127.0.0.1", self.ports["serial"]), timeout=5)
                s.settimeout(None)
                with open(path, "wb") as f:
                    while True:
                        b = s.recv(4096)
                        if not b:
                            break
                        f.write(b)
                        f.flush()
            except OSError:
                pass
        threading.Thread(target=pump, daemon=True).start()

    def push(self, pbw):
        """Install a package and start it, as the phone does."""
        from libpebble2.services.install import AppInstaller
        from libpebble2.protocol.apps import AppRunState, AppRunStateStart
        t = time.time()
        AppInstaller(self.conn, str(pbw)).install()
        print(f"installed {Path(pbw).name} in {time.time() - t:.1f}s", flush=True)
        self.conn.send_packet(AppRunState(data=AppRunStateStart(uuid=self.uuid)))

    def install(self, boot, pbw=None):
        time.sleep(1.0)
        self.serial_log()
        time.sleep(max(0.0, boot - 1.0))
        from libpebble2.communication import PebbleConnection
        from libpebble2.communication.transports.qemu import QemuTransport
        from libpebble2.services.install import AppInstaller
        from libpebble2.protocol.apps import AppRunState, AppRunStateStart
        c = PebbleConnection(QemuTransport(port=self.ports["app"]))
        c.connect()
        c.run_async()
        # the clock at --time (UTC), set as the phone sets it: the machines' clocks follow the PC's whatever -rtc says
        from datetime import datetime, timezone
        from libpebble2.protocol.system import SetUTC, TimeMessage
        t = int(datetime.fromisoformat(self.when).replace(tzinfo=timezone.utc).timestamp())
        c.send_packet(TimeMessage(message=SetUTC(unix_time=t, utc_offset=self.utc_offset,
                                                 tz_name="UTC" if not self.utc_offset else f"UTC{self.utc_offset / 60:+g}")))
        AppInstaller(c, str(pbw or APP / "build/watchface.pbw")).install()
        u = uuid.UUID(json.loads((APP / "package.json").read_text())["pebble"]["uuid"])
        c.send_packet(AppRunState(data=AppRunStateStart(uuid=u)))
        self.conn, self.uuid = c, u
        self.mon = Monitor(self.ports["monitor"])

    def settings(self, values):
        """Send settings the way the phone does: {KEY: int or text}."""
        from libpebble2.services.appmessage import AppMessageService, Int32, CString, ByteArray
        keys = json.loads((APP / "build/js/message_keys.json").read_text())
        svc = AppMessageService(self.conn)
        def value(v):
            if isinstance(v, str) and v.startswith("hex:"):        # a byte array, as the phone sends the tide's turns
                return ByteArray(bytes.fromhex(v[4:]))
            try:
                return Int32(int(v))
            except ValueError:
                return CString(v)
        svc.send_message(self.uuid, {keys[k]: value(v) for k, v in values.items()})

    def shot(self, path):
        from PIL import Image
        ppm = path.with_suffix(".ppm")
        self.mon.cmd(f"screendump {ppm}")
        Image.open(ppm).save(path)
        ppm.unlink()

    def gdb_setup(self):
        elf = Path(self.elf) if getattr(self, "elf", None) else APP / f"build/{self.plat}/pebble-app.elf"
        r = self.gdb_raw(["p/x g_app_load_address"], add=False)
        m = re.search(r"= (0x[0-9a-f]+)", r)
        if not m:
            raise RuntimeError("gdb: " + r[-2000:])
        base = int(m.group(1), 16)
        sections = {}
        for line in subprocess.check_output([str(TOOLS / "arm-none-eabi-objdump"), "--headers", "--wide", str(elf)],
                                            text=True).splitlines():
            p = line.split()
            if len(p) >= 8 and p[0].isdigit() and "ALLOC" in line:
                sections[p[1]] = int(p[3], 16)
        self.add = f"add-symbol-file {elf} {hex(base + sections['.text'])}" + "".join(
            f" -s {n} {hex(base + o)}" for n, o in sections.items() if n != ".text")
        return base

    def gdb_raw(self, commands, add=True, timeout=120, retry=True):
        fw = SDK / f"sdk-core/pebble/{self.plat}/qemu/{self.plat}_sdk_debug.elf"
        script = ["set confirm off", "set pagination off", f"target remote :{self.ports['gdb']}"]
        if add:
            script.append(self.add)
        script += commands + ["detach"]
        path = self.out / f"{self.plat}.gdb"
        path.write_text("\n".join(script) + "\n")
        # stopped inside the app (unprivileged), the MPU hides the system's
        # memory from the debugger: try again until it stops elsewhere
        for attempt in range(40 if retry else 1):
            r = subprocess.run([str(TOOLS / "arm-none-eabi-gdb"), str(fw), "-q", "-batch", "-x", str(path)],
                               capture_output=True, text=True, timeout=timeout)
            if "Cannot access memory" not in r.stdout + r.stderr:
                break
            time.sleep(0.15)
        return r.stdout + r.stderr

    def gdb(self, exprs):
        r = self.gdb_raw([f"p {e}" for e in exprs])
        return [l for l in r.splitlines() if l.startswith("$") or "No symbol" in l]

    def quit(self):
        try:
            if self.mon:
                self.mon.cmd("quit")
        except OSError:
            pass
        try:
            self.q.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.q.kill()


def blocks(path):
    """('decode', pc, instruction count) for each in_asm listing and
    ('exec', pc, None) for each executed block in a QEMU log."""
    rx = re.compile(r"^Trace \d+: 0x[0-9a-f]+ \[[^/]+/([0-9a-f]+)/")
    pc, data = None, bytearray()
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith("OBJD-T:"):
                if pc is not None:
                    data.extend(bytes.fromhex(line.split(":", 1)[1].strip()))
                continue
            if data:
                i = n = 0
                while i < len(data):
                    half = int.from_bytes(data[i:i + 2], "little")
                    i += 4 if half >> 11 >= 0x1D else 2
                    n += 1
                yield "decode", pc, n
                data = bytearray()
            pc = None
            if line.startswith("0x") and ":" in line:
                try:
                    pc = int(line.split(":")[0], 16)
                except ValueError:
                    pc = None
            m = rx.match(line)
            if m:
                yield "exec", int(m.group(1), 16), None


def symbols(plat, base, code=None):
    """Sorted (address, name) for the firmware, the app loaded at `base` and the renderer's code (the resource
    tools/build_blob.py builds) loaded at `code`."""
    out = []
    elves = [(SDK / f"sdk-core/pebble/{plat}/qemu/{plat}_sdk_debug.elf", 0, "fw"),
             (APP / f"build/{plat}/pebble-app.elf", base, "app")]
    if code:
        elves.append((ROOT / "build/blob/plan_code.elf", code, "plan"))
    for elf, off, tag in elves:
        for line in subprocess.check_output([str(TOOLS / "arm-none-eabi-nm"), "-n", str(elf)], text=True).splitlines():
            p = line.split()
            if len(p) == 3 and p[1] in "tTwW":
                out.append(((int(p[0], 16) & ~1) + off, f"{tag}:{p[2]}"))
    out.sort()
    return out


def count(known, measure, syms=None):
    import bisect, collections
    addrs = [a for a, _ in syms] if syms else []
    per = collections.Counter()
    lengths = {}
    for p in known:
        if p.exists():
            for kind, pc, n in blocks(p):
                if kind == "decode":
                    lengths[pc] = n
    total = missing = 0
    for kind, pc, n in blocks(measure):
        if kind == "decode":
            lengths[pc] = n
        elif pc in lengths:
            total += lengths[pc]
            if syms:
                i = bisect.bisect_right(addrs, pc) - 1
                per[syms[i][1] if i >= 0 else "?"] += lengths[pc]
        else:
            missing += 1
    return total, missing, per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("platform", choices=["emery", "gabbro"])
    ap.add_argument("mode", choices=["shots", "profile"])
    ap.add_argument("--time", default="2026-10-15T01:30:00")
    ap.add_argument("--utc-offset", type=int, default=0, help="minutes the watch's local time runs ahead of UTC")
    ap.add_argument("--shots", default="0,3,6")
    ap.add_argument("--out", default=str(ROOT / "out/emu"))
    ap.add_argument("--gdb", nargs="*", default=[])
    ap.add_argument("--fn", nargs="*", default=["update"])
    ap.add_argument("--boot", type=float, default=8.0)
    ap.add_argument("--wait", type=float, default=2.0)
    ap.add_argument("--set", nargs="*", default=[], help="KEY=value settings sent after start, e.g. THEME=2 "
                    "(hex:0a0b... a byte array)")
    ap.add_argument("--set-at", type=float, default=1.0, help="seconds after start to send --set")
    ap.add_argument("--then", nargs="*", default=[], help="a second message, KEY=value, sent at --then-at")
    ap.add_argument("--then-at", type=float, default=3.0)
    ap.add_argument("--send", nargs="+", action="append", default=[], metavar="AT KEY=value",
                    help="more messages, each at its second after start, e.g. --send 5 CALENDARS=0 --send 7 CALENDARS=2")
    ap.add_argument("--poke", nargs="*", default=[], help="app variables to set over gdb, e.g. g_debug_stamp=1")
    ap.add_argument("--poke-at", type=float, default=1.0)
    ap.add_argument("--relaunch-at", type=float, default=None, help="start the app again (leave and come back)")
    ap.add_argument("--tap-at", type=float, default=None, help="a wrist flick (accelerometer tap)")
    ap.add_argument("--pbw", default=None, help="package to install first (default: the build)")
    ap.add_argument("--elf", default=None, help="the installed package's app ELF, for --gdb/--poke (default: the build's)")
    ap.add_argument("--update", default=None, help="a package to install over the running face")
    ap.add_argument("--update-at", type=float, default=10.0)
    ap.add_argument("--icount", type=int, default=None, help="2^N ns an instruction: a fixed CPU speed")
    ap.add_argument("--qemu-trace", nargs="*", default=[], help="QEMU trace events, e.g. m25p80_flash_erase")
    ap.add_argument("--phone-off-at", type=float, default=None, help="the phone goes away (Bluetooth disconnected)")
    ap.add_argument("--battery", default=None, help="PERCENT[,charging] reported from --battery-at")
    ap.add_argument("--battery-at", type=float, default=5.0)
    ap.add_argument("--press", default=None, help="a button (back up select down) pressed at --press-at")
    ap.add_argument("--press-at", type=float, default=10.0)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    plat = a.platform
    if a.mode == "shots":
        e = Emu(plat, a.time, out, icount=a.icount, events=a.qemu_trace, utc_offset=a.utc_offset)
        e.elf = a.elf
        try:
            e.install(a.boot, a.pbw)
            t0 = time.time()
            messages = sorted([(a.set_at, a.set), (a.then_at, a.then)] + [(float(m[0]), m[1:]) for m in a.send])
            messages = [(at, dict(kv.split("=") for kv in kvs)) for at, kvs in messages if kvs]
            pokes = list(a.poke)
            if pokes:
                e.gdb_setup()
            relaunch, tap, update, press = a.relaunch_at, a.tap_at, a.update, a.press
            phone_off, batt = a.phone_off_at, a.battery
            for s in [float(x) for x in a.shots.split(",")]:
                from libpebble2.communication.transports.qemu import MessageTargetQemu
                from libpebble2.communication.transports.qemu.protocol import QemuBluetoothConnection, QemuBattery
                if phone_off is not None and s >= phone_off:
                    while time.time() - t0 < phone_off:
                        time.sleep(0.05)
                    e.conn.transport.send_packet(QemuBluetoothConnection(connected=False), target=MessageTargetQemu())
                    print(f"phone away at {time.time() - t0:.1f}s", flush=True)
                    phone_off = None
                if batt and s >= a.battery_at:
                    while time.time() - t0 < a.battery_at:
                        time.sleep(0.05)
                    pct, *chg = batt.split(",")
                    e.conn.transport.send_packet(QemuBattery(percent=int(pct), charging=bool(chg and chg[0] == "1")),
                                                 target=MessageTargetQemu())
                    print(f"battery {batt} at {time.time() - t0:.1f}s", flush=True)
                    batt = None
                if press and s >= a.press_at:
                    while time.time() - t0 < a.press_at:
                        time.sleep(0.05)
                    from libpebble2.communication.transports.qemu import MessageTargetQemu
                    from libpebble2.communication.transports.qemu.protocol import QemuButton
                    b = getattr(QemuButton.Button, press.capitalize())
                    e.conn.transport.send_packet(QemuButton(state=b), target=MessageTargetQemu())
                    time.sleep(0.15)
                    e.conn.transport.send_packet(QemuButton(state=0), target=MessageTargetQemu())
                    print(f"pressed {press} at {time.time() - t0:.1f}s", flush=True)
                    press = None
                if update and s >= a.update_at:
                    while time.time() - t0 < a.update_at:
                        time.sleep(0.05)
                    e.push(update)
                    update = None
                if tap is not None and s >= tap:
                    while time.time() - t0 < tap:
                        time.sleep(0.05)
                    from libpebble2.communication.transports.qemu import MessageTargetQemu
                    from libpebble2.communication.transports.qemu.protocol import QemuTap
                    e.conn.transport.send_packet(QemuTap(axis=QemuTap.Axis.X, direction=1), target=MessageTargetQemu())
                    print("tapped", flush=True)
                    tap = None
                if relaunch is not None and s >= relaunch:
                    while time.time() - t0 < relaunch:
                        time.sleep(0.05)
                    from libpebble2.protocol.apps import AppRunState, AppRunStateStart, AppRunStateStop
                    e.conn.send_packet(AppRunState(data=AppRunStateStop(uuid=e.uuid)))
                    time.sleep(1.0)
                    e.conn.send_packet(AppRunState(data=AppRunStateStart(uuid=e.uuid)))
                    print("relaunched", flush=True)
                    relaunch = None
                if pokes and s >= a.poke_at:
                    while time.time() - t0 < a.poke_at:
                        time.sleep(0.05)
                    e.gdb_raw([f"set var {p}" for p in pokes])
                    print("poked", pokes, f"at {time.time() - t0:.1f}s", flush=True)
                    pokes = []
                while messages and messages[0][0] <= s:
                    at, values = messages.pop(0)
                    while time.time() - t0 < at:
                        time.sleep(0.05)
                    e.settings(values)
                    print("sent", values, f"at {at:g}s", flush=True)
                while time.time() - t0 < s:
                    time.sleep(0.05)
                path = out / f"{plat}-{s:05.1f}.png"
                e.shot(path)
                print("shot", path, flush=True)
            if a.gdb:
                if not e.add:
                    e.gdb_setup()
                print("\n".join(e.gdb(a.gdb)))
        finally:
            e.quit()
        return
    boot_trace = out / f"{plat}-boot.trace"
    e = Emu(plat, a.time, out, trace=boot_trace, utc_offset=a.utc_offset)
    try:
        e.install(a.boot)
        time.sleep(a.wait)
        if a.set:      # settings first: a change of pattern or size starts a new regrowth to profile
            e.settings(dict(kv.split("=") for kv in a.set))
            time.sleep(1.0)
        base = e.gdb_setup()
        code = next((int(l.split("=")[1]) for l in e.gdb(["g_code"]) if "=" in l), 0)
        syms = symbols(plat, base, code)
        for fn in a.fn:
            tr = out / f"{plat}-{fn}.trace"
            after = out / f"{plat}-after-{fn}.trace"
            r = e.gdb_raw([f"tbreak {fn}", "continue", f"monitor logfile {tr}", "monitor log in_asm,exec,nochain",
                           "finish", f"monitor logfile {after}", "monitor log in_asm,nochain"], timeout=900, retry=False)
            n, missing, per = count([boot_trace], tr, syms)
            print(f"{fn}: {n} instructions ({missing} unresolved blocks)", flush=True)
            for name, c in per.most_common(int(os.environ.get('PROFILE_TOP', '10'))):
                print(f"    {c:>10}  {name}")
        if a.gdb:
            print("\n".join(e.gdb(a.gdb)))
    finally:
        e.quit()


if __name__ == "__main__":
    main()
