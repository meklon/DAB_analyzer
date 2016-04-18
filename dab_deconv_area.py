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
    parser.add_argument("-t", "--thresh", required=False, default=55,
                        type=int, help="Global threshold for DAB-positive area,"
                                       "from 0 to 100.Optimal values are usually"
                                       " located from 40 to 65.")
    parser.add_argument("-e", "--empty", required=False, default=92,
                        type=int, help="Global threshold for EMPTY area,"
                                       "from 0 to 100.Optimal values are usually"
                                       " located from 88 to 95.")
    parser.add_argument("-s", "--silent", required=False, help="Supress figure rendering during the analysis,"
                                                               " only the final results"
                                                               " would be saved", action="store_true")
    arguments = parser.parse_args()
    return arguments


def get_image_filenames(path):
    # Returns only the filenames in the path. Directories, subdirectories and files below the first level
    # are excluded
    return [name for name in sorted(os.listdir(path))
            if not os.path.isdir(os.path.join(path, name))]


def calc_deconv_matrix(matrix_raw_dh):
    # Custom calculated matrix of lab's stains DAB + Hematoxylin

    matrix_raw_dh[2, :] = np.cross(matrix_raw_dh[0, :], matrix_raw_dh[1, :])
    matrix_dh = linalg.inv(matrix_raw_dh)
    return matrix_dh


def separate_channels(image_original, matrix_dh):
    # Separate the stains using the custom matrix
    image_separated = color.separate_stains(image_original, matrix_dh)
    stain_dab = image_separated[..., 1]
    # stainHematox = image_separated[..., 0]

    # 1-D array for histogram conversion, 1 added to move the original range from
    # [-1,0] to [0,1] as black and white respectively. Warning! Magic numbers.
    # Anyway it's not a trouble for correct thresholding. Only for histogram aspect.
    stain_dab = (stain_dab + 1) * 200
    stain_dab_1d = np.ravel(stain_dab)

    # Extracting Value channel from HSV of original image
    image_hsv = color.rgb2hsv(image_original)
    channel_value = (image_hsv[..., 2] * 100)

    return stain_dab, stain_dab_1d, channel_value


def print_log(path_output_log, text_log, bool_log_new=False):
    # Write the log and show the text in console
    # bool_log_new is used to erase the log file if it exists to avoid appending new data to the old one
    if bool_log_new:
        print text_log
        # Initialize empty file
        with open(path_output_log, "a") as fileLog:
            fileLog.write("")
        with open(path_output_log, "w") as fileLog:
            fileLog.write(text_log)
            fileLog.write('\n')
    else:
        print text_log
        with open(path_output_log, "a") as fileLog:
            fileLog.write(text_log)
            fileLog.write('\n')


def count_thresholds(stain_dab, channel_value):
    # Counts thresholds. stain_dab is a distribution map of DAB stain, channel_value is a value channel from
    # original image in HSV color space. The output are the thresholded images of DAB-positive areas and
    # empty areas. thresh_default is also in output as plot_figure() needs it to make a vertical line of
    # threshold on a histogram.

    thresh_default = args.thresh
    thresh_empty_default = args.empty
    thresh_dab = stain_dab > thresh_default
    thresh_empty = channel_value > thresh_empty_default
    return thresh_dab, thresh_empty, thresh_default


def count_areas(thresh_dab, thresh_empty):
    # Count areas from numpy arrays
    area_all = float(thresh_dab.size)
    area_empty = float(np.count_nonzero(thresh_empty))
    area_dab_pos = float(np.count_nonzero(thresh_dab))

    # Count relative areas in % with rounding
    # NB! Relative DAB is counted without empty areas
    area_rel_empty = round((area_empty / area_all * 100), 2)
    area_rel_dab = round((area_dab_pos / (area_all - area_empty) * 100), 2)
    return area_dab_pos, area_rel_empty, area_rel_dab


def plot_figure(image_original, stain_dab, stain_dab_1d, channel_value, thresh_dab, thresh_empty, thresh_default):
    # Function plots the figure for every sample image. It creates the histogram from the stainDAB array.
    # Then it takes the bins values and clears the plot. That's done because fill_between function doesn't
    # work with histogram but only with ordinary plots. After all function fills the area between zero and
    # plot if the values are above the threshold.
    plt.figure(num=None, figsize=(15, 7), dpi=120, facecolor='w', edgecolor='k')
    plt.subplot(231)
    plt.title('Original')
    plt.imshow(image_original)

    plt.subplot(232)
    plt.title('DAB')
    plt.imshow(stain_dab, cmap=plt.cm.gray)

    plt.subplot(233)
    plt.title('Histogram of DAB')
    (n, bins, patches) = plt.hist(stain_dab_1d, bins=128, range=[0, 100], histtype='step', fc='k', ec='#ffffff')
    # As np.size(bins) = np.size(n)+1, we make the arrays equal to plot the area after threshold
    bins_equal = np.delete(bins, np.size(bins)-1, axis=0)
    # clearing subplot after getting the bins from hist
    plt.cla()
    plt.fill_between(bins_equal, n, 0, facecolor='#ffffff')
    plt.fill_between(bins_equal, n, 0, where=bins_equal >= thresh_default,  facecolor='#c4c4f4',
                     label='positive area')
    plt.axvline(thresh_default+0.5, color='k', linestyle='--', label='threshold', alpha=0.8)
    plt.legend(fontsize=8)
    plt.xlabel("Pixel intensity, %")
    plt.ylabel("Number of pixels")
    plt.grid(True, color='#888888')

    plt.subplot(234)
    plt.title('Value channel of original in HSV')
    plt.imshow(channel_value, cmap=plt.cm.gray)

    plt.subplot(235)
    plt.title('DAB positive area')
    plt.imshow(thresh_dab, cmap=plt.cm.gray)

    plt.subplot(236)
    plt.title('Empty area')
    plt.imshow(thresh_empty, cmap=plt.cm.gray)

    plt.tight_layout()


