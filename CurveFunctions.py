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



def GetSurgeCurve(margin: float, curves: pd.DataFrame, EquipmentName: str, Head_Unit: str = "kJ/kg", Flow_Unit: str = "m3/h") -> np.ndarray:
    #Get Column names for speed, flow and head. Assumes they contain "Speed", "Flow" and "Head" respectively.
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

    Control_curve_points = []
    
    for speed, speed_df in Speed_df.items():
        speed_polynomial = np.polynomial.Polynomial.fit(speed_df[Flow_column], speed_df[Head_column], 3)
        Control_curve_flow = speed_df[Flow_column].min() + (speed_df[Flow_column].max() - speed_df[Flow_column].min()) * (margin / 100)
        Control_curve_head = speed_polynomial(Control_curve_flow)
        Control_curve_points.append({
            speed_column: speed,
            Flow_column: Control_curve_flow,
            Head_column: Control_curve_head,
        })

    # Practical tabular format: one control point (speed, flow, head) per speed curve.
    Control_Line = pd.DataFrame(Control_curve_points).sort_values(by=speed_column).reset_index(drop=True)


    #Fit a second order polynomial to the surge points for each speed curve.
    Surge_Line = np.polynomial.Polynomial.fit(Control_Line[Flow_column], Control_Line[Head_column], 2)

    #Write the polynomial coefficients to a TSV file for reference.
    pd.DataFrame({'c': [Surge_Line.convert().coef[0]], 'b': [Surge_Line.convert().coef[1]], 'a': [Surge_Line.convert().coef[2]]}).to_csv(f"Surge_Line/Surge_Line_Equation_{EquipmentName}_{margin}%.tsv", sep='\t', index=False, header=True)


    # Generate surge line points for plotting and saving.
    SurgeFlow, Surge_Head = Surge_Line.linspace(20)

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
    plt.close(fig)
    return np.array([SurgeFlow, Surge_Head])

def GetStoneWallCurve(margin: float, curves: pd.DataFrame, EquipmentName: str, Head_Unit: str = "kJ/kg", Flow_Unit: str = "m3/h") -> np.ndarray:
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

    Control_curve_points = []
    
    for speed, speed_df in Speed_df.items():
        speed_polynomial = np.polynomial.Polynomial.fit(speed_df[Flow_column], speed_df[Head_column], 3)
        Control_curve_flow = speed_df[Flow_column].max() - (speed_df[Flow_column].max() - speed_df[Flow_column].min()) * (margin / 100)
        Control_curve_head = speed_polynomial(Control_curve_flow)
        Control_curve_points.append({
            speed_column: speed,
            Flow_column: Control_curve_flow,
            Head_column: Control_curve_head,
        })

    # Practical tabular format: one control point (speed, flow, head) per speed curve.
    Control_Line = pd.DataFrame(Control_curve_points).sort_values(by=speed_column).reset_index(drop=True)


    # Fit a second order polynomial to the stonewall points.
    Stonewall_Line = np.polynomial.Polynomial.fit(Control_Line[Flow_column], Control_Line[Head_column], 2)

    #Write the polynomial coefficients to a TSV file for reference.
    pd.DataFrame({'c': [Stonewall_Line.convert().coef[0]], 'b': [Stonewall_Line.convert().coef[1]], 'a': [Stonewall_Line.convert().coef[2]]}).to_csv(f"StoneWall_Line/Stonewall_Line_Equation_{EquipmentName}_{margin}%.tsv", sep='\t', index=False, header=True)

    # Generate surge line points for plotting and saving.
    StonewallFlow, Stonewall_Head = Stonewall_Line.linspace(20)
    
    pd.DataFrame({f'Flow [{Flow_Unit}]': StonewallFlow, f'Head [{Head_Unit}]': Stonewall_Head}).to_csv(f"StoneWall_Line/StoneWall_Line_{EquipmentName}_{margin}%.tsv", sep='\t', index=False, header=True)

    
    
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
    plt.close(fig)
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
    plt.close(fig)
    return 0
