"""
Converts the Kaggle top5-players.csv into our dashboard schema.
Filters to Premier League only and saves to data/pl_standard.csv
Usage: python fetch_data.py
"""

import pandas as pd

df = pd.read_csv("data/top5-players.csv")

# Filter to Premier League only
df = df[df["Comp"] == "eng Premier League"].copy()
print(f"Premier League players found: {len(df)}")

# Rename columns to match our dashboard schema exactly
df = df.rename(columns={
    "Player": "player",
    "Squad":  "team",
    "Pos":    "pos",
    "Age":    "age",
    "90s":    "nineties",
    "Gls":    "goals",
    "Ast":    "assists",
    "xG":     "xg",
    "xAG":    "xa",
    "PrgP":   "progressive_passes",
    "PrgC":   "progressive_carries",
    "Gls_90": "goals_per90",
    "Ast_90": "assists_per90",
    "xG_90":  "xg_per90",
    "xAG_90": "xa_per90",
})

# Compute missing columns
df["goal_contributions"]  = df["goals"] + df["assists"]
df["xg_overperformance"]  = (df["goals"] - df["xg"]).round(3)

# Simplify position (some entries are "MF,FW" — take first)
df["pos"] = df["pos"].str.split(",").str[0]
pos_map = {"GK": "Goalkeeper", "DF": "Defender", "MF": "Midfielder", "FW": "Forward"}
df["position_group"] = df["pos"].map(pos_map).fillna("Unknown")

# Keep only the columns our dashboard uses
keep = ["player","team","pos","age","nineties","goals","assists","xg","xa",
        "progressive_passes","progressive_carries","goal_contributions",
        "goals_per90","assists_per90","xg_per90","xa_per90",
        "xg_overperformance","position_group"]
df = df[keep]

# Filter min 3 x 90s played
df = df[df["nineties"] >= 3].reset_index(drop=True)

df.to_csv("data/pl_standard.csv", index=False)
print(f"✅ Saved {len(df)} players to data/pl_standard.csv")
print("Run: streamlit run app.py")
