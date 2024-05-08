from dataLib.TimingData import TimingData
from dataLib.Messenger import Messenger as m
from enum import Flag
from typing import Callable
import pandas as pd
from types import FunctionType


# If there is no singular Median, two points will be selected.
# note: using first and last in combination with other parameters may lead to errors.
#    Points will not be duplicated, and max, min and median are prioritized.
#    If point is first and min, it will be displayed as min.
class Filter(Flag):
    FIRST =     0b0000_0001  # entity with the lowest id in the set
    LAST =      0b0000_0010  # entity with the highest id in the set
    MIN =       0b0000_0100  # entity with the lowest value in the set
    MAX =       0b0000_1000  # entity with the highest value in the set
    MEDIAN =    0b0001_0000  # median of value-set, or 2 values which would be used to calculate median
    MIN_MAX_MED = MIN | MAX | MEDIAN
    ALL =       0b1111_1111  # todo remove


class Chunk:
    def __init__(self, td: TimingData, idx_start: int, idx_end: int, p_start: int, p_end: int):
        self.td = td
        self.idx_start = idx_start
        self.idx_end = idx_end
        self.p_start = p_start
        self.p_end = p_end
        self.__raw_data = None  # used only if chunk is standalone
        self.__data = None  # contains a copy of the data which may be filtered or grouped by user
        self.__mean_times_by_idx = None
        self.__operation_counter = 0  # counts the amount of filter and group operations on the chunk

    def __del__(self):
        if self.__raw_data is None:
            self.td._deregister_locking_chunk(self)

    # all values calculated on basis of __data are removed
    def __reset_calcs(self):
        self.__mean_times_by_idx = None
        self.__data = None  #todo add recalculation to get data, to maintain consistency for filtered and grouped data

    def get_raw_data(self) -> pd.DataFrame:
        if self.__raw_data is not None:
            return self.__raw_data
        else:
            df = self.td.get_loaded_dataframe()
            if df is None:
                # this should never happen, as data which is referred to by chunk is drop-locked
                m.critical("Chunk trying to access data which was dropped")
            return df[(df['idx'].between(self.idx_start, self.idx_end)) & (df['p'].between(self.p_start, self.p_end))]

    def get_data(self) -> pd.DataFrame:
        if self.__data is not None:
            return self.__data
        start = self.get_raw_data().copy()
        start['is_start'] = True
        start['context'] = ""

        end = self.get_raw_data().copy()
        end['is_start'] = False
        end['context'] = ""

        self.__data = pd.concat([start, end])
        return self.__data

    def make_standalone(self):
        if self.__raw_data is None:
            self.__raw_data = self.get_raw_data().copy()
            self.td._deregister_locking_chunk(self)

    def get_mean_times_by_idx(self):
        if self.__mean_times_by_idx is None:
            self.__mean_times_by_idx = self.get_raw_data().groupby('idx').agg({'start': 'mean', 'end': 'mean'})
            self.__mean_times_by_idx.rename(columns={'start': 'm_start', 'end': 'm_end'}, inplace=True)
        return self.__mean_times_by_idx

    # Updates the timestamps without changing the relative difference between the timestamps.
    # Now the first Timestamp is at exactly zero.
    def time_starts_zero_at_first_value(self):
        self.make_standalone()
        self.__reset_calcs()
        mini = self.__raw_data[self.__raw_data["idx"] == self.idx_start]['start'].min()
        self.__raw_data[["start", "end"]] = self.__raw_data[["start", "end"]].apply(lambda x: x - mini)
        return self

    # Updates the timestamps without changing the relative difference between the timestamps.
    # Now the first average of the given chunk starts at zero
    def time_starts_zero_at_first_mean(self):
        self.make_standalone()
        means = self.get_mean_times_by_idx()
        mini = means.loc[self.idx_start, "m_start"]
        self.__raw_data[["start", "end"]] = self.__raw_data[["start", "end"]].apply(lambda x: x - mini)
        self.__reset_calcs()
        return self

    # Filters the data, so only the selected datapoints will be shown. Calculations which require all data, like the
    #  mean of an idx will still be calculated over all data to avoid wrong data.
    def filter_entities(
            self,
            entity_selection_list: list[int] | None = None,
            entity_selection_lambda: Callable[[int], bool] | None = None,
            additional_selection: Filter = 0,
            filter_start: bool = True,
            filter_end: bool = True,
            keep_selection_and_drop_unselected: bool = True):
        """
        :param entity_selection_lambda: lambda function which can decide which entities shall be selected
            lambda functions receives the entity id for each entity and returns a boolean.
        :param entity_selection_list: list of entities which shall be selected.
        :param additional_selection: Contains a selection of entities which will additionally be used
            additional selection will be executed on the current dataset. if it was previously already filtered, the
            results might differ from the same calculations on the original data.
        :param filter_end: if true, the end-values will be filtered
        :param filter_start: if true, the start-values will be filtered
        :param keep_selection_and_drop_unselected: if True, selected entities will be kept, otherwise dismissed
            only applies to selection list and lambda, additional selection will always be shown and never dismissed
        :return: None
        """
        whitelist = None
        lam_func = None
        if type(entity_selection_list) is list:  #todo check if these typeofs work
            whitelist = entity_selection_list
        elif entity_selection_list is not None:
            m.warning("Invalid entity_selector_list, could not filter")
            return

        if type(entity_selection_lambda) is FunctionType:
            lam_func = entity_selection_lambda
        elif entity_selection_lambda is not None:
            m.warning("Invalid entity_selector_lambda, could not filter")
            return

        if ((whitelist is None and lam_func is None and additional_selection == 0)
                or (not filter_start and not filter_end)):
            m.info("Nothing to filter")
            return

        if filter_start:
            self.__filter_entities_helper(whitelist, lam_func, additional_selection, keep_selection_and_drop_unselected, True)
        if filter_end:
            self.__filter_entities_helper(whitelist, lam_func, additional_selection, keep_selection_and_drop_unselected, False)
        return

    def __filter_entities_helper(self, whitelist, lam_func, additional, keep, filter_start):
        key = ("start" if filter_start else "end")
        uf = self.get_data()
        filtered = uf[uf["is_start"] == (not filter_start)].copy()
        uf = uf[(uf["is_start"] == filter_start)]

        filter_opts = [
            dict(filter=Filter.MIN, agg_key=key, agg_oper="min", filter_name="min"),
            dict(filter=Filter.MAX, agg_key=key, agg_oper="max", filter_name="max"),
            dict(filter=Filter.FIRST, agg_key="p", agg_oper="min", filter_name="first"),
            dict(filter=Filter.LAST, agg_key="p", agg_oper="max", filter_name="last"),
        ]
        for x in filter_opts:
            if additional & x["filter"]:
                aggr = uf.groupby(['idx']).agg({x["agg_key"]: x["agg_oper"]})
                temp = pd.merge(aggr, uf, on=["idx", x["agg_key"]])
                temp = temp.drop_duplicates(subset=["idx", x["agg_key"]])
                temp["context"] += f"f{self.__operation_counter}:{x['filter_name']} "
                uf = uf.merge(aggr, on=["idx", x["agg_key"]], how="left", indicator=True)
                uf = uf[uf["_merge"] == "left_only"].drop(columns="_merge")
                filtered = pd.concat([filtered, temp])

        self.__data = filtered



class ChunkList(list):
    def each_time_starts_zero_at_first_value(self):
        for a in self:
            a.time_starts_zero_at_first_value()
        return self

    def each_time_starts_zero_at_first_mean(self):
        for a in self:
            a.time_starts_zero_at_first_mean()
        return self

    def __getitem__(self, index):
        if isinstance(index, slice):
            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else len(self)
            step = index.step if index.step is not None else 1

            sliced_chunk_list = ChunkList()
            for i in range(start, stop, step):
                sliced_chunk_list.append(self[i])
            return sliced_chunk_list
        else:
            return super().__getitem__(index)
