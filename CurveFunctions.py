import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt



def GetUserInputs():

    try:
        Equipment_Name = str(input("What is the name of the Equipment? "))
    except:
        print("Invalid Name.")
        Equipment_Name = ''

    try:
        margin_Surge = float(input("What percentage margin for the Surge Line? "))
    except:
        print("Invalid input. Must be a number. \n Defaulting to 10%.")
        margin_Surge = 10
    try:
        margin_StoneWall = float(input("What percentage margin for the Stone Wall Line? "))
    except:
        print("Invalid input. Must be a number. \n Defaulting to 10%.")
        margin_StoneWall = 10

    try:
        Head_Unit = str(input("What is the unit for head? (m: Meter, kJ/kg: Kilojoule per kilogram) ")).lower()
        if Head_Unit == 'kj/kg':
            Head_Unit = 'kJ/kg'
        elif Head_Unit not in ['m', 'kJ/kg']:
            print("Invalid input. Must be 'm' or 'kJ/kg'. \n Defaulting to kJ/kg.")
            Head_Unit = 'kJ/kg'
    except:
        print("Invalid input. Must be a string. \n Defaulting to kJ/kg.")
        Head_Unit = 'kJ/kg'
    try:
        Flow_Unit = str(input("What is the unit for flow? (m3/h: Cubic meter per hour, m3/d: Cubic meter per day) ")).lower()
        if Flow_Unit not in ['m3/h', 'm3/d']:
            print("Invalid input. Must be 'm3/h' or 'm3/d'. \n Defaulting to m3/h.")
            Flow_Unit = 'm3/h'
    except:
        print("Invalid input. Must be a string. \n Defaulting to m3/h.")
        Flow_Unit = 'm3/h'

    return Equipment_Name, margin_Surge, margin_StoneWall, Head_Unit, Flow_Unit

def GetProcessCurves(folder: str) -> pd.DataFrame:
    folder = Path(folder)
    files = list(folder.glob("*"))
    if files[0].suffix == ".csv":
        csv_files = sorted(folder.glob("*.csv"))
        first_df = pd.read_csv(csv_files[0], delimiter=";")
        main_header = list(first_df.columns)
        dfs = [first_df]
        for file in csv_files[1:]:
            # Reuse the first CSV header as canonical columns for all appended data.
            df = pd.read_csv(file, delimiter=";", header=0, names=main_header)
            dfs.append(df)
    elif files[0].suffix == ".tsv":
        tsv_files = sorted(folder.glob("*.tsv"))
        first_df = pd.read_csv(tsv_files[0], delimiter="\t")
        main_header = list(first_df.columns)
        dfs = [first_df]
        for file in tsv_files[1:]:
            # Reuse the first TSV header as canonical columns for all appended data.
            df = pd.read_csv(file, delimiter="\t", header=0, names=main_header)
            dfs.append(df)
    else:
        raise ValueError("Unsupported file type. Please provide a folder containing exclusively CSV or TSV files.")

    return pd.concat(dfs, ignore_index=True)



def GetSurgeLine(margin: float, curves: pd.DataFrame, EquipmentName: str, Head_Unit: str = "kJ/kg", Flow_Unit: str = "m3/h") -> np.ndarray:
    #Get Column names for speed, flow and head. Assumes they contain "Speed", "Flow" and "Head" respectively.
    speed_column = next((col for col in curves.columns if "Speed" in col), None)
    Flow_column = next((col for col in curves.columns if "Flow" in col), None)
    Head_column = next((col for col in curves.columns if "Head" in col), None)

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
    pd.DataFrame({'b': [Surge_Line.convert().coef[0]], 'a': [Surge_Line.convert().coef[1]]}).to_csv(f"Surge_Line/Surge_Line_Equation_{EquipmentName}_{margin}%.tsv", sep='\t', index=False, header=True)

    # Generate surge line points for plotting and saving.
    SurgeFlow = np.linspace(LowSpeed_Surge_Flow * 0.95, HighSpeed_Surge_Flow * 1.05, 10)
    Surge_Head = Surge_Line(SurgeFlow)
    pd.DataFrame({f'Flow [{Flow_Unit}]': SurgeFlow, f'Head [{Head_Unit}]': Surge_Head}).to_csv(f"Surge_Line/Surge_Line_{EquipmentName}_{margin}%.tsv", sep='\t', index=False, header=True)

    # Plot the curves and surge line.
    fig, ax = plt.subplots()
    for speed, speed_df in Speed_df.items():
        ax.plot(speed_df[Flow_column], speed_df[Head_column], label=f"{speed:.0f} rpm Curve")
    ax.plot(SurgeFlow, Surge_Head, label=f"Surge Line {margin}%")
    ax.set_xlabel(f"Flow [{Flow_Unit}]")
    ax.set_ylabel(f"Head [{Head_Unit}]")
    ax.legend()
    ax.set_title(f"{EquipmentName}")
    plt.savefig(f"Plots/SurgeLine_{EquipmentName}_{margin}%.png")
    return np.array([SurgeFlow, Surge_Head])

