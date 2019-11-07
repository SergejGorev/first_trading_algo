import quandl
import os
import pandas as pd
import sys

#use this line the first time you use quandl. For more info see: https://github.com/quandl/quandl-python
# quandl.save_key("supersecret")

#this line afterwards
quandl.read_key()

cot_period = 26
dir = 'data\\'
continue_contract_month_base = 2

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

dict_list = (quandl_cot_futures_map, quandl_cme_futures_map, quandl_ice_futures_map)

#Request COT Data and Market Data for each future and create COT Index
def get_data(dictionary):
    if dictionary is quandl_cot_futures_map:
        for future in quandl_name_generator(dictionary):
            data = quandl.get(future)[['Commercial Long', 'Commercial Short']]
            com_net = data['Commercial Long'] - data['Commercial Short']
            com_max = com_net.rolling(cot_period).max()
            com_min = com_net.rolling(cot_period).min()
            com_idx = 100 * (com_net - com_min) / (com_max-com_min)
            merge = pd.merge(data, com_idx.to_frame(), left_index=True, right_index=True)
            merge = merge.dropna().rename(columns={0:'Commercial Index'})
            yield merge
    else:
        for future in quandl_name_generator(dictionary):
            data = quandl.get(future)#[['Open', 'High', 'Low', 'Settle', 'Volume']]
            yield data

#Generator for creating ticker names and file names
def quandl_name_generator(dictionary, file = None):
    if file is True:
        if dictionary is quandl_cot_futures_map:
            for future in dictionary.keys():
                yield f'{future}_cot.csv'
        else:
            for future in dictionary.keys():
                yield f'{future}.csv'
    else:
        if dictionary is quandl_cot_futures_map:
            for future in dictionary.values():
                yield f'CFTC/{future}_F_L_ALL'
        if dictionary is quandl_cme_futures_map:
            for future in dictionary.values():
                yield f'CHRIS/CME_{future}{continue_contract_month_base}'
        if dictionary is quandl_ice_futures_map:
            for future in dictionary.values():
                yield f'CHRIS/ICE_{future}{continue_contract_month_base}'

#Create folder if it doesn't exists and save data into files
def write_into_file():
    try:
        os.makedirs(dir)
        print('Created Folder')
    except FileExistsError:
        pass
    for dict in dict_list:
        print('Dictionary started...', end=' ')
        sys.stdout.flush()
        for data, file in zip(get_data(dict), quandl_name_generator(dict, file=True)):
            file_path = f'{dir}{file}'
            data.to_csv(path_or_buf=file_path)
        print('Done')

write_into_file()

#todo check when Quandl updates the data, in order to hard code when to update
