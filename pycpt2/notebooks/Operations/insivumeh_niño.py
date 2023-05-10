import cptdl as dl 
import cptio as cio 
import cptcore as cc 
import cptextras as ce 


import xarray as xr 
import datetime as dt 
from pathlib import Path 
import matplotlib.pyplot as plt 
import cartopy.crs as ccrs
import numpy as np

import cartopy.feature as cartopyFeature

from PIL import Image
import os

import datetime
from requests import HTTPError


force_download = False
perform_analysis = True


case_name = "pycpt_GTM_EPS_NIÑO"
case_directory = f'/home/guillermo/DEV/EPS/cases/{case_name}'
os.makedirs(case_directory, exist_ok=True)

MOS = 'CCA'
predictor_names = [ 
    "CCSM4.SST", 
    "CanSIPSIC3.SST",
    "GEOSS2S.SST",
    "SPEAR.SST", 
    "CFSv2.SST",
    
    "SEAS5.SST",
    "METEOFRANCE8.SST",
    "GLOSEA6.SST"
]
predictand_name = 'UCSB.PRCP' # ERSSTV5.SST

download_args = { 
   # 'fdate':
   #   the initialization date of the model forecasts / hindcasts
   #   this field is defined by a python datetime.datetime object
   #   for example: dt.datetime(2022, 5, 1) # YYYY, MM, DD as integers
   #   The year field is only used for forecasts, otherwise ignored
   #   The day field is only used in subseasonal forecasts, otherwise ignored
   #   The month field is an integer representing a month - ie, May=5
  'fdate':  dt.datetime(2023, 4, 1), #dt.datetime(2022, 6, 1),  
    
   # 'first_year':
   #   the first year of hindcasts you want. **NOT ALL MODELS HAVE ALL YEARS**
   #   double check that your model has hindcast data for all years in [first_year, final_year]
   #   This field is defined by a python integer representing a year, ie: 1993
  'first_year': 1993,  
    
   # 'final_year':
   #   the final year of hindcasts you want. **NOT ALL MODELS HAVE ALL YEARS**
   #   double check that your model has hindcast data for all years in [first_year, final_year]
   #   This field is defined by a python integer representing a year, ie: 2016
  'final_year': 2016,  
    
   # 'predictor_extent':
   #   The geographic bounding box of the climate model data you want to download
   #   This field is defined by a python dictionary with the keys "north", "south",
   #   "east", and "west", each of which maps to a python integer representing the 
   #   edge of a bounding box. i.e., "north" will be the northernmost boundary,
   #   "south" the southernmost boundary. Example: {"north": 90, "south": 90, "east": 0, "west": 180}
  'predictor_extent': {
    'east':  -120,
    'west': -170, 
    'north': 5,
    'south': -5
  }, 
    
   # 'predictand_extent':
   #   The geographic bounding box of the observation data you want to download
   #   This field is defined by a python dictionary with the keys "north", "south",
   #   "east", and "west", each of which maps to a python integer representing the 
   #   edge of a bounding box. i.e., "north" will be the northernmost boundary,
   #   "south" the southernmost boundary. Example: {"north": 90, "south": 90, "east": 0, "west": 180}
  'predictand_extent': {
    'east':  -70,
    'west': -120, 
    'north': 40,
    'south': -5
  },

    
   # 'lead_low': 
   #   the number of months from the first of the initialization month to the center of 
   #   the first month included in the target period. Always an integer + 0.5. 
   #   this field is defined by a python floating point number 
   #   for example  a lead-1 forecast would use lead_low=1.5, if you want init=may, target=Jun-..
  'lead_low': 1.5,
    
   # 'lead_high': 
   #   the number of months from the first of the initialization month to the center of 
   #   the last month included in the target period. Always an integer + 0.5. 
   #   this field is defined by a python floating point number 
   #   for example  a forecast initialized in may, whose target period ended in Aug, 
   #   would use lead_high=3.5
  'lead_high': 3.5, 
    
   # 'target': 
   #   Mmm-Mmm indicating the months included in the target period of the forecast. 
   #   this field is defined by a python string, with two three-letter month name abbreviations 
   #   whose first letters are capitalized, and all other letters are lowercase
   #   and who are separated by a dash character. 
   #   for example, if you wanted a JJA target period, you would use 'Jun-Aug'
  'target': 'May-Jul',#'Jul-Sep',
    
   # 'filetype':
   #   the filetype to be downloaded. for now, it saves a lot of headache just to set this equal
   #   to 'cptv10.tsv' which is a boutique plain-text CPT filetype based on .tsv + metadata
  'filetype': 'cptv10.tsv'
}

