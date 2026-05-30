import os
import sys
import json
import datetime
import textwrap
import shlex
import urllib.parse
import time
import zipfile
import tempfile
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

if sys.platform == "win32":
    os.system("")

MEMORY_FILE = Path.home() / ".merge_files_memory.json"

ARCHIVE_EXTS = {".zip"}

LOCKED_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg",
    ".apk", ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    ".db", ".sqlite", ".sqlite3",
    ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".mkv", ".avi", ".mov",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".ttf", ".otf", ".woff", ".woff2",
    ".class", ".jar", ".dex",
    ".pyc", ".pyo",
    ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"
}

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
        "tip_main": "Type number to select, 'esc' to go back, or Ctrl+C to exit",
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
        "source": "Source",
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
        "unsupported": "Unsupported binary file type"
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
        "tip_main": "Введите номер для выбора, 'esc' для возврата, или Ctrl+C для выхода",
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
        "source": "Источник",
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
        "unsupported": "Неподдерживаемый бинарный тип файла"
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
        "tip_main": "输入数字进行选择，'esc' 返回，或按 Ctrl+C 退出",
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
        "source": "来源",
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
        "unsupported": "不支持的二进制文件类型"
    }
}


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

    p = os.path.expanduser(p)
    p = os.path.normpath(p)
    return p


def split_paths_smart(raw_input):
    """
    Поддерживает:
    1. Один путь с пробелами:
       /storage/emulated/0/Download/GitVPN-main (3).zip

    2. Несколько путей в кавычках:
       "/path/one file.zip" "/path/two folder"

    3. Несколько путей без пробелов внутри:
       /path/a.zip /path/b.zip /path/folder

    4. Частично пытается собрать пути с пробелами жадно.
    """
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

    if not tokens:
        return []

    result = []
    i = 0

    while i < len(tokens):
        current = tokens[i]
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
            candidate_clean = clean_path(current)
            if os.path.exists(candidate_clean):
                result.append(candidate_clean)
            i += 1

    return result


def parse_dropped_paths(raw_input):
    return split_paths_smart(raw_input)


def path_ext(name):
    return os.path.splitext(name.lower())[1]


def is_locked_file(name):
    return path_ext(name) in LOCKED_EXTS


def is_archive_name(name):
    return path_ext(name) in ARCHIVE_EXTS


def is_archive_path(path):
    return os.path.isfile(path) and is_archive_name(path)


def is_zip_name(name):
    return path_ext(name) == ".zip"


def normalize_arc_name(name):
    return name.replace("\\", "/")


def safe_rel_path(path, root):
    rel = os.path.relpath(path, root)
    return rel.replace("\\", "/")


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
    abs_dir = os.path.abspath(target_dir)
    memory[abs_dir] = {"disabled_files": disabled_files}

    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=4)
    except IOError:
        pass


def get_default_download_path():
    if sys.platform == "win32":
        return os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    elif "ANDROID_ROOT" in os.environ:
        return "/storage/emulated/0/Download"
    else:
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


def get_term_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def get_layout():
    tw = get_term_width()
    bw = max(10, min(tw - 4, 70))
    m_len = max(0, (tw - bw) // 2)
    return tw, bw, " " * m_len


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


def truncate_text(text, max_len):
    if max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]
    return text[:max_len - 3] + "..."


def print_wrapped_text(text, m, bw, color=C_GRAY):
    lines = textwrap.wrap(
        text,
        width=max(10, bw),
        break_long_words=False,
        break_on_hyphens=False
    )

    if not lines:
        print()
        return

    for line in lines:
        print(f"{m}{color}{line}{C_RESET}")


