import os
import sys
import json
import datetime
import textwrap
import shlex
import urllib.parse
import time
import atexit
import unicodedata
import tempfile
import zipfile
import shutil
from pathlib import Path

C_BLUE = "\033[38;2;0;175;255m"
C_YELLOW = "\033[38;2;248;246;117m"
C_GRAY = "\033[38;2;110;110;110m"
C_WHITE = "\033[38;2;210;210;210m"
C_DARK_GRAY = "\033[38;2;80;80;80m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"
C_BG_INPUT = "\033[48;2;45;45;45m"

COLOR_NORMAL = {
    "blue": "\033[38;2;0;175;255m",
    "yellow": "\033[38;2;248;246;117m",
    "gray": "\033[38;2;110;110;110m",
    "white": "\033[38;2;210;210;210m",
    "dark_gray": "\033[38;2;80;80;80m",
    "bold": "\033[1m",
    "bg_input": "\033[48;2;45;45;45m"
}

COLOR_DIM = {
    "blue": "\033[38;2;0;65;95m",
    "yellow": "\033[38;2;95;94;45m",
    "gray": "\033[38;2;42;42;42m",
    "white": "\033[38;2;78;78;78m",
    "dark_gray": "\033[38;2;28;28;28m",
    "bold": "",
    "bg_input": "\033[48;2;22;22;22m"
}

IGNORE_DIRS = {
    ".git", "node_modules", "venv", "env", ".venv", "__pycache__",
    ".idea", ".vscode", "dist", "build"
}

ARCHIVE_EXTS = {".zip"}

LOCKED_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg",
    ".apk", ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    ".db", ".sqlite", ".sqlite3",
    ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".mkv", ".avi", ".mov",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ".class", ".jar", ".dex",
    ".pyc", ".pyo",
    ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"
}

MEMORY_FILE = Path.home() / ".merge_files_memory.json"

old_mode_in = None
old_mode_out = None
win32_available = False
win_mouse_left_down = False
_input_queue = []

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32

    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    ENABLE_WINDOW_INPUT = 0x0008
    ENABLE_MOUSE_INPUT = 0x0010
    ENABLE_QUICK_EDIT_MODE = 0x0040
    ENABLE_EXTENDED_FLAGS = 0x0080
    ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    KEY_EVENT = 0x0001
    MOUSE_EVENT = 0x0002
    MOUSE_MOVED = 0x0001
    DOUBLE_CLICK = 0x0002
    MOUSE_WHEELED = 0x0004
    MOUSE_HWHEELED = 0x0008
    FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001

    VK_BACK = 0x08
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B
    VK_UP = 0x26
    VK_DOWN = 0x28
    VK_C = 0x43

    LEFT_CTRL_PRESSED = 0x0008
    RIGHT_CTRL_PRESSED = 0x0004

    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    class KEY_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("bKeyDown", wintypes.BOOL),
            ("wRepeatCount", wintypes.WORD),
            ("wVirtualKeyCode", wintypes.WORD),
            ("wVirtualScanCode", wintypes.WORD),
            ("uChar", wintypes.WCHAR),
            ("dwControlKeyState", wintypes.DWORD)
        ]

    class MOUSE_EVENT_RECORD(ctypes.Structure):
        _fields_ = [
            ("dwMousePosition", COORD),
            ("dwButtonState", wintypes.DWORD),
            ("dwControlKeyState", wintypes.DWORD),
            ("dwEventFlags", wintypes.DWORD)
        ]

    class EVENT_UNION(ctypes.Union):
        _fields_ = [
            ("KeyEvent", KEY_EVENT_RECORD),
            ("MouseEvent", MOUSE_EVENT_RECORD)
        ]

    class INPUT_RECORD(ctypes.Structure):
        _fields_ = [
            ("EventType", wintypes.WORD),
            ("Event", EVENT_UNION)
        ]

    hStdIn = kernel32.GetStdHandle(STD_INPUT_HANDLE)
    hStdOut = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    mode = ctypes.c_uint32()
    if kernel32.GetConsoleMode(hStdIn, ctypes.byref(mode)):
        old_mode_in = mode.value
        new_mode = mode.value
        new_mode &= ~ENABLE_QUICK_EDIT_MODE
        new_mode &= ~ENABLE_VIRTUAL_TERMINAL_INPUT
        new_mode |= ENABLE_EXTENDED_FLAGS
        new_mode |= ENABLE_MOUSE_INPUT
        new_mode |= ENABLE_WINDOW_INPUT
        kernel32.SetConsoleMode(hStdIn, new_mode)
        win32_available = True

    mode_out = ctypes.c_uint32()
    if kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode_out)):
        old_mode_out = mode_out.value
        kernel32.SetConsoleMode(hStdOut, mode_out.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)

    kernel32.GetNumberOfConsoleInputEvents.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD)
    ]
    kernel32.GetNumberOfConsoleInputEvents.restype = wintypes.BOOL
    kernel32.ReadConsoleInputW.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(INPUT_RECORD),
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD)
    ]
    kernel32.ReadConsoleInputW.restype = wintypes.BOOL
    kernel32.FlushConsoleInputBuffer.argtypes = [wintypes.HANDLE]
    kernel32.FlushConsoleInputBuffer.restype = wintypes.BOOL


