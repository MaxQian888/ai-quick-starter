#!/usr/bin/env python3
"""Serve the storage report with a guarded one-click delete API (macOS + Windows).

Starts on 127.0.0.1 + a random port + a random per-session token, serves the
interactive report, and exposes POST /action to move green-tier paths to Trash
or delete them outright. Stop with Ctrl+C.

Usage:
    server.py <analysis.json>

SAFETY MODEL — read before changing:
- Allowlist: only paths listed in this report's green items `trash_paths` are
  accepted. Every request path is realpath-resolved and must be in the allowlist
  AND under $HOME. Anything else is rejected. This is the core guard — the
  endpoint cannot be used to delete arbitrary files.
- Bound to 127.0.0.1 only; every POST requires the session token (compared with
  hmac.compare_digest); Host must be 127.0.0.1/localhost (blocks DNS-rebinding)
  and Origin, if present, must match this server (CSRF defense in depth). We
  NEVER emit Access-Control-Allow-* headers — cross-origin requests must fail.
- Destructive modes (rm/trash) are constrained to $HOME; "open" additionally
  allows the app install dir (/Applications on macOS, Program Files on Windows).
- Report data is injected via script_safe() so a crafted filename on disk can't
  break out of the <script> block (stored XSS into this token-bearing page).
- Two modes: "trash" (Finder -> Trash, reversible) and "rm" (immediate,
  irreversible). The browser confirms each action before sending.
"""
import hmac
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "report_template.html")
HOME = os.path.normcase(os.path.realpath(os.path.expanduser("~")))
TOKEN = secrets.token_urlsafe(24)
PORT = 0  # 真实端口在 main() 填入，供 Origin 校验
MAX_BODY = 1_000_000  # POST 体上限，防本机进程喂超大 Content-Length 撑爆内存

DATA = {}
TPL = ""
RM_ALLOW = set()
TRASH_ALLOW = set()
OPEN_ALLOW = set()


def expand(p):
    # normcase：Windows/NTFS、macOS 默认 APFS 都大小写不敏感，统一大小写再比白名单，
    # 避免同一文件换个大小写拼写就绕过（或误拒）白名单。
    return os.path.normcase(os.path.realpath(os.path.expanduser(p)))


def script_safe(obj):
    """注入 <script> 前中和 </script> 等闭合序列，挡住「磁盘上有个名为
    </script><img onerror=…> 的文件 → 报告页被注入脚本」的存储型 XSS。
    转义后仍是合法 JS 字符串，浏览器解码回原字符。"""
    return (json.dumps(obj, ensure_ascii=False)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def load(src):
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    # 三套白名单，权限从严到宽：
    #   rm    = 仅绿灯 trash_paths（可直接删的纯缓存）
    #   trash = 绿灯 + 橙灯 trash_paths（橙灯只准移废纸篓，不准直接删）
    #   open  = trash 全集 + 橙灯 path + 红灯 app_paths（仅"在文件管理器打开"，非破坏性）
    rm_allow, trash_allow, open_allow = set(), set(), set()
    for it in data.get("green", []):
        for p in (it.get("trash_paths") or []):
            rp = expand(p)
            rm_allow.add(rp); trash_allow.add(rp); open_allow.add(rp)
    for it in data.get("yellow", []):
        for p in (it.get("trash_paths") or []):
            rp = expand(p)
            trash_allow.add(rp); open_allow.add(rp)
        if it.get("path"):
            rp = expand(it["path"])
            if os.path.exists(rp):
                open_allow.add(rp)
    # 红灯只允许"打开"（应用本体在 /Applications，删除让用户在访达里自己卸）
    for it in data.get("red", []):
        for p in (it.get("app_paths") or []):
            rp = expand(p)
            if os.path.exists(rp):
                open_allow.add(rp)
    return data, tpl, rm_allow, trash_allow, open_allow


def move_to_trash(path):
    if sys.platform == "darwin":
        _trash_macos(path)
    elif sys.platform.startswith("win"):
        _trash_windows(path)
    else:
        raise OSError("移到废纸篓仅支持 macOS / Windows")


def _trash_macos(path):
    # osascript Finder delete -> macOS Trash, recoverable. First run may prompt
    # for Finder automation permission. Fall back to ~/.Trash move if it fails.
    script = 'tell application "Finder" to delete (POSIX file %s as alias)' % json.dumps(path)
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        dest = os.path.join(HOME, ".Trash",
                            os.path.basename(path.rstrip("/")) + "." + time.strftime("%H%M%S"))
        shutil.move(path, dest)


def _trash_windows(path):
    # Send to Recycle Bin via SHFileOperationW with FOF_ALLOWUNDO (stdlib ctypes).
    # UNTESTED on this build — verify on a real Windows machine.
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_uint16),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    FO_DELETE = 3
    FOF_ALLOWUNDO = 0x0040
    FOF_NOCONFIRMATION = 0x0010
    FOF_SILENT = 0x0004
    op = SHFILEOPSTRUCTW()
    op.wFunc = FO_DELETE
    # pFrom 必须双 \0 结尾。c_wchar_p 直接赋含内嵌 \0 的 str 会在第一个 \0 处截断、丢掉第二个
    # 终止符，所以用 create_unicode_buffer 保留内嵌 \0（缓冲区再自带一个终止符 = 双 \0），
    # 并保留 src_buf 引用直到调用结束，防止被 GC 回收。
    src_buf = ctypes.create_unicode_buffer(os.path.abspath(path) + "\x00")
    op.pFrom = ctypes.cast(src_buf, wintypes.LPCWSTR)
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
    rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if rc != 0:
        raise OSError("SHFileOperation failed (code %d)" % rc)


