# DAB analyzer
Python soft for DAB-chromagen analysis.

### Application:
Quantitative analysis of extracellular matrix proteins in IHC-analysis, designed for scientists in biotech sphere. 

### Requirements:
Python 2.7 (Not tested with Python 3+ versions)

Python libraries: numpy, scipy, skimage, PIL, matplotlib, argparse,os, csv, timeit

### Interface type:
No GUI, command line interface only.

### Basic principles:
Script uses the **color deconvolution method**. It was described by [G. Landini](http://www.mecourse.com/landinig/software/cdeconv/cdeconv.html). See also: *Ruifrok AC, Johnston DA. Quantification of histochemical staining by color deconvolution. Anal Quant Cytol Histol 23: 291-299, 2001.*

Color deconvolution is used to separate stains in multi-stained sample. This soft is applied for Hematoxyline + DAB staining. Script uses hardcoded stain matrix determined for our lab's dyes. You should determine your own for better result using ImageJ and hyperlink above. Determined custom matrix should replace the default one. For additional information see the comments in code.

After DAB separation, script determines the DAB-positive area using the default or user-defined threshold. The empty areas are excluded from the final realative area measurement as the sample could contain free space, which would affect the result accuracy.

Script creates the result folder inside the --path. Statistics, log and synthetic images for each sample are saved there.
### User manual
Place all the sample images (8-bit) inside the separate folder. Subdirectories are excluded from analysis. Use the following options:

*-p, --path* (obligate) - path to the target directory with samples

*-t, --thresh* (optional) - threshold for DAB+ area separation. If empty the default value would be used.

*-s, --silent* (otional) - if True, the real-time synthetic image visualisation would be supressed. The output will be just saved in the result folder.

### Authorship
Gumenyuk Ivan, Kuban state medical university, Russia.
