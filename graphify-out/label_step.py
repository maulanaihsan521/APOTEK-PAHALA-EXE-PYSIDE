import json
from pathlib import Path

LABELS = {
    0: "Mobile PWA App Shell",
    1: "Import Wizard API",
    2: "Auth and User API",
    3: "Desktop Shell Navigation",
    4: "Desktop Branding Assets",
    5: "Desktop Chart Components",
    6: "Desktop UI Primitives",
    7: "Desktop Dialogs",
    8: "Desktop Widgets",
    9: "Formatting and Badges",
    10: "Settings and Backup API",
    11: "Mobile Frontend Dependencies",
    12: "Sales API",
    13: "Inventory and Medicine API",
    14: "Desktop Formatters",
    15: "Win7 Code Transform",
    16: "Export Documents Service",
    17: "Real Dataset Importer",
    20: "Notifications and Activity",
    22: "Procurement API",
    23: "Desktop API Client",
    25: "ML Features and Forecast",
    27: "Desktop Dashboard Page",
    28: "Dataset Seeding",
    31: "Backend Startup and Static",
    36: "TypeScript Config",
    37: "Prediction API",
    38: "Prediction Service",
    39: "Desktop Theme",
    40: "Reports API and Service",
    41: "Tests and Static Serving",
    42: "Model Trainer",
    43: "Async Worker",
    44: "Asset Copy Scripts",
}

path = Path("graphify-out/graph.json")
graph = json.loads(path.read_text(encoding="utf-8"))
for node in graph["nodes"]:
    cid = node.get("community")
    if cid in LABELS:
        node["community_name"] = LABELS[cid]
path.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")

Path("graphify-out/.graphify_labels.json").write_text(
    json.dumps({str(k): v for k, v in LABELS.items()}, ensure_ascii=False), encoding="utf-8"
)

report = Path("graphify-out/GRAPH_REPORT.md")
text = report.read_text(encoding="utf-8")
for cid, name in LABELS.items():
    text = text.replace(f"Community {cid}\n", f"{name}\n")
    text = text.replace(f'Community {cid} - "Community {cid}"', f'Community {cid} - "{name}"')
report.write_text(text, encoding="utf-8")
print("labels applied:", len(LABELS))
