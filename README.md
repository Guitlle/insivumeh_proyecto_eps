## Installing CPT

First download CPT 17.7.4 from the official page, then untar and follow these instructions to build. These were run on manjaro but you can adapt it to your linux distro.

You need gfortran:
```
pacman -S gcc-fortran
```

(I had to add -fPIE to CCFLAGS to the lapack Makefile because it was complaining with this message: `/usr/bin/ld: lapack/lapack/liblapack.a(dlamch.o): relocation R_X86_64_32 against '.rodata' can not be used when making a PIE object; recompile with -fPIE`)
Download CPT, and make:
```
make distclean
make
make INSTALL_DIR=_cpt_dir_ install
```
This generates a bin folder in the install dir, I put it in the same CPT folder.

Make a bash file to activate this environment:
```
export PATH=$PATH:_cpt_dir_/bin
export CPT_BIN_DIR=_cpt_dir_/bin
```

Create and activate environment 
```
python -m venv devenv
```

Install requirements.txt
```
pip install -r requirements.txt
```

Setup env
```
source devenv/bin/activate
python -m ipykernel install --user --name=myenv
```


Had to reinstall shapely to avoid segment faults:
```
pip uninstall shapely
pip install --no-binary shapely shapely==1.8.5
```

When installing requirements you may see an error because of missing GEOS and Proj packages, do something like the following to install
```
pacman -S geos proj cairo gobject-introspection
```

Clone pycpt repo:
```
git clone https://bitbucket.org/py-iri/iri-pycpt.git
```