cpt_args = { 
    'transform_predictand': None,  # transformation to apply to the predictand dataset - None, 'Empirical', 'Gamma'
    'tailoring': None,  # tailoring None, 'Anomaly', 'StdAnomaly', or 'SPI' (SPI only available on Gamma)
    'cca_modes': (1,5), # minimum and maximum of allowed CCA modes 
    'x_eof_modes': (1,5), # minimum and maximum of allowed X Principal Componenets 
    'y_eof_modes': (1,5), # minimum and maximum of allowed Y Principal Components 
    'validation': 'crossvalidation', # the type of validation to use - crossvalidation, retroactive, or doublecrossvalidation
    'drymask': False, #whether or not to use a drymask of -999
    'scree': True, # whether or not to save % explained variance for eof modes
    'crossvalidation_window': 5,  # number of samples to leave out in each cross-validation step 
    'synchronous_predictors': True, # whether or not we are using 'synchronous predictors'
}

#extracting domain boundaries and create house keeping
domain = download_args['predictor_extent']
e,w,n,s = domain.values()

domainFolder = f"{w}W-{e}E_to_{s}S-{n}N"

domainDir = f'{case_directory}/{domainFolder}'
os.makedirs(case_directory, exist_ok=True)
print("DOMAIN DIR: ", domainDir)
dataDir = f'{case_directory}/{domainFolder}/data'
os.makedirs(dataDir, exist_ok=True)
figDir = f'{case_directory}/{domainFolder}/figures'
os.makedirs(figDir, exist_ok=True)
outputDir = f'{case_directory}/{domainFolder}/output'
os.makedirs(outputDir, exist_ok=True)
config_file = ce.save_configuration(case_directory+'/.config', download_args, cpt_args, MOS, predictor_names, predictand_name )

# Download observations data
# Deal with "Cross-year issues" where either the target season crosses Jan 1 (eg DJF),
# or where the forecast initialization is in the calendar year before the start of the target season
# (eg JFM from Dec 1 sart)

fmon=download_args['fdate'].month
tmon1 = fmon + download_args['lead_low'] # first month of the target season
tmon2 = fmon + download_args['lead_high'] # last month of the target season
download_args_obs = download_args.copy()


# For when the target season crossing Jan 1 (eg DJF)
# (i.e., when target season starts in the same calendar year as the forecast init
# and ends in the following calendar year)
# Here the final year of the obs dataset needs to be incremented by 1.
if tmon1 <= 12.5 and tmon2 > 12.5:
    download_args_obs['final_year'] +=1

# For JFM, FMA .. with forecast initialization in the previous year.
# (i.e., when target season starts in the calendar year after the forecast init.)
# Here both the first and final year of the obs dataset need to be incremented by 1.
if tmon1 > 12.5:
    download_args_obs['first_year'] +=1
    download_args_obs['final_year'] +=1

if not os.path.exists(f'{dataDir}/{predictand_name}.nc') or force_download:
    Y = dl.download(dl.observations[predictand_name],
                    f'{dataDir}/{predictand_name}.tsv',
                    **download_args_obs,
                    verbose=True,
                    use_dlauth=False)
    Y = getattr(Y, [i for i in Y.data_vars][0])
    Y.to_netcdf(f'{dataDir}/{predictand_name}.nc')
else:
    print("Predictand data already downloaded")
    Y = xr.open_dataset(f'{dataDir}/{predictand_name}.nc')
    Y = getattr(Y, [i for i in Y.data_vars][0])

