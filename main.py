import CurveFunctions

def main():

    Equipment_Name, margin_Surge, margin_StoneWall = GetUserInputs()
    
    Curves = CurveFunctions.GetProcessCurves("Curves")

    SurgeLine = CurveFunctions.GetSurgeLine(margin_Surge, Curves, Equipment_Name)
    
    StoneWallLine = CurveFunctions.GetStoneWallLine(margin_StoneWall, Curves, Equipment_Name)

    CurveFunctions.PlotBothConstainingLines(SurgeLine, StoneWallLine, Curves, Equipment_Name, margin_Surge, margin_StoneWall)

    return 0
    

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

    return Equipment_Name, margin_Surge, margin_StoneWall


if __name__ == "__main__":
    main()
