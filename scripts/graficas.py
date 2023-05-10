import cartopy.crs as ccrs
import cartopy.feature as cartopyFeature
import datetime as dt
import numpy as np
import os
import xarray as xr

from matplotlib import pyplot as plt
from PIL import Image

plot_skill_metrics = ['pearson', 'spearman', 'two_alternative_forced_choice', 'roc_area_below_normal', 'roc_area_above_normal']

def plot_skills(casedir: str, skills: dict, filename, title, skill_metrics = [], plot_models = []):
    # limits = [(-1, 1), (-1, 1), (0, 100), (0,1), (0,1)]
    missing_value_flag = -999
    nskills = len(plot_models)
    fig, ax = plt.subplots(
        nrows=nskills,
        ncols=len(skill_metrics),
        subplot_kw={'projection':ccrs.PlateCarree()},
        figsize=(4*len(skill_metrics), 4*nskills)
    )
    fig.suptitle(title)
    if nskills == 1:
        ax = [ax]

    i = 0
    for model, skill in skills.items():
        if model not in plot_models:
            continue
        for j, skill_metric in enumerate(skill_metrics):
            cbtitle = skill_metric.upper()
            if skill_metric.startswith("two_alt"):
                cbtitle = "2AFC"
                limits = (0,100)
            elif skill_metric == 'spearman':
                limits = (-1,1)
            elif skill_metric.startswith("roc_area_above_normal"):
                limits = (0,1)
                cbtitle = "ROC Above Normal"
            elif skill_metric.startswith("roc_area_below_normal"):
                limits = (0,1)
                cbtitle = "ROC Below Normal"
            n = getattr(skill, skill_metric)\
            .where(getattr(skill, skill_metric) > missing_value_flag).plot(
                ax=ax[i][j], vmin=limits[0], vmax=limits[1],
                cbar_kwargs = {"label": ""},
                cmap ="Spectral"
            )
            ax[i][j].set_xlim(-93,-87)
            ax[i][j].set_ylim(12,19)
            ax[i][j].coastlines()
            ax[i][j].add_feature(cartopyFeature.BORDERS)
            ax[0][j].set_title(cbtitle)

        ax[i][0].text(-0.07, 0.55, model.upper(), va='bottom', ha='center', rotation='vertical', rotation_mode='anchor',
                      transform=ax[i][0].transAxes)
        i+=1

    fig.savefig(f"{casedir}/figures/{filename}.png", bbox_inches='tight')
    plt.close()

def plot_ccamodes(casedir, ccamodes):
    nmodes = 5
    vmin=-10
    vmax = 10
    missing_value_flag = -999
    nmodels = len(ccamodes.keys())
    modelc=-1
    for model, modesdata in ccamodes.items():
        pxs = modesdata["pxs"]
        pys = modesdata["pys"]
        modelc+=1
        fig = plt.figure(figsize=(6*nmodes, 10), layout="tight")
        fig.suptitle(model, fontsize=24)

        for mode in range(nmodes):
            cancorr = np.correlate(pxs.x_cca_scores[:,mode],pys.y_cca_scores[:,mode])
            gs = fig.add_gridspec(3, nmodes, height_ratios=[4,4,2], width_ratios=[1]*nmodes)
            ax1 = fig.add_subplot(gs[0, mode], projection = ccrs.PlateCarree())
            ax2 = fig.add_subplot(gs[1, mode], projection = ccrs.PlateCarree())
            ax3 = fig.add_subplot(gs[2, mode])
            ts_ax = ax3


            map1_ax = ax1
            map2_ax = ax2

            map1_plot = pxs.x_cca_loadings.isel(Mode=mode)\
                .where(pxs.x_cca_loadings.isel(Mode=mode) > missing_value_flag)\
                .plot(ax=map1_ax, cbar_kwargs={"label": "X CCA MODE"}, cmap ="PiYG")
            map2_plot = pys.y_cca_loadings.isel(Mode=mode)\
                .where(pys.y_cca_loadings.isel(Mode=mode) > missing_value_flag)\
                .plot(ax=map2_ax, cbar_kwargs={"label": "Y CCA MODE"}, cmap ="PiYG")

            map1_ax.set_xticks([])
            map1_ax.set_yticks([])
            map2_ax.set_xticks([])
            map2_ax.set_yticks([])
            map1_ax.set_xlabel(None)
            map2_ax.set_xlabel(None)
            map1_ax.set_ylabel(None)
            map2_ax.set_ylabel(None)#map1_ax.set_xlim(-93,-87)
            #map1_ax.set_ylim(12,19)
            #map2_ax.set_xlim(-93,-87)
            #map2_ax.set_ylim(12,19)
            map1_ax.set_title(None)
            map2_ax.set_title(None)
            map1_ax.add_feature(cartopyFeature.BORDERS)
            map2_ax.add_feature(cartopyFeature.BORDERS)
            map1_ax.coastlines()
            map2_ax.coastlines()
            axtitle = f"M{mode+1} - CanCorr={cancorr[0]:.2f}"
            ax1.set_title(axtitle)

            ts = xr.concat(
                [pxs.x_cca_scores.isel(Mode=mode), pys.y_cca_scores.isel(Mode=mode)],
                'M'
            ).assign_coords({'M': ['x', 'y']})
            primitive = ts.plot.line(marker='x', ax=ts_ax, markersize=8, hue='M')
            ts_ax.grid(axis = 'x', linestyle = '-.')
            ts_ax.spines['top'].set_visible(False)
            ts_ax.spines['right'].set_visible(False)
            ts_ax.spines['bottom'].set_visible(False)
            ts_ax.legend(handles=primitive, labels = list(ts.coords['M'].values), loc="best")
            ts_ax.set_ylabel("CCA Scores")
        print("Guardando CCA modes de modelo", model)
        fig.savefig(f"{casedir}/figures/cca_modes_{model}.png", bbox_inches='tight')
        plt.close()


