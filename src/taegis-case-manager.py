# =============================================================================
# TAEGIS CASE MANAGER (Production, Investigations v2)
# Version: v1.0.1 (2026-03-04)
#
# Single-file Tkinter app to list and update Taegis investigations with:
# - Region selection via env vars
# - Investigations v2 queries with pagination
# - Per-row checkboxes + Select All / Clear All (iid == case id)
# - Apply ANY status (enum) via updateInvestigationV2(input: { id, status })
# - Add a COMMENT via addCommentToInvestigation(input: { investigationId: String!, comment: String! })
#   • Branding: comments include “Taegis Case Manager (API)”. If no user comment is supplied,
#     the tool posts: “Status set to <ENUM> — Taegis Case Manager (API)”. If a user comment is
#     supplied, the tool appends “— Taegis Case Manager (API)”.
# - Client-side Filter (matches any substring across any visible column on the current page)
# - NEW in v1.0.1: "Copy IDs" now copies **Short IDs** (not long GUIDs)
# - Compact UI, left-aligned Status, labeled Comment panel
# - Logging to taegis_case_manager.log + scrollable error dialogs on failure
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import traceback
import csv
from datetime import datetime

VERSION = "v1.0.1 (2026-03-04)"
LOG_FILE = "taegis_case_manager.log"
BRAND = "Taegis Case Manager (API)"

# ---- Tenant-specific comment mutation wiring ----
COMMENT_MUTATION_NAME = "addCommentToInvestigation"
COMMENT_INPUT_TYPE = "AddCommentToInvestigationInput"
COMMENT_INPUT_ID_FIELD = "investigationId"      # String!
COMMENT_INPUT_BODY_FIELD = "comment"             # String!


def log_line(msg: str):
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)

print("DEBUG: Script started...", VERSION)
log_line(f"=== Script launch: {VERSION} ===")

# =============================================================================
# Taegis SDK
# =============================================================================
try:
    from taegis_sdk_python import GraphQLService
    from taegis_sdk_python.services.investigations2.types import InvestigationsV2Arguments
    log_line("Taegis SDK import OK.")
except Exception as e:
    log_line(f"ERROR importing Taegis SDK: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")
    raise

# =============================================================================
# Region map
# =============================================================================
REGION_MAP = {
    "Charlie (US1)": "https://api.ctpx.secureworks.com",
    "Delta (US2)": "https://api.delta.taegis.secureworks.com",
    "Foxtrot (US3)": "https://api.foxtrot.taegis.secureworks.com",
    "Echo (EU)": "https://api.echo.taegis.secureworks.com",
}

# =============================================================================
# Status options (labels) + label→enum map
# =============================================================================
STATUS_OPTIONS = [
    "Awaiting Action",
    "Open",
    "Active",
    "Suspended",
    "Closed: Confirmed Security Incident",
    "Closed: Authorized Activity",
    "Closed: Threat Mitigated",
    "Closed: Not Vulnerable",
    "Closed: False Positive Alert",
    "Closed: Inconclusive",
    "Closed: Informational",
]
CLOSED_PREFIX = "Closed:"

STATUS_TO_ENUM = {
    "Awaiting Action": "AWAITING_ACTION",
    "Open": "OPEN",
    "Active": "ACTIVE",
    "Suspended": "SUSPENDED",
    "Closed: Confirmed Security Incident": "CLOSED_CONFIRMED_SECURITY_INCIDENT",
    "Closed: Authorized Activity": "CLOSED_AUTHORIZED_ACTIVITY",
    "Closed: Threat Mitigated": "CLOSED_THREAT_MITIGATED",
    "Closed: Not Vulnerable": "CLOSED_NOT_VULNERABLE",
    "Closed: False Positive Alert": "CLOSED_FALSE_POSITIVE_ALERT",
    "Closed: Inconclusive": "CLOSED_INCONCLUSIVE",
    "Closed: Informational": "CLOSED_INFORMATIONAL",
}