def GetStoneWallLine(margin: float, curves: pd.DataFrame, EquipmentName: str, Head_Unit: str = "kJ/kg", Flow_Unit: str = "m3/h") -> np.ndarray:
    # Get Column names for speed, flow and head. Assumes they contain "Speed", "Flow" and "Head" respectively.
    speed_column = next((col for col in curves.columns if "Speed" in col), None)
    Flow_column = next((col for col in curves.columns if "Flow" in col), None)
    Head_column = next((col for col in curves.columns if "Head" in col), None)

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
    pd.DataFrame({'b': [Stonewall_Line.convert().coef[0]], 'a': [Stonewall_Line.convert().coef[1]]}).to_csv(f"StoneWall_Line/Stonewall_Line_Equation_{EquipmentName}_{margin}%.tsv", sep='\t', index=False, header=True)

    # Generate stonewall line points for plotting and saving.
    StonewallFlow = np.linspace(LowSpeed_Stonewall_Flow * 0.95, HighSpeed_Stonewall_Flow * 1.05, 10)
    Stonewall_Head = Stonewall_Line(StonewallFlow)
    pd.DataFrame({f'Flow [{Flow_Unit}]': StonewallFlow, f'Head [{Head_Unit}]': Stonewall_Head}).to_csv(f"StoneWall_Line/Stonewall_Line_{EquipmentName}_{margin}%.tsv", sep='\t', index=False, header=True)
    
    # Plot the curves and stonewall line.
    fig, ax = plt.subplots()
    for speed, speed_df in Speed_df.items():
        ax.plot(speed_df[Flow_column], speed_df[Head_column], label=f"{speed:.0f} rpm Curve")
    ax.plot(StonewallFlow, Stonewall_Head, label=f"Stonewall Line {margin}%")
    ax.set_xlabel(f"Flow [{Flow_Unit}]")
    ax.set_ylabel(f"Head [{Head_Unit}]")
    ax.legend()
    ax.set_title(f"{EquipmentName}")
    plt.savefig(f"Plots/StonewallLine_{EquipmentName}_{margin}%.png")
    return np.array([StonewallFlow, Stonewall_Head])

def PlotBothConstainingLines(SurgeLine: np.ndarray, StoneWallLine: np.ndarray, curves: pd.DataFrame, EquipmentName: str, margin_Surge: float, margin_StoneWall: float, Head_Unit: str = "kJ/kg", Flow_Unit: str = "m3/h") -> int:
    # Get Column names for speed, flow and head. Assumes they contain "Speed", "Flow" and "Head" respectively.
    speed_column = next((col for col in curves.columns if "Speed" in col), None)
    Flow_column = next((col for col in curves.columns if "Flow" in col), None)
    Head_column = next((col for col in curves.columns if "Head" in col), None)

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
    ax.set_xlabel(f"Flow [{Flow_Unit}]")
    ax.set_ylabel(f"Head [{Head_Unit}]")
    ax.legend()
    ax.set_title(f"{EquipmentName}")
    plt.savefig(f"Plots/ConstrainingLines_{EquipmentName}.png")
    return 0