# download hindcast data
hindcast_data = []
for model in predictor_names:
    if not os.path.exists(f"{dataDir}/{model}.nc") or force_download:
        X = dl.download(dl.hindcasts[model],
                        f"{dataDir}/{model}.tsv",
                        **download_args,
                        verbose=True,
                        use_dlauth=False)
        X = getattr(X, [i for i in X.data_vars][0])
        X.name = Y.name
        X.to_netcdf(f"{dataDir}/{model}.nc")
    else:
        print("Predictor data already downloaded", model)
        X = xr.open_dataset(f"{dataDir}/{model}.nc")
        X = getattr(X, [i for i in X.data_vars][0])
        X.name = Y.name
    hindcast_data.append(X)

# download forecast data
forecast_data = []
for model in predictor_names:
    if not os.path.exists(f"{dataDir}/{model}_f.nc") or force_download:
        try:
            F = dl.download(dl.forecasts[model],
                            f"{dataDir}/{model}_f.tsv",
                            **download_args,
                            verbose=True,
                            use_dlauth=False)
            F = getattr(F, [i for i in F.data_vars][0])
            F.name = Y.name
            F.to_netcdf(f"{dataDir}/{model}_f.nc")
        except HTTPError as httperr:
            print(f"ERROR: No se encontró datos de forecast para el modelo {model} {httperr}")
            F = None
    else:
        print("Forecast data already downloaded", model)
        F = xr.open_dataset(f"{dataDir}/{model}_f.nc")
        F = getattr(F, [i for i in F.data_vars][0])
        F.name = Y.name
    forecast_data.append(F)


if perform_analysis is not True:
    print("Skipping analysis...")
    exit()
# Perform analysis
hcsts, fcsts, skill, pxs, pys = [], [], [], [], []

for i, model_hcst in enumerate(hindcast_data):
    print("Ejecutando análisis del modelo: ", predictor_names[i].split(".")[0])

    try:
        # fit CCA model between X & Y and produce real-time forecasts for F
        cca_h, cca_rtf, cca_s, cca_px, cca_py = cc.canonical_correlation_analysis(model_hcst, Y, \
        F=forecast_data[i], **cpt_args, cpt_kwargs={"interactive": False})

    #         fit CCA model again between X & Y, and produce in-sample probabilistic hindcasts
    #         this is using X in place of F, with the year coordinates changed to n+100 years
    #         because CPT does not allow you to make forecasts for in-sample data
    #        cca_h, cca_f, cca_s, cca_px, cca_py = cc.canonical_correlation_analysis(model_hcst, Y, \
    #        F=ce.redate(model_hcst, yeardelta=48), **cpt_args)
    #        cca_h = xr.merge([cca_h, ce.redate(cca_f.probabilistic, yeardelta=-48), ce.redate(cca_f.prediction_error_variance, yeardelta=-48)])

    #         # use the in-sample probabilistic hindcasts to perform probabilistic forecast verification
    #         # warning - this produces unrealistically optimistic values
    #        cca_pfv = cc.probabilistic_forecast_verification(cca_h.probabilistic, Y, **cpt_args)
    #        cca_s = xr.merge([cca_s, cca_pfv])

        hcsts.append(cca_h)
        fcsts.append(cca_rtf)
        skill.append(cca_s.where(cca_s > -999, other=np.nan))
        pxs.append(cca_px)
        pys.append(cca_py)

        cca_h.to_netcdf(f"{outputDir}/{predictor_names[i]}_crossvalidated_cca_hindcasts.nc")
        if cca_rtf is not None:
            cca_rtf.to_netcdf(f"{outputDir}/{predictor_names[i]}_realtime_cca_forecasts.nc")
        cca_s.to_netcdf(f"{outputDir}/{predictor_names[i]}_skillscores_cca.nc")
        cca_px.to_netcdf(f"{outputDir}/{predictor_names[i]}_cca_x_spatial_loadings.nc")
        cca_py.to_netcdf(f"{outputDir}/{predictor_names[i]}_cca_y_spatial_loadings.nc")
    except Exception as error:
        print("ERROR:", error)