T = {
    "en": {
        "commands": "Commands",
        "actions": "Actions",
        "start": "Start extraction",
        "settings": "Settings",
        "system": "System",
        "output_path": "Output path",
        "language": "Language",
        "lang_name": "English",
        "tip_main": "Type number to select, or Ctrl+C to exit",
        "action": "Action:",
        "change_path": "Change output path",
        "change_lang": "Change language",
        "new_path": "New path:",
        "path_updated": "Path successfully updated.",
        "press_enter": "Press Enter to continue",
        "press_enter_return": "Press Enter to return",
        "lang_updated": "Language successfully updated.",
        "target_dir": "Target Directory",
        "input": "Input",
        "enter_path": "Enter one or several paths to folders/files/ZIP archives. Use quotes for paths with spaces.",
        "path": "Path:",
        "err_not_found": "Error: Path or file not found.",
        "err_permission": "Error: Access denied (PermissionError).",
        "err_empty": "Nothing to extract.",
        "err_bad_archive": "Error: ZIP archive is corrupted or cannot be opened.",
        "select_files": "Select Files",
        "dir": "Source",
        "sources": "Sources",
        "files": "Files",
        "selected": "Selected:",
        "of": "of",
        "locked": "locked",
        "tip_toggle": "Type numbers to toggle, 0 to start, or Drag & Drop additional files/ZIP archives/folders here",
        "toggle": "Toggle:",
        "err_no_selected": "No files selected.",
        "success": "Success",
        "success_msg": "Data extracted successfully.",
        "output_loc": "Output location",
        "err_save": "Save error:",
        "exporting": "Exporting:"
    },
    "ru": {
        "commands": "Команды",
        "actions": "Действия",
        "start": "Начать извлечение",
        "settings": "Настройки",
        "system": "Система",
        "output_path": "Путь сохранения",
        "language": "Язык",
        "lang_name": "Русский",
        "tip_main": "Введите номер для выбора, или Ctrl+C для выхода",
        "action": "Действие:",
        "change_path": "Изменить путь сохранения",
        "change_lang": "Изменить язык",
        "new_path": "Новый путь:",
        "path_updated": "Путь успешно обновлен.",
        "press_enter": "Нажмите Enter для продолжения",
        "press_enter_return": "Нажмите Enter для возврата",
        "lang_updated": "Язык успешно обновлен.",
        "target_dir": "Целевая папка",
        "input": "Ввод",
        "enter_path": "Введите один или несколько путей к папкам/файлам/ZIP-архивам. Пути с пробелами лучше брать в кавычки.",
        "path": "Путь:",
        "err_not_found": "Ошибка: путь или файл не найден.",
        "err_permission": "Ошибка: нет доступа к папке (PermissionError).",
        "err_empty": "Нечего извлекать.",
        "err_bad_archive": "Ошибка: ZIP-архив поврежден или не может быть открыт.",
        "select_files": "Выбор файлов",
        "dir": "Источник",
        "sources": "Источники",
        "files": "Файлы",
        "selected": "Выбрано:",
        "of": "из",
        "locked": "заблок.",
        "tip_toggle": "Введите номера для выбора, 0 для старта, или перетащите сюда еще файлы/ZIP-архивы/папки",
        "toggle": "Выбор:",
        "err_no_selected": "Файлы не выбраны.",
        "success": "Успешно",
        "success_msg": "Данные успешно извлечены.",
        "output_loc": "Место сохранения",
        "err_save": "Ошибка сохранения:",
        "exporting": "Извлечение:"
    },
    "zh": {
        "commands": "命令",
        "actions": "操作",
        "start": "开始提取",
        "settings": "设置",
        "system": "系统",
        "output_path": "输出路径",
        "language": "语言",
        "lang_name": "中文",
        "tip_main": "输入数字进行选择，或按 Ctrl+C 退出",
        "action": "操作:",
        "change_path": "更改输出路径",
        "change_lang": "更改语言",
        "new_path": "新路径:",
        "path_updated": "路径已成功更新。",
        "press_enter": "按 Enter 键继续",
        "press_enter_return": "按 Enter 键返回",
        "lang_updated": "语言已成功更新。",
        "target_dir": "目标目录",
        "input": "输入",
        "enter_path": "输入一个或多个文件夹/文件/ZIP 压缩包路径。带空格的路径建议加引号。",
        "path": "路径:",
        "err_not_found": "错误: 找不到路径或文件。",
        "err_permission": "错误: 拒绝访问 (PermissionError)。",
        "err_empty": "没有可提取的内容。",
        "err_bad_archive": "错误: ZIP 文件损坏或无法打开。",
        "select_files": "选择文件",
        "dir": "来源",
        "sources": "来源",
        "files": "文件",
        "selected": "已选择:",
        "of": "/",
        "locked": "锁定",
        "tip_toggle": "输入数字切换，输入 0 开始，或拖放更多文件/ZIP 压缩包/文件夹",
        "toggle": "切换:",
        "err_no_selected": "未选择任何文件。",
        "success": "成功",
        "success_msg": "数据提取成功。",
        "output_loc": "输出位置",
        "err_save": "保存错误:",
        "exporting": "提取中:"
    }
}


def restore_console():
    if sys.platform == "win32" and old_mode_in is not None:
        kernel32.SetConsoleMode(hStdIn, old_mode_in)
        if old_mode_out is not None:
            kernel32.SetConsoleMode(hStdOut, old_mode_out)


atexit.register(restore_console)


def set_color_mode(dimmed=False):
    global C_BLUE, C_YELLOW, C_GRAY, C_WHITE, C_DARK_GRAY, C_BOLD, C_BG_INPUT
    palette = COLOR_DIM if dimmed else COLOR_NORMAL
    C_BLUE = palette["blue"]
    C_YELLOW = palette["yellow"]
    C_GRAY = palette["gray"]
    C_WHITE = palette["white"]
    C_DARK_GRAY = palette["dark_gray"]
    C_BOLD = palette["bold"]
    C_BG_INPUT = palette["bg_input"]


class RawInput:
    def __enter__(self):
        if sys.platform != "win32":
            import tty
            import termios
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, *args):
        if sys.platform != "win32":
            import termios
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)


def char_width(ch):
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1


def text_width(text):
    return sum(char_width(ch) for ch in str(text))


def truncate_text(text, max_len):
    text = str(text)
    if max_len <= 0:
        return ""
    if text_width(text) <= max_len:
        return text
    if max_len <= 3:
        return "." * max_len
    result = ""
    width = 0
    limit = max_len - 3
    for ch in text:
        cw = char_width(ch)
        if width + cw > limit:
            break
        result += ch
        width += cw
    return result + "..."


def pad_text(text, width):
    return str(text) + " " * max(0, width - text_width(text))