def draw_logo():
    ASCII_LOGO = [
        "██^^^^ ██ ██     ██^^^^   ▄█████ ██     ██ ",
        "██^^   ██ ██     ██^^     ██~~~~ ██     ██ ",
        "██     ██ ██████ ██████   ▀█████ ██████ ██ ",
        "~~     ~~ ~~~~~~ ~~~~~~    ~~~~~ ~~~~~~ ~~ "
    ]

    C_SHADOW_FG = "\033[38;2;90;90;40m"
    C_SHADOW_BG = "\033[48;2;90;90;40m"

    tw = get_term_width()
    logo_width = len(ASCII_LOGO[0])
    indent = " " * max(0, (tw - logo_width) // 2)

    print()

    for line in ASCII_LOGO:
        rendered_line = indent

        for char in line:
            if char == "_":
                rendered_line += f"{C_SHADOW_BG} {C_RESET}"
            elif char == "^":
                rendered_line += f"{C_YELLOW}{C_SHADOW_BG}▀{C_RESET}"
            elif char == "~":
                rendered_line += f"{C_SHADOW_FG}▀{C_RESET}"
            else:
                rendered_line += f"{C_YELLOW}{char}{C_RESET}"

        print(rendered_line)

    print("\n")


def print_tip(text, m, bw):
    lines = textwrap.wrap(
        text,
        width=max(10, bw - 6),
        break_long_words=False,
        break_on_hyphens=False
    )

    if lines:
        print(f"\n{m}{C_YELLOW}● Tip{C_RESET} {C_GRAY}{lines[0]}{C_RESET}")
        for line in lines[1:]:
            print(f"{m}      {C_GRAY}{line}{C_RESET}")

    print()


def read_escape_sequence_posix(stdin, first_timeout=0.18, next_timeout=0.03):
    import select

    seq = "\x1b"

    r, _, _ = select.select([stdin], [], [], first_timeout)
    if not r:
        return seq

    while True:
        r, _, _ = select.select([stdin], [], [], next_timeout)
        if not r:
            break

        ch = stdin.read(1)
        seq += ch

        if seq.endswith("~"):
            break

        if len(seq) >= 16:
            break

        if len(seq) >= 3 and seq.startswith("\x1b[") and seq[-1].isalpha():
            break

        if len(seq) >= 3 and seq.startswith("\x1bO") and seq[-1].isalpha():
            break

    return seq


def kilo_input(prompt, redraw_callback):
    chars = []

    try:
        sys.stdout.write(f"{C_RESET}\033[?25l")
        tw, bw, m = redraw_callback()

        def draw_prompt():
            prefix = f" {prompt} "
            avail = max(1, bw - len(prefix))
            disp = "".join(chars)

            if len(disp) > avail:
                disp = disp[-avail:]

            spaces = max(0, bw - len(prefix) - len(disp))

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

        if sys.platform == "win32":
            import msvcrt

            while True:
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()

                    if ch == "\x1b":
                        time.sleep(0.08)

                        if msvcrt.kbhit():
                            extra = msvcrt.getwch()

                            if extra in ("\x00", "\xe0"):
                                if msvcrt.kbhit():
                                    msvcrt.getwch()
                                continue

                            if extra == "[":
                                while msvcrt.kbhit():
                                    tail = msvcrt.getwch()
                                    if tail.isalpha() or tail == "~":
                                        break
                                continue

                            chars.append(extra)
                            draw_prompt()
                            continue

                        sys.stdout.write(f"{C_RESET}\033[?25l")
                        return "esc"

                    elif ch in ("\r", "\n"):
                        sys.stdout.write("\n")
                        sys.stdout.flush()
                        sys.stdout.write(f"{C_RESET}\033[?25l")
                        return "".join(chars)

                    elif ch == "\b":
                        if chars:
                            chars.pop()
                            draw_prompt()

                    elif ch == "\x03":
                        raise KeyboardInterrupt

                    elif ch in ("\x00", "\xe0"):
                        if msvcrt.kbhit():
                            msvcrt.getwch()
                        continue

                    else:
                        chars.append(ch)
                        draw_prompt()

                else:
                    curr_size = get_term_width()
                    if curr_size != last_size:
                        last_size = curr_size
                        sys.stdout.write(f"{C_RESET}\033[?25l")
                        tw, bw, m = redraw_callback()
                        sys.stdout.write(f"{C_WHITE}\033[?25h")
                        draw_prompt()

                    time.sleep(0.01)

        else:
            import tty
            import termios
            import select

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)

            try:
                tty.setcbreak(fd)

                while True:
                    r, _, _ = select.select([sys.stdin], [], [], 0.05)

                    if r:
                        ch = sys.stdin.read(1)

                        if ch == "\x1b":
                            seq = read_escape_sequence_posix(sys.stdin)

                            if seq == "\x1b":
                                sys.stdout.write(f"{C_RESET}\033[?25l")
                                return "esc"

                            if seq.startswith("\x1b[200~"):
                                paste_buffer = []

                                while True:
                                    c = sys.stdin.read(1)
                                    paste_buffer.append(c)

                                    if "".join(paste_buffer).endswith("\x1b[201~"):
                                        pasted = "".join(paste_buffer)[:-6]
                                        chars.extend(list(pasted))
                                        draw_prompt()
                                        break

                                continue

                            if (
                                seq.startswith("\x1b[")
                                or seq.startswith("\x1bO")
                                or seq.startswith("\x1b]")
                            ):
                                continue

                            continue

                        elif ch in ("\n", "\r"):
                            sys.stdout.write("\n")
                            sys.stdout.flush()
                            sys.stdout.write(f"{C_RESET}\033[?25l")
                            return "".join(chars)

                        elif ch in ("\x7f", "\b"):
                            if chars:
                                chars.pop()
                                draw_prompt()

                        elif ch == "\x03":
                            raise KeyboardInterrupt

                        elif ch == "\x04":
                            raise EOFError

                        elif ch in ("\x00",):
                            continue

                        else:
                            chars.append(ch)
                            draw_prompt()

                    else:
                        curr_size = get_term_width()
                        if curr_size != last_size:
                            last_size = curr_size
                            sys.stdout.write(f"{C_RESET}\033[?25l")
                            tw, bw, m = redraw_callback()
                            sys.stdout.write(f"{C_WHITE}\033[?25h")
                            draw_prompt()

            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

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


