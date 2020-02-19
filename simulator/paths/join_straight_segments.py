import csv

corners = open("straight_corners.csv", "r")
path = open("straight_segment.csv", "w+")
infile = csv.reader(corners)
outfile = csv.writer(path)
counter = 0
for row in infile:
    if not row[0] == 'x':
        outfile.writerow(row)
    else:
        if counter == 0:
            for y in range(326660, 399180, 100):
                x = (-0.0985934915 * y) + 486766.549
                outfile.writerow([x, y])
        elif counter == 1:
            for x in range(441440, 373850, -100):
                outfile.writerow([x, 404500])
        elif counter == 2:
            for y in range(394660, 321860, -100):
                outfile.writerow([364420, y])
        counter += 1

corners.close()
path.close()