def get_term_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def get_layout():
    tw = get_term_width()
    bw = max(10, min(tw - 4, 70))
    return tw, bw, " " * max(0, (tw - bw) // 2)


def clear_screen(lines=18):
    sys.stdout.write(f"{C_RESET}\033[2J\033[H")
    try:
        th = os.get_terminal_size().lines
        v_pad = max(0, (th - lines) // 2)
        if v_pad > 0:
            sys.stdout.write("\n" * v_pad)
    except OSError:
        pass
    sys.stdout.flush()


def print_wrapped_text(text, m, bw, color=C_GRAY):
    lines = textwrap.wrap(
        str(text),
        width=max(10, bw),
        break_long_words=False,
        break_on_hyphens=False
    )
    if not lines:
        print()
        return
    for line in lines:
        print(f"{m}{color}{line}{C_RESET}")


def print_tip(text, m, bw):
    lines = textwrap.wrap(
        str(text),
        width=max(10, bw - 6),
        break_long_words=False,
        break_on_hyphens=False
    )
    if lines:
        print(f"\n{m}{C_YELLOW}● Tip{C_RESET} {C_GRAY}{lines[0]}{C_RESET}")
        for line in lines[1:]:
            print(f"{m}      {C_GRAY}{line}{C_RESET}")
    print()


def draw_logo():
    ASCII_LOGO = [
        "██^^^^ ██ ██     ██^^^^   ▄█████ ██     ██ ",
        "██^^   ██ ██     ██^^     ██~~~~ ██     ██ ",
        "██     ██ ██████ ██████   ▀█████ ██████ ██ ",
        "~~     ~~ ~~~~~~ ~~~~~~    ~~~~~ ~~~~~~ ~~ "
    ]

    C_SHADOW_FG = "\033[38;2;90;90;40m"
    C_SHADOW_BG = "\033[48;2;90;90;40m"

    if C_YELLOW == COLOR_DIM["yellow"]:
        C_SHADOW_FG = "\033[38;2;34;34;16m"
        C_SHADOW_BG = "\033[48;2;34;34;16m"

    tw = get_term_width()
    indent = " " * max(0, (tw - len(ASCII_LOGO[0])) // 2)

    print()
    for line in ASCII_LOGO:
        rendered = indent
        for char in line:
            if char == "_":
                rendered += f"{C_SHADOW_BG} {C_RESET}"
            elif char == "^":
                rendered += f"{C_YELLOW}{C_SHADOW_BG}▀{C_RESET}"
            elif char == "~":
                rendered += f"{C_SHADOW_FG}▀{C_RESET}"
            else:
                rendered += f"{C_YELLOW}{char}{C_RESET}"
        print(rendered)
    print("\n")


def flush_input_events():
    global win_mouse_left_down, _input_queue
    win_mouse_left_down = False

    if sys.platform == "win32" and win32_available:
        kernel32.FlushConsoleInputBuffer(hStdIn)
    elif sys.platform == "win32":
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getwch()
        except Exception:
            pass
    else:
        _input_queue.clear()
        try:
            import select
            while True:
                r, _, _ = select.select([sys.stdin], [], [], 0)
                if not r:
                    break
                os.read(sys.stdin.fileno(), 4096)
        except Exception:
            pass


def parse_vt_sequence(seq):
    if seq == "\x1b[A":
        return "UP"
    if seq == "\x1b[B":
        return "DOWN"
    if seq == "\x1b[C":
        return "RIGHT"
    if seq == "\x1b[D":
        return "LEFT"

    if seq.startswith("\x1b[<") and seq.endswith(("M", "m")):
        parts = seq[3:-1].split(";")
        if len(parts) == 3:
            try:
                cb = int(parts[0])
                cx = int(parts[1])
                cy = int(parts[2])
                final = seq[-1]

                if cb & 64:
                    return "IGNORE"

                if final == "M":
                    if cb & 32:
                        return ("HOVER", cx, cy)
                    if (cb & 3) == 0:
                        return ("CLICK", cx, cy)
                    return ("HOVER", cx, cy)

                return "IGNORE"
            except ValueError:
                pass

    if seq.startswith("\x1b[M") and len(seq) >= 6:
        try:
            cb = ord(seq[3]) - 32
            cx = ord(seq[4]) - 32
            cy = ord(seq[5]) - 32

            if cb & 64:
                return "IGNORE"
            if cb & 32:
                return ("HOVER", cx, cy)
            if (cb & 3) == 0:
                return ("CLICK", cx, cy)
            return ("HOVER", cx, cy)
        except Exception:
            pass

    return "IGNORE"


def get_win32_event():
    global win_mouse_left_down

    count = wintypes.DWORD()

    if not kernel32.GetNumberOfConsoleInputEvents(hStdIn, ctypes.byref(count)):
        time.sleep(0.01)
        return None

    if count.value == 0:
        time.sleep(0.01)
        return None

    record = INPUT_RECORD()
    read = wintypes.DWORD()

    while count.value > 0:
        if not kernel32.ReadConsoleInputW(hStdIn, ctypes.byref(record), 1, ctypes.byref(read)):
            time.sleep(0.01)
            return None

        kernel32.GetNumberOfConsoleInputEvents(hStdIn, ctypes.byref(count))

        if record.EventType == KEY_EVENT:
            key = record.Event.KeyEvent
            if not key.bKeyDown:
                continue

            vk = key.wVirtualKeyCode
            ch = key.uChar
            ctrl = key.dwControlKeyState & (LEFT_CTRL_PRESSED | RIGHT_CTRL_PRESSED)

            if ctrl and vk == VK_C:
                raise KeyboardInterrupt
            if vk == VK_ESCAPE:
                return "ESC"
            if vk == VK_RETURN:
                return "ENTER"
            if vk == VK_BACK:
                return "BACKSPACE"
            if vk == VK_UP:
                return "UP"
            if vk == VK_DOWN:
                return "DOWN"

            if ch and ch not in ("\x00", "\r", "\n", "\b", "\x1b"):
                return ch

        elif record.EventType == MOUSE_EVENT:
            mouse = record.Event.MouseEvent
            x = int(mouse.dwMousePosition.X) + 1
            y = int(mouse.dwMousePosition.Y) + 1
            flags = mouse.dwEventFlags
            left_down = bool(mouse.dwButtonState & FROM_LEFT_1ST_BUTTON_PRESSED)

            if flags == MOUSE_MOVED:
                win_mouse_left_down = left_down
                return ("HOVER", x, y)

            if flags == 0:
                if left_down and not win_mouse_left_down:
                    win_mouse_left_down = True
                    return ("CLICK", x, y)
                if not left_down:
                    win_mouse_left_down = False
                    return "IGNORE"

            if flags in (DOUBLE_CLICK, MOUSE_WHEELED, MOUSE_HWHEELED):
                return "IGNORE"

    return None


def get_event():
    global _input_queue

    if sys.platform == "win32" and win32_available:
        return get_win32_event()

    if sys.platform == "win32":
        import msvcrt

        if msvcrt.kbhit():
            ch = msvcrt.getwch()

            if ch == "\x1b":
                time.sleep(0.08)
                seq = "\x1b"

                while msvcrt.kbhit():
                    seq += msvcrt.getwch()

                if seq == "\x1b":
                    return "ESC"

                return parse_vt_sequence(seq)

            if ch in ("\r", "\n"):
                return "ENTER"

            if ch == "\b":
                return "BACKSPACE"

            if ch == "\x03":
                raise KeyboardInterrupt

            if ch in ("\x00", "\xe0"):
                if msvcrt.kbhit():
                    ch2 = msvcrt.getwch()
                    if ch2 == "H":
                        return "UP"
                    if ch2 == "P":
                        return "DOWN"
                    if ch2 == "K":
                        return "LEFT"
                    if ch2 == "M":
                        return "RIGHT"
                return "IGNORE"

            return ch

        time.sleep(0.01)
        return None

    import select

    if not _input_queue:
        r, _, _ = select.select([sys.stdin], [], [], 0.05)
        if r:
            try:
                data = os.read(sys.stdin.fileno(), 4096).decode("utf-8", errors="replace")
                _input_queue.extend(list(data))
            except Exception:
                pass

    if not _input_queue:
        return None

    ch = _input_queue.pop(0)

    if ch == "\x1b":
        seq = "\x1b"

        if not _input_queue:
            r2, _, _ = select.select([sys.stdin], [], [], 0.18)
            if r2:
                try:
                    data = os.read(sys.stdin.fileno(), 4096).decode("utf-8", errors="replace")
                    _input_queue.extend(list(data))
                except Exception:
                    pass

        if _input_queue and _input_queue[0] in ("[", "O", "]"):
            seq += _input_queue.pop(0)

            while True:
                if not _input_queue:
                    r3, _, _ = select.select([sys.stdin], [], [], 0.03)
                    if r3:
                        try:
                            data = os.read(sys.stdin.fileno(), 4096).decode("utf-8", errors="replace")
                            _input_queue.extend(list(data))
                        except Exception:
                            pass
                    else:
                        break

                if _input_queue:
                    next_ch = _input_queue.pop(0)
                    seq += next_ch

                    if next_ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz~Mm":
                        break
                else:
                    break

            if seq.startswith("\x1b[200~"):
                pasted = []

                while True:
                    if not _input_queue:
                        r4, _, _ = select.select([sys.stdin], [], [], 0.03)
                        if r4:
                            try:
                                data = os.read(sys.stdin.fileno(), 4096).decode("utf-8", errors="replace")
                                _input_queue.extend(list(data))
                            except Exception:
                                pass

                    if not _input_queue:
                        break

                    c = _input_queue.pop(0)
                    pasted.append(c)

                    if "".join(pasted).endswith("\x1b[201~"):
                        text = "".join(pasted)[:-6]
                        _input_queue = list(text) + _input_queue
                        return "IGNORE"

            return parse_vt_sequence(seq)

        return "ESC"

    if ch in ("\n", "\r"):
        return "ENTER"

    if ch in ("\x7f", "\b"):
        return "BACKSPACE"

    if ch == "\x03":
        raise KeyboardInterrupt

    if ch == "\x04":
        raise EOFError

    return ch


def clean_path(p):
    if not p:
        return p

    p = p.strip(" \r\n\t")

    if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
        p = p[1:-1]

    p = p.strip(" \r\n\t")

    if p.startswith("file://"):
        p = p[7:]
        p = urllib.parse.unquote(p)

        if sys.platform == "win32" and p.startswith("/") and len(p) > 2 and p[2] == ":":
            p = p[1:]

    if sys.platform == "win32" and p.startswith("/") and len(p) >= 2 and p[1].isalpha() and (len(p) == 2 or p[2] == "/"):
        p = p[1] + ":" + p[2:]

    p = os.path.expanduser(p)
    p = os.path.normpath(p)
    return p


def split_paths_smart(raw_input):
    if not raw_input:
        return []

    raw_input = raw_input.strip()

    single = clean_path(raw_input)
    if os.path.exists(single):
        return [single]

    try:
        tokens = shlex.split(raw_input, posix=(os.name == "posix"))
    except ValueError:
        tokens = raw_input.split()

    result = []
    i = 0

    while i < len(tokens):
        best = None
        best_j = None

        for j in range(i, len(tokens)):
            candidate = " ".join(tokens[i:j + 1])
            candidate_clean = clean_path(candidate)

            if os.path.exists(candidate_clean):
                best = candidate_clean
                best_j = j

        if best is not None:
            result.append(best)
            i = best_j + 1
        else:
            candidate_clean = clean_path(tokens[i])
            if os.path.exists(candidate_clean):
                result.append(candidate_clean)
            i += 1

    return result


def parse_dropped_paths(raw_input):
    return split_paths_smart(raw_input)


def path_ext(name):
    return os.path.splitext(str(name).lower())[1]


def is_zip_name(name):
    return path_ext(name) == ".zip"


def is_archive_path(path):
    return os.path.isfile(path) and is_zip_name(path)


def is_locked_file(name):
    return path_ext(name) in LOCKED_EXTS


def normalize_arc_name(name):
    return str(name).replace("\\", "/")


def safe_rel_path(path, root):
    return os.path.relpath(path, root).replace("\\", "/")


def detect_encoding_from_bytes(raw):
    for enc in ["utf-8-sig", "utf-8", "utf-16", "cp1251", "cp1252"]:
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def detect_encoding(filepath):
    try:
        with open(filepath, "rb") as f:
            raw = f.read(8192)
    except Exception:
        return "utf-8"

    return detect_encoding_from_bytes(raw)


def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_memory(target_dir, disabled_files):
    memory = load_memory()
    memory[os.path.abspath(target_dir)] = {"disabled_files": disabled_files}

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=4)
    except IOError:
        pass


def get_default_download_path():
    if sys.platform == "win32":
        return os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    if "ANDROID_ROOT" in os.environ:
        return "/storage/emulated/0/Download"
    return os.path.join(str(Path.home()), "Downloads")


def load_config():
    mem = load_memory()
    conf = mem.get("_config_", {})
    lang = conf.get("lang", "en")
    out = conf.get("out", get_default_download_path())

    if lang not in T:
        lang = "en"

    return lang, clean_path(out)


def save_config(lang, out):
    mem = load_memory()
    mem["_config_"] = {"lang": lang, "out": out}

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=4)
    except IOError:
        pass


def draw_header(m, bw, title):
    spaces = " " * max(1, bw - text_width(title) - 3)
    print(f"{m}{C_WHITE}{C_BOLD}{title}{C_RESET}{spaces}{C_GRAY}esc{C_RESET}\n")


def draw_menu_item(m, num, text):
    print(f"{m}{C_YELLOW}{num}{C_RESET}  {C_WHITE}{text}{C_RESET}")


def draw_sys_item(m, bw, label, value):
    label_disp = label + "   "
    val_disp = truncate_text(value, bw - text_width(label_disp))
    print(f"{m}{C_WHITE}{label_disp}{C_RESET}{C_GRAY}{val_disp}{C_RESET}")


def make_file_item(source_type, display_name, selected=True, locked=False, lock_reason="", **kwargs):
    if is_locked_file(display_name):
        selected = False
        locked = True
        if not lock_reason:
            lock_reason = "Unsupported binary file type"

    item = {
        "source": source_type,
        "name": normalize_arc_name(display_name),
        "selected": selected,
        "locked": locked,
        "lock_reason": lock_reason
    }

    item.update(kwargs)
    return item


def item_unique_key(item):
    if item.get("source") == "file":
        return ("file", os.path.abspath(item.get("path", "")))

    if item.get("source") == "archive":
        return (
            "archive",
            os.path.abspath(item.get("archive_path", "")),
            item.get("member_chain", ""),
            item.get("name", "")
        )

    return (item.get("source"), item.get("name", ""))


def add_unique_item(file_data, item):
    key = item_unique_key(item)

    for old in file_data:
        if item_unique_key(old) == key:
            if not old.get("locked"):
                old["selected"] = True
            return

    file_data.append(item)


def collect_from_folder(folder_path, root_folder=None):
    folder_path = os.path.abspath(folder_path)

    if root_folder is None:
        root_folder = folder_path

    result = []

    for current_root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in sorted(dirs) if d not in IGNORE_DIRS]

        for filename in sorted(files):
            full_path = os.path.join(current_root, filename)
            rel_name = safe_rel_path(full_path, root_folder)

            if filename.startswith("extracted_data_") and filename.endswith(".txt"):
                continue

            if is_archive_path(full_path):
                result.extend(collect_from_archive_path(full_path, prefix=rel_name))
            else:
                result.append(
                    make_file_item(
                        "file",
                        rel_name,
                        path=os.path.abspath(full_path),
                        root=os.path.abspath(root_folder)
                    )
                )

    return result


