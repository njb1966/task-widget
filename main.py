import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib

import os
import sys
from datetime import date

import store
from task_row import TaskRow
from add_dialog import AddEditDialog


CSS_PATH = os.path.join(os.path.dirname(__file__), "style.css")


def load_css():
    provider = Gtk.CssProvider()
    provider.load_from_path(CSS_PATH)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def _sort_key(task):
    done = int(task["done"])
    due = task.get("due_date") or "9999-99-99"
    priority_order = {"high": 0, "medium": 1, "low": 2}
    pri = priority_order.get(task.get("priority", "medium"), 1)
    return (done, due, pri)


class TaskSidebarWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Tasks")
        self.set_default_size(340, 900)
        self.set_resizable(True)

        load_css()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.add_css_class("toolbar")
        toolbar.set_margin_start(4)
        toolbar.set_margin_end(4)

        title_lbl = Gtk.Label(label="Tasks")
        title_lbl.add_css_class("toolbar-title")
        title_lbl.set_hexpand(True)
        title_lbl.set_halign(Gtk.Align.START)
        toolbar.append(title_lbl)

        add_btn = Gtk.Button(label="+ Add")
        add_btn.add_css_class("add-button")
        add_btn.connect("clicked", self._on_add)
        toolbar.append(add_btn)

        root.append(toolbar)

        # Count label
        self.count_label = Gtk.Label(label="")
        self.count_label.add_css_class("count-label")
        self.count_label.set_halign(Gtk.Align.START)
        self.count_label.set_margin_start(10)
        root.append(self.count_label)

        # Scrolled task list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("task-list")
        self.list_box.set_show_separators(False)

        scroll.set_child(self.list_box)
        root.append(scroll)

        self.set_child(root)

        self._refresh()

        # Hourly re-check so highlights update without restart
        GLib.timeout_add_seconds(3600, self._hourly_refresh)

    def _refresh(self):
        # Remove all existing rows
        while True:
            child = self.list_box.get_first_child()
            if child is None:
                break
            self.list_box.remove(child)

        tasks = store.get_tasks()
        tasks.sort(key=_sort_key)

        active = sum(1 for t in tasks if not t["done"])
        total = len(tasks)
        self.count_label.set_text(f"{active} active / {total} total")

        for task in tasks:
            row = TaskRow(task)
            row.connect("done-toggled", self._on_done_toggled)
            row.connect("edit-requested", self._on_edit)
            row.connect("delete-requested", self._on_delete)
            self.list_box.append(row)

    def _hourly_refresh(self):
        store.auto_archive()
        self._refresh()
        return True  # keep timer running

    def _on_add(self, _btn):
        dialog = AddEditDialog(self)
        dialog.connect("response", self._on_add_response)
        dialog.present()

    def _on_add_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            title, due_date, priority, notes = dialog.get_values()
            if title:
                store.add_task(title, due_date, priority, notes)
                self._refresh()
        dialog.destroy()

    def _on_done_toggled(self, row, task_id, done):
        store.mark_done(task_id, done)
        store.auto_archive()
        self._refresh()

    def _on_edit(self, row, task_id):
        tasks = store.get_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        if not task:
            return
        dialog = AddEditDialog(self, task=task)
        dialog.connect("response", lambda d, r: self._on_edit_response(d, r, task_id))
        dialog.present()

    def _on_edit_response(self, dialog, response, task_id):
        if response == Gtk.ResponseType.OK:
            title, due_date, priority, notes = dialog.get_values()
            if title:
                store.update_task(task_id, title, due_date, priority, notes)
                self._refresh()
        dialog.destroy()

    def _on_delete(self, row, task_id):
        confirm = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Delete this task?",
        )
        confirm.connect("response", lambda d, r: self._on_delete_response(d, r, task_id))
        confirm.present()

    def _on_delete_response(self, dialog, response, task_id):
        if response == Gtk.ResponseType.OK:
            store.delete_task(task_id)
            self._refresh()
        dialog.destroy()


class TaskSidebarApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.njb1966.task-sidebar")

    def do_activate(self):
        store.init_db()
        store.auto_archive()
        win = TaskSidebarWindow(self)
        win.present()


def main():
    app = TaskSidebarApp()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
