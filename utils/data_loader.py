"""
Data loader for Premier League stats.
Run fetch_data.py once first to populate the data/ folder.
"""

import pandas as pd
import numpy as np
import os
import streamlit as st


@st.cache_data(ttl=86400)
def load_player_data() -> pd.DataFrame:
    standard_path = "data/pl_standard.csv"
    shooting_path = "data/pl_shooting.csv"
    passing_path  = "data/pl_passing.csv"

    if not os.path.exists(standard_path):
        st.info("💡 Run `python fetch_data.py` once to load the full dataset. Using sample data for now.")
        return load_sample_data()

    std = pd.read_csv(standard_path)
    std = std.rename(columns={"Player": "player", "Squad": "team", "Pos": "pos", "Age": "age"})

    if os.path.exists(shooting_path):
        shoot = pd.read_csv(shooting_path).rename(columns={"Player": "player", "Squad": "team"})
        std = std.merge(shoot, on=["player", "team"], how="left", suffixes=("", "_sh"))
        std = std[[c for c in std.columns if not c.endswith("_sh")]]

    if os.path.exists(passing_path):
        pas = pd.read_csv(passing_path).rename(columns={"Player": "player", "Squad": "team"})
        std = std.merge(pas, on=["player", "team"], how="left", suffixes=("", "_pa"))
        std = std[[c for c in std.columns if not c.endswith("_pa")]]

    return clean_and_engineer(std)


def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]

    rename_map = {
        'gls': 'goals', 'ast': 'assists', 'g+a': 'goal_contributions',
        'xg': 'xg', 'xag': 'xa', '90s': 'nineties',
        'prgp': 'progressive_passes', 'prgc': 'progressive_carries',
        'performance_gls': 'goals', 'performance_ast': 'assists',
        'expected_xg': 'xg', 'expected_xag': 'xa', 'playing_time_90s': 'nineties',
        'progression_prgp': 'progressive_passes', 'progression_prgc': 'progressive_carries',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    numeric_cols = ['goals', 'assists', 'xg', 'xa', 'nineties',
                    'goals_per90', 'assists_per90', 'xg_per90', 'xa_per90',
                    'progressive_passes', 'progressive_carries']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'nineties' in df.columns:
        df = df[df['nineties'] >= 3]

    if 'nineties' in df.columns:
        for base in ['goals', 'assists', 'xg', 'xa', 'progressive_passes']:
            per90_col = f'{base}_per90'
            if per90_col not in df.columns and base in df.columns:
                df[per90_col] = (df[base] / df['nineties']).round(3)

    if 'goals' in df.columns and 'assists' in df.columns:
        df['goal_contributions'] = df['goals'] + df['assists']

    if 'goals' in df.columns and 'xg' in df.columns:
        df['xg_overperformance'] = (df['goals'] - df['xg']).round(3)

    if 'pos' in df.columns:
        pos_map = {'GK': 'Goalkeeper', 'DF': 'Defender', 'MF': 'Midfielder', 'FW': 'Forward'}
        df['position_group'] = df['pos'].str[:2].map(pos_map).fillna('Unknown')

    df = df.dropna(subset=['player'])
    return df.reset_index(drop=True)


def load_sample_data() -> pd.DataFrame:
    players = [
        ("Erling Haaland","Manchester City","FW",23,31.2,27,5,24.5,4.2,38,85),
        ("Cole Palmer","Chelsea","MF",21,33.1,22,11,14.2,8.1,125,96),
        ("Alexander Isak","Newcastle United","FW",24,24.3,21,4,17.8,3.1,22,68),
        ("Ollie Watkins","Aston Villa","FW",28,34.8,19,13,16.3,7.4,45,92),
        ("Mohamed Salah","Liverpool","FW",31,32.4,18,10,17.1,9.2,88,110),
        ("Son Heung-min","Tottenham","FW",31,32.0,17,10,14.6,6.5,72,95),
        ("Phil Foden","Manchester City","MF",23,32.6,19,8,15.3,7.8,138,118),
        ("Jarrod Bowen","West Ham","FW",27,33.2,16,7,13.2,6.0,68,88),
        ("Bukayo Saka","Arsenal","FW",22,35.0,16,9,14.8,9.6,145,125),
        ("Bruno Fernandes","Manchester United","MF",29,33.5,10,8,12.4,9.2,165,88),
        ("Martin Odegaard","Arsenal","MF",25,32.1,8,10,9.3,8.5,210,102),
        ("Trent Alexander-Arnold","Liverpool","DF",25,31.5,9,13,6.2,9.1,285,68),
        ("Declan Rice","Arsenal","MF",25,34.0,7,8,5.8,5.2,248,95),
        ("Rodri","Manchester City","MF",27,30.3,8,5,4.8,3.8,252,72),
        ("James Maddison","Tottenham","MF",27,25.3,8,8,8.3,6.8,178,104),
        ("Virgil van Dijk","Liverpool","DF",32,33.8,3,3,2.8,1.4,185,22),
        ("Jean-Philippe Mateta","Crystal Palace","FW",27,28.5,16,4,13.5,3.2,22,72),
        ("Joao Pedro","Brighton","FW",22,26.4,11,4,10.8,3.8,42,86),
        ("Gabriel Magalhaes","Arsenal","DF",26,33.5,4,1,3.2,0.8,188,22),
        ("David Raya","Arsenal","GK",28,35.0,0,0,0.0,0.0,88,2),
        ("Alisson Becker","Liverpool","GK",31,32.0,0,0,0.0,0.0,72,2),
        ("Ederson","Manchester City","GK",30,34.0,0,1,0.0,0.0,95,3),
        ("Nick Pope","Newcastle United","GK",32,28.0,0,0,0.0,0.0,64,2),
        ("Andrew Robertson","Liverpool","DF",29,29.5,2,8,1.2,4.8,210,42),
    ]
    df = pd.DataFrame(players, columns=[
        'player','team','pos','age','nineties',
        'goals','assists','xg','xa','progressive_passes','progressive_carries'
    ])
    df['goal_contributions'] = df['goals'] + df['assists']
    df['goals_per90']   = (df['goals']   / df['nineties']).round(3)
    df['assists_per90'] = (df['assists'] / df['nineties']).round(3)
    df['xg_per90']      = (df['xg']     / df['nineties']).round(3)
    df['xa_per90']      = (df['xa']     / df['nineties']).round(3)
    df['xg_overperformance'] = (df['goals'] - df['xg']).round(3)
    pos_map = {'GK':'Goalkeeper','DF':'Defender','MF':'Midfielder','FW':'Forward'}
    df['position_group'] = df['pos'].map(pos_map)
    return df
