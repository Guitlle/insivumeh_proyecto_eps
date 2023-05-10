### Simple setup for PyCPTv2
------

Setup and activate virtual environment
```
python -m venv devenv
source devenv/bin/activate
```

Install requirements
```
pip install -r requirements.txt
```

Install cpt-dl:
```
git clone https://github.com/iri-pycpt/cpt-dl
RECIPE_DIR=`pwd`/cpt-dl/conda-recipe python cpt-dl/conda-recipe/setup.py install
```

Install cpt-core
```
git clone https://github.com/iri-pycpt/cpt-core --single-branch
RECIPE_DIR=`pwd`/cpt-core/conda-recipe python cpt-core/conda-recipe/setup.py install
```

Compile CPT in cpt-core:
```
cd devenv/lib/python3.10/site-packages/cptcore/fortran/Linux/CPT/
make
```

Make failed because lapack/lapack/make.inc was missing, but I copied the make.example.inc and it worked ok. It also had bad flags for fortran. I commented an if clause in the make file that worked only for conda environments.

Install CPT-extras:
```
git clone https://github.com/iri-pycpt/CPT-EXTRAS
cd CPT-EXTRAS
python setup.py install
```
