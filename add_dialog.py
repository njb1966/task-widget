import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from datetime import date


class AddEditDialog(Gtk.Dialog):
    def __init__(self, parent, task=None):
        title = "Edit Task" if task else "Add Task"
        super().__init__(title=title, transient_for=parent, modal=True)
        self.set_default_size(340, 320)

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        ok_btn = self.add_button("Save", Gtk.ResponseType.OK)
        ok_btn.add_css_class("suggested-action")

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)

        # Title
        box.append(self._label("Title"))
        self.title_entry = Gtk.Entry()
        self.title_entry.set_placeholder_text("What needs to be done?")
        self.title_entry.set_hexpand(True)
        if task:
            self.title_entry.set_text(task.get("title", ""))
        box.append(self.title_entry)

        # Due date
        box.append(self._label("Due Date (YYYY-MM-DD, leave blank for none)"))
        self.due_entry = Gtk.Entry()
        self.due_entry.set_placeholder_text("e.g. 2026-06-01")
        if task and task.get("due_date"):
            self.due_entry.set_text(task["due_date"])
        box.append(self.due_entry)

        # Priority
        box.append(self._label("Priority"))
        self.priority_combo = Gtk.ComboBoxText()
        for p in ("high", "medium", "low"):
            self.priority_combo.append(p, p.capitalize())
        active = (task or {}).get("priority", "medium")
        self.priority_combo.set_active_id(active)
        box.append(self.priority_combo)

        # Notes
        box.append(self._label("Notes (optional)"))
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(70)
        scroll.set_vexpand(False)
        self.notes_view = Gtk.TextView()
        self.notes_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        if task and task.get("notes"):
            self.notes_view.get_buffer().set_text(task["notes"])
        scroll.set_child(self.notes_view)
        box.append(scroll)

        self.title_entry.connect("activate", lambda *_: self.response(Gtk.ResponseType.OK))

    def _label(self, text):
        lbl = Gtk.Label(label=text)
        lbl.set_halign(Gtk.Align.START)
        lbl.add_css_class("task-meta")
        return lbl

    def get_values(self):
        title = self.title_entry.get_text().strip()
        due_raw = self.due_entry.get_text().strip()
        due_date = None
        if due_raw:
            try:
                date.fromisoformat(due_raw)
                due_date = due_raw
            except ValueError:
                pass
        priority = self.priority_combo.get_active_id() or "medium"
        buf = self.notes_view.get_buffer()
        notes = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        return title, due_date, priority, notes
