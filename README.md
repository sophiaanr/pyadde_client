# Python ADDE Client

This repo makes ADDE (Abstract Data Distribution Environment) protocol requests and displays images from the retrieved AREA files. Currently, it works for early GOES satellite imagery (GOES 1 to 7) from the 1970s to early 1990s. It can display the data in its original form as well as reproject the data to Geostationary, Plate Carree, Mollweide, and Robinson projections. More projections to come soon.

## Installation steps 

### Create Conda Environment

```
conda env create -f environment.yml
conda activate pyadde

```

### Clone and Install Required python modules

```
git clone https://github.com/sophiaanr/pyarea.git
cd pyarea
pip install .
cd ..
git clone https://github.com/sophiaanr/pyadde.git
cd pyadde
pip install .
cd ..
git clone https://gitlab.ssec.wisc.edu/sreiner/nvxgoes.git
cd nvxgoes
pip install .

```

## Run Script

```
conda activate pyadde  (if not already activated)
./fetchfile.py host=<host> group=<grp> descriptor=<desc> band=<band> position=<pos> file=<file> ...

```

## Help

```
./fetchfile.py -h
./fetchfile.py --help

```

### Examples:
`./fetchfile.py host=archive.ssec.wisc.edu user=DAS project=6999 group=AGOES02 descriptor=A-VIS file=AREA9998  unit=BRIT nlines=700 nelems=700 lmag=-22 emag=-22 stime=17.5 etime=17.5 position=0 band=1 day=1978055 netcdf=ncdf9998.nc`


`./fetchfile.py host=archive.ssec.wisc.edu user=DAS project=6999 group=AGOES02 descriptor=A-IR file=AREA9997 unit=BRIT nlines=99999 nelems=99999 lmag=1 emag=1 stime=17.5 etime=17.5 position=0 band=8 day=1978068 netcdf=ncdf9997.nc`
