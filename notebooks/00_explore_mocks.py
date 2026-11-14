# %% [markdown]
# # Explore mock contracts

# %%
import json
from pathlib import Path

ROOT = Path.cwd() if (Path.cwd() / "contracts").exists() else Path.cwd().parent
fields = json.loads((ROOT / "contracts/mock/fields.geojson").read_text())

# %%
for f in fields["features"]:
    p = f["properties"]
    print(p["field_id"], p["area_ha"], p["crop_history"]["2025"])
