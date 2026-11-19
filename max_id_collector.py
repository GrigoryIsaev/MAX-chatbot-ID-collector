import json
import queue
import threading
import urllib.error
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

API_BASE = "https://platform-api2.max.ru"
POLL_TIMEOUT = 30


class MaxApiClient:
    def __init__(self, token):
        self.token = token.strip()
        self.marker = None

    def get_updates(self, timeout):
        params = {"limit": 1000, "timeout": timeout}
        if self.marker is not None:
            params["marker"] = self.marker
        url = API_BASE + "/updates?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={"Authorization": "Bearer " + self.token,
                     "Accept": "application/json",
                     "User-Agent": "MAX-Teacher-ID-Collector/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout + 15) as response:
            data = json.loads(response.read().decode("utf-8"))
        if data.get("marker") is not None:
            self.marker = data["marker"]
        return data.get("updates") or []


class CollectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Сбор ID пользователей MAX")
        self.root.geometry("850x560")
        self.root.minsize(700, 430)
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = None
        self.users = {}
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Сбор ID пользователей MAX",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, 8))
        token_frame = ttk.Frame(outer)
        token_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(token_frame, text="Токен бота:").pack(side="left")
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(token_frame, textvariable=self.token_var,
                                     show="*", width=55)
        self.token_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.connect_button = ttk.Button(token_frame, text="Начать сбор",
                                         command=self.start)
        self.connect_button.pack(side="left")
        self.status_var = tk.StringVar(value="Введите токен MAX-бота и нажмите «Начать сбор».")
        ttk.Label(outer, textvariable=self.status_var,
                  foreground="#245a86").pack(anchor="w", pady=(0, 8))

        columns = ("user_id", "full_name", "username")
        self.table = ttk.Treeview(outer, columns=columns, show="headings",
                                  selectmode="extended")
        self.table.heading("user_id", text="User ID")
        self.table.heading("full_name", text="Имя и фамилия")
        self.table.heading("username", text="Username")
        self.table.column("user_id", width=190, anchor="center")
        self.table.column("full_name", width=330)
        self.table.column("username", width=220)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        right = ttk.Frame(outer)
        right.pack(side="right", fill="y", padx=(10, 0))
        ttk.Button(right, text="Выбрать всех", command=self.select_all).pack(fill="x", pady=(0, 6))
        ttk.Button(right, text="Снять выбор", command=self.clear_selection).pack(fill="x", pady=(0, 6))
        ttk.Button(right, text="Скопировать ID", command=self.copy_selected).pack(fill="x", pady=(0, 6))
        ttk.Button(right, text="Остановить", command=self.stop).pack(fill="x")
        self.count_var = tk.StringVar(value="Пользователей найдено: 0")
        ttk.Label(outer, textvariable=self.count_var).pack(anchor="w", pady=(8, 0))
        ttk.Label(outer,
                  text="Выберите строки (Ctrl/Shift), затем нажмите «Скопировать ID». ID будут скопированы через запятую.",
                  wraplength=800).pack(anchor="w", pady=(5, 0))
        self.root.after(150, self.process_events)

    def start(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("Нет токена", "Введите токен MAX-бота.")
            return
        if self.worker and self.worker.is_alive():
            return
        self.stop_event.clear()
        self.connect_button.config(state="disabled")
        self.token_entry.config(state="disabled")
        self.status_var.set("Подключение к MAX…")
        self.worker = threading.Thread(target=self.poll_loop, args=(token,), daemon=True)
        self.worker.start()

    def poll_loop(self, token):
        client = MaxApiClient(token)
        try:
            # Начальный запрос устанавливает marker; накопленные ранее события пропускаются.
            client.get_updates(timeout=0)
            self.events.put(("status", "Подключено. Ожидание новых сообщений…"))
        except Exception as exc:
            self.events.put(("error", self.format_error(exc)))
            self.events.put(("stopped", None))
            return

        while not self.stop_event.is_set():
            try:
                for update in client.get_updates(timeout=POLL_TIMEOUT):
                    if update.get("update_type") != "message_created":
                        continue
                    message = update.get("message") or {}
                    sender = message.get("sender") or {}
                    user_id = sender.get("user_id")
                    if user_id is None or sender.get("is_bot"):
                        continue
                    first = (sender.get("first_name") or "").strip()
                    last = (sender.get("last_name") or "").strip()
                    full_name = " ".join(x for x in (first, last) if x)
                    if not full_name:
                        full_name = "(имя не передано MAX)"
                    username = sender.get("username") or ""
                    self.events.put(("user", {
                        "user_id": str(user_id), "full_name": full_name,
                        "username": ("@" + username) if username else "—"
                    }))
            except urllib.error.HTTPError as exc:
                detail = ""
                try:
                    detail = exc.read().decode("utf-8", errors="replace")[:500]
                except Exception:
                    pass
                self.events.put(("status", f"Ошибка HTTP {exc.code}. Повтор через 5 секунд. {detail}"))
                if exc.code in (401, 403):
                    self.events.put(("stopped", None))
                    return
                self.stop_event.wait(5)
            except Exception as exc:
                self.events.put(("status", f"Ошибка соединения: {self.format_error(exc)}. Повтор через 5 секунд."))
                self.stop_event.wait(5)
        self.events.put(("stopped", None))

    @staticmethod
    def format_error(exc):
        if isinstance(exc, urllib.error.HTTPError):
            return f"HTTP {exc.code}: {exc.reason}"
        if isinstance(exc, urllib.error.URLError):
            return f"ошибка соединения: {exc.reason}"
        return str(exc)

    def process_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "status":
                    self.status_var.set(payload)
                elif kind == "error":
                    self.status_var.set("Не удалось подключиться.")
                    messagebox.showerror("Ошибка MAX API", payload)
                elif kind == "user":
                    uid = payload["user_id"]
                    self.users[uid] = payload
                    values = (uid, payload["full_name"], payload["username"])
                    if self.table.exists(uid):
                        self.table.item(uid, values=values)
                    else:
                        self.table.insert("", "end", iid=uid, values=values)
                    self.count_var.set(f"Пользователей найдено: {len(self.users)}")
                elif kind == "stopped":
                    self.connect_button.config(state="normal")
                    self.token_entry.config(state="normal")
                    if self.status_var.get().startswith("Подключено"):
                        self.status_var.set("Сбор остановлен.")
        except queue.Empty:
            pass
        self.root.after(150, self.process_events)

    def select_all(self):
        self.table.selection_set(self.table.get_children())

    def clear_selection(self):
        self.table.selection_remove(self.table.selection())

    def copy_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("Ничего не выбрано", "Сначала выберите пользователей в списке.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(",".join(selected))
        self.root.update()
        messagebox.showinfo("Скопировано", f"Скопировано ID: {len(selected)}")

    def stop(self):
        self.stop_event.set()
        self.status_var.set("Остановка…")

    def close(self):
        self.stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CollectorApp(root)
    root.mainloop()