def collect_from_zip_fileobj(fileobj, archive_label, prefix="", outer_chain=""):
    result = []

    with zipfile.ZipFile(fileobj, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue

            member_name = normalize_arc_name(info.filename)
            base = os.path.basename(member_name)

            if not base:
                continue

            display_name = normalize_arc_name(os.path.join(prefix, member_name)) if prefix else member_name

            if base.startswith("extracted_data_") and base.endswith(".txt"):
                continue

            chain = f"{outer_chain}::{member_name}" if outer_chain else member_name

            if is_zip_name(base):
                try:
                    with zf.open(info, "r") as src:
                        result.extend(
                            collect_nested_zip_stream(
                                src,
                                base,
                                archive_label,
                                nested_prefix=display_name,
                                outer_chain=chain
                            )
                        )
                except Exception:
                    result.append(
                        make_file_item(
                            "archive",
                            display_name,
                            selected=False,
                            locked=True,
                            lock_reason="Nested ZIP read error",
                            archive_type="zip",
                            archive_path=archive_label,
                            member_chain=chain
                        )
                    )
            else:
                result.append(
                    make_file_item(
                        "archive",
                        display_name,
                        archive_type="zip",
                        archive_path=archive_label,
                        member_chain=chain
                    )
                )

    return result


def collect_nested_zip_stream(stream, nested_name, root_archive_label, nested_prefix="", outer_chain=""):
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            tmp_path = tmp.name

            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)

        with open(tmp_path, "rb") as f:
            return collect_from_zip_fileobj(
                f,
                root_archive_label,
                prefix=nested_prefix,
                outer_chain=outer_chain
            )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def collect_from_archive_path(archive_path, prefix=""):
    archive_path = os.path.abspath(archive_path)

    try:
        with open(archive_path, "rb") as f:
            return collect_from_zip_fileobj(
                f,
                archive_path,
                prefix=prefix,
                outer_chain=""
            )
    except Exception:
        return [
            make_file_item(
                "archive",
                prefix or os.path.basename(archive_path),
                selected=False,
                locked=True,
                lock_reason="Bad ZIP archive",
                archive_type="zip",
                archive_path=archive_path,
                member_chain=""
            )
        ]


