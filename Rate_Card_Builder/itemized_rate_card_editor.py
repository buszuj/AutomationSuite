"""
Itemized Rate Card Editor - Embedded Version
UI components for creating and editing itemized rate cards, embedded in the main window tab.
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext, simpledialog, filedialog
import tkinter as tk
import tkinter.ttk as ttk
import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
import sys
from language_loader import get_language_manager

# Try to import Excel rate card loader
try:
    from excel_rate_card_loader import load_excel_rate_card
except ImportError:
    load_excel_rate_card = None


class ItemizedRateCardEditor:
    """Embedded editor for creating and editing itemized rate cards."""
    
    # Default services
    DEFAULT_SERVICES = [
        "Translation",
        "TM - Fuzzy Match Low",
        "TM - Fuzzy Match Medium",
        "TM - Fuzzy Match High",
        "TM - Exact Match"
    ]
    
    def __init__(self, parent_frame, root):
        """
        Initialize the itemized rate card editor.
        
        Args:
            parent_frame: The tab frame to embed into
            root: The root window
        """
        self.parent_frame = parent_frame
        self.root = root
        self.language_manager = get_language_manager()
        self.languages_data = {}  # {language_name: {iso_code, rates_dict}}
        self.missing_languages = []  # Languages not found in ISO database
        self.local_iso_codes = {}  # Per-rate-card ISO snapshot: {language_name: iso_code}
        self.current_edit_entry = None  # Track active inline edit Entry
        self.current_edit_item = None  # Track active item being edited
        self.current_edit_col = None  # Track active column being edited
        self.table_menu = None
        self.column_menu = None
        self.context_item = None
        self.context_col_index = None
        self.context_column_name = None
        self.base_service_columns = list(self.DEFAULT_SERVICES)
        self.column_visibility_vars = {}
        self.column_widths = {}
        self.hidden_service_columns = set()
        self.language_filter_names = None
        self.language_filter_active = False
        self.language_filter_status_label = None
        self.undo_stack = []  # Store previous states for undo functionality
        self.max_undo_steps = 10  # Maximum number of undo steps to keep
        
        self.DEFAULT_SERVICES = self._load_global_services()
        self.setup_ui()

    def _save_state_for_undo(self):
        """Save the current state for potential undo."""
        import copy
        state = {
            'languages_data': copy.deepcopy(self.languages_data),
            'DEFAULT_SERVICES': list(self.DEFAULT_SERVICES),
            'hidden_service_columns': set(self.hidden_service_columns)
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)

    def _restore_state_from_undo(self):
        """Restore the most recent saved state."""
        if not self.undo_stack:
            messagebox.showinfo("No Undo Available", "There are no recent changes to undo.")
            return
        
        state = self.undo_stack.pop()
        self.languages_data = state['languages_data']
        self.DEFAULT_SERVICES = state['DEFAULT_SERVICES']
        self.hidden_service_columns = state['hidden_service_columns']
        
        self._refresh_tree_structure()
        self.update_table()
        self.edit_status_label.configure(text="✓ Undid last change")

    def _service_columns_config_path(self):
        """Return the path used to persist the global service column list."""
        return Path(__file__).parent / "service_columns.json"

    def _load_global_services(self):
        """Load the shared service column list used for new and future rate cards."""
        config_path = self._service_columns_config_path()
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as file_handle:
                    data = json.load(file_handle)

                services = data.get("services", [])
                if isinstance(services, list) and services:
                    cleaned_services = []
                    for service in services:
                        service_name = str(service).strip()
                        if service_name and service_name not in cleaned_services:
                            cleaned_services.append(service_name)
                    if cleaned_services:
                        return cleaned_services
            except Exception:
                pass

        return list(self.base_service_columns)

    def _save_global_services(self):
        """Persist the shared service column list for future rate cards."""
        config_path = self._service_columns_config_path()
        try:
            with open(config_path, 'w', encoding='utf-8') as file_handle:
                json.dump({"services": self.DEFAULT_SERVICES}, file_handle, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _append_current_services_to_global_list(self):
        """Append any new service names from the current card to the shared service registry."""
        global_services = self._load_global_services()
        added_services = []

        for service_name in self.DEFAULT_SERVICES:
            if service_name not in global_services:
                global_services.append(service_name)
                added_services.append(service_name)

        if added_services:
            with open(self._service_columns_config_path(), 'w', encoding='utf-8') as file_handle:
                json.dump({"services": global_services}, file_handle, indent=2, ensure_ascii=False)

        return added_services

    def _merge_service_names(self, *service_groups):
        """Merge multiple service-name lists while preserving order and removing duplicates."""
        merged_services = []
        for group in service_groups:
            if not group:
                continue
            for service_name in group:
                cleaned_name = str(service_name).strip()
                if cleaned_name and cleaned_name not in merged_services:
                    merged_services.append(cleaned_name)
        return merged_services

    def _extract_services_from_loaded_card(self, data):
        """Collect service names from a saved card's services list and rate dictionaries."""
        discovered_services = []

        loaded_services = data.get("services", [])
        if isinstance(loaded_services, list):
            discovered_services.extend(loaded_services)

        for lang_info in data.get("languages", {}).values():
            rates = lang_info.get("rates", {})
            if isinstance(rates, dict):
                discovered_services.extend(rates.keys())

        return discovered_services

    def _prompt_iso_update_scope(self, title, message):
        """Prompt the user to choose local, global, or both updates for an ISO change."""
        result = {"choice": None}

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        message_label = ctk.CTkLabel(
            container,
            text=message,
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=360
        )
        message_label.pack(anchor="w", pady=(0, 12))

        def choose(choice):
            result["choice"] = choice
            dialog.destroy()

        button_row = ctk.CTkFrame(container, fg_color="transparent")
        button_row.pack(fill="x")

        local_button = ctk.CTkButton(button_row, text="Local Only", command=lambda: choose("local"))
        local_button.pack(side="left", padx=(0, 8))

        global_button = ctk.CTkButton(button_row, text="Global Only", command=lambda: choose("global"))
        global_button.pack(side="left", padx=(0, 8))

        both_button = ctk.CTkButton(button_row, text="Both", command=lambda: choose("both"))
        both_button.pack(side="left")

        dialog.protocol("WM_DELETE_WINDOW", lambda: choose(None))
        self.root.wait_window(dialog)
        return result["choice"]

    def _get_local_iso_code(self, language_name):
        """Get the per-card ISO code for a language if present."""
        return self.local_iso_codes.get(language_name, "")

    def _set_local_iso_code(self, language_name, iso_code):
        """Set or remove a per-card ISO code entry without touching the global list."""
        cleaned_code = str(iso_code).strip()
        if cleaned_code:
            self.local_iso_codes[language_name] = cleaned_code
        else:
            self.local_iso_codes.pop(language_name, None)

    def _rename_local_iso_code_key(self, old_language_name, new_language_name):
        """Rename a local ISO snapshot key if one exists for the old language name."""
        if old_language_name in self.local_iso_codes:
            self.local_iso_codes[new_language_name] = self.local_iso_codes.pop(old_language_name)

    def _build_local_iso_codes_snapshot(self):
        """Build the ISO snapshot to save with the current rate card."""
        snapshot = dict(self.local_iso_codes)
        for lang_name, lang_info in self.languages_data.items():
            iso_code = str(lang_info.get("iso_code", "")).strip()
            if iso_code:
                snapshot[lang_name] = iso_code
        return snapshot

    def _split_display_language_name(self, display_name):
        """Split a display name into language and country parts when possible."""
        cleaned_name = str(display_name).strip()
        match = re.match(r'^(.*?)\s*\((.*?)\)\s*$', cleaned_name)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return cleaned_name, ""

    def _split_pasted_language_lines(self, text):
        """Split pasted text into candidate language lines while preserving comma-separated country lists."""
        lines = []
        normalized_text = text.replace('\t', ' ')
        for raw_line in re.split(r'[\r\n]+', normalized_text):
            cleaned_line = raw_line.strip()
            if not cleaned_line:
                continue

            parts = [part.strip() for part in cleaned_line.split(';') if part.strip()]
            if parts:
                lines.extend(parts)
            else:
                lines.append(cleaned_line)

        return lines

    def _split_language_country_entry(self, entry):
        """Split a single pasted line into a base language and one or more country descriptors."""
        cleaned_entry = entry.strip()
        if not cleaned_entry:
            return []

        separator_match = re.search(r'\s+[-–—]\s+', cleaned_entry)
        if separator_match:
            language_name = cleaned_entry[:separator_match.start()].strip()
            remainder = cleaned_entry[separator_match.end():].strip()
        else:
            language_name = cleaned_entry
            remainder = ""

        if not remainder:
            return [(language_name, None)]

        variants = []
        variant_chunks = [chunk.strip() for chunk in re.split(r'\s+or\s+', remainder, flags=re.IGNORECASE) if chunk.strip()]
        if not variant_chunks:
            variant_chunks = [remainder]

        for variant_chunk in variant_chunks:
            description = variant_chunk
            countries = []

            paren_match = re.search(r'\((.*?)\)', variant_chunk)
            if paren_match:
                description = variant_chunk[:paren_match.start()].strip()
                parenthetical = paren_match.group(1)
                countries.extend([country.strip() for country in re.split(r'[,/]', parenthetical) if country.strip()])

            if description:
                if paren_match:
                    countries.insert(0, description)
                else:
                    countries.extend([country.strip() for country in re.split(r'[,/]', description) if country.strip()])

            if not countries:
                countries = [variant_chunk]

            for country_name in countries:
                if country_name:
                    variants.append((language_name, country_name))

        return variants

    def _normalize_pasted_languages(self, text):
        """Normalize pasted text into a deduplicated list of language display names."""
        normalized_entries = []
        seen_entries = set()

        for raw_entry in self._split_pasted_language_lines(text):
            for language_name, country_name in self._split_language_country_entry(raw_entry):
                if country_name:
                    display_name = f"{language_name} ({country_name})"
                else:
                    display_name = language_name

                display_name = display_name.strip()
                if display_name and display_name not in seen_entries:
                    normalized_entries.append(display_name)
                    seen_entries.add(display_name)

        return normalized_entries

    def _lookup_language_match(self, language_name, country_name=None):
        """Find the best ISO database match for a normalized language entry."""
        lookup_value = f"{language_name} ({country_name})" if country_name else language_name

        code_match = self.language_manager.get_by_code(lookup_value)
        if code_match:
            return code_match

        language_matches = self.language_manager.get_by_language(language_name)
        if not language_matches:
            search_matches = self.language_manager.search(lookup_value)
            if search_matches:
                language_matches = search_matches

        if not country_name:
            return language_matches[0] if language_matches else None

        country_lower = country_name.lower().strip()
        for language_match in language_matches:
            country_value = str(language_match.get("country", "")).lower()
            display_value = str(language_match.get("display_name", "")).lower()
            if country_lower == country_value.strip():
                return language_match
            if country_lower in country_value or country_lower in display_value:
                return language_match

        return language_matches[0] if language_matches else None

    def _normalize_lookup_text(self, text):
        """Normalize text for conservative matching across local and web results."""
        return re.sub(r"\s+", " ", str(text or "").strip()).casefold()

    def _wikidata_search_entities(self, query, limit=5):
        """Search Wikidata for candidate language entities."""
        params = urllib.parse.urlencode({
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "type": "item",
            "format": "json",
            "limit": str(limit),
        })
        request = urllib.request.Request(
            f"https://www.wikidata.org/w/api.php?{params}",
            headers={"User-Agent": "AutomationSuite/1.0"}
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        return payload.get("search", [])

    def _wikidata_fetch_iso_code(self, entity_id):
        """Fetch the best ISO language code from a Wikidata entity."""
        request = urllib.request.Request(
            f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json",
            headers={"User-Agent": "AutomationSuite/1.0"}
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        entity = payload.get("entities", {}).get(entity_id, {})
        claims = entity.get("claims", {})

        for property_name in ("P218", "P220"):
            property_claims = claims.get(property_name, [])
            for claim in property_claims:
                mainsnak = claim.get("mainsnak", {})
                datavalue = mainsnak.get("datavalue", {})
                value = datavalue.get("value", "")
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return None

    def _lookup_iso_code_from_web(self, language_name, country_name=None):
        """Look up an ISO code using Wikidata as a conservative web fallback."""
        search_terms = []

        combined_name = f"{language_name} ({country_name})" if country_name else language_name
        for term in (combined_name, language_name):
            normalized_term = self._normalize_lookup_text(term)
            if normalized_term and normalized_term not in search_terms:
                search_terms.append(normalized_term)

        seen_entity_ids = set()
        normalized_language = self._normalize_lookup_text(language_name)

        for search_term in search_terms:
            try:
                search_results = self._wikidata_search_entities(search_term)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
                continue

            for result in search_results:
                entity_id = result.get("id", "")
                if not entity_id or entity_id in seen_entity_ids:
                    continue

                seen_entity_ids.add(entity_id)
                label = self._normalize_lookup_text(result.get("label", ""))
                description = self._normalize_lookup_text(result.get("description", ""))

                if normalized_language not in label and label not in normalized_language:
                    if normalized_language not in description:
                        continue

                try:
                    iso_code = self._wikidata_fetch_iso_code(entity_id)
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
                    continue

                if iso_code:
                    return {
                        "code": iso_code,
                        "language": language_name,
                        "country": country_name or "",
                        "display_name": f"{language_name} ({country_name})" if country_name else language_name,
                        "entity_id": entity_id,
                    }

        return None

    def on_update_missing_iso_codes(self):
        """Try to resolve missing ISO codes using a web lookup fallback."""
        missing_languages = [
            lang_name for lang_name, lang_info in self.languages_data.items()
            if not str(lang_info.get("iso_code", "")).strip()
        ]

        if not missing_languages:
            messagebox.showinfo("No Missing ISO Codes", "Every language in the current rate card already has an ISO code.")
            return

        confirm = messagebox.askyesno(
            "Update Missing ISO Codes",
            f"Try to look up ISO codes on the web for {len(missing_languages)} missing language(s)?\n\nOnly high-confidence matches will be applied to the current rate card."
        )
        if not confirm:
            return

        resolved = []
        unresolved = []

        for lang_name in missing_languages:
            lang_info = self.languages_data.get(lang_name)
            if not lang_info:
                continue

            if str(lang_info.get("iso_code", "")).strip():
                continue

            base_language_name, country_name = self._split_display_language_name(lang_name)
            lookup_result = self._lookup_iso_code_from_web(base_language_name, country_name)

            if not lookup_result:
                unresolved.append(lang_name)
                continue

            iso_code = lookup_result["code"]
            lang_info["iso_code"] = iso_code
            lang_info["found"] = True
            self._set_local_iso_code(lang_name, iso_code)
            if lang_name in self.missing_languages:
                self.missing_languages.remove(lang_name)
            resolved.append(f"{lang_name} -> {iso_code}")

        self.update_table()

        if self.missing_languages:
            self.error_label.configure(text=f"⚠ Missing Languages:\n{', '.join(self.missing_languages)}\n\nPlease update the language names or ISO codes.")
        else:
            self.error_label.configure(text="")

        if resolved and unresolved:
            messagebox.showinfo(
                "ISO Lookup Complete",
                "Resolved:\n" + "\n".join(resolved) + "\n\nStill missing:\n" + ", ".join(unresolved)
            )
        elif resolved:
            messagebox.showinfo(
                "ISO Lookup Complete",
                "Resolved the following ISO codes:\n" + "\n".join(resolved)
            )
        else:
            messagebox.showwarning(
                "ISO Lookup Complete",
                "No missing ISO codes could be resolved from the web lookup."
            )

    def reload_global_services_from_file(self):
        """Reload the shared service list and sync the current card to it."""
        self._set_service_columns(self._load_global_services(), persist=False)
        self._normalize_hidden_service_columns()

        for lang_info in self.languages_data.values():
            rates = lang_info.setdefault("rates", {})
            for service_name in self.DEFAULT_SERVICES:
                rates.setdefault(service_name, "")

            for service_name in list(rates.keys()):
                if service_name not in self.DEFAULT_SERVICES:
                    rates.pop(service_name, None)

        self._refresh_tree_structure()
        self.update_table()

    def on_refresh_services(self):
        """Reload the shared service list and refresh the current card view."""
        self.reload_global_services_from_file()
        messagebox.showinfo("Services Refreshed", "Reloaded the global service list and refreshed the current card.")

    def _set_service_columns(self, services, persist=True):
        """Replace the current service column list and optionally persist it globally."""
        cleaned_services = []
        for service in services:
            service_name = str(service).strip()
            if service_name and service_name not in cleaned_services:
                cleaned_services.append(service_name)

        if not cleaned_services:
            cleaned_services = list(self.base_service_columns)

        self.DEFAULT_SERVICES = cleaned_services
        if persist:
            self._save_global_services()

    def _apply_service_visibility(self):
        """Apply the current service-column visibility settings to the table."""
        if not hasattr(self, "tree"):
            return

        visible_service_columns = [
            service for service in self.DEFAULT_SERVICES
            if service not in self.hidden_service_columns
        ]
        visible_columns = ["Language", "ISO_CODE"] + visible_service_columns
        self.tree.configure(displaycolumns=visible_columns)

        self.tree.column("Language", width=150, anchor="center")
        self.tree.column("ISO_CODE", width=120, anchor="center")

        for service in self.DEFAULT_SERVICES:
            if service not in self.column_widths:
                self.column_widths[service] = 120
            if service not in self.hidden_service_columns:
                self.tree.column(service, width=self.column_widths.get(service, 120), anchor="center")

    def _normalize_hidden_service_columns(self):
        """Drop hidden entries that no longer exist in the current service list."""
        self.hidden_service_columns = {
            service for service in self.hidden_service_columns
            if service in self.DEFAULT_SERVICES
        }

    def _get_displayed_column_names(self):
        """Return the currently displayed Treeview column names in order."""
        if not hasattr(self, "tree"):
            return []

        displaycolumns = self.tree['displaycolumns']
        if displaycolumns in ("#all", None, ""):
            return list(self.tree['columns'])

        return list(displaycolumns)

    def _get_column_name_from_display_index(self, display_index):
        """Map a displayed column index to the actual Treeview column name."""
        displayed_columns = self._get_displayed_column_names()
        if display_index < 0 or display_index >= len(displayed_columns):
            return None
        return displayed_columns[display_index]

    def _get_column_value_index(self, column_name):
        """Return the index of a column inside the row values list."""
        if not hasattr(self, "tree"):
            return None

        try:
            return list(self.tree['columns']).index(column_name)
        except ValueError:
            return None

    def on_show_hide_columns(self):
        """Open a dialog for showing or hiding service columns."""
        if not hasattr(self, "tree"):
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Show/Hide Columns")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        title_label = ctk.CTkLabel(
            container,
            text="Show / Hide Service Columns",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 8))

        instruction_label = ctk.CTkLabel(
            container,
            text="Tick a service to show it. Untick it to hide it.",
            font=ctk.CTkFont(size=10)
        )
        instruction_label.pack(anchor="w", pady=(0, 10))

        list_frame = ctk.CTkScrollableFrame(container, width=320, height=260)
        list_frame.pack(fill="both", expand=True, pady=(0, 12))

        column_vars = {}
        for service_name in self.DEFAULT_SERVICES:
            var = tk.BooleanVar(value=service_name not in self.hidden_service_columns)
            column_vars[service_name] = var
            checkbox = ctk.CTkCheckBox(
                list_frame,
                text=service_name,
                variable=var,
                command=self._apply_column_visibility_from_dialog
            )
            checkbox.pack(anchor="w", pady=4)

        self.column_visibility_vars = column_vars

        def close_dialog():
            dialog.destroy()

        def apply_and_close():
            self.hidden_service_columns = {
                service_name for service_name, variable in column_vars.items()
                if not variable.get()
            }
            self._apply_service_visibility()
            dialog.destroy()

        button_row = ctk.CTkFrame(container, fg_color="transparent")
        button_row.pack(fill="x")

        cancel_button = ctk.CTkButton(button_row, text="Close", command=close_dialog)
        cancel_button.pack(side="right", padx=(8, 0))

        apply_button = ctk.CTkButton(button_row, text="Apply", command=apply_and_close)
        apply_button.pack(side="right")

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

    def _apply_column_visibility_from_dialog(self):
        """Apply checkbox changes from the visibility dialog immediately."""
        if not hasattr(self, "tree"):
            return

        self.hidden_service_columns = {
            service_name for service_name, variable in self.column_visibility_vars.items()
            if not variable.get()
        }
        self._apply_service_visibility()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main container with two sections
        main_container = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel: Inputs
        left_panel = ctk.CTkFrame(main_container, fg_color="transparent", width=400)
        left_panel.pack(side="left", fill="both", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Load/Create buttons at top
        button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 15))
        
        load_button = ctk.CTkButton(
            button_frame,
            text="Load Rate Card",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="blue",
            hover_color="darkblue",
            height=35,
            command=self.on_load_rate_card
        )
        load_button.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        create_button = ctk.CTkButton(
            button_frame,
            text="Create New",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="gray60",
            hover_color="gray70",
            height=35,
            command=self.on_create_new
        )
        create_button.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        # Rate Card Name
        name_label = ctk.CTkLabel(
            left_panel,
            text="Rate Card Name:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        name_label.pack(anchor="w", pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(left_panel, placeholder_text="Enter rate card name")
        self.name_entry.pack(anchor="w", fill="x", pady=(0, 10))
        
        # Sponsor
        sponsor_label = ctk.CTkLabel(
            left_panel,
            text="Sponsor:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        sponsor_label.pack(anchor="w", pady=(0, 5))
        
        self.sponsor_entry = ctk.CTkEntry(left_panel, placeholder_text="Enter sponsor name")
        self.sponsor_entry.pack(anchor="w", fill="x", pady=(0, 15))
        
        # Language input section
        lang_label = ctk.CTkLabel(
            left_panel,
            text="Paste the languages for your rate card:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lang_label.pack(anchor="w", pady=(0, 5))
        
        lang_instructions = ctk.CTkLabel(
            left_panel,
            text="(Separated by ', ' or '; ')",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        lang_instructions.pack(anchor="w", pady=(0, 5))
        
        # Text area for language input
        self.language_text = scrolledtext.ScrolledText(
            left_panel,
            height=8,
            width=40,
            wrap="word",
            bg="#212121",
            fg="white",
            insertbackground="white"
        )
        self.language_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # Import button
        import_button = ctk.CTkButton(
            left_panel,
            text="Import Languages",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.on_import_languages
        )
        import_button.pack(fill="x", pady=(0, 10))
        
        # Error message area
        self.error_label = ctk.CTkLabel(
            left_panel,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="red",
            justify="left",
            wraplength=300
        )
        self.error_label.pack(anchor="w", pady=(0, 10))
        
        # Save button
        save_button = ctk.CTkButton(
            left_panel,
            text="Save Rate Card",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            command=self.on_save
        )
        save_button.pack(fill="x", pady=(0, 10))

        export_csv_button = ctk.CTkButton(
            left_panel,
            text="Export Visible Columns as CSV",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#5a4d9a",
            hover_color="#6d5bb8",
            command=self.on_export_csv
        )
        export_csv_button.pack(fill="x", pady=(0, 10))
        
        # Right panel: Viewing pane (table)
        right_panel = ctk.CTkFrame(main_container, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        table_label = ctk.CTkLabel(
            right_panel,
            text="Rate Card:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        table_label.pack(anchor="w", pady=(0, 10))
        
        # Create table frame
        table_frame = ctk.CTkFrame(right_panel, fg_color="gray20", corner_radius=5)
        table_frame.pack(fill="both", expand=True)
        
        # Create Treeview
        self.create_table(table_frame)
    
    def create_table(self, parent):
        """Create the rate card table."""
        # Build columns: Language, ISO Code, then services
        columns = ["Language", "ISO_CODE"] + self.DEFAULT_SERVICES
        
        # Create Treeview with scrollbars
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side="right", fill="y")
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side="bottom", fill="x")
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15,
            selectmode="extended",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        self.tree.pack(fill="both", expand=True)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure column headings and widths
        self.tree.heading("Language", text="Language Name")
        self.tree.column("Language", width=150, anchor="center")
        
        self.tree.heading("ISO_CODE", text="ISO CODE")
        self.tree.column("ISO_CODE", width=120, anchor="center")
        
        for service in self.DEFAULT_SERVICES:
            self.tree.heading(service, text=service)
            self.tree.column(service, width=120, anchor="center")
        
        # Bind double-click for editing
        self.tree.bind("<Double-1>", self.on_cell_click)
        self.tree.bind("<Button-3>", self.on_tree_right_click)

        self._apply_service_visibility()

        # Context menus
        self.table_menu = tk.Menu(self.tree, tearoff=0)
        self.table_menu.add_command(label="Delete Language", command=self.on_delete_language)

        self.column_menu = tk.Menu(self.tree, tearoff=0)
        self.column_menu.add_command(label="Fill Empty Cells in Column", command=self.on_fill_column_empty_cells)
        self.column_menu.add_command(label="Spill Value to Visible Languages", command=self.on_spill_value_to_visible_languages)
        self.column_menu.add_command(label="Overwrite Entire Column", command=self.on_overwrite_service_column)
        self.column_menu.add_command(label="Clone Service Column", command=self.on_clone_service_column)
        self.column_menu.add_command(label="Rename Service Column", command=self.on_rename_service_column)
        self.column_menu.add_command(label="Delete Service Column", command=self.on_delete_service_column)
        
        # Add control buttons area below tree
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        # Status label
        self.edit_status_label = ctk.CTkLabel(
            button_frame,
            text="Click a cell and start typing. Press Enter to save, Escape to cancel.",
            font=ctk.CTkFont(size=10),
            text_color="gray80"
        )
        self.edit_status_label.pack(anchor="w", pady=(0, 10))

        show_hide_button = ctk.CTkButton(
            button_frame,
            text="Show/Hide Columns",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#345a7d",
            hover_color="#436f9a",
            command=self.on_show_hide_columns
        )
        show_hide_button.pack(side="left", padx=(0, 10))

        update_global_button = ctk.CTkButton(
            button_frame,
            text="Update Global Services",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#5b4b18",
            hover_color="#7a6520",
            command=self.on_update_global_services
        )
        update_global_button.pack(side="left", padx=(0, 10))

        refresh_button = ctk.CTkButton(
            button_frame,
            text="Refresh Services",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="gray60",
            hover_color="gray70",
            command=self.on_refresh_services
        )
        refresh_button.pack(side="left", padx=(0, 10))

        lookup_button = ctk.CTkButton(
            button_frame,
            text="Update Missing ISO Codes",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#4d6b2f",
            hover_color="#5d8140",
            command=self.on_update_missing_iso_codes
        )
        lookup_button.pack(side="left", padx=(0, 10))
        
        # Bulk fill button
        bulk_fill_button = ctk.CTkButton(
            button_frame,
            text="Fill Column with Selected Value",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2d5016",
            hover_color="#3d7020",
            command=self.on_bulk_fill
        )
        bulk_fill_button.pack(side="left", padx=(0, 10))

        delete_button = ctk.CTkButton(
            button_frame,
            text="Delete Selected Language",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7a1f1f",
            hover_color="#9a2a2a",
            command=self.on_delete_language
        )
        delete_button.pack(side="left", padx=(0, 10))

        undo_button = ctk.CTkButton(
            button_frame,
            text="Undo Last Change",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#8e44ad",
            hover_color="#9b59b6",
            command=self._restore_state_from_undo
        )
        undo_button.pack(side="left", padx=(0, 10))

        filter_button = ctk.CTkButton(
            button_frame,
            text="Filter/Unfilter Languages",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.toggle_language_filter
        )
        filter_button.pack(side="left", padx=(0, 10))

        self.language_filter_status_label = ctk.CTkLabel(
            button_frame,
            text="No language filter active",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        self.language_filter_status_label.pack(side="left")
        
        # Info label for bulk fill
        self.bulk_fill_info = ctk.CTkLabel(
            button_frame,
            text="(Ctrl-click multiple languages, filter them, spill a service value to visible rows, or click to fill all empty cells in that column)",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        self.bulk_fill_info.pack(side="left")
    
    def on_import_languages(self):
        """Import languages from text input."""
        text = self.language_text.get("1.0", "end-1c").strip()
        
        if not text:
            messagebox.showwarning("Empty Input", "Please paste languages first.")
            return
        
        # Normalize pasted lines into one or more Language (Country) records
        languages = self._normalize_pasted_languages(text)
        
        if not languages:
            messagebox.showwarning("No Languages", "No valid languages found.")
            return

        added_languages = []
        missing_added = []
        
        # Process each language
        for lang in languages:
            if lang in self.languages_data:
                continue

            if "(" in lang and lang.endswith(")"):
                language_name = lang[:lang.rfind("(")].strip()
                country_name = lang[lang.rfind("(") + 1:-1].strip()
            else:
                language_name = lang.strip()
                country_name = None

            iso_data = self._lookup_language_match(language_name, country_name)
            
            if iso_data:
                # Found in database
                self.languages_data[lang] = {
                    "iso_code": iso_data["code"],
                    "found": True,
                    "rates": {service: "" for service in self.DEFAULT_SERVICES}
                }
                self._set_local_iso_code(lang, iso_data["code"])
            else:
                # Not found - add as missing
                self.languages_data[lang] = {
                    "iso_code": "",
                    "found": False,
                    "rates": {service: "" for service in self.DEFAULT_SERVICES}
                }
                self.missing_languages.append(lang)
                missing_added.append(lang)

            added_languages.append(lang)
        
        # Update table
        self.update_table()
        
        # Show error if any languages are missing
        if self.missing_languages:
            error_msg = f"⚠ Missing Languages:\n{', '.join(self.missing_languages)}\n\nPlease update the language names or ISO codes."
            self.error_label.configure(text=error_msg)
            if missing_added:
                messagebox.showwarning(
                    "Missing ISO Codes",
                    f"The following newly added languages were not found:\n{', '.join(missing_added)}\n\nYou can edit them in the table."
                )

        if added_languages:
            messagebox.showinfo("Success", f"Added {len(added_languages)} new language(s) to the current rate card.")
        else:
            messagebox.showinfo("No Changes", "No new languages were added.")
    
    def update_table(self):
        """Update the table with current languages data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        visible_language_names = None
        if self.language_filter_active and self.language_filter_names:
            visible_language_names = set(self.language_filter_names)
        
        # Add data rows
        for idx, (lang_name, lang_info) in enumerate(self.languages_data.items()):
            if visible_language_names is not None and lang_name not in visible_language_names:
                continue

            iso_code = lang_info["iso_code"]
            rates = lang_info["rates"]
            
            # Create values list
            values = [lang_name, iso_code] + [rates.get(service, "") for service in self.DEFAULT_SERVICES]
            
            # Add row with tag if missing
            tag = "missing" if not lang_info["found"] else ""
            iid = self.tree.insert("", "end", values=values, tags=(tag,))
            
            # Configure tag colors
            if tag:
                self.tree.tag_configure("missing", background="#4d3333", foreground="#ff9999")

        self._update_language_filter_status()

    def _update_language_filter_status(self):
        """Refresh the language filter status label."""
        if not self.language_filter_status_label:
            return

        if self.language_filter_active and self.language_filter_names:
            visible_count = len(self.tree.get_children()) if hasattr(self, "tree") else len(self.language_filter_names)
            self.language_filter_status_label.configure(
                text=f"Filter active: {visible_count} language(s) visible"
            )
        else:
            self.language_filter_status_label.configure(text="No language filter active")

    def on_filter_selected_languages(self):
        """Filter the table to only the selected languages."""
        if not hasattr(self, "tree"):
            return

        selected_items = list(self.tree.selection())
        if not selected_items:
            messagebox.showwarning("No Selection", "Please Ctrl-click one or more languages to filter.")
            return

        selected_names = []
        for item in selected_items:
            values = self.tree.item(item).get("values", [])
            if values:
                selected_names.append(values[0])

        if not selected_names:
            messagebox.showwarning("No Selection", "Please select one or more languages to filter.")
            return

        self.language_filter_names = set(selected_names)
        self.language_filter_active = True
        self.update_table()

    def toggle_language_filter(self):
        """Toggle language filtering on/off"""
        if self.language_filter_active:
            # Unfilter: show all languages
            self.language_filter_names = None
            self.language_filter_active = False
            self.update_table()
        else:
            # Filter: use selected languages
            selected_items = self.tree.selection()
            if not selected_items:
                messagebox.showwarning("No Selection", "Please select one or more languages to filter.")
                return
            
            selected_names = []
            for item in selected_items:
                values = self.tree.item(item).get("values", [])
                if values:
                    selected_names.append(values[0])
            
            if not selected_names:
                messagebox.showwarning("No Selection", "Please select one or more languages to filter.")
                return
            
            self.language_filter_names = set(selected_names)
            self.language_filter_active = True
            self.update_table()

    def _get_visible_tree_items(self):
        """Return currently visible tree items."""
        if not hasattr(self, "tree"):
            return []
        return list(self.tree.get_children())

    def _refresh_tree_structure(self):
        """Refresh tree columns and headings after service list changes."""
        # Clear all items first to avoid column mismatch
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset displaycolumns to avoid references to old columns
        self.tree.configure(displaycolumns="#all")
        
        columns = ["Language", "ISO_CODE"] + self.DEFAULT_SERVICES
        self.tree.configure(columns=columns)

        # Clear all existing headings first
        for col in self.tree.cget("columns"):
            try:
                self.tree.heading(col, text="")
            except:
                pass

        self.tree.heading("Language", text="Language Name")
        self.tree.column("Language", width=150, anchor="center")

        self.tree.heading("ISO_CODE", text="ISO CODE")
        self.tree.column("ISO_CODE", width=120, anchor="center")

        for service in self.DEFAULT_SERVICES:
            self.tree.heading(service, text=service)
            self.tree.column(service, width=120, anchor="center")

        self._normalize_hidden_service_columns()
        self._apply_service_visibility()
        
        # Force UI update
        self.tree.update_idletasks()

    def _reset_service_columns(self):
        """Restore the editor to the default service-column set."""
        self.DEFAULT_SERVICES = list(self.base_service_columns)
        if hasattr(self, "tree"):
            self._refresh_tree_structure()

    def _get_selected_language(self):
        """Return the selected tree item and row values, if any."""
        try:
            item = self.tree.selection()[0]
        except IndexError:
            return None, []

        values = list(self.tree.item(item).get('values', []))
        return item, values

    def _update_service_column_data(self, old_service_name, new_service_name, clone=False):
        """Rename or clone a service column in the internal data model."""
        if clone:
            insert_index = self.DEFAULT_SERVICES.index(old_service_name) + 1
            self.DEFAULT_SERVICES.insert(insert_index, new_service_name)
            for lang_info in self.languages_data.values():
                lang_info["rates"][new_service_name] = lang_info["rates"].get(old_service_name, "")
        else:
            index = self.DEFAULT_SERVICES.index(old_service_name)
            self.DEFAULT_SERVICES[index] = new_service_name
            for lang_info in self.languages_data.values():
                lang_info["rates"][new_service_name] = lang_info["rates"].pop(old_service_name, "")

    def on_tree_right_click(self, event):
        """Show a context menu for rows or service columns."""
        if self.current_edit_entry:
            self.cancel_inline_edit()

        region = self.tree.identify_region(event.x, event.y)
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        self.context_item = item if item else None
        self.context_col_index = int(column.lstrip('#')) - 1 if column and column.startswith('#') else None
        self.context_column_name = self._get_column_name_from_display_index(self.context_col_index) if self.context_col_index is not None else None

        if region == "heading" and self.context_col_index is not None:
            if self.context_column_name in self.DEFAULT_SERVICES:
                self.column_menu.tk_popup(event.x_root, event.y_root)
            return

        if item:
            self.tree.selection_set(item)
            if self.context_column_name in self.DEFAULT_SERVICES:
                self.column_menu.tk_popup(event.x_root, event.y_root)
            else:
                self.table_menu.tk_popup(event.x_root, event.y_root)

    def on_fill_column_empty_cells(self):
        """Fill empty cells in the selected service column with a chosen value."""
        if self.context_column_name not in self.DEFAULT_SERVICES:
            messagebox.showwarning("Invalid Column", "Please right-click a service column header or cell.")
            return

        col_name = self.context_column_name
        value_index = self._get_column_value_index(col_name)
        if value_index is None:
            messagebox.showwarning("Invalid Column", "Could not identify the selected column.")
            return

        current_value = None

        if self.context_item:
            values = self.tree.item(self.context_item).get('values', [])
            if value_index < len(values):
                current_value = values[value_index]

        prompt = simpledialog.askstring(
            "Fill Empty Cells",
            f"Enter the value to apply to empty cells in column '{col_name}':",
            initialvalue=current_value if current_value else ""
        )

        if prompt is None:
            return

        fill_value = prompt.strip()
        if not fill_value:
            messagebox.showwarning("Empty Value", "Please enter a non-empty value.")
            return

        self._save_state_for_undo()
        filled_count = 0
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            lang_name = values[0]
            if value_index >= len(values):
                continue

            if not str(values[value_index]).strip():
                values[value_index] = fill_value
                self.tree.item(item, values=values)
                self.languages_data[lang_name]["rates"][col_name] = fill_value
                filled_count += 1

        self.edit_status_label.configure(text=f"✓ Filled {filled_count} empty cells in: {col_name}")

    def on_overwrite_service_column(self):
        """Overwrite every value in the selected service column with one value."""
        if self.context_column_name not in self.DEFAULT_SERVICES:
            messagebox.showwarning("Invalid Column", "Please right-click a service column.")
            return

        col_name = self.context_column_name
        value_index = self._get_column_value_index(col_name)
        if value_index is None:
            messagebox.showwarning("Invalid Column", "Could not identify the selected column.")
            return

        current_value = None

        if self.context_item:
            values = self.tree.item(self.context_item).get('values', [])
            if value_index < len(values):
                current_value = values[value_index]

        prompt = simpledialog.askstring(
            "Overwrite Entire Column",
            f"Enter the value to overwrite every cell in '{col_name}':",
            initialvalue=current_value if current_value is not None else ""
        )

        if prompt is None:
            return

        overwrite_value = prompt.strip()

        # Keep service columns numeric unless the user explicitly clears the column.
        if overwrite_value:
            try:
                overwrite_value = str(float(overwrite_value))
            except ValueError:
                messagebox.showerror("Invalid Value", f"'{prompt}' is not a valid number. Please enter a numeric value.")
                return

        # Check if there are any non-empty values that will be overwritten
        has_existing_data = False
        for item in self.tree.get_children():
            values = self.tree.item(item).get('values', [])
            if value_index < len(values) and str(values[value_index]).strip():
                has_existing_data = True
                break

        if has_existing_data:
            confirm = messagebox.askyesno(
                "Confirm Overwrite",
                f"This will overwrite existing data in column '{col_name}'. Are you sure you want to continue?"
            )
            if not confirm:
                return

        self._save_state_for_undo()
        overwritten_count = 0
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            if value_index >= len(values):
                continue

            values[value_index] = overwrite_value
            self.tree.item(item, values=values)

            lang_name = values[0]
            if lang_name in self.languages_data:
                self.languages_data[lang_name]["rates"][col_name] = overwrite_value
            overwritten_count += 1

        self.edit_status_label.configure(text=f"✓ Overwrote {overwritten_count} cells in: {col_name}")

    def on_spill_value_to_visible_languages(self):
        """Apply one value to the selected service column for all visible languages."""
        if self.context_column_name not in self.DEFAULT_SERVICES:
            messagebox.showwarning("Invalid Column", "Please right-click a service column.")
            return

        col_name = self.context_column_name
        value_index = self._get_column_value_index(col_name)
        if value_index is None:
            messagebox.showwarning("Invalid Column", "Could not identify the selected column.")
            return

        current_value = None
        if self.context_item:
            values = self.tree.item(self.context_item).get('values', [])
            if value_index < len(values):
                current_value = values[value_index]

        prompt = simpledialog.askstring(
            "Spill Value to Visible Languages",
            f"Enter the value to apply to all visible languages in column '{col_name}':",
            initialvalue=current_value if current_value is not None else ""
        )

        if prompt is None:
            return

        spill_value = prompt.strip()
        if spill_value:
            try:
                spill_value = str(float(spill_value))
            except ValueError:
                messagebox.showerror("Invalid Value", f"'{prompt}' is not a valid number. Please enter a numeric value.")
                return

        # Check if there are any non-empty values that will be overwritten
        has_existing_data = False
        visible_items = self._get_visible_tree_items()
        for item in visible_items:
            values = self.tree.item(item).get('values', [])
            if value_index < len(values) and str(values[value_index]).strip():
                has_existing_data = True
                break

        if has_existing_data:
            confirm = messagebox.askyesno(
                "Confirm Overwrite",
                f"This will overwrite existing data in column '{col_name}' for {len(visible_items)} visible language(s). Are you sure you want to continue?"
            )
            if not confirm:
                return

        self._save_state_for_undo()
        spilled_count = 0
        visible_items = self._get_visible_tree_items()
        if not visible_items:
            messagebox.showwarning("No Visible Languages", "There are no visible languages to update.")
            return

        for item in visible_items:
            values = list(self.tree.item(item)['values'])
            if value_index >= len(values):
                continue

            values[value_index] = spill_value
            self.tree.item(item, values=values)

            lang_name = values[0]
            if lang_name in self.languages_data:
                self.languages_data[lang_name]["rates"][col_name] = spill_value
            spilled_count += 1

        self.edit_status_label.configure(text=f"✓ Spilled {spilled_count} visible cells in: {col_name}")

    def on_update_global_services(self):
        """Append the current card's service names to the shared global list."""
        added_services = self._append_current_services_to_global_list()

        if added_services:
            messagebox.showinfo(
                "Global Services Updated",
                f"Added to global list:\n{', '.join(added_services)}"
            )
        else:
            messagebox.showinfo("Global Services Updated", "No new service names were found to add.")

    def on_delete_service_column(self):
        """Delete the selected service column from the table and internal data."""
        if self.context_column_name not in self.DEFAULT_SERVICES:
            messagebox.showwarning("Invalid Column", "Please right-click a service column.")
            return

        service_name = self.context_column_name
        confirm = messagebox.askyesno(
            "Delete Service Column",
            f"Delete the service column '{service_name}'?\n\nThis removes the column from the rate card and cannot be undone."
        )
        if not confirm:
            return

        self._save_state_for_undo()
        if service_name in self.DEFAULT_SERVICES:
            updated_services = [service for service in self.DEFAULT_SERVICES if service != service_name]
            self._set_service_columns(updated_services, persist=False)

        self.hidden_service_columns.discard(service_name)

        for lang_info in self.languages_data.values():
            lang_info["rates"].pop(service_name, None)

        self.current_edit_col = None
        self._refresh_tree_structure()
        self.update_table()
        self.edit_status_label.configure(text=f"✓ Deleted column: {service_name}")

    def on_rename_service_column(self):
        """Rename a service column and update the underlying rates keys."""
        if self.context_column_name not in self.DEFAULT_SERVICES:
            messagebox.showwarning("Invalid Column", "Please right-click a service column.")
            return

        old_service_name = self.context_column_name
        new_service_name = simpledialog.askstring(
            "Rename Service Column",
            f"Rename '{old_service_name}' to:"
        )

        if new_service_name is None:
            return

        new_service_name = new_service_name.strip()
        if not new_service_name:
            messagebox.showwarning("Invalid Name", "Service column name cannot be empty.")
            return

        if new_service_name in self.DEFAULT_SERVICES:
            messagebox.showerror("Duplicate", f"Service '{new_service_name}' already exists.")
            return

        self._save_state_for_undo()
        self._update_service_column_data(old_service_name, new_service_name, clone=False)
        if old_service_name in self.hidden_service_columns:
            self.hidden_service_columns.remove(old_service_name)
            self.hidden_service_columns.add(new_service_name)
        self._refresh_tree_structure()
        self.update_table()
        self.edit_status_label.configure(text=f"✓ Renamed column: {old_service_name} -> {new_service_name}")

    def on_clone_service_column(self):
        """Clone a service column into a new service column."""
        if self.context_column_name not in self.DEFAULT_SERVICES:
            messagebox.showwarning("Invalid Column", "Please right-click a service column.")
            return

        old_service_name = self.context_column_name
        new_service_name = simpledialog.askstring(
            "Clone Service Column",
            f"Name for the cloned copy of '{old_service_name}':"
        )

        if new_service_name is None:
            return

        new_service_name = new_service_name.strip()
        if not new_service_name:
            messagebox.showwarning("Invalid Name", "Cloned service column name cannot be empty.")
            return

        if new_service_name in self.DEFAULT_SERVICES:
            messagebox.showerror("Duplicate", f"Service '{new_service_name}' already exists.")
            return

        self._save_state_for_undo()
        self._update_service_column_data(old_service_name, new_service_name, clone=True)
        self.hidden_service_columns.discard(new_service_name)
        self._refresh_tree_structure()
        self.update_table()
        self.edit_status_label.configure(text=f"✓ Added column from: {old_service_name} -> {new_service_name}")
    
    def on_cell_click(self, event):
        """Handle cell double-click to enable inline editing."""
        # Close any existing edit entry
        if self.current_edit_entry:
            self.current_edit_entry.destroy()
            self.current_edit_entry = None
        
        try:
            item = self.tree.selection()[0]
        except IndexError:
            return
        
        col = self.tree.identify_column(event.x)
        display_index = int(col.lstrip('#')) - 1

        col_name = self._get_column_name_from_display_index(display_index)
        if not col_name:
            return

        col_index = self._get_column_value_index(col_name)
        if col_index is None:
            return
        
        # Get current values
        values = self.tree.item(item)['values']
        lang_name = values[0] if values else ""
        current_value = values[col_index] if col_index < len(values) else ""
        
        # Check if this is a missing language row
        item_tags = self.tree.item(item, 'tags')
        is_missing = 'missing' in item_tags if item_tags else False
        
        # Get cell bbox for positioning the entry widget
        bbox = self.tree.bbox(item, col)
        if not bbox:
            return
        
        # Create inline entry widget
        self.current_edit_entry = tk.Entry(self.tree, font=("Arial", 10))
        self.current_edit_entry.insert(0, str(current_value))
        self.current_edit_entry.select_range(0, len(self.current_edit_entry.get()))
        
        # Position entry over cell using geometry placement instead of Treeview window embedding
        self.current_edit_entry.place(
            in_=self.tree,
            x=bbox[0],
            y=bbox[1],
            width=bbox[2],
            height=bbox[3]
        )
        self.current_edit_entry.focus()
        
        # Store edit context
        self.current_edit_item = item
        self.current_edit_col = col_index
        
        # Bind keys for save/cancel
        def on_return(e):
            self.save_inline_edit(item, col_index, col_name, lang_name, is_missing)
        
        def on_escape(e):
            self.cancel_inline_edit()
        
        def on_focus_out(e):
            # Save on focus out
            self.save_inline_edit(item, col_index, col_name, lang_name, is_missing)
        
        self.current_edit_entry.bind("<Return>", on_return)
        self.current_edit_entry.bind("<Escape>", on_escape)
        self.current_edit_entry.bind("<FocusOut>", on_focus_out)
    
    def save_inline_edit(self, item, col_index, col_name, lang_name, is_missing):
        """Save inline edit and update data."""
        if not self.current_edit_entry:
            return
        
        self._save_state_for_undo()
        new_value = self.current_edit_entry.get()
        
        # Validate if it's a rate column (numeric)
        if col_name in self.DEFAULT_SERVICES:
            # This is a rate column - validate float
            if new_value and new_value.strip():
                try:
                    float_val = float(new_value)
                    new_value = str(float_val)
                except ValueError:
                    messagebox.showerror("Invalid Value", f"'{new_value}' is not a valid number. Please enter a numeric value.")
                    self.cancel_inline_edit()
                    return
        
        # Get all values
        values = list(self.tree.item(item)['values'])
        old_lang_name = values[0]
        old_iso_code = values[1] if len(values) > 1 else ""
        
        # Handle language name change (col 0)
        if col_index == 0:
            new_value = new_value.strip()

            if not new_value:
                messagebox.showerror("Invalid Value", "Language name cannot be empty.")
                self.cancel_inline_edit()
                return

            # Check if new language name already exists
            if new_value != old_lang_name and new_value in self.languages_data:
                messagebox.showerror("Duplicate", f"Language '{new_value}' already exists in the rate card.")
                self.cancel_inline_edit()
                return
            
            # Update the languages_data dictionary with new key
            self.languages_data[new_value] = self.languages_data.pop(old_lang_name)
            values[0] = new_value
            lang_name = new_value
            self._rename_local_iso_code_key(old_lang_name, new_value)
            
            # Prompt for ISO list scope when this language already exists in the snapshot or has an ISO code.
            if old_iso_code or old_lang_name in self.local_iso_codes:
                choice = self._prompt_iso_update_scope(
                    "Update ISO Code List",
                    f"'{old_lang_name}' was renamed to '{new_value}'.\n\nWhere should the ISO code list be updated?"
                )

                if choice in ("global", "both") and old_iso_code:
                    self.language_manager.update_language_name(old_iso_code, new_value)
        else:
            values[col_index] = new_value
        
        # Update tree display
        self.tree.item(item, values=values)
        
        # Update internal data
        if col_index == 1:  # ISO CODE column
            self.languages_data[lang_name]["iso_code"] = new_value
            self._set_local_iso_code(lang_name, new_value)

            # If this is an existing record, ask where to apply the update.
            choice = self._prompt_iso_update_scope(
                "Update ISO Code",
                f"ISO code for '{lang_name}' changed from '{old_iso_code or 'blank'}' to '{new_value}'.\n\nWhere should the ISO code list be updated?"
            )

            if choice in ("global", "both") and new_value:
                if old_iso_code:
                    self.language_manager.update_language_code(old_iso_code, new_value)
                else:
                    base_language_name, country_name = self._split_display_language_name(lang_name)
                    self.language_manager.add_or_update_language(new_value, base_language_name, country_name, display_name=lang_name)
            
            # Check if now found
            if new_value:
                self.languages_data[lang_name]["found"] = True
                if lang_name in self.missing_languages:
                    self.missing_languages.remove(lang_name)
                self.tree.item(item, tags=())
                self.error_label.configure(text="")
        elif col_index > 1:  # Rate column
            self.languages_data[lang_name]["rates"][col_name] = new_value
        
        # Update status
        self.edit_status_label.configure(text=f"✓ Saved: {col_name} = {new_value}")
        
        # Track this for bulk fill
        self.current_edit_col = col_index
        
        self.cancel_inline_edit()

    def on_delete_language(self):
        """Delete the selected language row and all of its stored data."""
        if self.current_edit_entry:
            self.cancel_inline_edit()

        try:
            item = self.tree.selection()[0]
        except IndexError:
            messagebox.showwarning("No Selection", "Please select a language row to delete.")
            return

        values = self.tree.item(item).get('values', [])
        if not values:
            messagebox.showwarning("Invalid Selection", "Could not determine the selected language.")
            return

        lang_name = values[0]
        confirm = messagebox.askyesno(
            "Delete Language",
            f"Delete language '{lang_name}' and all of its data?\n\nThis removes the language from the rate card and cannot be undone."
        )
        if not confirm:
            return

        self._save_state_for_undo()
        if lang_name in self.languages_data:
            del self.languages_data[lang_name]

        if lang_name in self.missing_languages:
            self.missing_languages.remove(lang_name)

        self.tree.delete(item)

        if self.language_filter_names and lang_name in self.language_filter_names:
            self.language_filter_names.discard(lang_name)
            if not self.language_filter_names:
                self.language_filter_names = None
                self.language_filter_active = False
                self.update_table()

        if self.missing_languages:
            self.error_label.configure(text=f"⚠ Missing Languages:\n{', '.join(self.missing_languages)}\n\nPlease update the language names or ISO codes.")
        else:
            self.error_label.configure(text="")

        self.edit_status_label.configure(text=f"✓ Deleted: {lang_name}")
    
    def cancel_inline_edit(self):
        """Cancel inline editing and cleanup."""
        if self.current_edit_entry:
            try:
                self.current_edit_entry.place_forget()
                self.current_edit_entry.destroy()
            except:
                pass
            self.current_edit_entry = None
        self.current_edit_item = None
    
    def on_bulk_fill(self):
        """Fill all empty cells in the last edited column with the selected value."""
        if self.current_edit_col is None:
            messagebox.showwarning("No Selection", "Please edit a cell first to select which column to fill.")
            return
        
        # Get column name and the value to fill from first language
        col_name = self.tree['columns'][self.current_edit_col] if self.current_edit_col < len(self.tree['columns']) else None
        if not col_name:
            messagebox.showwarning("Invalid Column", "Could not identify the column to fill.")
            return
        
        # Find the value to fill (from first edited item or current selection)
        try:
            selected_item = self.tree.selection()[0]
            values = self.tree.item(selected_item)['values']
            fill_value = values[self.current_edit_col] if self.current_edit_col < len(values) else ""
        except (IndexError, KeyError):
            messagebox.showwarning("No Selection", "Please select a cell with a value to fill from.")
            return
        
        if not fill_value or not fill_value.strip():
            messagebox.showwarning("Empty Value", "The selected cell is empty. Please enter a value first.")
            return
        
        # Confirm bulk fill
        result = messagebox.askyesno(
            "Bulk Fill",
            f"Fill all empty cells in column '{col_name}' with value '{fill_value}'?"
        )
        
        if not result:
            return
        
        self._save_state_for_undo()
        # Fill all empty cells in this column
        filled_count = 0
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            lang_name = values[0]
            
            # Only fill if empty
            if not values[self.current_edit_col] or not str(values[self.current_edit_col]).strip():
                values[self.current_edit_col] = fill_value
                self.tree.item(item, values=values)
                
                # Update internal data
                if col_name in self.DEFAULT_SERVICES:
                    self.languages_data[lang_name]["rates"][col_name] = fill_value
                
                filled_count += 1
        
        messagebox.showinfo("Bulk Fill Complete", f"Filled {filled_count} cells in column '{col_name}'.")

    def on_delete_language(self):
        """Delete the selected language row and all of its stored data."""
        if self.current_edit_entry:
            self.cancel_inline_edit()

        item, values = self._get_selected_language()
        if not item or not values:
            messagebox.showwarning("No Selection", "Please select a language row to delete.")
            return

        lang_name = values[0]
        confirm = messagebox.askyesno(
            "Delete Language",
            f"Delete language '{lang_name}' and all of its data?\n\nThis removes the language from the rate card and cannot be undone."
        )
        if not confirm:
            return

        if lang_name in self.languages_data:
            del self.languages_data[lang_name]

        if lang_name in self.missing_languages:
            self.missing_languages.remove(lang_name)

        self.tree.delete(item)

        if self.missing_languages:
            self.error_label.configure(text=f"⚠ Missing Languages:\n{', '.join(self.missing_languages)}\n\nPlease update the language names or ISO codes.")
        else:
            self.error_label.configure(text="")

        self.edit_status_label.configure(text=f"✓ Deleted: {lang_name}")
    
    def on_save(self):
        """Save the rate card to JSON."""
        if not self.name_entry.get():
            messagebox.showwarning("Missing Name", "Please enter a rate card name.")
            return
        
        if not self.languages_data:
            messagebox.showwarning("No Data", "Please import languages first.")
            return
        
        # Build save data
        rate_card = {
            "name": self.name_entry.get(),
            "sponsor": self.sponsor_entry.get(),
            "services": self.DEFAULT_SERVICES,
            "iso_codes": self._build_local_iso_codes_snapshot(),
            "languages": {}
        }
        
        for lang_name, lang_info in self.languages_data.items():
            rate_card["languages"][lang_name] = {
                "iso_code": lang_info["iso_code"],
                "rates": lang_info["rates"]
            }
        
        # Save to JSON
        file_path = Path(__file__).parent / f"rate_cards_{self.name_entry.get().replace(' ', '_')}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rate_card, f, indent=2, ensure_ascii=False)

            self._save_global_services()
            
            messagebox.showinfo("Success", f"Rate card saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save rate card:\n{str(e)}")

    def on_export_csv(self):
        """Export the currently visible columns and rows to CSV."""
        if not self.languages_data:
            messagebox.showwarning("No Data", "Please import languages first.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Rate Card as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(Path(__file__).parent),
            initialfile=f"rate_cards_{self.name_entry.get().replace(' ', '_')}.csv" if self.name_entry.get() else "rate_card.csv"
        )

        if not file_path:
            return

        visible_columns = self._get_displayed_column_names()
        if not visible_columns:
            messagebox.showwarning("No Visible Columns", "There are no visible columns to export.")
            return

        tree_columns = list(self.tree['columns'])
        column_indexes = []
        csv_headers = []

        for column_name in visible_columns:
            if column_name not in tree_columns:
                continue
            column_indexes.append(tree_columns.index(column_name))
            if column_name == "Language":
                csv_headers.append("Language Name")
            elif column_name == "ISO_CODE":
                csv_headers.append("ISO CODE")
            else:
                csv_headers.append(column_name)

        if not column_indexes:
            messagebox.showwarning("No Visible Columns", "There are no exportable visible columns.")
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(csv_headers)

                for item in self.tree.get_children():
                    row_values = list(self.tree.item(item).get('values', []))
                    row = []
                    for column_index in column_indexes:
                        row.append(row_values[column_index] if column_index < len(row_values) else "")
                    writer.writerow(row)

            messagebox.showinfo("Export Complete", f"CSV exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV:\n{str(e)}")
    
    def on_load_rate_card(self):
        """Open dialog to load an existing rate card (JSON or Excel)."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Select Rate Card",
            initialdir=str(Path(__file__).parent),
            filetypes=[
                ("All Supported", ("*.json", "*.xlsx")),
                ("JSON files", "*.json"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Check if current data modified and prompt save
        if self.languages_data:
            result = messagebox.askyesnocancel(
                "Save Current Rate Card?",
                "You have unsaved changes. Save before loading?"
            )
            if result is True:  # Yes
                self.on_save()
            elif result is None:  # Cancel
                return
        
        try:
            file_path = Path(file_path)
            
            # Load based on file type
            if file_path.suffix.lower() == '.xlsx':
                if load_excel_rate_card is None:
                    messagebox.showerror("Error", "Excel support not available.\nPlease install: pip install openpyxl pandas")
                    return
                data = load_excel_rate_card(str(file_path))
            else:
                # JSON file
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            loaded_iso_codes = data.get("iso_codes", {})
            if isinstance(loaded_iso_codes, dict):
                self.local_iso_codes = {
                    str(language_name).strip(): str(iso_code).strip()
                    for language_name, iso_code in loaded_iso_codes.items()
                    if str(language_name).strip() and str(iso_code).strip()
                }
            else:
                self.local_iso_codes = {}

            global_services = self._load_global_services()
            loaded_services = self._extract_services_from_loaded_card(data)
            merged_services = self._merge_service_names(global_services, loaded_services)
            if not merged_services:
                merged_services = self._merge_service_names(global_services, self.base_service_columns)

            self._set_service_columns(merged_services, persist=False)
            self._normalize_hidden_service_columns()
            
            # Load data into editor
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, data.get("name", ""))
            
            self.sponsor_entry.delete(0, "end")
            self.sponsor_entry.insert(0, data.get("sponsor", ""))
            
            # Clear and reload languages data
            self.languages_data = {}
            self.missing_languages = []
            self.error_label.configure(text="")
            
            # Populate languages_data from loaded file
            for lang_name, lang_info in data.get("languages", {}).items():
                iso_code = lang_info.get("iso_code", "")
                loaded_rates = lang_info.get("rates", {}) if isinstance(lang_info.get("rates", {}), dict) else {}

                if lang_name in self.local_iso_codes:
                    iso_code = self.local_iso_codes[lang_name]
                
                # Try to verify ISO code
                iso_data = self.language_manager.get_by_code(iso_code) if iso_code else None
                is_found = iso_data is not None if iso_code else False
                
                self.languages_data[lang_name] = {
                    "iso_code": iso_code,
                    "found": is_found,
                    "rates": {
                        service_name: loaded_rates.get(service_name, "")
                        for service_name in self.DEFAULT_SERVICES
                    }
                }

                if iso_code:
                    self._set_local_iso_code(lang_name, iso_code)
                
                if not is_found and iso_code:
                    self.missing_languages.append(lang_name)
            
            # Update table
            self._refresh_tree_structure()
            self.update_table()
            
            # Clear language text area
            self.language_text.delete("1.0", "end")
            
            # Show success message
            messagebox.showinfo("Loaded", f"Loaded: {file_path.name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load rate card:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def on_create_new(self):
        """Create a new rate card with prompt to save current one."""
        if self.languages_data:
            result = messagebox.askyesnocancel(
                "Save Current Rate Card?",
                "You have unsaved changes. Save before creating new?"
            )
            if result is True:  # Yes
                self.on_save()
            elif result is None:  # Cancel
                return
        
        # Clear all fields
        self.name_entry.delete(0, "end")
        self.sponsor_entry.delete(0, "end")
        self.language_text.delete("1.0", "end")
        
        # Clear data
        self.languages_data = {}
        self.missing_languages = []
        self.local_iso_codes = {}
        self.error_label.configure(text="")
        self._set_service_columns(self._load_global_services(), persist=False)
        self.hidden_service_columns = set()
        
        # Clear table
        self._refresh_tree_structure()
        self.update_table()
        
        messagebox.showinfo("New Rate Card", "Ready to create a new rate card!")


def setup_itemized_editor(parent_frame, root):
    """
    Setup function to initialize the itemized editor in a given tab.
    
    Args:
        parent_frame: The tab frame to embed the editor into
        root: The root window
    """
    editor = ItemizedRateCardEditor(parent_frame, root)
    return editor
