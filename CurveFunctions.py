import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


def GetProcessCurves(folder: str) -> pd.DataFrame:
    csv_folder = Path(folder)
    csv_files = sorted(csv_folder.glob("*.csv"))
    if not csv_files:
        return pd.DataFrame()

    first_df = pd.read_csv(csv_files[0], delimiter=";")
    main_header = list(first_df.columns)
    dfs = [first_df]

    for file in csv_files[1:]:
        # Reuse the first CSV header as canonical columns for all appended data.
        df = pd.read_csv(file, delimiter=";", header=0, names=main_header)
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)



def GetSurgeLine(margin: float, curves: pd.DataFrame, EquipmentName: str) -> np.ndarray:
    #Get Column names for speed, flow and head. Assumes they start with "Speed", "Flow" and "Head" respectively.
    speed_column = next((col for col in curves.columns if col.startswith("Speed")), None)
    Flow_column = next((col for col in curves.columns if col.startswith("Flow")), None)
    Head_column = next((col for col in curves.columns if col.startswith("Head")), None)

    # Get the lowest and highest speed curves.
    Lowest_Speed = curves[speed_column].min() if speed_column else None
    Low_Speed_df = curves[curves[speed_column] == Lowest_Speed]

    Highest_Speed = curves[speed_column].max() if speed_column else None
    High_Speed_df = curves[curves[speed_column] == Highest_Speed]

    # Build a dataframe per speed for all speeds.
    unique_speeds = np.sort(curves[speed_column].dropna().unique()) if speed_column else []
    Speeds = [speed for speed in unique_speeds if speed]
    Speed_df = {
        speed: curves[curves[speed_column] == speed].copy()
        for speed in Speeds
    }

    # Calculate surge line points for low and high speed curves.
    Low_Speed_Low_Flow = Low_Speed_df[Flow_column].min()
    Low_Speed_High_Flow = Low_Speed_df[Flow_column].max()
    LowSpeed_Surge_Flow = Low_Speed_Low_Flow + (Low_Speed_High_Flow - Low_Speed_Low_Flow) * (margin / 100)
    LowSpeed_Surge_Head = np.interp(LowSpeed_Surge_Flow, Low_Speed_df[Flow_column], Low_Speed_df[Head_column])
    
    High_Speed_Low_Flow = High_Speed_df[Flow_column].min()
    High_Speed_High_Flow = High_Speed_df[Flow_column].max()
    HighSpeed_Surge_Flow = High_Speed_Low_Flow + (High_Speed_High_Flow - High_Speed_Low_Flow) * (margin / 100)
    HighSpeed_Surge_Head = np.interp(HighSpeed_Surge_Flow, High_Speed_df[Flow_column], High_Speed_df[Head_column])

    # Fit a line between the two surge points.
    Surge_Line = np.polynomial.Polynomial.fit([LowSpeed_Surge_Flow, HighSpeed_Surge_Flow], [LowSpeed_Surge_Head, HighSpeed_Surge_Head], 1)

    # Generate surge line points for plotting and saving.
    SurgeFlow = np.linspace(LowSpeed_Surge_Flow * 0.95, HighSpeed_Surge_Flow * 1.05, 10)
    Surge_Head = Surge_Line(SurgeFlow)
    np.savetxt(f"Surge_Line/Surge_Line_{EquipmentName}_{margin}%.tsv", np.array([SurgeFlow, Surge_Head]).T)

    # Plot the curves and surge line.
    fig, ax = plt.subplots()
    for speed, speed_df in Speed_df.items():
        ax.plot(speed_df[Flow_column], speed_df[Head_column], label=f"{speed:.0f} rpm Curve")
    ax.plot(SurgeFlow, Surge_Head, label=f"Surge Line {margin}%")
    ax.legend()
    ax.set_title(f"{EquipmentName}")
    plt.savefig(f"Plots/SurgeLine_{EquipmentName}_{margin}%.png")
    return np.array([SurgeFlow, Surge_Head])

