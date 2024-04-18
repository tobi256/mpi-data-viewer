import pandas as pd
from dataLib.Messenger import Messenger as m


def read_dat_file(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if line[0:2] != '#@':
                    break

            header = [x.strip() for x in line.split('\t')]
            return pd.read_csv(file, delimiter='\t', names=header)
    except IOError as e:
        m.error(f"Could not read file {file_path}")
        m.debug(f"File error: {e}")





