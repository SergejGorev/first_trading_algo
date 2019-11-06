import quandl
import os
import pandas as pd

quandl.ApiConfig.api_key = 'XJPvvU9QyVvM8fMT1LE9'
cot_period = 26
dir = 'data\\'
cont_contract_month_base = 2

quandl_cot_futures_map = {
    "ZN": "043602",
    "ZS": "005602",
    "ZM": "026603",
    "ZL": "007601",
    "ZC": "002602",
    "ZW": "001602",
    "HE": "054642",
    "LE": "057642",
    "GC": "088691",
    "SI": "084691",
    "HG": "085692",
    "CL": "067651",
    "HO": "022651",
    "RB": "111659",
    "NG": "023651",
    "A6": "232741",
    "B6": "096742",
    "D6": "090741",
    "E6": "099741",
    "J6": "097741",
    "S6": "092741",
    "SB": "080732",
    "KC": "083731",
    "CC": "073732",
    "CT": "033661",
    "ES": "13874A",
    "YM": "12460P",
    "NQ": "209742",
    "PA": "075651",
    "PL": "076651",
    "AUP": "191693",
    "HRC": "192651",
    "ZR": "039601",
    "ZO": "004603",
    # "DL": "052641",
    "OJ": "040701",
    "LB": "058643",
    "FC": "061641",
    "N6": "112741",
}

quandl_cme_futures_map = {
    "ZN": "TY",
    "ZS": "S",
    "ZM": "SM",
    "ZL": "BO",
    "ZC": "C",
    "ZW": "W",
    "HE": "LN",
    "LE": "LC",
    "GC": "GC",
    "SI": "SI",
    "HG": "HG",
    "CL": "CL",
    "HO": "HO",
    "RB": "RB",
    "NG": "NG",
    "A6": "AD",
    "B6": "BP",
    "D6": "CD",
    "E6": "EC",
    "J6": "JY",
    "S6": "SF",
    "ES": "ES",
    "YM": "YM",
    "NQ": "NQ",
    "PA": "PA",
    "PL": "PL",
    "AUP": "ALI",
    "HRC": "HR",
    "ZR": "RR",
    "ZO": "O",
    # "DL": "052641", # Milk CME no idea
    "LB": "LB",
    "FC": "FC",
    "N6": "NE",
}

quandl_ice_futures_map = {
    "SB": "SB",  # ICE
    "KC": "KC",  # ice
    "CC": "CC",  # ice
    "CT": "CT",  # ICE
    "OJ": "OJ",  # ICE
}
#Generate dict value - future IDs for Quandl to get COT Report
def quandl_cot_future():
    for future in quandl_cot_futures_map.values():
        yield f'CFTC/{future}_F_L_ALL'

#Request COT Data for each future and create COT Index
def df_cot_index():
    for future in quandl_cot_future():
        data = quandl.get(future)[['Commercial Long', 'Commercial Short']]
        com_net = data['Commercial Long'] - data['Commercial Short']
        com_max = com_net.rolling(cot_period).max()
        com_min = com_net.rolling(cot_period).min()
        com_idx = 100 * (com_net - com_min) / (com_max-com_min)
        merge = pd.merge(data, com_idx.to_frame(), left_index=True, right_index=True).dropna()
        yield merge

#Generate file name
def file_name_generator():
    for future in quandl_cot_futures_map.keys():
        yield f'{future}_cot.csv'

#Create folder if it doesn't exists and save data into files
def write_into_file():
    try:
        os.makedirs(dir)
        print('Created Folder')
    except FileExistsError:
        pass
    counter = 1
    for data, file in zip(df_cot_index(), file_name_generator()):
        file_path = f'{dir}{file}'
        data.to_csv(path_or_buf=file_path)
        print(f'{100*counter/len(quandl_cot_futures_map)}% Done!')
        counter += 1

write_into_file()
#todo check the last row in files to see if the data is uptodate
#todo if not uptodate download data, for specific markets
#todo check when Quandl updates the data, in order to hard code when to update

#todo how to structure that script, classes or just functions