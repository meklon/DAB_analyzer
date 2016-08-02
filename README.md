# DAB analyzer
Python soft for DAB-chromagen analysis. Software counts the stained area with DAB-chromagen using the typical immunohistochemistry protocols. After the analysis user can measure the difference of proteins content in tested samples.

### Application:
Quantitative analysis of extracellular matrix proteins in IHC-analysis, designed for scientists in biotech sphere. 

### Requirements:
Python 2.7 or Python 3.4-3.5

Python libraries: numpy, scipy, skimage, matplotlib
Optional (for group analysis): pandas, seaborn

### Interface type:
No GUI, command line interface only.

### Basic principles:
Script uses the **color deconvolution method**. It was well described by [G. Landini](http://www.mecourse.com/landinig/software/cdeconv/cdeconv.html). Python port from Skimage package of his algorythm was used. See also: *Ruifrok AC, Johnston DA. Quantification of histochemical staining by color deconvolution. Anal Quant Cytol Histol 23: 291-299, 2001.*

Color deconvolution is used to separate stains in multi-stained sample. This soft is applied for Hematoxyline + DAB staining. Script uses hardcoded stain matrix determined for our lab's dyes. You should determine your own for better result using ImageJ and hyperlink above. Determined custom matrix should replace the default one. For additional information see the comments in code.

After DAB separation, script determines the DAB-positive area using the default or user-defined threshold. The empty areas are excluded from the final relative area measurement as the sample could contain free space, which would affect the result accuracy.

Script creates the result folder inside the --path. Statistics, log and composite images for each sample are saved there.
### Examples
You can find test images in this repository.

#### Composite image examples
Script will render this type of image for **each of your samples**. User should control the result to be sure that the threshold values are right
![Composite image example 1](https://github.com/meklon/DAB_analyzer/blob/master/test%20images/result%20example/Native_Pan_05_analysis.png "Composite image example")

![Composite image example 2](https://github.com/meklon/DAB_analyzer/blob/master/test%20images/result%20example/Alex_Pan_08_analysis.png "Composite image example")

#### Log example
```
Images for analysis: 62
DAB threshold = 40, Empty threshold = 101
Empty area filtering is disabled.
It should be adjusted in a case of hollow organ or unavoidable edge defects
CPU cores used: 2
Image saved: /home/meklon/temp/sample_native/result/Col1_02_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Col1_01_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Col4_02_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Col4_03_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Fibr_04_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Fibr_05_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Fibr_06_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Fibr_07_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Fibr_08_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Lam_02_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Lam_01_analysis.png
Image saved: /home/meklon/temp/sample_native/result/Lam_04_analysis.png
Group analysis is active
Statistical data for each group was saved as stats.csv
Boxplot with statistics was saved as summary_statistics.png
Analysis time: 44.3 seconds
Average time per image: 0.7 seconds
```
#### CSV output example
Filename | DAB-positive area, %
------------ | -------------
Alex_Pan_06.jpg|61.55
Native_Pan_05.jpg|14.23
Native_Trop_02.jpg|10.83

### User manual
Place all the sample images (8-bit) inside the separate folder. Subdirectories are excluded from analysis. Use the following options:

*-p, --path* (obligate) - path to the target directory with samples

*-t, --thresh* (optional) - threshold for DAB+ area separation. If empty the default value would be used (threshDefault = 30).

*-e, --empty* (optional) - threshold for **empty area** separation. If empty the default value would be used (threshEmptyDefault = 92).

*-s, --silent* (otional) - if True, the real-time composite image visualisation would be supressed. The output will be just saved in the result folder.

####Example
````
python dab_deconv_area.py -p /home/meklon/Data/sample/test/ -t 35 -e 89 -s -a
````

### Image samples requirements
1. Image samples' **white balance should be normalized**! It is important to get the right colors of stains before separation. I could suggest free software like [Rawtherapee](http://rawtherapee.com/)
2. Images should be acquired using the **same exposure values**
3. Threshold should be the same at the whole image sequence if you want to compare them
4. It would be better to use the manual mode in microscope camera to be sure, that your images were taken with the same parameters.
5. Don't change light intensity in microscope during the sequence acquiring.

### Authorship
Gumenyuk Ivan, Kuban state medical university, Russia.