def GetStoneWallLine(margin: float, curves: pd.DataFrame, EquipmentName: str) -> np.ndarray:
    # Get Column names for speed, flow and head. Assumes they start with "Speed", "Flow" and "Head" respectively.
    speed_column = next((col for col in curves.columns if col.startswith("Speed")), None)
    Flow_column = next((col for col in curves.columns if col.startswith("Flow")), None)
    Head_column = next((col for col in curves.columns if col.startswith("Head")), None)

    # Get the lowest and highest speed curves.
    Lowest_Speed = curves[speed_column].min() if speed_column else None
    Low_Speed_df = curves[curves[speed_column] == Lowest_Speed]

    Highest_Speed = curves[speed_column].max() if speed_column else None
    High_Speed_df = curves[curves[speed_column] == Highest_Speed]

    # Build a dataframe per speed for all speeds.
    unique_speeds = np.sort(curves[speed_column].dropna().unique()) if speed_column else []
    Speeds = [speed for speed in unique_speeds if speed]
    Speed_df = {
        speed: curves[curves[speed_column] == speed].copy()
        for speed in Speeds
    }

    # Calculate stonewall line points for low and high speed curves.
    Low_Speed_Low_Flow = Low_Speed_df[Flow_column].min()
    Low_Speed_High_Flow = Low_Speed_df[Flow_column].max()
    LowSpeed_Stonewall_Flow = Low_Speed_High_Flow - (Low_Speed_High_Flow - Low_Speed_Low_Flow) * (margin / 100)
    LowSpeed_Stonewall_Head = np.interp(LowSpeed_Stonewall_Flow, Low_Speed_df[Flow_column], Low_Speed_df[Head_column])
    
    High_Speed_Low_Flow = High_Speed_df[Flow_column].min()
    High_Speed_High_Flow = High_Speed_df[Flow_column].max()
    HighSpeed_Stonewall_Flow = High_Speed_High_Flow - (High_Speed_High_Flow - High_Speed_Low_Flow) * (margin / 100)
    HighSpeed_Stonewall_Head = np.interp(HighSpeed_Stonewall_Flow, High_Speed_df[Flow_column], High_Speed_df[Head_column])

    # Fit a line between the two stonewall points.
    Stonewall_Line = np.polynomial.Polynomial.fit([LowSpeed_Stonewall_Flow, HighSpeed_Stonewall_Flow], [LowSpeed_Stonewall_Head, HighSpeed_Stonewall_Head], 1)

    # Generate stonewall line points for plotting and saving.
    StonewallFlow = np.linspace(LowSpeed_Stonewall_Flow * 0.95, HighSpeed_Stonewall_Flow * 1.05, 10)
    Stonewall_Head = Stonewall_Line(StonewallFlow)
    np.savetxt(f"StoneWall_Line/Stonewall_Line_{EquipmentName}_{margin}%.tsv", np.array([StonewallFlow, Stonewall_Head]).T)

    # Plot the curves and stonewall line.
    fig, ax = plt.subplots()
    for speed, speed_df in Speed_df.items():
        ax.plot(speed_df[Flow_column], speed_df[Head_column], label=f"{speed:.0f} rpm Curve")
    ax.plot(StonewallFlow, Stonewall_Head, label=f"Stonewall Line {margin}%")
    ax.legend()
    ax.set_title(f"{EquipmentName}")
    plt.savefig(f"Plots/StonewallLine_{EquipmentName}_{margin}%.png")
    return np.array([StonewallFlow, Stonewall_Head])

def PlotBothConstainingLines(SurgeLine: np.ndarray, StoneWallLine: np.ndarray, curves: pd.DataFrame, EquipmentName: str, margin_Surge: float, margin_StoneWall: float) -> int:
    # Get Column names for speed, flow and head. Assumes they start with "Speed", "Flow" and "Head" respectively.
    speed_column = next((col for col in curves.columns if col.startswith("Speed")), None)
    Flow_column = next((col for col in curves.columns if col.startswith("Flow")), None)
    Head_column = next((col for col in curves.columns if col.startswith("Head")), None)

    # Build a dataframe per speed for all speeds.
    unique_speeds = np.sort(curves[speed_column].dropna().unique()) if speed_column else []
    Speeds = [speed for speed in unique_speeds if speed]
    Speed_df = {
        speed: curves[curves[speed_column] == speed].copy()
        for speed in Speeds
    }
    # Plot the curves and both lines.
    fig, ax = plt.subplots()
    for speed, speed_df in Speed_df.items():
        ax.plot(speed_df[Flow_column], speed_df[Head_column], label=f"{speed:.0f} rpm Curve")
    ax.plot(SurgeLine[0], SurgeLine[1], label=f"Surge Line {margin_Surge}%")
    ax.plot(StoneWallLine[0], StoneWallLine[1], label=f"Stonewall Line {margin_StoneWall}%")
    ax.legend()
    ax.set_title(f"{EquipmentName}")
    plt.savefig(f"Plots/ConstrainingLines_{EquipmentName}.png")
    return 0
