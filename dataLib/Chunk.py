from dataLib.TimingData import TimingData
from dataLib.Messenger import Messenger as m
import pandas as pd


class Chunk:
    def __init__(self, td: TimingData, idx_start: int, idx_end: int, p_start: int, p_end: int):
        self.td = td
        self.idx_start = idx_start
        self.idx_end = idx_end
        self.p_start = p_start
        self.p_end = p_end
        self.__data = None  # used only if chunk is standalone

    def __del__(self):
        if self.__data is None:
            self.td._deregister_locking_chunk(self)

    def get_data(self) -> pd.DataFrame:
        if self.__data is not None:
            return self.__data
        else:
            df = self.td.get_loaded_dataframe()
            if df is None:
                # this should never happen, as data which is referred to by chunk is drop-locked
                m.critical("Chunk trying to access data which was dropped")
            return df[(df['idx'].between(self.idx_start, self.idx_end)) & (df['p'].between(self.p_start, self.p_end))]

    def make_standalone(self):
        self.__data = self.get_data().copy()
        self.td._deregister_locking_chunk(self)



