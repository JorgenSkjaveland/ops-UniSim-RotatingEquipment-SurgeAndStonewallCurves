import CurveFunctions

def main():

    Equipment_Name, margin_Surge, margin_StoneWall, Head_Unit, Flow_Unit = CurveFunctions.GetUserInputs()
    
    Curves = CurveFunctions.GetProcessCurves("Curves")

    SurgeLine = CurveFunctions.GetSurgeLine(margin_Surge, Curves, Equipment_Name, Head_Unit, Flow_Unit)
    
    StoneWallLine = CurveFunctions.GetStoneWallLine(margin_StoneWall, Curves, Equipment_Name, Head_Unit, Flow_Unit)

    CurveFunctions.PlotBothConstainingLines(SurgeLine, StoneWallLine, Curves, Equipment_Name, margin_Surge, margin_StoneWall, Head_Unit, Flow_Unit)

    return 0
    


if __name__ == "__main__":
    main()
