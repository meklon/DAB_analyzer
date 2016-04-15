import argparse
import os
import csv
import timeit
from PIL import Image

import numpy as np
from scipy import linalg
from skimage import color
import matplotlib.pyplot as plt


def parse_arguments():
    # Parsing arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", required=True, help="Path to the directory or file")
    parser.add_argument("-t", "--thresh", required=False, type=int, help="Global threshold for DAB-positive area,"
                                                                         "from 0 to 100.Optimal values are usually"
                                                                         " located from 40 to 65.")
    parser.add_argument("-e", "--empty", required=False, type=int, help="Global threshold for EMPTY area,"
                                                                        "from 0 to 100.Optimal values are usually"
                                                                        " located from 88 to 95.")
    parser.add_argument("-s", "--silent", required=False, help="Supress figure rendering during the analysis,"
                                                               " only the final results"
                                                               " would be saved", action="store_true")
    arguments = parser.parse_args()
    return arguments


def get_image_filenames(path):
    return [name for name in sorted(os.listdir(path))
            if not os.path.isdir(os.path.join(path, name))]


def calc_deconv_matrix():
    # Custom calculated matrix of lab's stains DAB + Hematoxylin
    # Yor own matrix should be placed here. You can use ImageJ and color deconvolution module for it.
    # More information here: http://www.mecourse.com/landinig/software/cdeconv/cdeconv.html
    custom_dab = np.array([[0.66504073, 0.61772484, 0.41968665],
                          [0.4100872, 0.5751321, 0.70785],
                          [0.6241389, 0.53632, 0.56816506]])
    # Alternative matrix DAB + Hematoxylin
    # custom_dab = np.array([[0.34388107, 0.9115486, 0.22544378],
    #                       [0.14550355, 0.4053599, 0.90250325],
    #                       [0.92767155, 0.06901047, 0.3669646]])

    custom_dab[2, :] = np.cross(custom_dab[0, :], custom_dab[1, :])
    custom_dab_matrix = linalg.inv(custom_dab)
    return custom_dab_matrix


def print_log(text_log, bool_log_new=False):
    # Write the log and show the text in console
    output_log_path = outputPath + "log.txt"
    if bool_log_new:
        print text_log
        # Initialize empty file
        with open(output_log_path, "a") as fileLog:
            fileLog.write("")
        with open(output_log_path, "w") as fileLog:
            fileLog.write(text_log)
            fileLog.write('\n')
    else:
        print text_log
        with open(output_log_path, "a") as fileLog:
            fileLog.write(text_log)
            fileLog.write('\n')


def plot_figure():
    plt.figure(num=None, figsize=(15, 7), dpi=120, facecolor='w', edgecolor='k')
    plt.subplot(231)
    plt.title('Original')
    plt.imshow(ihc)

    plt.subplot(232)
    plt.title('DAB')
    plt.imshow(stainDAB, cmap=plt.cm.gray)

    plt.subplot(233)
    plt.title('Histogram of DAB')
    (n, bins, patches) = plt.hist(stainDAB_1D, bins=128, range=[0, 100], histtype='step', fc='k', ec='#ffffff')
    # As np.size(bins) = np.size(n)+1, we make the arrays equal to plot the area after threshold
    bins_equal = np.delete(bins, np.size(bins)-1, axis=0)
    # clearing subplot after getting the bins from hist
    plt.cla()
    plt.fill_between(bins_equal, n, 0, facecolor='#ffffff')
    plt.fill_between(bins_equal, n, 0, where=bins_equal >= threshDefault,  facecolor='#c4c4f4',
                     label='positive area')
    plt.axvline(threshDefault+0.5, color='k', linestyle='--', label='threshold', alpha=0.8)
    plt.legend(fontsize=8)
    plt.xlabel("Pixel intensity, %")
    plt.ylabel("Number of pixels")
    plt.grid(True, color='#888888')

    plt.subplot(234)
    plt.title('Value channel of original in HSV')
    plt.imshow(ihc_v, cmap=plt.cm.gray)

    plt.subplot(235)
    plt.title('DAB positive area')
    plt.imshow(threshDAB_pos, cmap=plt.cm.gray)

    plt.subplot(236)
    plt.title('Empty area')
    plt.imshow(threshIHC_v, cmap=plt.cm.gray)

    plt.tight_layout()


