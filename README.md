# DAB_analyzer
Python soft for DAB-chromagen analysis.

### Application:
Quantative analysis of extracellular matrix proteins in IHC-analysis, designed for scientists in biotech sphere. 

### Requirements:
Python 2.7 (Don't tested Python 3+ versions)

Python libraries: numpy, scipy, skimage, PIL, matplotlib, argparse,os, csv, timeit

### Interface type:
No GUI, command line interface only.

### Basic principles:
Script uses the **color deconvolution method**. It was described by [G. Landini](http://www.mecourse.com/landinig/software/cdeconv/cdeconv.html). See also *Ruifrok AC, Johnston DA. Quantification of histochemical staining by color deconvolution. Anal Quant Cytol Histol 23: 291-299, 2001.*
