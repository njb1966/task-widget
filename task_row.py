import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GObject
from datetime import date


def _due_status(due_date_str):
    if not due_date_str:
        return "none"
    try:
        due = date.fromisoformat(due_date_str)
    except ValueError:
        return "none"
    today = date.today()
    delta = (due - today).days
    if delta < 0:
        return "overdue"
    if delta == 0:
        return "due-today"
    if delta <= 3:
        return "due-soon"
    return "future"


class TaskRow(Gtk.ListBoxRow):
    __gsignals__ = {
        "done-toggled": (GObject.SignalFlags.RUN_FIRST, None, (int, bool)),
        "edit-requested": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "delete-requested": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self, task):
        super().__init__()
        self.task = task
        self.task_id = task["id"]
        self.add_css_class("task-row")
        self._build()
        self._apply_css_state()

    def _build(self):
        task = self.task
        done = bool(task["done"])

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.set_margin_top(4)
        outer.set_margin_bottom(4)

        # Checkbox
        self.check = Gtk.CheckButton()
        self.check.set_active(done)
        self.check.set_valign(Gtk.Align.CENTER)
        self.check.connect("toggled", self._on_toggled)
        outer.append(self.check)

        # Text column
        text_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_col.set_hexpand(True)

        title_cls = "task-title-done" if done else "task-title"
        self.title_label = Gtk.Label(label=task["title"])
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_wrap(True)
        self.title_label.set_xalign(0)
        self.title_label.add_css_class(title_cls)
        text_col.append(self.title_label)

        # Meta line: due date + priority
        meta_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        if task.get("due_date"):
            status = _due_status(task["due_date"])
            prefix = {
                "overdue": "⚠ OVERDUE: ",
                "due-today": "⚡ TODAY: ",
                "due-soon": "→ ",
                "future": "📅 ",
            }.get(status, "")
            meta_lbl = Gtk.Label(label=prefix + task["due_date"])
            meta_lbl.set_halign(Gtk.Align.START)
            meta_lbl.add_css_class("task-meta")
            meta_box.append(meta_lbl)

        pri = task.get("priority", "medium")
        pri_lbl = Gtk.Label(label=pri[0].upper())
        pri_lbl.add_css_class(f"priority-{pri}")
        pri_lbl.set_valign(Gtk.Align.CENTER)
        meta_box.append(pri_lbl)

        text_col.append(meta_box)
        outer.append(text_col)

        # ⋮ button with popover
        menu_btn = Gtk.Button(label="⋮")
        menu_btn.set_valign(Gtk.Align.CENTER)
        menu_btn.set_has_frame(False)
        menu_btn.connect("clicked", self._show_popover)
        outer.append(menu_btn)

        self._menu_btn = menu_btn
        self.set_child(outer)

    def _show_popover(self, btn):
        popover = Gtk.Popover()
        popover.set_parent(btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(8)
        box.set_margin_end(8)

        edit_btn = Gtk.Button(label="Edit")
        edit_btn.set_has_frame(False)
        edit_btn.connect("clicked", lambda *_: (popover.popdown(), self.emit("edit-requested", self.task_id)))
        box.append(edit_btn)

        del_btn = Gtk.Button(label="Delete")
        del_btn.set_has_frame(False)
        del_btn.add_css_class("destructive-action")
        del_btn.connect("clicked", lambda *_: (popover.popdown(), self.emit("delete-requested", self.task_id)))
        box.append(del_btn)

        popover.set_child(box)
        popover.popup()

    def _apply_css_state(self):
        for cls in ("overdue", "due-today", "due-soon", "done-row"):
            self.remove_css_class(cls)

        if self.task["done"]:
            self.add_css_class("done-row")
            return

        status = _due_status(self.task.get("due_date"))
        if status in ("overdue", "due-today", "due-soon"):
            self.add_css_class(status)

    def _on_toggled(self, check):
        self.emit("done-toggled", self.task_id, check.get_active())
