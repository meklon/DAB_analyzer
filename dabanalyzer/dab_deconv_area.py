import argparse
import os
import csv
import timeit
import json
from multiprocessing import Pool, cpu_count
from functools import partial

import numpy as np
from scipy import linalg, misc
from skimage import color
import matplotlib.image as mpimg
import matplotlib.pyplot as plt


from . import hasel

# Optional imports of pandas and seaborn are located in functions
# group_analyze() and plot_group().


def parse_arguments():
    """
    Parsing arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", required=True, help="Path to the directory or file")
    parser.add_argument("-t", "--thresh", required=False, default=40,
                        type=int, help="Global threshold for DAB-positive area,"
                                       "from 0 to 100.Optimal values are usually"
                                       " located from 35 to 55.")
    parser.add_argument("-e", "--empty", required=False, default=101,
                        type=int, help="Global threshold for EMPTY area,"
                                       "from 0 to 100. Default value is 101,"
                                       " which is equal to disabled empty area filter.")
    parser.add_argument("-s", "--silent", required=False, help="Supress figure rendering during the analysis,"
                                                               " only final results"
                                                               " will be saved", action="store_true")
    parser.add_argument("-a", "--analyze", required=False, help="Add group analysis after the indvidual image"
                                                                " processing. The groups are created using the"
                                                                " filename. Everything before '_' symbol will"
                                                                " be recognized as a group name. Example:"
                                                                " sample01_10.jpg, sample01_11.jpg will be"
                                                                " counted as a single group 'sample01'",
                                                                action="store_true")
    parser.add_argument("-m", "--matrix", required=False, help="Your matrix in a JSON formatted file")
    arguments = parser.parse_args()
    return arguments


def get_image_filenames(path):
    """
    Returns only the filenames in the path. Directories, subdirectories and files below the first level
    are excluded
    """

    return [name for name in sorted(os.listdir(path))
            if not os.path.isdir(os.path.join(path, name))]


def calc_deconv_matrix(matrix_vector_dab_he):
    """
    Custom calculated matrix of lab's stains DAB + Hematoxylin
    The raw matrix was moved to the global scope before main() function as a constant
    """

    matrix_vector_dab_he[2, :] = np.cross(matrix_vector_dab_he[0, :], matrix_vector_dab_he[1, :])
    matrix_dh = linalg.inv(matrix_vector_dab_he)
    return matrix_dh


def separate_channels(image_original, matrix_dh):
    """
    Separate the stains using the custom matrix
    """

    image_separated = color.separate_stains(image_original, matrix_dh)
    stain_dab = image_separated[..., 1]
    # Hematox channel separation is disabled, it could be switched on if image with both stains is needed.
    # one of plot_figure() subplots should be replaced with stainHematox

    # stainHematox = image_separated[..., 0]

    # 1-D array for histogram conversion, 1 was added to move the original range from
    # [-1,0] to [0,1] as black and white respectively. Warning! Magic numbers.
    # Anyway it's not a trouble for correct thresholding. Only for histogram aspect.
    stain_dab = (stain_dab + 1) * 200
    # Histogram shift. This correcion makes the background really blank. After the correction
    # numpy clipping is performed to fit the 0-100 range
    stain_dab -= 18
    stain_dab = np.clip(stain_dab, 0, 100)
    stain_dab_1d = np.ravel(stain_dab)
    # Extracting Lightness channel from HSL of original image
    # L-channel is multiplied to 100 to get the range 0-100 % from 0-1. It's easier to use with
    # empty area threshold
    image_hsl = hasel.rgb2hsl(image_original)
    channel_lightness = (image_hsl[..., 2] * 100)
    return stain_dab, stain_dab_1d, channel_lightness


def log_and_console(path_output_log, text_log, bool_log_new=False):
    """
    Write the log and show the text in console
    bool_log_new is used to erase the log file if it exists to avoid appending new data to the old one
    """

    if bool_log_new:
        print(text_log)
        # Initialize empty file
        with open(path_output_log, "a") as fileLog:
            fileLog.write("")
        with open(path_output_log, "w") as fileLog:
            fileLog.write(text_log)
            fileLog.write('\n')
    else:
        print(text_log)
        with open(path_output_log, "a") as fileLog:
            fileLog.write(text_log)
            fileLog.write('\n')


def log_only(path_output_log, text_log):
    """
    Write the log to the file only
    """
    with open(path_output_log, "a") as fileLog:
            fileLog.write(text_log)
            fileLog.write('\n')


def count_thresholds(stain_dab, channel_lightness, thresh_default, thresh_empty_default):
    """
    Counts thresholds. stain_dab is a distribution map of DAB stain, channel_lightness is a L channel from
    original image in HSL color space. The output are the thresholded images of DAB-positive areas and
    empty areas. thresh_default is also in output as plot_figure() needs it to make a vertical line of
    threshold on a histogram.
    """

    thresh_dab = stain_dab > thresh_default
    thresh_empty = channel_lightness > thresh_empty_default
    return thresh_dab, thresh_empty


def count_areas(thresh_dab, thresh_empty):
    """
    Count areas from numpy arrays
    """

    area_all = float(thresh_dab.size)
    area_empty = float(np.count_nonzero(thresh_empty))
    area_dab_pos = float(np.count_nonzero(thresh_dab))

    # Count relative areas in % with rounding
    # NB! Relative DAB is counted without empty areas
    area_rel_empty = round((area_empty / area_all * 100), 2)
    area_rel_dab = round((area_dab_pos / (area_all - area_empty) * 100), 2)
    return area_rel_empty, area_rel_dab


def plot_figure(image_original, stain_dab, stain_dab_1d, channel_lightness, thresh_dab, thresh_empty,
                thresh_default, tresh_empty_default):
    """
    Function plots the figure for every sample image. It creates the histogram from the stainDAB array.
    Then it takes the bins values and clears the plot. That's done because fill_between function doesn't
    work with histogram but only with ordinary plots. After all function fills the area between zero and
    plot if the values are above the threshold.
    """
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
    plt.title('Lightness channel')
    plt.imshow(channel_lightness, cmap=plt.cm.gray)

    plt.subplot(235)
    plt.title('DAB positive area')
    plt.imshow(thresh_dab, cmap=plt.cm.gray)

    if not tresh_empty_default>100:
        plt.subplot(236)
        plt.title('Empty area')
        plt.imshow(thresh_empty, cmap=plt.cm.gray)

    plt.tight_layout()


def stack_data(array_filenames, array_data):
    """
    Function stacks the data from numpy arrays.
    """
    array_output = np.hstack((array_filenames, array_data))
    array_output = np.vstack((["Filename", "DAB-positive area, %"], array_output))
    return array_output


def save_csv(path_output_csv, array_filenames, array_data):
    """
    Function puts data array to the output csv file.
    """
    array_output = stack_data(array_filenames, array_data)

    # write array to csv file
    with open(path_output_csv, 'w') as f:
        csv.writer(f).writerows(array_output)
    print("CSV saved: " + path_output_csv)


def get_output_paths(path_root):
    """
    Output path generating
    """

    path_output = os.path.join(path_root, "result/")
    path_output_log = os.path.join(path_output, "log.txt")
    path_output_csv = os.path.join(path_output, "analysis.csv")
    return path_output, path_output_log, path_output_csv


def check_mkdir_output_path(path_output):
    """
    Function checks if the output path exists and creates it if not
    """

    if not os.path.exists(path_output):
        os.mkdir(path_output)
        print("Created result directory")
    else:
        print("Output result directory already exists. All the files inside would be overwritten!")


def grayscale_to_stain_color(stain_dab):
    """
    Converts grayscale map of stain distribution to the colour representation.
    The original grayscale is used as a L-channel in HSL colour space.
    Hue and Saturation channels are defined manually.
    Disabled now, fix needed.
    """
    # todo: Fix the grayscale to colour conversion
    # DAB colour in HSL
    array_image_hsl = np.zeros((480, 640, 3), dtype='float')
    array_image_hsl[..., 0] = 0.0859375  # 25/256 Hue
    array_image_hsl[..., 1] = 0.34375  # 88/256 Saturation
    stain_dab = (255 - stain_dab)/256
    array_image_hsl[..., 2] = stain_dab  # Lightness
    image_stain_dab_color = hasel.hsl2rgb(array_image_hsl)
    return image_stain_dab_color


def resize_input_image(image_original, size):
    """
    Resizing the original images makes the slowest functions calc_deconv_matrix() and hasel.hsl2rgb()
    work much faster. There are no visual troubles or negative effects to the accuracy.
    """

    image_original = misc.imresize(image_original, size, interp='nearest')
    return image_original


def image_process(array_data, var_pause, matrix_dh, args, pathOutput, pathOutputLog, filename):
    """
    Main cycle, split into several processes using the Pool(). All images pass through this
    function. The result of this function is composite images, saved in the target directory,
    log output and array_data - numpy array, containing the data obtained.
    """

    path_input_image = os.path.join(args.path, filename)
    path_output_image = os.path.join(pathOutput, filename.split(".")[0] + "_analysis.png")
    image_original = mpimg.imread(path_input_image)

    size_image = 480, 640
    image_original = resize_input_image(image_original, size_image)

    stain_dab, stain_dab_1d, channel_lightness = separate_channels(image_original, matrix_dh)
    thresh_dab, thresh_empty = count_thresholds(stain_dab, channel_lightness, args.thresh, args.empty)
    area_rel_empty, area_rel_dab = count_areas(thresh_dab, thresh_empty)
    # stain_dab = grayscale_to_stain_color(stain_dab)

    # Close all figures after cycle end
    plt.close('all')

    array_data = np.vstack((array_data, area_rel_dab))

    # Creating the complex image
    plot_figure(image_original, stain_dab, stain_dab_1d, channel_lightness, thresh_dab, thresh_empty, args.thresh,
                args.empty)
    plt.savefig(path_output_image, dpi=120)

    log_and_console(pathOutputLog, "Image saved: {}".format(path_output_image))

    # In silent mode image will be closed immediately
    if not args.silent:
        plt.pause(var_pause)
    return array_data


def group_filenames(filenames):
    """
    Creates groups of samples cutting filename after "_" symbol. Used to count
     statistics for each sample group.
    """

    array_file_group = np.empty([0, 1])
    for filename in filenames:
        filename = filename.split("_")[0]
        array_file_group = np.vstack((array_file_group, filename))
    return array_file_group


def group_analyze(filenames, array_data, path_output):
    # optional import
    import pandas as pd

    path_output_stats = os.path.join(path_output, "stats.csv")
    # Creating groups of samples using the filename
    array_file_group = group_filenames(filenames)

    # Creating pandas DataFrame
    column_names = ['Group', 'DAB+ area, %']
    data_frame_data = np.hstack((array_file_group, array_data))

    df = pd.DataFrame(data_frame_data, columns=column_names)
    df = df.convert_objects(convert_numeric=True)
    groupby_group = df['DAB+ area, %'].groupby(df['Group'])
    data_stats = groupby_group.agg([np.mean, np.std, np.median, np.min, np.max])
    data_stats.to_csv(path_output_stats)
    print(data_stats)
    plot_group(df, path_output)


def plot_group(data_frame, path_output):
    # optional import
    import seaborn as sns
    path_output_image = os.path.join(path_output, "summary_statistics.png")

    # # Plotting swarmplot
    # plt.figure(num=None, figsize=(15, 7), dpi=120)
    # sns.set_style("whitegrid")
    #
    # plt.title('Violin plot with single measurements')
    # sns.violinplot(x="Group", y="DAB+ area", data=data_frame, inner=None)
    # sns.swarmplot(x="Group", y="DAB+ area", data=data_frame, color="w", alpha=.5)
    # plt.savefig(path_output_image)
    #
    # plt.tight_layout()

    sns.set_style("whitegrid")
    sns.set_context("talk")
    plt.figure(num=None, figsize=(15, 7), dpi=120)
    plt.ylim(0, 100)
    plt.title('Box plot')
    sns.boxplot(x="Group", y="DAB+ area, %", data=data_frame)

    plt.tight_layout()
    plt.savefig(path_output_image, dpi=300)


def main():
    """
    Yor own matrix should be placed here. You can use ImageJ and color deconvolution module for it.
    More information here: http://www.mecourse.com/landinig/software/cdeconv/cdeconv.html
    Declare vectors as a constant
    """
    matrixVectorDabHE = np.array([[0.66504073, 0.61772484, 0.41968665],
                                  [0.4100872, 0.5751321, 0.70785],
                                  [0.6241389, 0.53632, 0.56816506]])

    arrayData = np.empty([0, 1])
    # Pause in seconds between the composite images when --silent(-s) argument is not active
    varPause = 5

    # Initialize the global timer
    startTimeGlobal = timeit.default_timer()

    # Parse the arguments
    args = parse_arguments()

    if args.matrix:
        with open(args.matrix) as f:
            matrixVectorDabHE = np.array(json.load(f))

    pathOutput, pathOutputLog, pathOutputCSV = get_output_paths(args.path)

    check_mkdir_output_path(pathOutput)
    filenames = get_image_filenames(args.path)
    log_and_console(pathOutputLog, "Images for analysis: " + str(len(filenames)), True)
    log_and_console(pathOutputLog, "DAB threshold = " + str(args.thresh) +
                    ", Empty threshold = " + str(args.empty))
    if args.empty>100:
        log_and_console(pathOutputLog, "Empty area filtering is disabled.")
        log_and_console(pathOutputLog, "It should be adjusted in a case of hollow organ or unavoidable edge defects")


    # Calculate the DAB and HE deconvolution matrix
    matrixDH = calc_deconv_matrix(matrixVectorDabHE)

    # Multiprocess implementation
    cores = cpu_count()
    log_and_console(pathOutputLog, "CPU cores used: {}".format(cores))

    # Main cycle where the images are processed and the data is obtained
    pool = Pool(cores)
    wrapper_image_process = partial(image_process, arrayData, varPause, matrixDH,
                                    args, pathOutput, pathOutputLog)
    for poolResult in pool.imap(wrapper_image_process, filenames):
        arrayData = np.append(arrayData, poolResult, axis=0)
    pool.close()
    pool.join()

    arrayFilenames = np.empty([0, 1])
    for filename in filenames:
        arrayFilenames = np.vstack((arrayFilenames, filename))

    # Creating summary csv after main cycle end
    save_csv(pathOutputCSV, arrayFilenames, arrayData)

    # Optional statistical group analysis.
    if args.analyze:
        log_and_console(pathOutputLog,"Group analysis is active")
        group_analyze(filenames, arrayData, pathOutput)
        log_and_console(pathOutputLog,"Statistical data for each group was saved as stats.csv")
        log_and_console(pathOutputLog,"Boxplot with statistics was saved as summary_statistics.png")

    # End of the global timer
    elapsedGlobal = timeit.default_timer() - startTimeGlobal
    if not args.silent:
        averageImageTime = (elapsedGlobal - len(filenames)*varPause)/len(filenames)  # compensate the pause
    else:
        averageImageTime = elapsedGlobal/len(filenames)
    log_and_console(pathOutputLog, "Analysis time: {:.1f} seconds".format(elapsedGlobal))
    log_and_console(pathOutputLog, "Average time per image: {:.1f} seconds".format(averageImageTime))
