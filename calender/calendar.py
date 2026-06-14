import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from datetime import datetime, date
import json
import os


class ReminderDialog(tk.Toplevel):
    def __init__(self, parent, title="Add Reminder", time_val="", text_val=""):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self.grab_set()

        self.geometry("380x220")
        self.transient(parent)

        # Center on parent
        parent.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - 190
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - 110
        self.geometry(f"+{px}+{py}")

        # Header
        hdr = tk.Frame(self, bg="#2563eb", height=50)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title, font=("Segoe UI", 13, "bold"),
                 bg="#2563eb", fg="white").pack(side=tk.LEFT, padx=18, pady=12)

        body = tk.Frame(self, bg="#1e1e2e", padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        # Time row
        tk.Label(body, text="Time (HH:MM)", font=("Segoe UI", 10),
                 bg="#1e1e2e", fg="#94a3b8").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.time_var = tk.StringVar(value=time_val)
        time_entry = tk.Entry(body, textvariable=self.time_var, font=("Segoe UI", 12),
                              bg="#2d2d44", fg="white", insertbackground="white",
                              relief=tk.FLAT, bd=6, width=10)
        time_entry.grid(row=1, column=0, sticky="w", pady=(0, 12))
        time_entry.focus_set()

        # Text row
        tk.Label(body, text="Reminder text", font=("Segoe UI", 10),
                 bg="#1e1e2e", fg="#94a3b8").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.text_var = tk.StringVar(value=text_val)
        text_entry = tk.Entry(body, textvariable=self.text_var, font=("Segoe UI", 12),
                              bg="#2d2d44", fg="white", insertbackground="white",
                              relief=tk.FLAT, bd=6, width=30)
        text_entry.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 16))
        body.columnconfigure(0, weight=1)

        # Buttons
        btn_frame = tk.Frame(body, bg="#1e1e2e")
        btn_frame.grid(row=4, column=0, columnspan=3, sticky="e")

        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  font=("Segoe UI", 10), bg="#374151", fg="#d1d5db",
                  relief=tk.FLAT, padx=16, pady=6, cursor="hand2",
                  activebackground="#4b5563", activeforeground="white").pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(btn_frame, text="Save", command=self._save,
                  font=("Segoe UI", 10, "bold"), bg="#2563eb", fg="white",
                  relief=tk.FLAT, padx=16, pady=6, cursor="hand2",
                  activebackground="#1d4ed8", activeforeground="white").pack(side=tk.LEFT)

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _save(self):
        time_str = self.time_var.get().strip()
        text_str = self.text_var.get().strip()

        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            self._shake()
            return

        if not text_str:
            self._shake()
            return

        self.result = (time_str, text_str)
        self.destroy()

    def _shake(self):
        x, y = self.winfo_x(), self.winfo_y()
        for dx in [8, -8, 6, -6, 4, -4, 0]:
            self.geometry(f"+{x + dx}+{y}")
            self.update()
            self.after(30)


