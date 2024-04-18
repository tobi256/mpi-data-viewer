from dataLib.Messenger import Messenger as m
import dataLib.util as util


class DataManager:
    def __init__(self):
        self.logs = {}

    def read_timing(self, file_name: str, name: str = "hallo") -> None:
        m.debug(f"{file_name}, {name}")
        df = util.read_dat_file("../raw_time_data/allreduce_10/32_s1/1.dat")
        print(df)


