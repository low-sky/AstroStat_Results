
import numpy as np
import turbustat.analysis as ta
from turbustat.statistics import statistics_list
import os
import subprocess
import sys
import shutil
from datetime import datetime

'''
Runs the basic analysis pipeline, starting from the outputted HDF5 files

Creates a time-stamped folder with the expected structure.
'''


def timestring():
    TimeString = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return TimeString

# Specify path with results

path = os.path.abspath(sys.argv[1])

if path.split("/")[-1] == "HDF5_files":
    hdf5_path = path + "/"
    path = "/".join(path.split("/")[:-1]) + "/"
    if path == "/":
        path = "./"
else:
    hdf5_path = os.path.join(path, "HDF5_files/")
    path += "/"

design_matrix = sys.argv[2]

if design_matrix == "None":
    design_matrix = None

scripts_path = sys.argv[3]

run_name = sys.argv[4]

# Redefine the path with the timestamped output folder
path = os.path.join(path, run_name+"_"+timestring())
os.mkdir(path)
shutil.move(hdf5_path, path)
hdf5_path = os.path.join(path, "HDF5_files")

os.chdir(path)

# Convert into combined csv files.

good_comparison = []

print "Converting to combined csv files."

try:
    ta.convert_format(hdf5_path, 0, face2=0, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_0_0.csv"), path)
    good_comparison.append("0_0")
except StandardError as err:
    print err
try:
    ta.convert_format(hdf5_path, 0, face2=1, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_0_1.csv"), path)
    good_comparison.append("0_1")
except StandardError as err:
    print err
try:
    ta.convert_format(hdf5_path, 0, face2=2, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_0_2.csv"), path)
    good_comparison.append("0_2")
except StandardError as err:
    print err
try:
    ta.convert_format(hdf5_path, 1, face2=0, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_1_0.csv"), path)
    good_comparison.append("1_0")
except StandardError as err:
    print err
try:
    ta.convert_format(hdf5_path, 1, face2=1, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_1_1.csv"), path)
    good_comparison.append("1_1")
except StandardError as err:
    print err
try:
    ta.convert_format(hdf5_path, 1, face2=2, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_1_2.csv"), path)
    good_comparison.append("1_2")
except StandardError as err:
    print err
try:
    ta.convert_format(hdf5_path, 2, face2=0, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_2_0.csv"), path)
    good_comparison.append("2_0")
except StandardError as err:
    print err
try:
    ta.convert_format(hdf5_path, 2, face2=1, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_2_1.csv"), path)
    good_comparison.append("2_1")
except StandardError as err:
    print err
try:
    ta.convert_format(hdf5_path, 2, face2=2, design=design_matrix)
    shutil.move(os.path.join(hdf5_path, "distances_2_2.csv"), path)
    good_comparison.append("2_2")
except StandardError as err:
    print err

# Next convert the fiducial comparisons

for fil in os.listdir(hdf5_path):
    full_file = os.path.join(hdf5_path, fil)
    if os.path.isfile(full_file) and "fid_comp" in fil:
        print("Fiducial comparison: " + full_file)
        out_name = ta.convert_fiducial(full_file,
                                       return_name=True)

        # shutil.move(out_name, path)

# Now make the distance plots.

print "Making distance plots."

if not os.path.exists(os.path.join(path, "Distance Plots")):
    os.mkdir(os.path.join(path, "Distance Plots"))

ta.comparison_plot(path, comparisons=good_comparison,
                   out_path=os.path.join(path, "Distance Plots/"),
                   design_matrix=design_matrix)

# Run the R-script to fit the data to the model

# Must have 0_0 and 2_2 comparisons to run

if "0_0" not in good_comparison and "2_2" not in good_comparison:
    raise StandardError("Model fitting requires 0_0 and 2_2 to be available.")

os.chdir(path)

print "Fitting model of given design."

subprocess.call(['Rscript',
                 os.path.join(scripts_path, "FactorialAnalysis.R")])

# This should create two output tables of the whole dataset.

# Now run the metric validation

print "Running metric validation."

subprocess.call(['Rscript',
                 os.path.join(scripts_path, "noise_validation.r"),
                 path, "5000"])

subprocess.call(['Rscript',
                 os.path.join(scripts_path, "signal_validation.r"),
                 path, "5000"])

# Finally, create the model plots

print "Creating model plots."

execfile(os.path.join(scripts_path, "effect_plots.py"))

# Remove PDF_AD from the list

# statistics_list.remove("PDF_AD")

if not os.path.exists(os.path.join(path, "Model Plots")):
    os.mkdir(os.path.join(path, "Model Plots"))

effect_plots("DataforFits.csv", "ResultsFactorial.csv", save=True,
             out_path='Model Plots/')

# Only show results of the good statistics
good_stats = ["Cramer", "DeltaVariance", "Dendrogram_Hist",
              "Dendrogram_Num", "PCA", "PDF_Hellinger", "SCF", "VCA", "VCS",
              "VCS_Small_Scale", "VCS_Large_Scale", "Skewness", "Kurtosis"]

# THE ASPECT RATIO IS FUNKY
# NEED TO ADJUST BY HAND
# Use: p.ion(), and set save_name=None to alter by-hand

map_all_results("ResultsFactorial.csv", normed=False, max_order=2,
                save_name="map_all_results.pdf",
                out_path='Model Plots/', statistics=good_stats)

print "Finished!"