# =============================================================================
# Checkbox glyphs
# =============================================================================
CHECKED = "☑"
UNCHECKED = "☐"

# =============================================================================
# Help popup
# =============================================================================

def show_help():
    help_text = (
        f"TAEGIS CASE MANAGER — {VERSION}\n"
        "---------------------------------------------\n"
        "• Bulk-select investigations and set ANY status.\n"
        "• Status is updated via updateInvestigationV2(input: { id, status }).\n"
        "• Comment is posted via addCommentToInvestigation(input: {\n"
        f"    {COMMENT_INPUT_ID_FIELD}: String!, {COMMENT_INPUT_BODY_FIELD}: String!\n"
        "  }).\n"
        "• Filter box matches any substring in any visible column on the current page.\n"
        "• Copy IDs copies **Short IDs** (not GUIDs).\n\n"
        "All actions are branded as ‘Taegis Case Manager (API)’.\n"
        "See taegis_case_manager.log for details."
    )
    win = tk.Toplevel()
    win.title(f"Help — {VERSION}")
    win.geometry("700x480")
    txt = tk.Text(win, wrap="word", padx=10, pady=10)
    txt.insert("1.0", help_text)
    txt.configure(state="disabled")
    txt.pack(expand=True, fill="both")

# =============================================================================
# Main app
# =============================================================================
class TaegisCaseManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Taegis Case Manager (Production, v2) — {VERSION}")
        self.root.geometry("1060x840")

        # UI state
        self.client_id = tk.StringVar()
        self.client_secret = tk.StringVar()
        self.selected_region = tk.StringVar()
        self.selected_status = tk.StringVar()
        self.results_info = tk.StringVar(value="")
        self.sel_counter = tk.StringVar(value="Selected 0 of 0")
        self.last_action = tk.StringVar(value="Ready.")
        self.last_mode = "open"
        self.per_page_var = tk.StringVar(value="25")
        self.page_num = 1
        self.total_count = None
        self.filter_var = tk.StringVar()
        self._filter_after_id = None

        # Data & SDK
        self.service = None
        self.selected_map = {}  # id -> bool
        self._rows_cache = []   # list of dict rows for current page

        self.build_ui()
        log_line("UI initialized successfully.")

    # --------------------------- UI ---------------------------
    def build_ui(self):
        # Top: creds/region
        top = tk.Frame(self.root)
        top.pack(pady=8, fill="x")

        tk.Label(top, text="Client ID:").grid(row=0, column=0, sticky="e", padx=(8,4))
        tk.Entry(top, textvariable=self.client_id, width=56).grid(row=0, column=1, sticky="w")

        tk.Label(top, text="Client Secret:").grid(row=1, column=0, sticky="e", padx=(8,4))
        tk.Entry(top, textvariable=self.client_secret, width=56, show="*").grid(row=1, column=1, sticky="w")

        tk.Label(top, text="Region:").grid(row=2, column=0, sticky="e", padx=(8,4))
        region_picker = ttk.Combobox(top, textvariable=self.selected_region,
                                     values=list(REGION_MAP.keys()), state="readonly", width=53)
        region_picker.grid(row=2, column=1, sticky="w")
        region_picker.current(0)

        # Controls + Filter row
        controls = tk.Frame(self.root)
        controls.pack(fill="x", pady=(2, 0), padx=8)

        left = tk.Frame(controls)
        left.pack(side="left")
        tk.Button(left, text="Select All", command=lambda: self._safe_call(self.set_all_checked, True)).pack(side="left")
        tk.Button(left, text="Clear All", command=lambda: self._safe_call(self.set_all_checked, False)).pack(side="left", padx=(6, 0))

        right = tk.Frame(controls)
        right.pack(side="right")
        tk.Label(right, textvariable=self.sel_counter, fg="#555555").pack(side="right")
        # Filter widgets
        filter_box = tk.Frame(controls)
        filter_box.pack(fill="x", pady=(6,0))
        tk.Label(filter_box, text="Filter:").pack(side="left")
        entry = tk.Entry(filter_box, textvariable=self.filter_var, width=48)
        entry.pack(side="left", padx=(6, 6))
        tk.Button(filter_box, text="✕", command=self.clear_filter, width=2).pack(side="left")
        entry.bind("<KeyRelease>", self._on_filter_change)

        # Table
        table_frame = tk.Frame(self.root, bd=1, relief="sunken")
        table_frame.pack(padx=8, pady=6, fill="both", expand=True)

        columns = ("sel", "short_id", "title", "status", "updated_at")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)

        self.tree.heading("sel", text="✓")
        self.tree.heading("short_id", text="Short ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("status", text="Status")
        self.tree.heading("updated_at", text="Updated")

        self.tree.column("sel", width=40, anchor="center", stretch=False)
        self.tree.column("short_id", width=160, anchor="w")
        self.tree.column("title", width=640, anchor="w")
        self.tree.column("status", width=160, anchor="w")
        self.tree.column("updated_at", width=160, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Button-1>", self._on_mouse_down)

        # Action row (Status + Comment)
        action = tk.Frame(self.root)
        action.pack(fill="both", padx=8, pady=(4, 8))
        action.grid_columnconfigure(0, weight=0)
        action.grid_columnconfigure(1, weight=1)

        status_col = tk.Frame(action)
        status_col.grid(row=0, column=0, sticky="n", padx=(0, 12))
        tk.Label(status_col, text="New Status:").pack(anchor="w")
        status_picker = ttk.Combobox(status_col, textvariable=self.selected_status,
                                     values=STATUS_OPTIONS, state="readonly", width=28)
        status_picker.pack(anchor="w", pady=(2, 0))
        status_picker.current(0)

        note_col = ttk.LabelFrame(action, text="Comment")
        note_col.grid(row=0, column=1, sticky="nsew")
        note_col.grid_rowconfigure(0, weight=1)
        note_col.grid_columnconfigure(0, weight=1)
        self.note_entry = tk.Text(note_col, height=6, wrap="word")
        self.note_entry.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)

        # Bottom buttons
        buttons = tk.Frame(self.root)
        buttons.pack(pady=6)

        tk.Button(buttons, text="Load Cases (OPEN)", command=lambda: self._safe_call(self.load_cases_v2, "open", True)).grid(row=0, column=0, padx=4)
        tk.Button(buttons, text="Load Recent (All)", command=lambda: self._safe_call(self.load_cases_v2, "all", True)).grid(row=0, column=1, padx=4)
        tk.Button(buttons, text="Refresh Cases", command=lambda: self._safe_call(self.load_cases_v2, self.last_mode, False)).grid(row=0, column=2, padx=4)
        tk.Button(buttons, text="Prev Page", command=lambda: self._safe_call(self.prev_page)).grid(row=0, column=3, padx=4)
        tk.Button(buttons, text="Next Page", command=lambda: self._safe_call(self.next_page)).grid(row=0, column=4, padx=4)

        tk.Label(buttons, text="Per Page:", anchor="e").grid(row=0, column=5, padx=(16, 4))
        per_page_combo = ttk.Combobox(buttons, textvariable=self.per_page_var, values=["10", "25", "50", "100"], state="readonly", width=5)
        per_page_combo.grid(row=0, column=6, padx=4)
        per_page_combo.bind("<<ComboboxSelected>>", lambda e: self._safe_call(self.on_per_page_change))

        tk.Button(buttons, text="Apply Status to Selected", command=lambda: self._safe_call(self.apply_status_to_selected)).grid(row=0, column=7, padx=(10,6))
        tk.Button(buttons, text="Close Selected Cases", command=lambda: self._safe_call(self.close_cases_v2_safe)).grid(row=0, column=8, padx=6)

        tk.Button(buttons, text="Copy IDs", command=lambda: self._safe_call(self.copy_selected_ids)).grid(row=0, column=9, padx=4)
        tk.Button(buttons, text="Export CSV", command=lambda: self._safe_call(self.export_csv_current_page)).grid(row=0, column=10, padx=4)
        tk.Button(buttons, text="Help", command=show_help).grid(row=0, column=11, padx=6)

        # Status bar
        status_bar = tk.Frame(self.root)
        status_bar.pack(fill="x", padx=8, pady=(0,8))
        tk.Label(status_bar, textvariable=self.results_info, fg="#555555").pack(side="left")
        tk.Label(status_bar, textvariable=self.last_action, fg="#777777").pack(side="right")

    # ----------------------- Filter logic -----------------------
    def _on_filter_change(self, event=None):
        # debounce
        if self._filter_after_id:
            self.root.after_cancel(self._filter_after_id)
        self._filter_after_id = self.root.after(200, self.apply_filter)

    def clear_filter(self):
        self.filter_var.set("")
        self.apply_filter()

    def apply_filter(self):
        self._filter_after_id = None
        q = (self.filter_var.get() or "").strip().lower()
        if not q:
            self.render_rows(self._rows_cache)
            return
        filtered = []
        for r in self._rows_cache:
            hay = f"{r['short_id']} {r['title']} {r['status']} {r['updated_at']}".lower()
            if q in hay:
                filtered.append(r)
        self.render_rows(filtered)

    def render_rows(self, rows):
        # preserve selection_map; only re-render the Treeview
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            iid = r['id']
            if iid not in self.selected_map:
                self.selected_map[iid] = False
            mark = CHECKED if self.selected_map[iid] else UNCHECKED
            self.tree.insert("", "end", iid=iid, values=(mark, r['short_id'], r['title'], r['status'], r['updated_at']))
        self.update_selected_counter()

    # ----------------------- Event routing -----------------------
    def _on_mouse_down(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if region == "heading" and column == "#1":
            self.last_action.set("Tip: Use Select All / Clear All above the table.")
            log_line("Heading clicked on checkbox column; hint shown.")
            return "break"
        if region == "cell" and column == "#1" and row:
            self.on_tree_click_cell(row)
            return "break"

    # ----------------------- Safe call wrapper -----------------------
    def _safe_call(self, func, *args, **kwargs):
        try:
            name = getattr(func, "__name__", str(func))
            self.last_action.set(f"Calling {name}() ...")
            log_line(f"CALL {name} args={args} kwargs={kwargs}")
            return func(*args, **kwargs)
        except Exception as e:
            log_line(f"ERROR in {name}: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", f"{name} failed:\n{e}")
        finally:
            self.last_action.set(f"Last: {name} done.")

    # ----------------------- Checkbox mgmt -----------------------
    def update_selected_counter(self):
        total = len(self.tree.get_children())
        selected = sum(1 for iid in self.tree.get_children() if self.selected_map.get(iid, False))
        self.sel_counter.set(f"Selected {selected} of {total}")

    def _refresh_row_checkbox(self, iid: str):
        try:
            vals = list(self.tree.item(iid, "values"))
            if not vals:
                return
            mark = CHECKED if self.selected_map.get(iid, False) else UNCHECKED
            self.tree.set(iid, "sel", mark)
            vals[0] = mark
            self.tree.item(iid, values=tuple(vals))
        except Exception as e:
            log_line(f"_refresh_row_checkbox error for iid={iid}: {e}")

    def refresh_checkmarks(self):
        try:
            rows = self.tree.get_children()
            for iid in rows:
                self._refresh_row_checkbox(iid)
            self.update_selected_counter()
            self.tree.update_idletasks()
        except Exception as e:
            log_line(f"refresh_checkmarks error: {e}")

    def set_all_checked(self, state: bool):
        rows = self.tree.get_children()
        log_line(f"set_all_checked({state}) rows={len(rows)}")
        if not rows:
            self.last_action.set("No rows to select.")
            return
        for iid in rows:
            self.selected_map[iid] = state
        self.refresh_checkmarks()

    def on_tree_click_cell(self, row_iid: str):
        self.selected_map[row_iid] = not self.selected_map.get(row_iid, False)
        log_line(f"on_tree_click_cell: row={row_iid} -> {self.selected_map[row_iid]}")
        self._refresh_row_checkbox(row_iid)
        self.update_selected_counter()
        self.tree.update_idletasks()

    # ----------------------- SDK init -----------------------
    def init_sdk(self):
        log_line("Initializing Taegis SDK...")
        if not self.client_id.get().strip() or not self.client_secret.get().strip():
            messagebox.showerror("Missing Credentials", "Client ID and Secret are required.")
            return False

        region_url = REGION_MAP.get(self.selected_region.get())
        os.environ["CLIENT_ID"] = self.client_id.get().strip()
        os.environ["CLIENT_SECRET"] = self.client_secret.get().strip()
        os.environ["BASE_URL"] = region_url
        log_line(f"BASE_URL set to {region_url}")

        try:
            self.service = GraphQLService()
            log_line("SDK initialized OK.")
            return True
        except Exception as e:
            log_line(f"ERROR during SDK initialization: {e}")
            traceback.print_exc()
            messagebox.showerror("SDK Error", f"SDK initialization failed:\n{e}")
            return False

    # ----------------------- CQL -----------------------
    def build_cql(self, mode: str) -> str:
        if mode == "open":
            return "WHERE status = 'OPEN' AND deleted_at IS NULL EARLIEST=-90d | sort updated_at desc"
        return "WHERE deleted_at IS NULL EARLIEST=-90d | sort updated_at desc"

    # ----------------------- Load cases -----------------------
    def load_cases_v2(self, mode: str = "open", reset_page: bool = False):
        log_line(f"load_cases_v2(mode={mode}, reset_page={reset_page})")
        self.last_mode = mode

        if not self.init_sdk():
            log_line("SDK init failed.")
            return

        if reset_page:
            self.page_num = 1

        self.tree.delete(*self.tree.get_children())
        self._rows_cache.clear()
        self.selected_map = {iid: sel for iid, sel in self.selected_map.items()}  # keep
        self.results_info.set("")
        self.update_selected_counter()

        cql = self.build_cql(mode)
        try:
            page = self.page_num
            per_page = int(self.per_page_var.get())
            log_line(f"CQL query page={page} per_page={per_page}\n{cql}")

            inv_out = self.service.investigations2.query.investigations_v2(
                InvestigationsV2Arguments(page=page, per_page=per_page, cql=cql)
            )

            investigations = getattr(inv_out, "investigations", None)
            self.total_count = getattr(inv_out, "total_count", None)

            if not investigations:
                self.results_info.set("No cases found for this filter/page.")
                messagebox.showinfo("No Cases", "No cases found for this filter/page.")
                return

            def clean_status(s):
                if s is None: return ""
                s = str(s)
                return s.split(".")[-1] if "." in s else s

            def to_str_time(t):
                if t is None: return ""
                if isinstance(t, datetime): return t.strftime("%Y-%m-%d %H:%M:%S")
                try: return str(t)[:19].replace("T", " ")
                except Exception: return str(t)

            for idx, inv in enumerate(investigations):
                get = lambda obj, n1, n2=None: getattr(obj, n1, None) if hasattr(obj, n1) else (getattr(obj, n2, None) if n2 else None)
                cid = get(inv, "id") or get(inv, "investigation_id") or get(inv, "uuid") or get(inv, "short_id") or f"row{idx}"
                short_id = get(inv, "short_id") or get(inv, "shortId") or ""
                title = get(inv, "title") or get(inv, "name") or "(No Title)"
                status = clean_status(get(inv, "status"))
                updated = get(inv, "updated_at") or get(inv, "updatedAt")
                updated_s = to_str_time(updated)

                self._rows_cache.append({
                    'id': str(cid),
                    'short_id': short_id,
                    'title': title,
                    'status': status,
                    'updated_at': updated_s,
                })

            shown = len(self._rows_cache)
            tc = self.total_count if self.total_count is not None else "?"
            self.results_info.set(f"Loaded {shown} (page {self.page_num}) of total_count={tc}")

            # Render all, then apply existing filter if present
            self.render_rows(self._rows_cache)
            if self.filter_var.get().strip():
                self.apply_filter()

        except Exception as e:
            log_line(f"ERROR querying Investigations v2: {e}")
            traceback.print_exc()
            messagebox.showerror("API Error", f"Failed to load v2 cases:\n{e}")

    # ----------------------- Copy/Export -----------------------
    def get_selected_ids(self):
        return [cid for cid, sel in self.selected_map.items() if sel]

    def copy_selected_ids(self):
        # NEW in v1.0.1: Copy **Short IDs** for selected rows on the current (possibly filtered) view
        rows = self.tree.get_children()
        short_ids = []
        for iid in rows:
            if self.selected_map.get(iid, False):
                vals = self.tree.item(iid, "values")
                # values: (checkbox, short_id, title, status, updated_at)
                sid = vals[1] if len(vals) > 1 else ""
                if sid:
                    short_ids.append(str(sid))
        if not short_ids:
            messagebox.showinfo("Copy IDs", "No rows selected (or no Short IDs available).")
            return
        s = ",".join(short_ids)
        self.root.clipboard_clear()
        self.root.clipboard_append(s)
        messagebox.showinfo("Copy IDs", f"Copied {len(short_ids)} Short ID(s) to clipboard.")

    def export_csv_current_page(self):
        rows = self.tree.get_children()
        if not rows:
            messagebox.showinfo("Export CSV", "No cases on this page.")
            return
        suggested = "taegis_cases_page.csv"
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=suggested,
                                            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["id (guid)", "short_id", "title", "status", "updated_at", "selected"])
                for iid in rows:
                    vals = self.tree.item(iid, "values")
                    short_id = vals[1] if len(vals) > 1 else ""
                    title = vals[2] if len(vals) > 2 else ""
                    status = vals[3] if len(vals) > 3 else ""
                    updated = vals[4] if len(vals) > 4 else ""
                    selected = self.selected_map.get(iid, False)
                    w.writerow([iid, short_id, title, status, updated, selected])
            messagebox.showinfo("Export CSV", f"Wrote {len(rows)} rows to:\n{path}")
        except Exception as e:
            log_line(f"export_csv_current_page error: {e}")
            messagebox.showerror("Export CSV", f"Failed to write CSV:\n{e}")

    # ----------------------- Apply status + comment -----------------------
    def apply_status_to_selected(self):
        if not self.init_sdk():
            log_line("SDK init failed in apply_status_to_selected.")
            return

        ids_ = self.get_selected_ids()
        if not ids_:
            messagebox.showwarning("No Selection", "Select at least one case.")
            return

        label = self.selected_status.get()
        new_status = STATUS_TO_ENUM.get(label, label.strip().upper().replace(" ", "_"))
        user_comment = self.note_entry.get("1.0", tk.END).strip()

        # Always brand the update in the comment step
        if user_comment:
            comment_to_post = f"{user_comment}\n\n— {BRAND}"
        else:
            comment_to_post = f"Status set to {new_status} — {BRAND}"

        if label.startswith(CLOSED_PREFIX) and not user_comment:
            messagebox.showwarning("Comment Required", "Please enter a comment when choosing a Closed status.")
            return

        preview = (
            f"Apply this status to {len(ids_)} case(s):\n\n"
            f"Status: {new_status}\n"
            f"Comment to post: {comment_to_post if comment_to_post else '(none)'}\n\nProceed?"
        )
        if not messagebox.askyesno("Confirm Apply", preview):
            return

        mutation_update_status = """
        mutation UpdateInvestigationV2($input: UpdateInvestigationV2Input!) {
          updateInvestigationV2(input: $input) { id status title }
        }
        """

        mutation_add_comment = f"""
        mutation AddComment($input: {COMMENT_INPUT_TYPE}!) {{
          {COMMENT_MUTATION_NAME}(input: $input) {{ id }}
        }}
        """

        failures = []
        comment_failures = []

        for cid in ids_:
            # 1) Status
            try:
                res = self.service.core.execute(
                    query_string=mutation_update_status,
                    variables={"input": {"id": cid, "status": new_status}},
                )
                log_line(f"STATUS OK for {cid}: {res}")
            except Exception as e:
                log_line(f"STATUS update failed for {cid}: {e}")
                failures.append(cid)
                continue

            # 2) Comment (always post brand)
            try:
                vars_input = {COMMENT_INPUT_ID_FIELD: cid, COMMENT_INPUT_BODY_FIELD: comment_to_post}
                res = self.service.core.execute(query_string=mutation_add_comment, variables={"input": vars_input})
                log_line(f"COMMENT {COMMENT_MUTATION_NAME} OK for {cid}: {res}")
            except Exception as e:
                log_line(f"COMMENT {COMMENT_MUTATION_NAME} failed for {cid}: {e}")
                comment_failures.append(cid)

        # Summaries
        if failures:
            win = tk.Toplevel(self.root)
            win.title("Apply Errors (details)")
            win.geometry("740x360")
            txt = tk.Text(win, wrap="word")
            txt.pack(fill="both", expand=True)
            txt.insert("1.0", "Some cases failed to update status:\n")
            for cid in failures:
                txt.insert("end", f"- {cid}\n")
            txt.insert("end", "\nSee taegis_case_manager.log for details.")
            txt.configure(state="disabled")
            tk.Button(win, text="OK", command=win.destroy).pack(pady=8)
        else:
            if comment_failures:
                messagebox.showwarning(
                    "Partial Success",
                    "Status was updated for all selected cases, but the branded Comment could not be added for some.\n\n"
                    "Open taegis_case_manager.log and look for COMMENT entries for details."
                )
            else:
                messagebox.showinfo("Success", f"Applied status '{new_status}' to {len(ids_)} case(s) and posted branded comment.")

        self.load_cases_v2(mode=self.last_mode, reset_page=False)

    def close_cases_v2_safe(self):
        return self.apply_status_to_selected()

    # ----------------------- Pagination -----------------------
    def next_page(self):
        try:
            if self.total_count is not None:
                per_page = int(self.per_page_var.get())
                max_page = max(1, (self.total_count + per_page - 1) // per_page)
                if self.page_num >= max_page:
                    messagebox.showinfo("End", "You are on the last page.")
                    return
            self.page_num += 1
            self.load_cases_v2(mode=self.last_mode, reset_page=False)
        except Exception as e:
            log_line(f"next_page error: {e}")

    def prev_page(self):
        try:
            if self.page_num <= 1:
                messagebox.showinfo("Start", "You are on the first page.")
                return
            self.page_num -= 1
            self.load_cases_v2(mode=self.last_mode, reset_page=False)
        except Exception as e:
            log_line(f"prev_page error: {e}")

    def on_per_page_change(self):
        try:
            self.page_num = 1
            self.load_cases_v2(mode=self.last_mode, reset_page=False)
        except Exception as e:
            log_line(f"on_per_page_change error: {e}")

# =============================================================================
# Main entry
# =============================================================================
log_line("Creating TK window...")
root = tk.Tk()
app = TaegisCaseManagerApp(root)
log_line("Entering TK mainloop...")
root.mainloop()
log_line("Mainloop exited.")
# ============================== END OF FILE (v1.0.1) ===============================
