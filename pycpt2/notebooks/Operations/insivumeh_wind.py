from base import setup, download, analysis

config = {
    "force_download": False,
    "case_name": "pycpt_GTM_EPS_UA_JJA",
    "MOS": 'CCA',
    "predictor_names": [
        "CanSIPSIC3.UA",
        "CFSv2.UA",

        "SEAS5.UA",
        "METEOFRANCE8.UA",
        "GLOSEA6.UA"
    ],
    "predictand_name": 'UCSB.PRCP', # ERSSTV5.SST

    "download_args": {
        # 'fdate':
        #   the initialization date of the model forecasts / hindcasts
        #   this field is defined by a python datetime.datetime object
        #   for example: dt.datetime(2022, 5, 1) # YYYY, MM, DD as integers
        #   The year field is only used for forecasts, otherwise ignored
        #   The day field is only used in subseasonal forecasts, otherwise ignored
        #   The month field is an integer representing a month - ie, May=5
        'fdate':  dt.datetime(2023, 5, 1), #dt.datetime(2022, 6, 1),

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
          'east':  -70,
          'west': -120,
          'north': 40,
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
        'target': 'Jun-Aug',#'Jul-Sep',

        # 'filetype':
        #   the filetype to be downloaded. for now, it saves a lot of headache just to set this equal
        #   to 'cptv10.tsv' which is a boutique plain-text CPT filetype based on .tsv + metadata
        'filetype': 'cptv10.tsv'
    },

    "cpt_args": {
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
}


analysis(download(setup(config)))
