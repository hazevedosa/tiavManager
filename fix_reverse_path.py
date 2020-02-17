import csv

with open("reverse_path.csv", "r") as infile:
    csv_in = csv.reader(infile)
    with open("fixed_reverse_path.csv", "w+") as outfile:
        csv_out = csv.writer(outfile)
        for line in csv_in:
            if len(line) == 2 and line[0] != "nan" and line[1] != "nan":
                coord = [0, 0]
                coord[0] = float(line[0]) + 470
                coord[1] = float(line[1]) + 150
                csv_out.writerow(coord)