def collect_from_path(path):
    path = clean_path(path)

    if os.path.isdir(path):
        return collect_from_folder(path)

    if os.path.isfile(path):
        if is_archive_path(path):
            return collect_from_archive_path(path)

        return [
            make_file_item(
                "file",
                os.path.basename(path),
                path=os.path.abspath(path),
                root=os.path.dirname(os.path.abspath(path))
            )
        ]

    return []


def add_paths_to_file_data(file_data, paths):
    for p in paths:
        for item in collect_from_path(p):
            add_unique_item(file_data, item)


def read_text_stream_to_output(outfile, stream):
    pending = b""
    detected = False
    enc = "utf-8"

    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break

        if not detected:
            pending += chunk

            if len(pending) >= 8192:
                enc = detect_encoding_from_bytes(pending[:8192])
                outfile.write(pending.decode(enc, errors="replace"))
                pending = b""
                detected = True
        else:
            outfile.write(chunk.decode(enc, errors="replace"))

    if pending:
        enc = detect_encoding_from_bytes(pending[:8192])
        outfile.write(pending.decode(enc, errors="replace"))


def read_regular_file_to_output(outfile, item):
    filepath = item["path"]
    outfile.write(f"--- {item['name']} ---\n")

    enc = detect_encoding(filepath)

    try:
        with open(filepath, "r", encoding=enc, errors="replace") as infile:
            while True:
                chunk = infile.read(1024 * 1024)
                if not chunk:
                    break
                outfile.write(chunk)
    except Exception as e:
        outfile.write(f"[Read error: {e}]")

    outfile.write("\n\n\n")


