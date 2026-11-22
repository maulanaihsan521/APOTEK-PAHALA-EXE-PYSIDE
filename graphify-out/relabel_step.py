"""Terapkan label komunitas yang mudah dibaca ke graph.json dan laporan.

Dipakai setelah ``graphify update .`` karena pelabelan LLM tidak tersedia di
lingkungan build. Label dipetakan berdasarkan ID komunitas hasil clustering
terakhir; perbarui peta ini bila jumlah/urutan komunitas berubah drastis.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

LABELS = {
    0: "Mobile PWA App Shell",
    1: "Database Models and Test Fixtures",
    2: "Desktop Shared UI Components",
    3: "Desktop Shell and Navigation",
    4: "Desktop Pages and Shared UI",
    5: "Desktop Chart Components",
    6: "Desktop UI Primitives and Pages",
    7: "Desktop Reports Page and Formatters",
    8: "Desktop Widgets",
    9: "Prediction API and Service",
    10: "Settings and Backup API",
    11: "Mobile Frontend Dependencies",
    12: "Sales and Dashboard API",
    13: "Backend Models and Core APIs",
    14: "Desktop Utils and Stock Widgets",
    15: "Windows 7 Build Transform",
    16: "Export Documents Service",
    17: "Real Dataset Importer and ML Training",
    18: "Desktop Settings Page",
    19: "Desktop Main Window",
    20: "Pytest Fixtures",
    21: "Desktop Prediction Page",
    22: "Procurement and Activity API",
    23: "Desktop API Client",
    24: "Desktop Procurement Page",
    25: "Prediction ML Pipeline",
    26: "Desktop Stock Page",
    27: "Desktop Dashboard Page",
    28: "Import Wizard API",
    29: "Desktop Weather Page",
    30: "Desktop Login Page",
    31: "Backend Startup and Health",
    32: "API Tests and Import Helpers",
    33: "Desktop Sales, Reports, and Sale Dialog",
    34: "Reports Export Service",
    35: "Desktop Page Actions and Loading",
    36: "TypeScript Config",
    37: "Desktop Medicine and User Dialogs",
    38: "Desktop Weather Loaders and Async Helpers",
    39: "Desktop Theme",
    40: "User Guide Documentation",
    41: "Desktop API Helpers and Downloads",
    42: "Desktop Settings Event Handlers",
    43: "Async Worker",
    44: "Asset Copy Scripts",
    45: "Desktop Preferences and Paths",
    46: "Desktop Toast",
    47: "Backend Launcher",
    48: "Work Log 2026-11-21",
    49: "Login Documentation",
    50: "Global Error Handlers",
    51: "Notification Bell and Navigation",
    54: "Windows 7 Documentation",
    56: "README and Project Overview",
    58: "API Schemas and Authentication",
    59: "Architecture Documentation",
    60: "Desktop Components Package",
    61: "Desktop Core Package",
    62: "Desktop App Package",
    63: "Desktop Pages Package",
    64: "Tailwind Config",
    65: "Windows 7 Build Script",
    66: "Backend Core Package",
    67: "Database Package",
    68: "Backend App Package",
    69: "ML Package",
    70: "Models Package",
    71: "Schemas Package",
    72: "Seed Package",
    73: "Services Package",
    74: "Tests Package",
    75: "PostCSS Config",
    76: "Vite Env Types",
    79: "Testing Documentation",
    81: "Windows Run Guide",
    82: "Desktop Confirmation Dialogs",
    83: "Project Documentation Index",
}

graph_path = Path("graphify-out/graph.json")
report_path = Path("graphify-out/GRAPH_REPORT.md")
labels_path = Path("graphify-out/.graphify_labels.json")

graph = json.loads(graph_path.read_text(encoding="utf-8"))
counts: dict[int, int] = {}
for node in graph["nodes"]:
    cid = node.get("community")
    if cid is None:
        continue
    counts[cid] = counts.get(cid, 0) + 1
    if cid in LABELS:
        node["community_name"] = LABELS[cid]
graph_path.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")
labels_path.write_text(json.dumps({str(k): v for k, v in LABELS.items()}, ensure_ascii=False), encoding="utf-8")

text = report_path.read_text(encoding="utf-8")
for cid, name in LABELS.items():
    text = re.sub(
        rf'^### Community {cid} - ".*"$',
        f'### Community {cid} - "{name}"',
        text,
        flags=re.M,
    )

shown = [int(m) for m in re.findall(r"^### Community (\d+) - ", text, flags=re.M)]
ordered = sorted(shown, key=lambda cid: (-counts.get(cid, 0), cid))
hubs = "\n".join(f"- {LABELS.get(cid, 'Community ' + str(cid))}" for cid in ordered)
text = re.sub(
    r"## Community Hubs \(Navigation\)\n(?:- .*\n)+",
    f"## Community Hubs (Navigation)\n{hubs}\n",
    text,
)
report_path.write_text(text, encoding="utf-8")
print(f"labeled {sum(1 for cid in LABELS if cid in counts)} communities; {len(shown)} headings updated")
