"""ClipVault application — main window orchestration and entry point."""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

import pyperclip
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QListWidgetItem,
    QDialog, QMessageBox, QFileDialog, QMenu, QSystemTrayIcon,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence, QAction

from clipvault.config import (
    APP_NAME, EntryType, CYBER_ORANGE, CYBER_NEON_GREEN,
    DATA_FILE, SALT_FILE,
)
from clipvault.models.entry import ClipboardEntry
from clipvault.storage.vault import StorageManager
from clipvault.storage.config_store import ConfigStore
from clipvault.capture.monitor import ClipboardMonitor
from clipvault.ui.main_window import init_ui, setup_tray, apply_font_size
from clipvault.ui.mini_panel import MiniTrayPanel
from clipvault.ui.command_palette import CommandPalette
from clipvault.ui.settings_dialog import SettingsDialog
from clipvault.ui.stats_dialog import StatsDialog
from clipvault.ui.pin_dialog import PinDialog
from clipvault.ui.entry_widget import add_entry_to_list, update_selection_styles
from clipvault.ui.tag_editor import TagEditorPopup, get_tag_color
from clipvault.ui.search_suggestions import SearchSuggestionPopup
from clipvault.ui.timeline_dialog import TimelineDialog
from clipvault.ui.theme import get_status_label_style, get_tooltip_style
from clipvault.hotkeys import GlobalHotkeyManager
from clipvault.paste_ring import PasteRing
from clipvault.utils import setup_logger, generate_id

_log = setup_logger("clipvault.app")