def hard_delete(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def open_in_file_manager(path):
    # 非破坏性：在访达 / 资源管理器里打开该位置，方便用户自己审查删除
    target = path if os.path.isdir(path) else os.path.dirname(path)
    if sys.platform == "darwin":
        # .app 是 bundle，对它用 open 会"启动应用"而非显示；必须用 open -R 在访达里选中。
        if target.rstrip("/").endswith(".app"):
            r = subprocess.run(["open", "-R", target], capture_output=True, text=True)
            if r.returncode != 0:
                raise OSError((r.stderr or "open -R 失败").strip())
            return
        # 普通文件夹：先试直接打开看内容；沙盒容器（如微信）open 会报 -10814，
        # 退回 open -R 在父目录里选中它。两者都失败才算错。
        r = subprocess.run(["open", target], capture_output=True, text=True)
        if r.returncode != 0:
            r2 = subprocess.run(["open", "-R", target], capture_output=True, text=True)
            if r2.returncode != 0:
                raise OSError((r.stderr or r2.stderr or "open 失败").strip())
    elif sys.platform.startswith("win"):
        subprocess.run(["explorer", target])  # explorer 退出码不可靠，不据此判成败
    else:
        raise OSError("打开文件夹仅支持 macOS / Windows")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            blob = script_safe(DATA)
            cfg = json.dumps({"token": TOKEN, "endpoint": "/action"})
            html = TPL.replace("__REPORT_DATA__", blob).replace("__DELETE_CONFIG__", cfg)
            self._send(200, html, "text/html; charset=utf-8")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/action":
            self._send(404, json.dumps({"ok": False, "error": "not found"}))
            return
        # DNS-rebinding guard: only accept local Host
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            self._send(403, json.dumps({"ok": False, "error": "host 不被允许"}))
            return
        # CSRF：跨源页面发 application/json 会触发 CORS 预检(OPTIONS)，本服务不回 OPTIONS、
        # 也绝不发任何 Access-Control-Allow-* 头——跨源 fetch 根本到不了这里。下面再显式拒绝
        # 带外源 Origin，作为冗余护栏，防日后有人补 do_OPTIONS 时把 CORS 不慎放开。
        origin = self.headers.get("Origin")
        if origin is not None and origin not in (
                "http://127.0.0.1:%d" % PORT, "http://localhost:%d" % PORT):
            self._send(403, json.dumps({"ok": False, "error": "origin 不被允许"}))
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, json.dumps({"ok": False, "error": "请求格式错误"}))
            return
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self._send(400, json.dumps({"ok": False, "error": "请求格式错误"}))
            return
        tok = req.get("token")
        if not isinstance(tok, str) or not hmac.compare_digest(tok, TOKEN):
            self._send(403, json.dumps({"ok": False, "error": "token 校验失败"}))
            return
        mode = req.get("mode")
        allow = {"rm": RM_ALLOW, "trash": TRASH_ALLOW, "open": OPEN_ALLOW}.get(mode)
        if allow is None:
            self._send(400, json.dumps({"ok": False, "error": "未知操作"}))
            return
        done = []
        for p in (req.get("paths") or []):
            rp = expand(p)
            if rp not in allow:
                self._send(403, json.dumps({"ok": False, "error": "路径不在白名单：%s" % p}))
                return
            # 二级护栏（fail-closed）：删除(rm/trash)只许在用户主目录内；open 非破坏性，额外
            # 放行应用安装目录——macOS 是 /Applications，Windows 是 Program Files(_x86)，
            # 否则 Windows 红灯「在资源管理器打开去卸载」会被误判越界。
            roots = [HOME]
            if mode == "open":
                if sys.platform == "darwin":
                    roots.append("/Applications")
                else:
                    roots += [d for d in (os.environ.get("ProgramFiles"),
                                          os.environ.get("ProgramFiles(x86)")) if d]
            roots = [os.path.normcase(os.path.realpath(r)) for r in roots]
            if not any(rp == base or rp.startswith(base + os.sep) for base in roots):
                self._send(403, json.dumps({"ok": False, "error": "路径越界：%s" % p}))
                return
            # 收窄 TOCTOU：删除前拒绝用户传入即为符号链接的路径；hard_delete 顶层不跟随符号链接，
            # shutil.rmtree 在支持 dir_fd 的平台对树内替换有抵抗。残留竞态需本机另一恶意进程精确
            # 抢点，单用户模型下风险有限。
            if mode in ("rm", "trash") and os.path.islink(os.path.expanduser(p)):
                self._send(403, json.dumps({"ok": False, "error": "拒绝符号链接：%s" % p}))
                return
            try:
                if mode == "open":
                    open_in_file_manager(rp)
                elif not os.path.exists(rp):
                    pass  # already gone, treat as success
                elif mode == "trash":
                    move_to_trash(rp)
                else:
                    hard_delete(rp)
                done.append(p)
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}))
                return
        self._send(200, json.dumps({"ok": True, "done": done}))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    global DATA, TPL, RM_ALLOW, TRASH_ALLOW, OPEN_ALLOW, PORT
    DATA, TPL, RM_ALLOW, TRASH_ALLOW, OPEN_ALLOW = load(sys.argv[1])
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    PORT = srv.server_address[1]
    port = PORT
    url = "http://127.0.0.1:%d/" % port
    print("报告服务已启动：" + url)
    print("绿灯可删 %d 项 | 橙灯可移废纸篓/打开文件夹 %d 项 | 页面上点" % (len(RM_ALLOW), len(TRASH_ALLOW) - len(RM_ALLOW)))
    print("用完按 Ctrl+C 停止服务（服务关掉后按钮即失效）")
    webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止服务。")


if __name__ == "__main__":
    main()
