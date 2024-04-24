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
        self.__mean_times_by_idx = None

    def __del__(self):
        if self.__data is None:
            self.td._deregister_locking_chunk(self)

    # all values calculated on basis of __data are removed
    def __reset_calcs(self):
        self.__mean_times_by_idx = None

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
        if self.__data is None:
            self.__data = self.get_data().copy()
            self.td._deregister_locking_chunk(self)

    def get_mean_times_by_idx(self):
        if self.__mean_times_by_idx is None:
            self.__mean_times_by_idx = self.get_data().groupby('idx').agg({'start': 'mean', 'end': 'mean'})
            self.__mean_times_by_idx.rename(columns={'start': 'm_start', 'end': 'm_end'}, inplace=True)
        return self.__mean_times_by_idx

    # Refactors the time to start at zero. The earliest start time is used as zero, all values are linearly recalculated
    def time_starts_zero_at_first(self):
        self.make_standalone()
        self.__reset_calcs()
        mini = self.__data[self.__data["idx"] == self.idx_start]['start'].min()
        self.__data[["start", "end"]] = self.__data[["start", "end"]].apply(lambda x: x - mini)


class ChunkList(list):
    def each_time_starts_zero_at_first(self):
        for a in self:
            a.time_starts_zero_at_first()

    def __getitem__(self, index):
        return super().__getitem__(index)