class ClipVaultMain(QMainWindow):
    """Main application window with all enhancements"""

    def __init__(self):
        super().__init__()
        self.entries: List[ClipboardEntry] = []
        self.storage = StorageManager()
        self.config_store = ConfigStore()
        self.config = self.config_store.load_config()
        self.boards = self.config_store.load_boards()
        self.current_filter = ""
        self.current_tab = "recent"
        self._last_deleted: Optional[ClipboardEntry] = None
        self._delete_undo_timer = None
        self._last_activity = datetime.now()
        self._locked = False
        self._force_quit = False
        self._tray_notified = False
        self._search_history = self.config_store.load_search_history()
        self._search_debounce = QTimer(self)
        self._search_debounce.setSingleShot(True)
        self._search_debounce.setInterval(500)
        self._search_debounce.timeout.connect(self._commit_search_history)

        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(30000)
        self._idle_timer.timeout.connect(self._check_idle)

        self._backup_timer = QTimer(self)
        self._backup_timer.setInterval(3600000)
        self._backup_timer.timeout.connect(self._check_backup)

        if not self.init_pin():
            sys.exit(0)

        self.entries = self.storage.load_entries()
        self.apply_retention_policy()

        self.monitor = ClipboardMonitor(self.config)
        self.monitor.new_entry.connect(self.add_clipboard_entry)
        self.monitor.new_image_entry.connect(self.add_image_entry)

        init_ui(self)
        self.apply_config()
        self.refresh_list()
        try:
            if hasattr(self, 'bg') and self.bg is not None:
                self.bg.set_entries(self.entries)
        except Exception:
            pass

        QApplication.instance().installEventFilter(self)

        setup_tray(self)

        self.mini_panel = MiniTrayPanel(self)
        self.mini_panel.copy_requested.connect(self.copy_entry)
        self.mini_panel.pin_requested.connect(self.toggle_pin_entry)
        self.mini_panel.delete_requested.connect(self.delete_entry)

        self.command_palette = CommandPalette()
        self.command_palette.action_triggered.connect(self.execute_command)

        self.hotkey_manager = GlobalHotkeyManager(self.config, {
            "command_palette": self.show_command_palette,
            "paste_ring": self._on_paste_ring,
            "quick_search": lambda: self.search_input.setFocus(),
            "toggle_pin": self.toggle_pin_selected,
            "pause_capture": lambda: self._toggle_pause(),
        })
        self.hotkey_manager.start()

        self.paste_ring = PasteRing(
            entries_provider=lambda: self.entries,
            timeout=self.config.get('paste_ring_timeout', 10),
            enabled=self.config.get('paste_ring_enabled', True),
        )

        self.monitor.start()

        if self.config.get('start_minimized', False):
            self.hide()
        else:
            self.show_with_animation()

    def init_pin(self) -> bool:
        """Initialize PIN protection using the stylized PinDialog."""
        dialog = PinDialog(parent=None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            old_pin, new_pin = dialog.get_pins()
            pin = new_pin if new_pin else old_pin
            if pin:
                return self.storage.set_pin(pin)
        return False

    def eventFilter(self, obj, event):
        try:
            if obj is self.centralWidget() and event.type() == QEvent.Type.Resize:
                if hasattr(self, 'bg') and self.bg is not None:
                    self.bg.setGeometry(self.centralWidget().rect())
        except Exception:
            pass
        if self.config.get('auto_lock', False) and not self._locked:
            et = event.type()
            if et in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress,
                      QEvent.Type.KeyPress, QEvent.Type.Wheel):
                self._record_activity()
        return super().eventFilter(obj, event)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts from config."""
        shortcuts = {
            "hotkey_quick_search": lambda: self.search_input.setFocus(),
            "hotkey_command_palette": self.show_command_palette,
            "hotkey_paste_ring": self._on_paste_ring,
            "hotkey_toggle_pin": self.toggle_pin_selected,
            "hotkey_pause_capture_key": lambda: self._toggle_pause(),
        }
        for config_key, handler in shortcuts.items():
            seq = self.config.get(config_key, "")
            if seq:
                try:
                    QShortcut(QKeySequence(seq), self).activated.connect(handler)
                except Exception:
                    pass
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self.copy_selected)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.delete_selected)
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.undo_delete)

    def tray_activated(self, reason):
        """Handle tray activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.mini_panel.set_entries(self.entries[:20])
            self.mini_panel.show_at_cursor()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def show_with_animation(self):
        """Show with fade animation"""
        self.setWindowOpacity(0)
        self.show()

        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_anim.start()

    def apply_config(self):
        """Apply configuration settings"""
        reduce_motion = self.config.get('reduce_motion', False)

        self.setStyleSheet(get_tooltip_style())

        if hasattr(self, 'bg'):
            if self.config.get('disable_bg', False):
                self.bg.set_intensity(0)
            else:
                self.bg.set_intensity(self.config.get('cyber_intensity', 0.3))
            if hasattr(self.bg, 'set_reduce_motion'):
                self.bg.set_reduce_motion(reduce_motion)

        for btn_attr in ('copy_btn', 'pin_btn', 'delete_btn'):
            btn = getattr(self, btn_attr, None)
            if btn and hasattr(btn, 'set_reduce_motion'):
                btn.set_reduce_motion(reduce_motion)

        if self.config.get('incognito_mode', False):
            self.status_label.setText("🥷 INCOGNITO")
            self.status_label.setStyleSheet(get_status_label_style(CYBER_NEON_GREEN))
        elif self.config.get('pause_capture', False):
            self.status_label.setText("● PAUSED")
            self.status_label.setStyleSheet(get_status_label_style(CYBER_ORANGE))
        else:
            self.status_label.setText("● MONITORING")
            self.status_label.setStyleSheet(get_status_label_style(CYBER_NEON_GREEN))

        if self.config.get('auto_lock', False):
            self._idle_timer.start()
        else:
            self._idle_timer.stop()

        if self.config.get('auto_backup', False):
            self._backup_timer.start()
        else:
            self._backup_timer.stop()

        apply_font_size(self, self.config.get('font_size', 12))

        self._update_status_bar()

    def apply_retention_policy(self):
        """Apply data retention policy"""
        if not self.config.get('enable_retention', False):
            return

        retention_days = self.config.get('retention_days', 30)
        max_entries = self.config.get('max_entries', 1000)

        cutoff = datetime.now() - timedelta(days=retention_days)
        self.entries = [e for e in self.entries
                       if e.timestamp > cutoff or e.pinned]

        if len(self.entries) > max_entries:
            pinned = [e for e in self.entries if e.pinned]
            unpinned = [e for e in self.entries if not e.pinned]
            unpinned.sort(key=lambda e: e.timestamp, reverse=True)
            self.entries = pinned + unpinned[:max_entries - len(pinned)]

    def _get_selected_entry(self) -> Optional[ClipboardEntry]:
        """Return the currently selected entry from the active tab, or None."""
        current_list = self.tabs.currentWidget()
        for lst in (self.recent_list, self.pinned_list, self.all_list, self.tagged_list):
            if lst is current_list:
                items = lst.selectedItems()
                if items:
                    return items[0].data(Qt.ItemDataRole.UserRole)
                break
        return None

    def _get_selected_entries(self) -> list:
        """Return all selected entries from the active tab."""
        current_list = self.tabs.currentWidget()
        for lst in (self.recent_list, self.pinned_list, self.all_list, self.tagged_list):
            if lst is current_list:
                return [item.data(Qt.ItemDataRole.UserRole)
                        for item in lst.selectedItems()]
        return []

    def bulk_delete(self, entries: list):
        if not entries:
            return
        if self.config.get('confirm_delete', True):
            reply = QMessageBox.question(
                self, "Delete Entries",
                f"Delete {len(entries)} selected entries?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        ids = {e.id for e in entries}
        self.entries = [e for e in self.entries if e.id not in ids]
        self.save_entries()
        self.refresh_list()

    def bulk_pin(self, entries: list):
        if not entries:
            return
        majority_pinned = sum(1 for e in entries if e.pinned) > len(entries) // 2
        for e in entries:
            e.pinned = not majority_pinned
        self.save_entries()
        self.refresh_list()

    def bulk_copy(self, entries: list):
        if not entries:
            return
        texts = [e.text for e in entries if not e.image_data]
        if texts:
            pyperclip.copy("\n\n".join(texts))

    def bulk_export(self, entries: list):
        if not entries:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Selected", "clipvault_export.json", "JSON Files (*.json)")
        if file_path:
            import json
            data = [e.to_dict() for e in entries]
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            QMessageBox.information(self, "Exported", f"Exported {len(entries)} entries.")

    def _update_status_bar(self):
        """Update the bottom status bar with entry count and last capture time."""
        count_label = getattr(self, 'status_entry_count', None)
        if count_label:
            count_label.setText(f"{len(self.entries)} entries")
        last_label = getattr(self, 'status_last_capture', None)
        if last_label and self.entries:
            from clipvault.ui.entry_widget import _relative_time
            last_label.setText(f"Last: {_relative_time(self.entries[0].timestamp)}")
        elif last_label:
            last_label.setText("")

    def _update_tab_labels(self):
        """Update tab labels with entry counts."""
        filtered = self.entries
        if self.current_filter:
            qry = self.current_filter.lower()
            filtered = [e for e in self.entries
                       if qry in e.text.lower()
                       or (e.ocr_text and qry in e.ocr_text.lower())]
        pinned = [e for e in filtered if e.pinned]
        unpinned = [e for e in filtered if not e.pinned]
        if hasattr(self, 'tabs'):
            self.tabs.setTabText(0, f"RECENT ({len(unpinned[:50])})")
            self.tabs.setTabText(1, f"PINNED ({len(pinned)})")
            self.tabs.setTabText(2, f"ALL ({len(filtered[:100])})")
            tagged_count = len([e for e in filtered if e.tags])
            self.tabs.setTabText(3, f"🏷 TAGS ({tagged_count})")

    def filter_entries(self, text: str):
        """Handle search/filter input from the UI."""
        try:
            qry = text if isinstance(text, str) else str(text or '')
        except Exception:
            qry = ''

        self.current_filter = qry.strip()
        self.refresh_list()

        if self.config.get('enable_search_history', True) and self.current_filter:
            self._search_debounce.start()

    def _commit_search_history(self):
        """Add current search query to history (debounced)."""
        qry = self.current_filter
        if not qry or len(qry) < 2:
            return
        if qry in self._search_history:
            self._search_history.remove(qry)
        self._search_history.insert(0, qry)
        self._search_history = self._search_history[:50]
        self.config_store.save_search_history(self._search_history)

    def _show_search_suggestions(self):
        """Show the search suggestion popup below the search input."""
        if not self.config.get('enable_search_history', True):
            return
        if not hasattr(self, '_suggestion_popup'):
            self._suggestion_popup = SearchSuggestionPopup(self)
            self._suggestion_popup.query_selected.connect(self._apply_suggestion)
        self._suggestion_popup.set_queries(self._search_history, self.current_filter)
        if self._search_history:
            self._suggestion_popup.show_below(self.search_input)

    def _apply_suggestion(self, query: str):
        self.search_input.setText(query)
        self.filter_entries(query)

    def on_tab_changed(self, index: int):
        """Handle left panel tab changes."""
        mapping = {0: 'recent', 1: 'pinned', 2: 'all'}
        self.current_tab = mapping.get(index, 'recent')
        for name in ('recent_list', 'pinned_list', 'all_list'):
            lst = getattr(self, name, None)
            if lst is not None:
                try:
                    lst.clearSelection()
                except Exception:
                    pass
        self.refresh_list()
        for attr in ('detail_text', 'copy_btn', 'pin_btn', 'delete_btn'):
            w = getattr(self, attr, None)
            if w is not None:
                if attr == 'detail_text':
                    w.clear()
                else:
                    w.setEnabled(False)

    def _record_activity(self):
        self._last_activity = datetime.now()

    def _check_idle(self):
        if self._locked:
            return
        lock_minutes = self.config.get('lock_time', 10)
        idle_delta = datetime.now() - self._last_activity
        if idle_delta >= timedelta(minutes=lock_minutes):
            self._lock_vault()

    def _lock_vault(self):
        self._locked = True
        self.monitor.stop()
        self.monitor.wait(2000)
        self.entries = []
        self.refresh_list()
        if hasattr(self, 'tray_icon') and self.tray_icon is not None:
            self.tray_icon.showMessage(
                APP_NAME, "Vault locked due to inactivity",
                QSystemTrayIcon.MessageIcon.Information, 3000,
            )
        dlg = PinDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            old_pin, new_pin = dlg.get_pins()
            pin = new_pin if new_pin else old_pin
            if pin and self.storage.set_pin(pin):
                self.entries = self.storage.load_entries()
                self.apply_retention_policy()
                self.refresh_list()
                self._locked = False
                self._record_activity()
                self.monitor.start()
            else:
                QMessageBox.warning(self, "Lock Failed", "Failed to unlock. Application will close.")
                self.close()
        else:
            self.close()

    def _check_backup(self):
        if self._locked:
            return
        last_backup = self.config.get('last_backup')
        if last_backup:
            try:
                last_dt = datetime.fromisoformat(last_backup)
            except (ValueError, TypeError):
                last_dt = None
        else:
            last_dt = None

        if last_dt and datetime.now() - last_dt < timedelta(hours=24):
            return

        backup_path = self.config.get('backup_path', '')
        if not backup_path:
            return
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            try:
                backup_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                _log.error("Backup dir creation failed: %s", e)
                return

        try:
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            if DATA_FILE.exists():
                shutil.copy2(DATA_FILE, backup_dir / f"vault_backup_{date_str}.encrypted")
            if SALT_FILE.exists():
                shutil.copy2(SALT_FILE, backup_dir / f"salt_backup_{date_str}")
            self.config['last_backup'] = datetime.now().isoformat()
            self.config_store.save_config(self.config)
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                self.tray_icon.showMessage(
                    APP_NAME, f"Backup created in {backup_path}",
                    QSystemTrayIcon.MessageIcon.Information, 2000,
                )
            _log.info("Backup completed to %s", backup_path)
        except Exception as e:
            _log.error("Backup failed: %s", e)

    def add_clipboard_entry(self, text: str):
        """Add new entry with deduplication"""
        self._record_activity()
        for entry in self.entries:
            if entry.text == text:
                entry.duplicate_count += 1
                entry.last_used = datetime.now()
                self.save_entries()
                return

        if self.config.get('smart_dedupe', True):
            for entry in self.entries:
                if entry.is_similar_to(ClipboardEntry(text)):
                    entry.duplicate_count += 1
                    entry.last_used = datetime.now()
                    self.save_entries()
                    return

        new_entry = ClipboardEntry(text)

        if new_entry.entry_type == EntryType.SENSITIVE:
            if self.config.get('ephemeral_otp', True):
                new_entry.ephemeral_ttl = 300

        self.entries.insert(0, new_entry)
        self.apply_retention_policy()
        self.save_entries()
        self.refresh_list()
        try:
            if hasattr(self, 'bg') and self.bg is not None:
                self.bg.set_entries(self.entries)
        except Exception:
            pass

        if self.mini_panel.isVisible():
            self.mini_panel.set_entries(self.entries[:20])

    def add_image_entry(self, placeholder: str, image_b64: str):
        """Add new image entry with deduplication."""
        self._record_activity()
        for entry in self.entries:
            if entry.image_data and entry.image_data == image_b64:
                entry.duplicate_count += 1
                entry.last_used = datetime.now()
                self.save_entries()
                return

        new_entry = ClipboardEntry(
            text=placeholder,
            entry_type=EntryType.IMAGE,
            image_data=image_b64,
        )

        self.entries.insert(0, new_entry)
        self.apply_retention_policy()
        self.save_entries()
        self.refresh_list()
        try:
            if hasattr(self, 'bg') and self.bg is not None:
                self.bg.set_entries(self.entries)
        except Exception:
            pass

        if self.mini_panel.isVisible():
            self.mini_panel.set_entries(self.entries[:20])

        if self.config.get('enable_ocr', False):
            self._run_ocr(new_entry)

    def _run_ocr(self, entry: ClipboardEntry):
        """Run OCR on an image entry asynchronously."""
        try:
            from clipvault.ocr import extract_text, is_available
            if not is_available():
                return
            from PyQt6.QtCore import QThread, pyqtSignal

            class OCRWorker(QThread):
                done = pyqtSignal(str, str)

                def __init__(self, image_b64):
                    super().__init__()
                    self._image_b64 = image_b64

                def run(self):
                    text = extract_text(self._image_b64)
                    if text:
                        self.done.emit(entry.id, text)

            worker = OCRWorker(entry.image_data)
            worker.done.connect(self._on_ocr_done)
            worker.start()
            self._ocr_worker = worker
        except Exception as e:
            _log.debug("OCR run failed: %s", e)

    def _on_ocr_done(self, entry_id: str, ocr_text: str):
        """Handle OCR completion by updating the entry and refreshing."""
        for e in self.entries:
            if e.id == entry_id:
                e.ocr_text = ocr_text
                self.save_entries()
                self.refresh_list()
                break

    def refresh_list(self):
        """Refresh all entry lists"""
        tabs = getattr(self, 'tabs', None)
        current_widget = tabs.currentWidget() if tabs is not None else None

        for name in ('recent_list', 'pinned_list', 'all_list', 'tagged_list'):
            lst = getattr(self, name, None)
            if lst is not None:
                try:
                    lst.clear()
                except Exception:
                    pass

        filtered = self.entries
        if self.current_filter:
            qry = self.current_filter.lower()
            filtered = [e for e in self.entries
                       if qry in e.text.lower()
                       or (e.ocr_text and qry in e.ocr_text.lower())
                       or (e.entry_type == EntryType.IMAGE and qry in 'image')]

        pinned = [e for e in filtered if e.pinned]
        unpinned = [e for e in filtered if not e.pinned]

        recent_widget = getattr(self, 'recent_list', None)
        pinned_widget = getattr(self, 'pinned_list', None)
        all_widget = getattr(self, 'all_list', None)

        if recent_widget is not None:
            for entry in unpinned[:50]:
                add_entry_to_list(recent_widget, entry, self.config, self)

        if pinned_widget is not None:
            for entry in pinned:
                add_entry_to_list(pinned_widget, entry, self.config, self)

        if all_widget is not None:
            for entry in filtered[:100]:
                add_entry_to_list(all_widget, entry, self.config, self)

        tagged_widget = getattr(self, 'tagged_list', None)
        if tagged_widget is not None:
            tagged = [e for e in filtered if e.tags]
            for entry in tagged[:100]:
                add_entry_to_list(tagged_widget, entry, self.config, self)

        self._update_tab_labels()
        self._update_status_bar()

    def on_selection_changed(self):
        """Update detail pane when selection changes"""
        selected = self._get_selected_entry()

        if selected:
            if selected.image_data:
                detail = "[Image entry — use copy to paste the image]"
                if selected.ocr_text:
                    detail += f"\n\nOCR Text:\n{selected.ocr_text}"
                self.detail_text.setPlainText(detail)
            else:
                self.detail_text.setPlainText(selected.text)
            self.copy_btn.setEnabled(True)
            self.pin_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.pin_btn.setText("📌 UNPIN" if selected.pinned else "📌 PIN")

            meta_type = getattr(self, 'meta_type_label', None)
            if meta_type:
                meta_type.setText(f"Type: {selected.entry_type}")
            meta_time = getattr(self, 'meta_time_label', None)
            if meta_time:
                from clipvault.ui.entry_widget import _relative_time
                meta_time.setText(f"Copied: {_relative_time(selected.timestamp)}")
            meta_count = getattr(self, 'meta_count_label', None)
            if meta_count:
                meta_count.setText(f"×{selected.duplicate_count}" if selected.duplicate_count > 1 else "")
        else:
            self.detail_text.clear()
            self.copy_btn.setEnabled(False)
            self.pin_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            for attr in ('meta_type_label', 'meta_time_label', 'meta_count_label'):
                lbl = getattr(self, attr, None)
                if lbl:
                    lbl.setText("")

        update_selection_styles(self)

    def show_tag_editor(self, entry: ClipboardEntry, btn=None):
        all_tags = sorted(set(t for e in self.entries for t in e.tags))
        popup = TagEditorPopup(entry, all_tags, parent=self)
        popup.tags_changed.connect(self._on_tags_changed)
        if btn is not None:
            pos = btn.mapToGlobal(btn.rect().bottomLeft())
            popup.move(pos)
        popup.show()

    def _on_tags_changed(self, entry_id: str, tags: list):
        self.save_entries()
        self.refresh_list()

    def show_context_menu(self, pos):
        sender = self.sender()
        if not isinstance(sender, QListWidget):
            return
        selected_items = sender.selectedItems()
        if not selected_items:
            return

        if len(selected_items) > 1:
            entries = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
            menu = QMenu()
            copy_action = QAction(f"Copy {len(entries)} entries")
            copy_action.triggered.connect(lambda: self.bulk_copy(entries))
            menu.addAction(copy_action)

            pin_action = QAction(f"Pin/Unpin {len(entries)} entries")
            pin_action.triggered.connect(lambda: self.bulk_pin(entries))
            menu.addAction(pin_action)

            delete_action = QAction(f"Delete {len(entries)} entries")
            delete_action.triggered.connect(lambda: self.bulk_delete(entries))
            menu.addAction(delete_action)

            export_action = QAction(f"Export {len(entries)} entries")
            export_action.triggered.connect(lambda: self.bulk_export(entries))
            menu.addAction(export_action)

            menu.exec(sender.mapToGlobal(pos))
            return

        item = sender.itemAt(pos)
        if not item:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu()
        copy_action = QAction("Copy")
        copy_action.triggered.connect(lambda: self.copy_entry(entry))
        menu.addAction(copy_action)

        pin_action = QAction("Unpin" if entry.pinned else "Pin")
        pin_action.triggered.connect(lambda: self.toggle_pin_entry(entry))
        menu.addAction(pin_action)

        delete_action = QAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_entry(entry))
        menu.addAction(delete_action)

        menu.exec(sender.mapToGlobal(pos))

    def copy_selected(self):
        """Copy currently selected entry to clipboard"""
        selected = self._get_selected_entry()
        if not selected:
            return
        self.copy_entry(selected)

    def toggle_pin_selected(self):
        selected = self._get_selected_entry()
        if not selected:
            return
        self.toggle_pin_entry(selected)

    def delete_selected(self):
        selected = self._get_selected_entry()
        if not selected:
            return
        self.delete_entry(selected)

    def copy_entry(self, entry: ClipboardEntry):
        try:
            if entry.image_data:
                from PyQt6.QtGui import QImage, QPixmap
                from PyQt6.QtCore import QByteArray
                from PyQt6.QtWidgets import QApplication
                img_bytes = QByteArray.fromBase64(entry.image_data.encode("ascii"))
                img = QImage()
                img.loadFromData(img_bytes, "PNG")
                if img.isNull():
                    QMessageBox.warning(self, "Error", "Failed to reconstruct image.")
                    return
                clip = QApplication.clipboard()
                clip.setImage(img)
            else:
                pyperclip.copy(entry.text)
            entry.last_used = datetime.now()
            self.save_entries()
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                self.tray_icon.showMessage(
                    APP_NAME, "Copied to clipboard",
                    QSystemTrayIcon.MessageIcon.Information, 1500,
                )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to copy: {e}")

    def toggle_pin_entry(self, entry: ClipboardEntry):
        entry.pinned = not entry.pinned
        self.save_entries()
        self.refresh_list()

    def delete_entry(self, entry: ClipboardEntry):
        """Delete an entry. If config has confirm_delete enabled, ask first.

        Stores the deleted entry for 30 s so the user can undo via
        ``undo_delete``.
        """
        confirm = self.config.get('confirm_delete', True)
        if confirm:
            reply = QMessageBox.question(
                self, "Delete", "Delete this entry?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        try:
            self._last_deleted = entry
            self.entries = [e for e in self.entries if e.id != entry.id]
            self.save_entries()
            self.refresh_list()
            try:
                if hasattr(self, 'bg') and self.bg is not None:
                    self.bg.set_entries(self.entries)
            except Exception:
                pass
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                self.tray_icon.showMessage(
                    APP_NAME, "Entry deleted (Ctrl+Z to undo)",
                    QSystemTrayIcon.MessageIcon.Information, 3000,
                )
            if hasattr(self, 'status_last_capture'):
                self.status_last_capture.setText("Entry deleted — Ctrl+Z to undo")
            if self._delete_undo_timer is not None:
                self._delete_undo_timer.stop()
            self._delete_undo_timer = QTimer.singleShot(30000, self._clear_deleted)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete: {e}")

    def _clear_deleted(self):
        """Clear the last-deleted entry after the undo window expires."""
        self._last_deleted = None
        self._delete_undo_timer = None
        if hasattr(self, 'status_last_capture'):
            self._update_status_bar()

    def undo_delete(self):
        """Restore the most recently deleted entry (within 30 s)."""
        if self._last_deleted is None:
            return
        self.entries.insert(0, self._last_deleted)
        self._last_deleted = None
        self.save_entries()
        self.refresh_list()
        try:
            if hasattr(self, 'bg') and self.bg is not None:
                self.bg.set_entries(self.entries)
        except Exception:
            pass
        if hasattr(self, 'tray_icon') and self.tray_icon is not None:
            self.tray_icon.showMessage(
                APP_NAME, "Entry restored",
                QSystemTrayIcon.MessageIcon.Information, 1500,
            )

    def save_entries(self):
        if self.config.get('incognito_mode', False):
            return
        self.storage.save_entries(self.entries)

    def export_all(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Entries", "clipvault_export.json", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
            QMessageBox.information(self, "Exported", "Entries exported successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {e}")

    def import_entries(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Entries", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            imported = [ClipboardEntry.from_dict(d) for d in data]
            existing_ids = {e.id for e in self.entries}
            for e in imported:
                if e.id in existing_ids:
                    e.id = generate_id(e.text, e.timestamp)
                self.entries.insert(0, e)
            self.save_entries()
            self.refresh_list()
            try:
                if hasattr(self, 'bg') and self.bg is not None:
                    self.bg.set_entries(self.entries)
            except Exception:
                pass
            QMessageBox.information(self, "Imported", f"Imported {len(imported)} entries.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Import failed: {e}")

    def show_settings(self):
        dialog = SettingsDialog(self.config, self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()

    def on_settings_changed(self, new_config: dict):
        was_incognito = self.config.get('incognito_mode', False)
        self.config.update(new_config)
        self.config_store.save_config(self.config)
        now_incognito = self.config.get('incognito_mode', False)
        if was_incognito and not now_incognito:
            self.save_entries()
        self.apply_config()
        self.hotkey_manager.update_hotkeys(self.config)
        if hasattr(self, 'paste_ring'):
            self.paste_ring.set_timeout(self.config.get('paste_ring_timeout', 10))
            self.paste_ring.set_enabled(self.config.get('paste_ring_enabled', True))

    def show_stats(self):
        dialog = StatsDialog(self.entries, self)
        dialog.exec()

    def show_timeline(self):
        dialog = TimelineDialog(self.entries, self)
        dialog.exec()

    def _toggle_pause(self):
        self.config['pause_capture'] = not self.config.get('pause_capture', False)
        self.apply_config()

    def _on_paste_ring(self):
        if hasattr(self, 'paste_ring'):
            entry = self.paste_ring.next()
            if entry:
                self.copy_entry(entry)

    def show_command_palette(self):
        """Open the command palette overlay."""
        self.command_palette.set_data(self.entries)
        self.command_palette.show_centered()

    def execute_command(self, action: str, data: object):
        if action == 'copy' and isinstance(data, ClipboardEntry):
            self.copy_entry(data)
        elif action == 'settings':
            self.show_settings()
        elif action == 'clear':
            self.entries = []
            self.save_entries()
            self.refresh_list()
        elif action == 'export':
            self.export_all()
        elif action == 'import':
            self.import_entries()
        elif action == 'stats':
            self.show_stats()
        elif action == 'timeline':
            self.show_timeline()
        elif action == 'pause':
            self.config['pause_capture'] = not self.config.get('pause_capture', False)
            self.apply_config()
        elif action == 'pin_mode':
            self.toggle_pin_selected()

    def closeEvent(self, event):
        """Hide to system tray on close unless _force_quit is set."""
        if not self._force_quit:
            event.ignore()
            self.hide()
            if not self._tray_notified and hasattr(self, 'tray_icon') and self.tray_icon is not None:
                self.tray_icon.showMessage(
                    APP_NAME, "ClipVault is still running in the system tray",
                    QSystemTrayIcon.MessageIcon.Information, 3000,
                )
                self._tray_notified = True
            return

        # Force quit — stop everything
        try:
            self._idle_timer.stop()
            self._backup_timer.stop()
        except Exception:
            pass
        try:
            self.hotkey_manager.stop()
        except Exception:
            pass
        try:
            self.monitor.stop()
            self.monitor.wait(2000)
        except Exception:
            pass
        try:
            if hasattr(self, 'bg') and self.bg is not None:
                if hasattr(self.bg, 'timer'):
                    self.bg.timer.stop()
        except Exception:
            pass
        super().closeEvent(event)


def main() -> int:
    """Application entry point."""
    app = QApplication(sys.argv)
    QApplication.setApplicationName(APP_NAME)

    try:
        main_window = ClipVaultMain()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            from pathlib import Path
            crash_log = Path.home() / ".clipvault" / "crash.log"
            crash_log.parent.mkdir(parents=True, exist_ok=True)
            crash_log.write_text(tb, encoding="utf-8")
        except Exception:
            pass
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, APP_NAME + " — Startup Error",
                             f"ClipVault failed to start:\n\n{tb}\n\n"
                             f"Crash log written to ~/.clipvault/crash.log")
        return 1

    return app.exec()
