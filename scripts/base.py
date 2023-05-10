import cptdl as dl
import cptio as cio
import cptcore as cc
import cptextras as ce
import datetime
import datetime as dt
import numpy as np
import os
import xarray as xr

from requests import HTTPError


def setup(config):
    case_name = config["case_name"]
    print(f"Setting up case {case_name}")
    download_args = config["download_args"]
    base_case_directory = config["base_case_directory"]
    cpt_args, MOS, predictor_names, predictand_name = (config["cpt_args"], config["MOS"], config["predictor_names"],
                                                       config["predictand_name"])
    case_directory = f"{base_case_directory}/{case_name}"
    os.makedirs(case_directory, exist_ok=True)

    #extracting domain boundaries and create house keeping
    domain = download_args['predictor_extent']
    e,w,n,s = domain.values()

    domainFolder = f"{w}W-{e}E_to_{s}S-{n}N"

    domainDir = f'{case_directory}/{domainFolder}'
    print("DOMAIN DIR: ", domainDir)
    os.makedirs(case_directory, exist_ok=True)
    dataDir = f'{case_directory}/{domainFolder}/data'
    os.makedirs(dataDir, exist_ok=True)
    figDir = f'{case_directory}/{domainFolder}/figures'
    os.makedirs(figDir, exist_ok=True)
    outputDir = f'{case_directory}/{domainFolder}/output'
    os.makedirs(outputDir, exist_ok=True)
    config_file = ce.save_configuration(case_directory+'/.config', download_args, cpt_args, MOS, predictor_names, predictand_name )

    return config, domainDir, dataDir, figDir, outputDir, config_file


def download(setup_output):
    config, domainDir, dataDir, figDir, outputDir, config_file = setup_output

    case_name = config["case_name"]
    download_args = config["download_args"]
    force_download = config["force_download"]
    cpt_args, MOS, predictor_names, predictand_name = (config["cpt_args"], config["MOS"], config["predictor_names"], config["predictand_name"])
    print(f"Fetching data for case {case_name}")
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
                            pressure=850,
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
                                pressure=850,
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
    return setup_output, hindcast_data, forecast_data, Y

def analysis(downloads_output):
    setup_output, hindcast_data, forecast_data, Y = downloads_output
    config, domainDir, dataDir, figDir, outputDir, config_file = setup_output
    case_name = config["case_name"]
    download_args = config["download_args"]
    perform_analysis = config.get("perform_analysis", False)
    cpt_args, MOS, predictor_names, predictand_name = (config["cpt_args"], config["MOS"], config["predictor_names"],
                                                       config["predictand_name"])
    print(f"MOS Analysis for case {case_name}")

    if perform_analysis is not True:
        print("Skipping analysis...")
    # Perform analysis
    hcsts, fcsts, skill, pxs, pys = [], [], [], [], []

    for i, model_hcst in enumerate(hindcast_data):
        print("Ejecutando análisis CCA del modelo: ", predictor_names[i].split(".")[0])

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