class CalendarReminderApp:
    # ── palette ────────────────────────────────────────────────────────────
    BG_DARK      = "#0f0f1a"
    BG_PANEL     = "#1a1a2e"
    BG_CARD      = "#16213e"
    BG_SIDEBAR   = "#1a1a2e"
    ACCENT       = "#2563eb"
    ACCENT_LIGHT = "#3b82f6"
    SUCCESS      = "#10b981"
    DANGER       = "#ef4444"
    WARNING      = "#f59e0b"
    TEXT_PRI     = "#f1f5f9"
    TEXT_SEC     = "#94a3b8"
    TEXT_MUT     = "#64748b"
    BORDER       = "#2d3748"
    TODAY_BG     = "#2563eb"
    TODAY_FG     = "#ffffff"
    SEL_BG       = "#1d4ed8"
    SEL_FG       = "#ffffff"
    REMIND_BG    = "#064e3b"
    REMIND_FG    = "#6ee7b7"
    WEEKEND_FG   = "#f87171"
    HEADER_BG    = "#0d1117"
    DAY_HDR_BG   = "#1e293b"
    DAY_HDR_FG   = "#64748b"

    def __init__(self, root):
        self.root = root
        self.root.title("Calendar & Reminders")
        self.root.geometry("980x680")
        self.root.configure(bg=self.BG_DARK)
        self.root.minsize(820, 580)

        self.data_file = "reminders.json"
        self.reminders = self._load()

        self.current_year  = datetime.now().year
        self.current_month = datetime.now().month
        self.selected_date = None
        self._sel_btn_key  = None          # track which button is selected

        self._build_ui()
        self._render_calendar()

    # ──────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── top bar ───────────────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg=self.HEADER_BG, height=58)
        topbar.pack(fill=tk.X)
        topbar.pack_propagate(False)

        tk.Label(topbar, text="📅", font=("Segoe UI Emoji", 18),
                 bg=self.HEADER_BG, fg=self.TEXT_PRI).pack(side=tk.LEFT, padx=(18, 6), pady=12)
        tk.Label(topbar, text="Calendar & Reminders",
                 font=("Segoe UI", 15, "bold"),
                 bg=self.HEADER_BG, fg=self.TEXT_PRI).pack(side=tk.LEFT, pady=12)

        # nav buttons on right
        nav = tk.Frame(topbar, bg=self.HEADER_BG)
        nav.pack(side=tk.RIGHT, padx=16, pady=10)

        self._nav_btn(nav, "◀", self._prev_month).pack(side=tk.LEFT)
        self.month_label = tk.Label(nav, font=("Segoe UI", 13, "bold"),
                                    bg=self.HEADER_BG, fg=self.TEXT_PRI, width=18)
        self.month_label.pack(side=tk.LEFT, padx=8)
        self._nav_btn(nav, "▶", self._next_month).pack(side=tk.LEFT)
        self._pill_btn(nav, "Today", self._go_today,
                       bg=self.SUCCESS).pack(side=tk.LEFT, padx=(12, 0))

        # ── body ──────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=self.BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        # Calendar area
        cal_wrap = tk.Frame(body, bg=self.BG_CARD,
                            bd=0, relief=tk.FLAT, padx=2, pady=2)
        cal_wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_calendar_grid(cal_wrap)

        # Sidebar
        self._build_sidebar(body)

        # ── status bar ────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Select a date to view or add reminders")
        sb = tk.Label(self.root, textvariable=self.status_var,
                      font=("Segoe UI", 9), bg=self.HEADER_BG, fg=self.TEXT_MUT,
                      anchor=tk.W, padx=14, pady=4)
        sb.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_calendar_grid(self, parent):
        cal_frame = tk.Frame(parent, bg=self.BG_CARD)
        cal_frame.pack(fill=tk.BOTH, expand=True)

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d in enumerate(weekdays):
            fg = self.WEEKEND_FG if i >= 5 else self.DAY_HDR_FG
            tk.Label(cal_frame, text=d, font=("Segoe UI", 9, "bold"),
                     bg=self.DAY_HDR_BG, fg=fg, pady=7).grid(
                row=0, column=i, sticky="nsew", padx=1, pady=(0, 2))
            cal_frame.grid_columnconfigure(i, weight=1)

        self.day_buttons = {}
        for r in range(1, 7):
            cal_frame.grid_rowconfigure(r, weight=1)
            for c in range(7):
                btn = tk.Button(cal_frame, text="",
                                font=("Segoe UI", 11), relief=tk.FLAT,
                                bg=self.BG_PANEL, fg=self.TEXT_PRI,
                                activebackground=self.ACCENT,
                                activeforeground="white",
                                bd=0, cursor="hand2",
                                command=lambda rr=r, cc=c: self._on_click(rr, cc))
                btn.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                self.day_buttons[(r, c)] = btn

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=self.BG_SIDEBAR, width=270)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        sb.pack_propagate(False)

        # Date header
        hdr = tk.Frame(sb, bg=self.ACCENT, height=54)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        self.date_label = tk.Label(hdr, text="No date selected",
                                   font=("Segoe UI", 11, "bold"),
                                   bg=self.ACCENT, fg="white", wraplength=240)
        self.date_label.pack(expand=True, fill=tk.BOTH, padx=14, pady=10)

        # Reminder count badge
        count_row = tk.Frame(sb, bg=self.BG_SIDEBAR, pady=8)
        count_row.pack(fill=tk.X, padx=14)
        tk.Label(count_row, text="REMINDERS", font=("Segoe UI", 8, "bold"),
                 bg=self.BG_SIDEBAR, fg=self.TEXT_MUT).pack(side=tk.LEFT)
        self.count_badge = tk.Label(count_row, text="",
                                    font=("Segoe UI", 8, "bold"),
                                    bg=self.ACCENT, fg="white",
                                    padx=6, pady=1)
        self.count_badge.pack(side=tk.RIGHT)

        # Divider
        tk.Frame(sb, bg=self.BORDER, height=1).pack(fill=tk.X)

        # Listbox
        lf = tk.Frame(sb, bg=self.BG_SIDEBAR)
        lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        scrollbar = tk.Scrollbar(lf, bg=self.BG_SIDEBAR,
                                 troughcolor=self.BG_SIDEBAR,
                                 activebackground=self.ACCENT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.reminder_list = tk.Listbox(
            lf,
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set,
            bg=self.BG_CARD,
            fg=self.TEXT_PRI,
            selectbackground=self.ACCENT,
            selectforeground="white",
            activestyle="none",
            selectmode=tk.SINGLE,
            relief=tk.FLAT, bd=0,
            highlightthickness=0
        )
        self.reminder_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.reminder_list.yview)

        # Empty state label
        self.empty_label = tk.Label(lf, text="No reminders\nfor this date",
                                    font=("Segoe UI", 10),
                                    bg=self.BG_CARD, fg=self.TEXT_MUT,
                                    justify=tk.CENTER)

        # Action buttons
        tk.Frame(sb, bg=self.BORDER, height=1).pack(fill=tk.X)
        btn_area = tk.Frame(sb, bg=self.BG_SIDEBAR, pady=10)
        btn_area.pack(fill=tk.X, padx=10)

        self._action_btn(btn_area, "+ Add Reminder",
                         self._add, self.ACCENT).pack(fill=tk.X, pady=(0, 6))
        row2 = tk.Frame(btn_area, bg=self.BG_SIDEBAR)
        row2.pack(fill=tk.X)
        self._action_btn(row2, "✏  Edit",
                         self._edit, "#374151").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self._action_btn(row2, "🗑  Delete",
                         self._delete, self.DANGER).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ──────────────────────────────────────────────────────────────────────
    # Calendar rendering
    # ──────────────────────────────────────────────────────────────────────
    def _render_calendar(self):
        mn = calendar.month_name[self.current_month]
        self.month_label.config(text=f"{mn} {self.current_year}")

        cal = calendar.Calendar()
        weeks = cal.monthdayscalendar(self.current_year, self.current_month)
        today = date.today()

        # hide all buttons first
        for (r, c), btn in self.day_buttons.items():
            btn.config(text="", bg=self.BG_DARK, state=tk.DISABLED,
                       font=("Segoe UI", 11), fg=self.TEXT_PRI, relief=tk.FLAT)

        # hide unused row 6
        for c in range(7):
            self.day_buttons[(6, c)].grid_remove()

        rows_needed = len(weeks)
        for r in range(1, rows_needed + 1):
            for c in range(7):
                self.day_buttons[(r, c)].grid()

        for r_idx, week in enumerate(weeks, start=1):
            for c_idx, day in enumerate(week):
                if day == 0:
                    continue
                btn = self.day_buttons[(r_idx, c_idx)]
                dk = self._dkey(self.current_year, self.current_month, day)
                has = bool(self.reminders.get(dk))
                cnt = len(self.reminders.get(dk, []))

                is_today = (self.current_year == today.year and
                            self.current_month == today.month and
                            day == today.day)
                is_sel = (self.selected_date ==
                          (self.current_year, self.current_month, day))
                is_weekend = c_idx >= 5

                # pick style
                if is_sel:
                    bg, fg, weight = self.SEL_BG, self.SEL_FG, "bold"
                elif is_today:
                    bg, fg, weight = self.TODAY_BG, self.TODAY_FG, "bold"
                elif has:
                    bg, fg, weight = self.REMIND_BG, self.REMIND_FG, "bold"
                elif is_weekend:
                    bg, fg, weight = self.BG_PANEL, self.WEEKEND_FG, "normal"
                else:
                    bg, fg, weight = self.BG_PANEL, self.TEXT_PRI, "normal"

                label = str(day)
                if has and not is_today and not is_sel:
                    label = f"{day}  ·{cnt}"   # dot + count

                btn.config(text=label, state=tk.NORMAL,
                           bg=bg, fg=fg, font=("Segoe UI", 10, weight))

    def _on_click(self, row, col):
        btn = self.day_buttons[(row, col)]
        raw = btn.cget("text").split()[0]       # strip the "·N" badge
        if not raw:
            return
        day = int(raw)
        self.selected_date = (self.current_year, self.current_month, day)
        self._render_calendar()
        self._refresh_sidebar()

    def _refresh_sidebar(self):
        if not self.selected_date:
            return
        y, m, d = self.selected_date
        dk = self._dkey(y, m, d)
        items = self.reminders.get(dk, [])

        weekday = date(y, m, d).strftime("%A")
        mname   = calendar.month_name[m]
        self.date_label.config(text=f"{weekday}, {mname} {d}, {y}")

        cnt = len(items)
        if cnt:
            self.count_badge.config(text=str(cnt))
            self.count_badge.pack(side=tk.RIGHT)
        else:
            self.count_badge.pack_forget()

        self.reminder_list.delete(0, tk.END)
        if items:
            self.empty_label.place_forget()
            for item in items:
                self.reminder_list.insert(tk.END, f"  {item['time']}   {item['text']}")
        else:
            self.empty_label.place(relx=0.5, rely=0.4, anchor="center")

        self.status_var.set(
            f"{weekday}, {mname} {d}, {y}  —  "
            + (f"{cnt} reminder{'s' if cnt != 1 else ''}" if cnt else "no reminders"))

    # ──────────────────────────────────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────────────────────────────────
    def _add(self):
        if not self.selected_date:
            messagebox.showwarning("No date selected",
                                   "Please click a date on the calendar first.",
                                   parent=self.root)
            return
        dlg = ReminderDialog(self.root, "Add Reminder")
        self.root.wait_window(dlg)
        if dlg.result:
            t, txt = dlg.result
            dk = self._dkey(*self.selected_date)
            self.reminders.setdefault(dk, []).append({"time": t, "text": txt})
            self.reminders[dk].sort(key=lambda x: x["time"])
            self._save()
            self._render_calendar()
            self._refresh_sidebar()
            self.status_var.set("✓  Reminder added.")

    def _delete(self):
        sel = self.reminder_list.curselection()
        if not sel or not self.selected_date:
            return
        if not messagebox.askyesno("Delete reminder",
                                   "Delete this reminder?", parent=self.root):
            return
        dk = self._dkey(*self.selected_date)
        idx = sel[0]
        if dk in self.reminders and idx < len(self.reminders[dk]):
            self.reminders[dk].pop(idx)
            if not self.reminders[dk]:
                del self.reminders[dk]
            self._save()
            self._render_calendar()
            self._refresh_sidebar()
            self.status_var.set("Reminder deleted.")

    def _edit(self):
        sel = self.reminder_list.curselection()
        if not sel or not self.selected_date:
            return
        dk = self._dkey(*self.selected_date)
        idx = sel[0]
        if dk not in self.reminders or idx >= len(self.reminders[dk]):
            return
        old = self.reminders[dk][idx]
        dlg = ReminderDialog(self.root, "Edit Reminder",
                             time_val=old["time"], text_val=old["text"])
        self.root.wait_window(dlg)
        if dlg.result:
            t, txt = dlg.result
            self.reminders[dk][idx] = {"time": t, "text": txt}
            self.reminders[dk].sort(key=lambda x: x["time"])
            self._save()
            self._render_calendar()
            self._refresh_sidebar()
            self.status_var.set("✓  Reminder updated.")

    # ──────────────────────────────────────────────────────────────────────
    # Navigation
    # ──────────────────────────────────────────────────────────────────────
    def _prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self._render_calendar()

    def _next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self._render_calendar()

    def _go_today(self):
        self.current_year  = datetime.now().year
        self.current_month = datetime.now().month
        self._render_calendar()

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────
    def _dkey(self, y, m, d):
        return f"{y}-{m:02d}-{d:02d}"

    def _load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        with open(self.data_file, "w") as f:
            json.dump(self.reminders, f, indent=2)

    def _nav_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd,
                         font=("Segoe UI", 11), bg=self.HEADER_BG, fg=self.TEXT_SEC,
                         relief=tk.FLAT, padx=10, cursor="hand2",
                         activebackground=self.BG_PANEL, activeforeground=self.TEXT_PRI)

    def _pill_btn(self, parent, text, cmd, bg=None):
        bg = bg or self.ACCENT
        return tk.Button(parent, text=text, command=cmd,
                         font=("Segoe UI", 9, "bold"), bg=bg, fg="white",
                         relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
                         activebackground=self.ACCENT_LIGHT, activeforeground="white")

    def _action_btn(self, parent, text, cmd, bg):
        return tk.Button(parent, text=text, command=cmd,
                         font=("Segoe UI", 10), bg=bg, fg="white",
                         relief=tk.FLAT, padx=10, pady=8, cursor="hand2",
                         activebackground=self.ACCENT_LIGHT, activeforeground="white")


def main():
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.25)   # crisp on HiDPI
    except Exception:
        pass
    app = CalendarReminderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()