from casos import cases, base_config


if __name__ == "__main__":
    base_case_dir = base_config["base_case_directory"]
    for case in cases:
        
        # TODO: filtrar
        if "MJJ" not in case["case_name"]:
            continue
            
            
        print(f"Generando gráficas de skill para el caso {case['case_name']}")
        domain = case["download_args"]['predictor_extent']
        e,w,n,s = domain.values()
        domain = f"{w}W-{e}E_to_{s}S-{n}N"

        casedir = f"{base_case_dir}/{case['case_name']}/{domain}"
        outputdir = f"{casedir}/output"
        outputs = os.listdir(outputdir)
        skills = {}
        for filename in filter(lambda item: "skillscores_cca.nc" in item, outputs):
            model = filename.split(".")[0]
            print(f"Loading data file {filename}")
            skills[model] = xr.open_dataset(f"{outputdir}/{filename}")
        
        #
        # plot_skills(casedir, skills, f"{}")
        plot_skills("/home/guillermo/DEV/EPS/temp", 
                    skills, 
                    f"skills_NMME_{case['case_name']}",
                    f"{case['case_name']}",
                    ["spearman", "two_alternative_forced_choice"],
                    [key for key in skills.keys() if key not in ["GLOSEA6", "SEAS5", "METEOFRANCE8"]]
                   )
        plot_skills("/home/guillermo/DEV/EPS/temp", 
                    skills, 
                    f"skills_C3S_{case['case_name']}",
                    f"{case['case_name']}",
                    ["spearman", "two_alternative_forced_choice"],
                    [key for key in skills.keys() if key in ["GLOSEA6", "SEAS5", "METEOFRANCE8"]]
                   )
        plot_skills("/home/guillermo/DEV/EPS/temp", 
                    skills, 
                    f"skill_roc_NMME_{case['case_name']}",
                    f"{case['case_name']}",
                    ['roc_area_below_normal', 'roc_area_above_normal'],
                    [key for key in skills.keys() if key not in ["GLOSEA6", "SEAS5", "METEOFRANCE8"]]
                   )
        plot_skills("/home/guillermo/DEV/EPS/temp", 
                    skills, 
                    f"skill_roc_C3S_{case['case_name']}",
                    f"{case['case_name']}",
                    ['roc_area_below_normal', 'roc_area_above_normal'],
                    [key for key in skills.keys() if key in ["GLOSEA6", "SEAS5", "METEOFRANCE8"]]
                   )
        continue
        
        print(f"Generando gráficas de EOF CCA para el caso {case}")
        ccamodes = {}
        for filename in filter(lambda item: "_spatial_loadings.nc" in item, outputs):
            model = filename.split(".")[0]
            print(f"Loading data file {filename}")
            if model not in ccamodes:
                ccamodes[model] = {}
            ccamodes[model]["pxs" if "_x_" in filename else "pys"] = xr.open_dataset(f"{outputdir}/{filename}")

        plot_ccamodes(casedir, ccamodes)