def save_csv(path_output_csv, array_filenames, array_data):
    # Function formats the data from numpy array and puts it to the output csv file.
    array_output = np.hstack((array_filenames, array_data))
    array_output = np.vstack((["Filename", "DAB-positive area, pixels",
                                           "Empty area, %", "DAB-positive area, %"], array_output))
    # write array to csv file
    with open(path_output_csv, 'w') as f:
        csv.writer(f).writerows(array_output)
    print "CSV saved: " + path_output_csv


def get_output_paths(path_root):
    # Output path generating
    path_output = os.path.join(path_root, "result/")
    path_output_log = os.path.join(path_output, "log.txt")
    path_output_csv = os.path.join(path_output, "analysis.csv")
    return path_root, path_output, path_output_log, path_output_csv


def check_mkdir_output_path(path_output):
    # Function checks if the output path exists and creates it if not
    if not os.path.exists(path_output):
        os.mkdir(path_output)
        print "Created result directory"
    else:
        print "Output result directory already exists. All the files inside would be overwritten!"


def resize_input_image(image_original):
    # Resizing the original images makes the slowest functions calc_deconv_matrix() and color.rgb2hsv()
    # work much faster. No visual troubles or negative effects to the accuracy.
    size = 640, 480
    image_original = image_original.resize(size, Image.NEAREST)
    return image_original

# Yor own matrix should be placed here. You can use ImageJ and color deconvolution module for it.
# More information here: http://www.mecourse.com/landinig/software/cdeconv/cdeconv.html
# Declare the matrix as a constant
matrixRawDH = np.array([[0.66504073, 0.61772484, 0.41968665],
                        [0.4100872, 0.5751321, 0.70785],
                        [0.6241389, 0.53632, 0.56816506]])

# Declare the zero values and empty arrays
count_cycle = 0
arrayData = np.empty([0, 3])
arrayFilenames = np.empty([0, 1])

# Initialize the global timer
startTimeGlobal = timeit.default_timer()

args = parse_arguments()
pathRoot, pathOutput, pathOutputLog, pathOutputCSV = get_output_paths(args.path)
boolSilent = args.silent
matrixDH = calc_deconv_matrix(matrixRawDH)
check_mkdir_output_path(pathOutput)

# Recursive search through the path from argument
filenames = get_image_filenames(args.path)
print_log(pathOutputLog, "Images for analysis: " + str(len(filenames)), True)
for filename in sorted(filenames):
    pathInputImage = os.path.join(pathRoot, filename)
    pathOutputImage = os.path.join(pathOutput, filename.split(".")[0] + "_analysis.png")
    imageOriginal = Image.open(pathInputImage)
    imageOriginal = resize_input_image(imageOriginal)

    stainDAB, stainDAB_1D, channelValue = separate_channels(imageOriginal, matrixDH)
    threshDAB, threshEmpty, threshDefault = count_thresholds(stainDAB, channelValue)
    areaDAB_pos, areaRelEmpty, areaRelDAB = count_areas(threshDAB, threshEmpty)

    # Close all figures after cycle end
    plt.close('all')

    # Loop for filling the list with file names and area results
    count_cycle += 1
    if count_cycle <= len(filenames):
        arrayData = np.vstack((arrayData, [areaDAB_pos, areaRelEmpty, areaRelDAB]))
        arrayFilenames = np.vstack((arrayFilenames, filename))

        # Creating the summary image
        plot_figure(imageOriginal, stainDAB, stainDAB_1D, channelValue, threshDAB, threshEmpty, threshDefault)
        plt.savefig(pathOutputImage)

        print_log(pathOutputLog, "Image " + str(count_cycle) + "/" + str(len(filenames)) + " saved: " + pathOutputImage)

        # In silent mode image would be closed immediately
        if not boolSilent:
            varPause = 5
            plt.pause(varPause)

    # At the last cycle we're saving the summary csv
    if count_cycle == len(filenames):
        save_csv(pathOutputCSV, arrayFilenames, arrayData)
        break

# End the global timer
elapsedGlobal = timeit.default_timer() - startTimeGlobal
if not boolSilent:
    averageImageTime = (elapsedGlobal - len(filenames)*varPause)/len(filenames)  # compensate the pause
else:
    averageImageTime = elapsedGlobal/len(filenames)
print_log(pathOutputLog, "Analysis time: {:.1f} seconds".format(elapsedGlobal))
print_log(pathOutputLog, "Average time per image: {:.1f} seconds".format(averageImageTime))
