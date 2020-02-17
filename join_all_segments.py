import csv

with open("full_path.csv", "w+") as outfile:
    path = csv.writer(outfile)
    with open("straight_segment.csv", "r") as infile:
        path.writerow("STRAIGHT")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
    with open("A-B_curvy.csv", "r") as infile:
        path.writerow("A-B CURVY")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
    with open("B-C_curvy-conv.csv", "r") as infile:
        path.writerow("B-C CURVY")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
    with open("C-D_curvy.csv", "r") as infile:
        path.writerow("C-D CURVY")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
    with open("D-A_curvy.csv", "r") as infile:
        path.writerow("D-A CURVY")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
    with open("A-B_curvy.csv", "r") as infile:
        path.writerow("A-B CURVY")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
    with open("B-C_curvy-conv.csv", "r") as infile:
        path.writerow("B-C CURVY")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
    with open("C-D_dirt.csv", "r") as infile:
        path.writerow("C-D DIRT")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
    with open("D-A_curvy.csv", "r") as infile:
        path.writerow("D-A CURVY")
        segment = csv.reader(infile)
        for coord in segment:
            if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan":
                path.writerow([coord[0], coord[1]])
