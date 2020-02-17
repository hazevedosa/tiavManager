import csv

START_X = 452720.0
START_Y = 322110.0

infile = open("B-C_curvy.csv", "r")
outfile = open("B-C_curvy-conv.csv", "w+")

in_points = csv.reader(infile)
out_points = csv.writer(outfile)

for coord in in_points:
    if len(coord) == 2:
        x = (float(coord[0]) * 100) + START_X
        y = (float(coord[1]) * 100) + START_Y
        out_points.writerow([x, y])

infile.close()
outfile.close()
