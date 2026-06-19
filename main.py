import CurveFunctions

def main():
    try:
        Equipment_Name = str(input("What is the name of the Equipment? "))
    except:
        print("Invalid Name.")
        Equipment_Name = ''

    try:
        margin = float(input("What percentage margin? "))
    except:
        print("Invalid input. Must be a number.")
        margin = 10
    
    Curves = CurveFunctions.GetProcessCurves("Curves")

    CurveFunctions.GetSurgeLine(margin, Curves, Equipment_Name)
    
    CurveFunctions.GetStoneWallLine(margin, Curves, Equipment_Name)
    return 0
    


if __name__ == "__main__":
    main()