def save_csv():
    array_output = np.hstack((arrayFilenames, arrayData))
    array_output = np.vstack((["Filename", "DAB-positive area, pixels",
                                           "Empty area, %", "DAB-positive area, %"], array_output))
    # write array to csv file
    output_csv_path = os.path.join(outputPath, "test.csv")
    with open(output_csv_path, 'w') as f:
        csv.writer(f).writerows(array_output)
    print "CSV saved: " + output_csv_path


# Declare the zero values and empty arrays
count_cycle = 0
arrayData = np.empty([0, 3])
arrayFilenames = np.empty([0, 1])

# Initialize the global timer
startTimeGlobal = timeit.default_timer()

args = parse_arguments()
root = args.path
boolProgress_show = args.silent

# Calc the matrix of stain
matrix = calc_deconv_matrix()

# mkdir for output if not exist
outputPath = os.path.join(root, "result/")
if not os.path.exists(outputPath):
    os.mkdir(outputPath)
    print "Created result directory"
else:
    print "Output result directory already exists. All the files inside would be overwritten!"

# Recursive search through the path from argument
filenames = get_image_filenames(root)
print_log("Images for analysis: " + str(len(filenames)), True)
for filename in sorted(filenames):
    imagePath = os.path.join(root, filename)

    # Image selection
    ihc = Image.open(imagePath)

    # Separate the stains using the custom matrix
    ihc_DH = color.separate_stains(ihc, matrix)
    stainDAB = ihc_DH[:, :, 1]
    stainHematox = ihc_DH[:, :, 0]

    # 1-D array for histogram conversion, 1 added to move the original range from
    # [-1,0] to [0,1] as black and white respectively. Warning! Magic numbers.
    # Anyway it's not a trouble for correct thresholding. Only for histogram aspect.
    stainDAB = (stainDAB + 1) * 200
    stainDAB_1D = np.ravel(stainDAB)

    # Extracting Value channel from HSV of original image
    ihc_hcv = color.rgb2hsv(ihc)
    ihc_v = (ihc_hcv[:, :, 2] * 100)

    # Binary non-adaptive threshold for DAB and empty areas
    # Default threshold is used when no -t option is available
    if args.thresh:
        threshDefault = args.thresh
    else:
        threshDefault = 55
    threshDAB_pos = stainDAB > threshDefault
    if args.empty:
        threshEmptyDefault = args.empty
    else:
        threshEmptyDefault = 92
    threshIHC_v = ihc_v > threshEmptyDefault

    # Count areas from numpy arrays
    areaAll = float(threshDAB_pos.size)
    areaEmpty = float(np.count_nonzero(threshIHC_v))
    areaDAB_pos = float(np.count_nonzero(threshDAB_pos))

    # Count relative areas in % with rounding
    # NB! Relative DAB is counted without empty areas
    areaRelEmpty = round((areaEmpty / areaAll * 100), 2)
    areaRelDAB = round((areaDAB_pos / (areaAll - areaEmpty) * 100), 2)

    # Close all figures after cycle end
    plt.close('all')

    # Loop for filling the list with file names and area results
    count_cycle += 1
    if count_cycle <= len(filenames):
        arrayData = np.vstack((arrayData, [areaDAB_pos, areaRelEmpty, areaRelDAB]))
        arrayFilenames = np.vstack((arrayFilenames, filename))

        # Creating the summary image
        plot_figure()

        # In silent mode image would be closed immediately
        if not boolProgress_show:
            plt.pause(5)
        # Save the plot
        outputImagePath = outputPath + filename.split(".")[0] + "_analysis.png"
        print_log("Image " + str(count_cycle) + "/" + str(len(filenames)) + " saved: " + outputImagePath)
        plt.savefig(outputImagePath)

    # At the last cycle we're saving the summary csv
    if count_cycle == len(filenames):
        save_csv()
        break
# End the global timer
elapsedGlobal = timeit.default_timer() - startTimeGlobal
averageImageTime = elapsedGlobal/len(filenames)
elapsedGlobal = "{:.1f}".format(elapsedGlobal)
averageImageTime = "{:.1f}".format(averageImageTime)
print_log("Analysis time: " + str(elapsedGlobal) + " seconds")
print_log("Average time per image: " + str(averageImageTime) + " seconds")