def read_archive_item_to_output(outfile, item):
    outfile.write(f"--- {item['name']} ---\n")

    archive_path = item.get("archive_path")
    parts = [p for p in item.get("member_chain", "").split("::") if p]

    if not archive_path or not parts:
        outfile.write("[Archive read error: empty archive chain]\n\n\n")
        return

    tmp_to_cleanup = []

    try:
        if len(parts) == 1:
            with zipfile.ZipFile(archive_path, "r") as zf:
                with zf.open(parts[0], "r") as src:
                    read_text_stream_to_output(outfile, src)

        else:
            current_archive = archive_path

            for idx, part in enumerate(parts):
                is_last = idx == len(parts) - 1

                with zipfile.ZipFile(current_archive, "r") as zf:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=path_ext(part))
                    tmp_path = tmp.name

                    with zf.open(part, "r") as src:
                        shutil.copyfileobj(src, tmp, length=1024 * 1024)

                    tmp.close()

                tmp_to_cleanup.append(tmp_path)

                if is_last:
                    with open(tmp_path, "rb") as final_stream:
                        read_text_stream_to_output(outfile, final_stream)
                else:
                    current_archive = tmp_path

    except Exception as e:
        outfile.write(f"[Archive read error: {e}]")

    finally:
        for p in tmp_to_cleanup:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    outfile.write("\n\n\n")


