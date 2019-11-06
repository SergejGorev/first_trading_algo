import quandl
import os
quandl.ApiConfig.api_key = 'XJPvvU9QyVvM8fMT1LE9'
cot_period = 26
cot_dir = '\\cot'
market_dir = '\\market'

quandl_cot_future_map = {
    "ZB": "020601",
    "ZN": "043602",
    "ZS": "005602",
    "ZM": "026603",
    "ZL": "007601",
    "ZC": "002602",
    "ZW": "001602",
    "KE": "001612",
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
    "RTY": "239742",
    "YM": "12460P",
    "NQ": "209742",
    "PA": "075651",
    "PL": "076651",
    "AUP": "191693",
    "HRC": "192651",
    "AEZ": "025651",
    "J26": "06765T",
    "ZR": "039601",
    "ZO": "004603",
    "DL": "052641",
    "JO": "040701",
    "LS": "058643",
    "GF": "061641",
    "SP": "138741",
    "DJIA": "12460P",
    "N6": "112741",
}

#Generate dict value - future IDs for Quandl to get COT Report
def quandl_cot_future():
    for future in quandl_cot_future_map.values():
        yield f'CFTC/{future}_F_L_ALL'

#Request COT Data for each future and create COT Index
def df_cot_index():
    for future in quandl_cot_future():
        data = quandl.get(future, columns=['Date', 'Commercial Long', 'Commercial Short'])
        com_net = data['Commercial Long']-data['Commercial Short']
        com_max = com_net.rolling(cot_period).max()
        com_min = com_net.rolling(cot_period).min()
        com_idx = 100 * (com_net - com_min) / (com_max-com_min)
        data.append(com_idx)
        yield data

#Generate file name
def file_name():
    for future in quandl_cot_future_map.keys():
        yield f'cot_{future}.csv'

#Create folder if it doesn't exists and save data into files
def write_into_file():
    try:
        os.makedirs(cot_dir)
    except FileExistsError:
        pass
    for data in df_cot_index():
        data.to_csv(f'{cot_dir}\\{file_name()}')

#If it exists check last row of each file when was the last update and load only new row(slice)

#todo check the last row in files to see if the data is uptodate

#todo if not uptodate download data, for specific markets

#todo check when Quandl updates the data, in order to hard code when to update

#todo how to structure that script, classes or just functions