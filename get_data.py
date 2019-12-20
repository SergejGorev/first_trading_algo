import quandl
import os
import pandas as pd
import sys
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#In order to have more then 50 request a day, register account in quandl for FREE. You will get Credential Key. Use it.
# Reqest Limit is going to rise to 500 a day.
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
    # "ZR": "039601", #stahl
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

def get_data(dictionary, weekly=None) -> pd.DataFrame:
    '''
    Request COT Data and Market Data for each future and create COT Index
    :param dictionary: Ticker Names
    :param weekly: bool to get weekly data
    :return: DataFrame
    '''
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
    elif weekly is True:
        for future in quandl_name_generator(dictionary):
            data = quandl.get(future, collapse='weekly')
            yield data
    else:
        for future in quandl_name_generator(dictionary):
            data = quandl.get(future)#[['Open', 'High', 'Low', 'Settle', 'Volume']]
            yield data

#Generator for creating ticker names and file names
def quandl_name_generator(dictionary, file=None, weekly=None) -> str:
    '''
    Creates file names as string and ticker code for quandl query as string.
    :param dictionary: Takes a dictionary with ticker names.
    :param file: If its True, a file name going to be created. Else quandl ticker name.
    :param weekly: If weekly is true, file name is going to contain weekly in the suffix.
    :return: string
    '''
    if file is True:
        if dictionary is quandl_cot_futures_map:
            for future in dictionary.keys():
                yield f'{future}_cot.csv'
        elif weekly is True:
            for future in dictionary.keys():
                yield f'{future}_weekly.csv'
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


def write_into_file():
    '''
    Creates folder if it doesn't exists and save data into files
    '''
    try:
        os.makedirs(dir)
        print('Created Folder')
    except FileExistsError:
        pass
    for dict in dict_list:
        print('Daily. Dictionary started...', end=' ')
        sys.stdout.flush()
        for data, file in zip(get_data(dict), quandl_name_generator(dict, file=True)):
            file_path = f'{dir}{file}'
            data.to_csv(path_or_buf=file_path)
        print('Done')

    for dict in dict_list[1:]:
        print('Weekly. Dictionary started...', end=' ')
        sys.stdout.flush()
        for data, file in zip(get_data(dict, weekly=True), quandl_name_generator(dict, file=True, weekly=True)):
            file_path = f'{dir}{file}'
            data.to_csv(path_or_buf=file_path)
        print('Done')



def append_cot_to_market_file():
    '''
    Set all cot dates couple dates into the future since i dont have concrete release dates.
    Especially is tuesday interesting, cuz since ~1990 CFTC started to implement COT Report on weekly basis
    Calculation week is Tuesday BUT the Release is on Friday. To avoid look ahead bias, need to shift it up.
    :return: cleaned and merged symbol.csv file. Essentially overwrites the existing file.
    '''
    print('Start removing look ahead bias in COT... ', end=' ')
    sys.stdout.flush()
    symbol_dict = {**quandl_cme_futures_map, **quandl_ice_futures_map}
    for s in symbol_dict.keys():
        m_path = f'{dir}{s}.csv'
        cot_path = f'{dir}{s}_cot.csv'

        # Load content into DataFrames
        m_df = pd.read_csv(m_path, index_col='Date', parse_dates=True)
        cot_df = pd.read_csv(cot_path, index_col='Date', parse_dates=True)

        # merge them together
        merge = m_df.join(cot_df)
        merge = merge.reset_index()

        # reindex the cot to friday or next day on the index in the next week
        iter = merge[['Date', 'Commercial Index', 'Commercial Short', 'Commercial Long']]#.fillna(0)
        m_df = m_df.reset_index()

        # iterate over files and remove look ahead bias by shifting COT Dates forward to friday or further
        for v in iter.itertuples():
            if pd.notnull(v[2]):
                if v[1].weekday() == 0:
                    m_df.set_value(v[0] + 4,'Commercial Index', v[2])
                    m_df.set_value(v[0] + 4,'Commercial Short', v[3])
                    m_df.set_value(v[0] + 4,'Commercial Long', v[4])
                if v[1].weekday() == 1:
                    m_df.set_value(v[0] + 3, 'Commercial Index', v[2])
                    m_df.set_value(v[0] + 3, 'Commercial Short', v[3])
                    m_df.set_value(v[0] + 3, 'Commercial Long', v[4])
                if v[1].weekday() == 2:
                    m_df.set_value(v[0] + 2, 'Commercial Index', v[2])
                    m_df.set_value(v[0] + 2, 'Commercial Short', v[3])
                    m_df.set_value(v[0] + 2, 'Commercial Long', v[4])
                if v[1].weekday() == 3:
                    m_df.set_value(v[0] + 1, 'Commercial Index', v[2])
                    m_df.set_value(v[0] + 1, 'Commercial Short', v[3])
                    m_df.set_value(v[0] + 1, 'Commercial Long', v[4])
                if v[1].weekday() == 4:
                    m_df.set_value(v[0] + 5, 'Commercial Index', v[2])
                    m_df.set_value(v[0] + 5, 'Commercial Short', v[3])
                    m_df.set_value(v[0] + 5, 'Commercial Long', v[4])

        # write to csv
        m_df = m_df.set_index('Date')
        m_df.to_csv(m_path)
    print('Done')

# call everything
if __name__ == "__main__":
    write_into_file()
    append_cot_to_market_file()
    print('Application Finished')