def show_floating_modal(title, items, bg_draw_func):
    flush_input_events()

    max_len = text_width(title) + 10

    for item in items:
        length = text_width(item["label"]) + (text_width(item.get("shortcut", "")) + 4 if item.get("shortcut") else 0)
        max_len = max(max_len, length)

    mw = min(80, max(40, max_len + 6))
    mh = len(items) + 4

    sys.stdout.write("\033[?1000h\033[?1002h\033[?1003h\033[?1015h\033[?1006h\033[?25l")
    sys.stdout.flush()

    try:
        selectable = [i for i, it in enumerate(items) if it["type"] == "item"]

        if not selectable:
            return None

        sel_pos = 0
        last_size = (-1, -1)
        force_redraw = True
        sx = 1
        sy = 1

        def draw_dimmed_background():
            try:
                set_color_mode(True)
                bg_draw_func()
            finally:
                set_color_mode(False)

        def update_hover_selection(my):
            nonlocal sel_pos, force_redraw
            best_dist = 99999
            best_idx = sel_pos

            for i_sel, row_idx in enumerate(selectable):
                item_y = sy + 2 + row_idx
                dist = abs(my - item_y)

                if dist < best_dist:
                    best_dist = dist
                    best_idx = i_sel

            if best_idx != sel_pos:
                sel_pos = best_idx
                force_redraw = True

        with RawInput():
            while True:
                tw = get_term_width()

                try:
                    th = os.get_terminal_size().lines
                except OSError:
                    th = 24

                if (tw, th) != last_size:
                    draw_dimmed_background()
                    last_size = (tw, th)
                    force_redraw = True

                if force_redraw:
                    sx = max(1, (tw - mw) // 2)
                    sy = max(1, (th - mh) // 2)

                    title_part = f"  {title}"
                    esc_part = "esc  "
                    spaces = " " * max(0, mw - text_width(title_part) - text_width(esc_part))

                    sys.stdout.write(f"\033[{sy};{sx}H")
                    sys.stdout.write(
                        f"\033[48;2;30;30;30m"
                        f"\033[38;2;210;210;210m{title_part}"
                        f"{spaces}"
                        f"\033[38;2;110;110;110m{esc_part}"
                        f"\033[0m"
                    )

                    sys.stdout.write(f"\033[{sy + 1};{sx}H\033[48;2;30;30;30m{' ' * mw}\033[0m")

                    for i, item in enumerate(items):
                        sys.stdout.write(f"\033[{sy + 2 + i};{sx}H")
                        is_sel = selectable[sel_pos] == i

                        if item["type"] == "category":
                            line = pad_text(f"  {item['label']}", mw)
                            sys.stdout.write(
                                f"\033[48;2;30;30;30m"
                                f"\033[38;2;0;175;255m{line}"
                                f"\033[0m"
                            )
                        else:
                            bg = "\033[48;2;248;246;117m" if is_sel else "\033[48;2;30;30;30m"
                            fg = "\033[38;2;0;0;0m" if is_sel else "\033[38;2;210;210;210m"
                            s_fg = "\033[38;2;80;80;80m" if is_sel else "\033[38;2;110;110;110m"
                            lbl = item["label"]
                            sh = item.get("shortcut", "")
                            sp = max(0, mw - text_width(lbl) - text_width(sh) - 4)

                            sys.stdout.write(f"{bg}{fg}  {lbl}{' ' * sp}{s_fg}{sh}  \033[0m")

                    sys.stdout.write(f"\033[{sy + 2 + len(items)};{sx}H\033[48;2;30;30;30m{' ' * mw}\033[0m")
                    sys.stdout.write(f"\033[{sy + 3 + len(items)};{sx}H\033[48;2;30;30;30m{' ' * mw}\033[0m")
                    sys.stdout.flush()
                    force_redraw = False

                ev = get_event()

                if ev:
                    if ev == "UP":
                        sel_pos = (sel_pos - 1) % len(selectable)
                        force_redraw = True
                    elif ev == "DOWN":
                        sel_pos = (sel_pos + 1) % len(selectable)
                        force_redraw = True
                    elif ev in ("LEFT", "RIGHT", "IGNORE"):
                        continue
                    elif ev == "ESC":
                        return None
                    elif ev == "ENTER":
                        return items[selectable[sel_pos]]["id"]
                    elif isinstance(ev, tuple):
                        action, mx, my = ev

                        if action == "HOVER":
                            update_hover_selection(my)
                        elif action == "CLICK":
                            update_hover_selection(my)

                            if sx <= mx < sx + mw and sy <= my < sy + mh:
                                row = my - sy - 2

                                if 0 <= row < len(items) and items[row]["type"] == "item":
                                    return items[row]["id"]
                            else:
                                return None

    finally:
        sys.stdout.write("\033[?1006l\033[?1015l\033[?1003l\033[?1002l\033[?1000l\033[0m")
        sys.stdout.flush()


def kilo_input(prompt, redraw_callback):
    chars = []

    try:
        sys.stdout.write(f"{C_RESET}\033[?25l")
        tw, bw, m = redraw_callback()

        def draw_prompt():
            prefix = f" {prompt} "
            avail = max(1, bw - text_width(prefix))
            disp = "".join(chars)

            if text_width(disp) > avail:
                while text_width(disp) > avail - 3 and disp:
                    disp = disp[1:]
                disp = "..." + disp

            spaces = max(0, bw - text_width(prefix) - text_width(disp))

            box_render = (
                f"\r{m}{C_BLUE}▌"
                f"{C_BG_INPUT}{C_GRAY}{prefix}"
                f"{C_WHITE}{disp}"
                f"{' ' * spaces}{C_RESET}"
            )

            sys.stdout.write(box_render)

            if spaces > 0:
                sys.stdout.write(f"\033[{spaces}D")

            sys.stdout.flush()

        draw_prompt()
        sys.stdout.write(f"{C_WHITE}\033[?25h")
        sys.stdout.flush()

        last_size = get_term_width()

        with RawInput():
            while True:
                ev = get_event()

                curr_size = get_term_width()
                if curr_size != last_size:
                    last_size = curr_size
                    sys.stdout.write(f"{C_RESET}\033[?25l")
                    tw, bw, m = redraw_callback()
                    sys.stdout.write(f"{C_WHITE}\033[?25h")
                    draw_prompt()

                if ev in ("LEFT", "RIGHT", "UP", "DOWN", "IGNORE"):
                    continue

                if ev == "ESC":
                    sys.stdout.write(f"{C_RESET}\033[?25l")
                    return "esc"

                if ev == "ENTER":
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    sys.stdout.write(f"{C_RESET}\033[?25l")
                    return "".join(chars)

                if ev == "BACKSPACE":
                    if chars:
                        chars.pop()
                        draw_prompt()

                elif isinstance(ev, str) and len(ev) == 1:
                    chars.append(ev)
                    draw_prompt()

    except KeyboardInterrupt:
        sys.stdout.write(f"{C_RESET}\033[?1049l\033[?25h\n")
        sys.stdout.flush()
        sys.exit(0)

    except EOFError:
        sys.stdout.write(f"{C_RESET}\033[?25l")
        sys.stdout.flush()
        return "esc"


def is_esc(val):
    if val is None:
        return False
    return val.lower() in ("esc", "q", "\x1b", "exit")


def draw_message_screen(lang, title_key, message, prompt_key="press_enter_return"):
    t = T[lang]

    def draw_msg():
        clear_screen(13)
        draw_logo()
        tw, bw, m = get_layout()
        draw_header(m, bw, t[title_key])
        print()
        print_wrapped_text(message, m, bw, C_YELLOW)
        print()
        return tw, bw, m

    kilo_input(f"{t[prompt_key]}:", draw_msg)


def settings_menu(lang, output_dir):
    while True:
        t = T[lang]

        def draw_bg():
            clear_screen(18)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["commands"])

            print(f"{m}{C_BLUE}{t['actions']}{C_RESET}")
            draw_menu_item(m, "1", t["start"])
            draw_menu_item(m, "2", t["settings"])
            print()

            print(f"{m}{C_BLUE}{t['system']}{C_RESET}")
            draw_sys_item(m, bw, t["output_path"], output_dir)

            print_tip(t["tip_main"], m, bw)

        items = [
            {"type": "category", "label": t["settings"]},
            {"type": "item", "id": "path", "label": t["change_path"]},
            {"type": "item", "id": "lang", "label": t["change_lang"]}
        ]

        choice = show_floating_modal(t["settings"], items, draw_bg)

        if not choice:
            break

        elif choice == "path":
            def draw_path_bg():
                clear_screen(15)
                draw_logo()
                tw, bw, m = get_layout()
                draw_header(m, bw, t["settings"])
                print()
                return tw, bw, m

            raw_path = kilo_input(t["new_path"], draw_path_bg)

            if not is_esc(raw_path) and raw_path:
                new_path = clean_path(raw_path)

                try:
                    os.makedirs(new_path, exist_ok=True)
                    output_dir = new_path
                    save_config(lang, output_dir)
                except Exception as e:
                    draw_message_screen(lang, "settings", f"Error: {e}")

        elif choice == "lang":
            lang_items = [
                {"type": "category", "label": t["language"]},
                {"type": "item", "id": "en", "label": "English"},
                {"type": "item", "id": "ru", "label": "Русский"},
                {"type": "item", "id": "zh", "label": "中文"}
            ]

            new_lang = show_floating_modal(t["change_lang"], lang_items, draw_bg)

            if new_lang:
                lang = new_lang
                save_config(lang, output_dir)

    return lang, output_dir


def main_menu(lang, output_dir):
    while True:
        t = T[lang]

        def draw_main():
            clear_screen(18)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["commands"])

            print(f"{m}{C_BLUE}{t['actions']}{C_RESET}")
            draw_menu_item(m, "1", t["start"])
            draw_menu_item(m, "2", t["settings"])
            print()

            print(f"{m}{C_BLUE}{t['system']}{C_RESET}")
            draw_sys_item(m, bw, t["output_path"], output_dir)

            print_tip(t["tip_main"], m, bw)
            return tw, bw, m

        choice = kilo_input(t["action"], draw_main)

        if is_esc(choice):
            continue

        elif choice == "1":
            run_script(lang, output_dir)

        elif choice == "2":
            lang, output_dir = settings_menu(lang, output_dir)


