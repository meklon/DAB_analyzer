# DAB analyzer
Python soft for DAB-chromagen analysis.

### Application:
Quantitative analysis of extracellular matrix proteins in IHC-analysis, designed for scientists in biotech sphere. 

### Requirements:
Python 2.7 or Python 3.4-3.5

Python libraries: numpy, scipy, skimage, matplotlib

### Interface type:
No GUI, command line interface only.

### Basic principles:
Script uses the **color deconvolution method**. It was well described by [G. Landini](http://www.mecourse.com/landinig/software/cdeconv/cdeconv.html). Python port from Skimage package of his algorythm was used. See also: *Ruifrok AC, Johnston DA. Quantification of histochemical staining by color deconvolution. Anal Quant Cytol Histol 23: 291-299, 2001.*

Color deconvolution is used to separate stains in multi-stained sample. This soft is applied for Hematoxyline + DAB staining. Script uses hardcoded stain matrix determined for our lab's dyes. You should determine your own for better result using ImageJ and hyperlink above. Determined custom matrix should replace the default one. For additional information see the comments in code.

After DAB separation, script determines the DAB-positive area using the default or user-defined threshold. The empty areas are excluded from the final realative area measurement as the sample could contain free space, which would affect the result accuracy.

Script creates the result folder inside the --path. Statistics, log and synthetic images for each sample are saved there.
### Examples
You can find test images in this repository.
#### Synthetic image examples
Script will render this type of image for **each of your samples**. User should control the result to be sure that the threshold values are right
![Synthetic image example 1](https://github.com/meklon/DAB_analyzer/blob/master/test%20images/result%20example/Native_Pan_05_analysis.png "Synthetic image example")

![Synthetic image example 2](https://github.com/meklon/DAB_analyzer/blob/master/test%20images/result%20example/Alex_Pan_08_analysis.png "Synthetic image example")
#### Log example
```
Created result directory
Images for analysis: 4
Image 1/4 saved: /home/meklon/temp/sample/result/Native_Lam_08_analysis.png
Image 2/4 saved: /home/meklon/temp/sample/result/Native_Lam_09_analysis.png
Image 3/4 saved: /home/meklon/temp/sample/result/Native_Pan_01_analysis.png
Image 4/4 saved: /home/meklon/temp/sample/result/Native_Pan_02_analysis.png
CSV saved: /home/meklon/temp/sample/result/test.csv
Analysis time: 5.4 seconds
Average time per image: 1.3 seconds
```
#### CSV output example
Filename | DAB-positive area, pixels | Empty area, % | DAB-positive area, %
------------ | ------------- | ------------- | -------------
Alex_Pan_06.jpg|1575294.0|20.31|61.55
Native_Pan_05.jpg|382690.0|16.26|14.23
Native_Trop_02.jpg|248915.0|28.42|10.83

### User manual
Place all the sample images (8-bit) inside the separate folder. Subdirectories are excluded from analysis. Use the following options:

*-p, --path* (obligate) - path to the target directory with samples

*-t, --thresh* (optional) - threshold for DAB+ area separation. If empty the default value would be used (threshDefault = 55).

*-e, --empty* (optional) - threshold for **empty area** separation. If empty the default value would be used (threshEmptyDefault = 92).

*-s, --silent* (otional) - if True, the real-time synthetic image visualisation would be supressed. The output will be just saved in the result folder.

####Example
````
python dab_deconv_area.py -p /home/meklon/Data/sample/test/ -t 60 -e 89 -s 
````

### Image samples requirements
1. Image samples' **white balance should be normalized**! It is important to get the right colors of stains before separation. I could suggest free software like [Rawtherapee](http://rawtherapee.com/)
2. Images should be acquired using the **same exposure values**
3. Threshold should be the same at the whole image sequence if you want to compare them
4. It would be better to use the manual mode in microscope camera to be sure, that your images were taken with the same parameters.
5. Don't change light intensity in microscope during the sequence acquiring.

### Authorship
Gumenyuk Ivan, Kuban state medical university, Russia.