def draw_header(m, bw, title):
    spaces = " " * max(1, bw - len(title) - 3)
    print(f"{m}{C_WHITE}{C_BOLD}{title}{C_RESET}{spaces}{C_GRAY}esc{C_RESET}\n")


def draw_menu_item(m, num, text):
    print(f"{m}{C_YELLOW}{num}{C_RESET}  {C_WHITE}{text}{C_RESET}")


def draw_sys_item(m, bw, label, value):
    label_disp = label + "   "
    val_disp = truncate_text(value, bw - len(label_disp))
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


def add_unique_item(file_data, item):
    key = item_unique_key(item)

    for old in file_data:
        if item_unique_key(old) == key:
            if not old.get("locked"):
                old["selected"] = True
            return

    file_data.append(item)


def item_unique_key(item):
    source = item.get("source")

    if source == "file":
        return ("file", os.path.abspath(item.get("path", "")))

    if source == "archive":
        return (
            "archive",
            os.path.abspath(item.get("archive_path", "")),
            item.get("member_chain", ""),
            item.get("name", "")
        )

    return (source, item.get("name", ""))


def collect_from_folder(folder_path, root_folder=None):
    folder_path = os.path.abspath(folder_path)

    if root_folder is None:
        root_folder = folder_path

    result = []

    for current_root, dirs, files in os.walk(folder_path):
        dirs.sort()
        files.sort()

        for filename in files:
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
        infos = zf.infolist()

        for info in infos:
            if info.is_dir():
                continue

            member_name = normalize_arc_name(info.filename)
            base = os.path.basename(member_name)

            if not base:
                continue

            display_name = normalize_arc_name(os.path.join(prefix, member_name)) if prefix else member_name
            display_name = normalize_arc_name(display_name)

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
    """
    Для вложенных ZIP поток временно сохраняется на диск.
    Это позволяет не держать весь архив в памяти постоянно.
    """
    suffix = path_ext(nested_name)
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name

            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)

        if suffix == ".zip":
            with open(tmp_path, "rb") as f:
                return collect_from_zip_fileobj(
                    f,
                    root_archive_label,
                    prefix=nested_prefix,
                    outer_chain=outer_chain
                )

        return []

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def collect_from_archive_path(archive_path, prefix=""):
    archive_path = os.path.abspath(archive_path)
    ext = path_ext(archive_path)

    if ext == ".zip":
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

    return []


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
    chain = item.get("member_chain", "")
    parts = [p for p in chain.split("::") if p]

    if not archive_path or not parts:
        outfile.write("[Archive read error: empty archive chain]")
        outfile.write("\n\n\n")
        return

    try:
        root_ext = path_ext(archive_path)

        if root_ext != ".zip":
            outfile.write("[Archive read error: unsupported archive]")
            outfile.write("\n\n\n")
            return

        if len(parts) == 1:
            member = parts[0]

            with zipfile.ZipFile(archive_path, "r") as zf:
                with zf.open(member, "r") as src:
                    read_text_stream_to_output(outfile, src)

        else:
            tmp_current_archive = archive_path
            tmp_to_cleanup = []

            try:
                for idx, part in enumerate(parts):
                    is_last = idx == len(parts) - 1
                    current_ext = path_ext(tmp_current_archive)

                    if current_ext != ".zip":
                        outfile.write("[Archive read error: unsupported nested archive]")
                        return

                    with zipfile.ZipFile(tmp_current_archive, "r") as zf:
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
                        tmp_current_archive = tmp_path

            finally:
                for p in tmp_to_cleanup:
                    try:
                        if os.path.exists(p):
                            os.remove(p)
                    except Exception:
                        pass

    except Exception as e:
        outfile.write(f"[Archive read error: {e}]")

    outfile.write("\n\n\n")


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

        def draw_main():
            clear_screen(15)
            draw_logo()
            tw, bw, m = get_layout()
            draw_header(m, bw, t["settings"])
            print(f"{m}{C_BLUE}{t['actions']}{C_RESET}")
            draw_menu_item(m, "1", t["change_path"])
            draw_menu_item(m, "2", t["change_lang"])
            print()
            print_tip(t["tip_main"], m, bw)
            return tw, bw, m

        choice = kilo_input(t["action"], draw_main)

        if is_esc(choice):
            break

        elif choice == "1":
            def draw_path():
                clear_screen(15)
                draw_logo()
                tw, bw, m = get_layout()
                draw_header(m, bw, t["settings"])
                print()
                return tw, bw, m

            raw_path = kilo_input(t["new_path"], draw_path)

            if not is_esc(raw_path) and raw_path:
                new_path = clean_path(raw_path)

                try:
                    os.makedirs(new_path, exist_ok=True)
                    output_dir = new_path
                    save_config(lang, output_dir)

                    def draw_success():
                        clear_screen(15)
                        draw_logo()
                        tw, bw, m = get_layout()
                        draw_header(m, bw, t["settings"])
                        print(f"\n{m}{C_WHITE}{t['path_updated']}{C_RESET}\n")
                        return tw, bw, m

                    kilo_input(f"{t['press_enter']}:", draw_success)

                except Exception as e:
                    def draw_err():
                        clear_screen(15)
                        draw_logo()
                        tw, bw, m = get_layout()
                        draw_header(m, bw, t["settings"])
                        print()
                        print_wrapped_text(str(e), m, bw, C_YELLOW)
                        print()
                        return tw, bw, m

                    kilo_input(f"{t['press_enter']}:", draw_err)

        elif choice == "2":
            def draw_lang():
                clear_screen(15)
                draw_logo()
                tw, bw, m = get_layout()
                draw_header(m, bw, t["settings"])
                print(f"\n{m}{C_WHITE}1 - English, 2 - Русский, 3 - 中文{C_RESET}\n")
                return tw, bw, m

            l_choice = kilo_input("Language:", draw_lang)

            if is_esc(l_choice):
                continue

            if l_choice == "1":
                lang = "en"
            elif l_choice == "2":
                lang = "ru"
            elif l_choice == "3":
                lang = "zh"

            if l_choice in ["1", "2", "3"]:
                save_config(lang, output_dir)
                t = T[lang]

                def draw_l_success():
                    clear_screen(15)
                    draw_logo()
                    tw, bw, m = get_layout()
                    draw_header(m, bw, t["settings"])
                    print(f"\n{m}{C_WHITE}{t['lang_updated']}{C_RESET}\n")
                    return tw, bw, m

                kilo_input(f"{t['press_enter']}:", draw_l_success)

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

    while True:
        def draw_selection():
            total_lines = 17 + min(len(file_data), 200)
            clear_screen(total_lines)
            draw_logo()
            tw, bw, m = get_layout()

            draw_header(m, bw, t["select_files"])

            print(f"{m}{C_BLUE}{t['sources']}{C_RESET}")
            print_wrapped_text(truncate_text(sources_display, bw * 3), m, bw, C_WHITE)
            print()

            print(f"{m}{C_BLUE}{t['files']}{C_RESET}")

            max_show = max(1, min(len(file_data), 160))

            for i, item in enumerate(file_data[:max_show]):
                num = str(i + 1)
                suffix = ""

                if item.get("locked"):
                    suffix = f" [{t['locked']}]"

                file_disp = truncate_text(item["name"] + suffix, bw - 6)

                if item.get("locked"):
                    print(f"{m}{C_DARK_GRAY}{num:<2}  {file_disp}{C_RESET}")
                elif item["selected"]:
                    print(f"{m}{C_WHITE}{num:<2}{C_RESET}  {C_WHITE}{file_disp}{C_RESET}")
                else:
                    print(f"{m}{C_DARK_GRAY}{num:<2}  {file_disp}{C_RESET}")

            if len(file_data) > max_show:
                more = len(file_data) - max_show
                print(f"{m}{C_GRAY}... +{more}{C_RESET}")

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

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(output_dir, f"extracted_data_{timestamp}.txt")

    try:
        os.makedirs(output_dir, exist_ok=True)

        with open(out_file, "w", encoding="utf-8") as outfile:
            for item in file_data:
                if not item["selected"]:
                    continue

                if item.get("locked"):
                    continue

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