def run_script(lang, output_dir):
    t = T[lang]

    def draw_target():
        clear_screen(13)
        draw_logo()
        tw, bw, m = get_layout()
        draw_header(m, bw, t["target_dir"])

        print(f"{m}{C_BLUE}{t['input']}{C_RESET}")
        print_wrapped_text(t["enter_path"], m, bw, C_GRAY)
        print()

        return tw, bw, m

    raw_path = kilo_input(t["path"], draw_target)

    if is_esc(raw_path):
        return

    paths = parse_dropped_paths(raw_path)

    if not paths:
        draw_message_screen(lang, "target_dir", t["err_not_found"])
        return

    file_data = []

    try:
        add_paths_to_file_data(file_data, paths)
    except PermissionError:
        draw_message_screen(lang, "target_dir", t["err_permission"])
        return
    except Exception as e:
        draw_message_screen(lang, "target_dir", f"{t['err_bad_archive']} {e}")
        return

    if not file_data:
        draw_message_screen(lang, "target_dir", t["err_empty"])
        return

    sources_display = ", ".join(paths)

    memory_key = paths[0] if len(paths) == 1 else sources_display
    disabled_files = load_memory().get(os.path.abspath(memory_key), {}).get("disabled_files", [])

    for item in file_data:
        if item["name"] in disabled_files and not item.get("locked"):
            item["selected"] = False

    while True:
        def draw_selection():
            display_limit = 160
            total_lines = 17 + min(len(file_data), display_limit)

            if len(file_data) > display_limit:
                total_lines += 1

            clear_screen(total_lines)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["select_files"])

            print(f"{m}{C_BLUE}{t['sources']}{C_RESET}")
            print_wrapped_text(truncate_text(sources_display, bw * 3), m, bw, C_WHITE)
            print()

            print(f"{m}{C_BLUE}{t['files']}{C_RESET}")

            for i, item in enumerate(file_data[:display_limit]):
                num = str(i + 1)
                suffix = f" [{t['locked']}]" if item.get("locked") else ""
                file_disp = truncate_text(item["name"] + suffix, bw - 7)

                if item.get("locked"):
                    print(f"{m}{C_DARK_GRAY}{num:<3} {file_disp}{C_RESET}")
                elif item["selected"]:
                    print(f"{m}{C_WHITE}{num:<3}{C_RESET} {C_WHITE}{file_disp}{C_RESET}")
                else:
                    print(f"{m}{C_DARK_GRAY}{num:<3} {file_disp}{C_RESET}")

            if len(file_data) > display_limit:
                rem = len(file_data) - display_limit
                print(f"{m}{C_GRAY}... +{rem}{C_RESET}")

            selected_count = sum(1 for item in file_data if item["selected"])
            total_count = len(file_data)

            print(
                f"\n{m}{C_GRAY}{t['selected']} "
                f"{C_WHITE}{selected_count}{C_GRAY} "
                f"{t['of']} {total_count}{C_RESET}"
            )

            print_tip(t["tip_toggle"], m, bw)
            return tw, bw, m

        choice = kilo_input(t["toggle"], draw_selection).strip()

        if is_esc(choice):
            return

        elif choice == "0":
            break

        elif choice:
            more_paths = parse_dropped_paths(choice)

            if more_paths:
                try:
                    add_paths_to_file_data(file_data, more_paths)
                    sources_display += ", " + ", ".join(more_paths)
                except Exception:
                    pass
                continue

            try:
                tokens = shlex.split(choice, posix=(os.name == "posix"))
            except ValueError:
                tokens = choice.split()

            for tok in tokens:
                if tok.isdigit():
                    idx = int(tok) - 1

                    if 0 <= idx < len(file_data):
                        if file_data[idx].get("locked"):
                            continue
                        file_data[idx]["selected"] = not file_data[idx]["selected"]

    if not any(item["selected"] for item in file_data):
        draw_message_screen(lang, "select_files", t["err_no_selected"])
        return

    disabled_to_save = [
        item["name"]
        for item in file_data
        if not item["selected"] and not item.get("locked")
    ]
    save_memory(memory_key, disabled_to_save)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(output_dir, f"extracted_data_{timestamp}.txt")

    try:
        os.makedirs(output_dir, exist_ok=True)

        clear_screen(15)
        draw_logo()
        tw, bw, m = get_layout()
        draw_header(m, bw, t["actions"])
        print(f"\n{m}{C_BLUE}{t.get('exporting', 'Exporting:')}{C_RESET}")
        sys.stdout.write("\033[s")

        with open(out_file, "w", encoding="utf-8") as outfile:
            selected_items = [
                item
                for item in file_data
                if item["selected"] and not item.get("locked")
            ]

            total = len(selected_items)

            for idx, item in enumerate(selected_items, 1):
                sys.stdout.write("\033[u\033[J")
                sys.stdout.write(
                    f"{m}{C_WHITE}{idx} / {total} : "
                    f"{truncate_text(item['name'], bw - 15)}"
                    f"{C_RESET}\n"
                )
                sys.stdout.flush()

                if item.get("source") == "file":
                    read_regular_file_to_output(outfile, item)
                elif item.get("source") == "archive":
                    read_archive_item_to_output(outfile, item)

        def draw_success():
            clear_screen(15)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["success"])

            print(f"{m}{C_WHITE}{t['success_msg']}{C_RESET}\n")
            print(f"{m}{C_BLUE}{t['output_loc']}{C_RESET}")
            print(f"{m}{C_WHITE}{truncate_text(out_file, bw)}{C_RESET}\n")

            return tw, bw, m

        kilo_input(f"{t['press_enter_return']}:", draw_success)

    except Exception as e:
        def draw_save_err():
            clear_screen(15)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["system"])
            print()
            print_wrapped_text(f"{t['err_save']} {e}", m, bw, C_YELLOW)
            print()
            return tw, bw, m

        kilo_input(f"{t['press_enter_return']}:", draw_save_err)


if __name__ == "__main__":
    sys.stdout.write("\033[?1049h\033[?25l")
    sys.stdout.flush()

    try:
        init_lang, init_out = load_config()
        main_menu(init_lang, init_out)

    except KeyboardInterrupt:
        pass

    finally:
        sys.stdout.write(f"{C_RESET}\033[?1049l\033[?25h")
        sys.stdout.flush()
