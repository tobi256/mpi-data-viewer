import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from dataLib.TimingData import TimingData
from dataLib.Messenger import Messenger as m
from enum import Flag
from typing import Callable
import pandas as pd
from types import FunctionType
from typing import Self

pd.set_option('display.expand_frame_repr', False)


# If there is no singular Median, two points will be selected.
# note: using first and last in combination with other parameters may lead to errors.
#    Points will not be duplicated, and max, min and median are prioritized.
#    If point is first and min, it will be displayed as min.
class Filter(Flag):
    NOTHING = 0  # will be overwritten if used in combination with something else
    FIRST =     0b0000_0001  # entity with the lowest id in the set
    LAST =      0b0000_0010  # entity with the highest id in the set
    MIN =       0b0000_0100  # entity with the lowest value in the set
    MAX =       0b0000_1000  # entity with the highest value in the set
    MEDIAN =    0b0001_0000  # median of value-set, or 2 values which would be used to calculate median
    MIN_MAX_MED = MIN | MAX | MEDIAN


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
        self.__min_times_by_idx = None
        self.__max_times_by_idx = None
        self.__operation_counter = 0  # counts the amount of filter and group operations on the chunk
        self.__name_extension = ""
        self.__min_start = None
        self.__max_end = None
        self.__min_max_last_op = -1

    def __del__(self):
        if self.__raw_data is None:
            self.td._deregister_locking_chunk(self)

    # implies standalone
    def copy(self):
        self.make_standalone()
        c = Chunk(self.td, self.idx_start, self.idx_end, self.p_start, self.p_end)
        c.__raw_data = self.__raw_data.copy()
        c.__operation_counter = self.__operation_counter
        c.__name_extension = self.__name_extension
        c.__min_start = self.__min_start
        c.__max_end = self.__max_end
        if self.__data is not None:
            c.__data = self.__data
        return c

    def get_execution_duration(self):
        if self.__min_max_last_op != self.__operation_counter:
            self.__min_start = self.get_data()['start'].min()
            self.__max_end = self.get_data()['end'].max()
            self.__min_max_last_op = self.__operation_counter
        return self.__max_end - self.__min_start

    # all values calculated on basis of __data are removed
    # needed if actual underlying data is changed (for example if start times are updated)
    def __reset_calcs(self):
        self.__mean_times_by_idx = None
        self.__max_times_by_idx = None
        self.__min_times_by_idx = None
        self.__min_max_last_op = -1
        if self.__data is not None:
            m.warning("Filters and groups are reset. ")
            self.reset_filters_and_groups()

    def reset_filters_and_groups(self):
        self.__data = None
        self.__operation_counter = 0
        self.__name_extension = ""


    def get_name_extension(self):
        return self.__name_extension

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

    def set_data(self, data: pd.DataFrame, operation_desc: str = "unknown"):
        m.info("Set Data was used. Data may have inconsistencies.")
        self.__data = data
        self.__name_extension += f"u{self.__operation_counter}:{operation_desc}"
        self.__operation_counter += 1

    def make_standalone(self):
        if self.__raw_data is None:
            self.__raw_data = self.get_raw_data().copy()
            self.td._deregister_locking_chunk(self)

    def get_mean_times_by_idx(self):
        if self.__mean_times_by_idx is None:
            self.__mean_times_by_idx = self.get_raw_data().groupby('idx').agg({'start': 'mean', 'end': 'mean'})
            self.__mean_times_by_idx.rename(columns={'start': 'm_start', 'end': 'm_end'}, inplace=True)
        return self.__mean_times_by_idx

    def get_min_times_by_idx(self):
        if self.__min_times_by_idx is None:
            self.__min_times_by_idx = self.get_raw_data().groupby('idx').agg({'start': 'min', 'end': 'min'})
            self.__min_times_by_idx.rename(columns={'start': 'm_start', 'end': 'm_end'}, inplace=True)
        return self.__min_times_by_idx

    def get_max_times_by_idx(self):
        if self.__max_times_by_idx is None:
            self.__max_times_by_idx = self.get_raw_data().groupby('idx').agg({'start': 'max', 'end': 'max'})
            self.__max_times_by_idx.rename(columns={'start': 'm_start', 'end': 'm_end'}, inplace=True)
        return self.__max_times_by_idx

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

    # this filter may completely destroy the consistency of data, if used badly
    # function expects lambda which gets the value of the selected column and returns a boolean
    def filter_column(self, column_name: str, filter_lambda: Callable[[any], bool], custom_name_extension: str | None = None):
        uf = self.get_data()
        selector = uf[column_name].apply(filter_lambda)
        uf = uf[selector].copy()
        nameex = ""
        if custom_name_extension == None:
            nameex = f"cf{self.__operation_counter}:{column_name} "
        elif custom_name_extension != "":
            nameex = f"{custom_name_extension} "
        uf["context"] += nameex
        self.__name_extension += nameex
        self.__data = uf
        self.__operation_counter += 1
        return self

    # function expects lambda which gets the rows of the dataframe and returns a boolean
    def filter_rows(self, filter_lambda: Callable[[dict], bool], custom_name_extension: str | None = None):
        uf = self.get_data()
        selector = uf.apply(filter_lambda, axis=1)
        uf = uf[selector].copy()
        nameex = ""
        if custom_name_extension == None:
            nameex = f"rf{self.__operation_counter} "
        elif custom_name_extension != "":
            nameex = f"{custom_name_extension} "
        uf["context"] += nameex
        self.__name_extension += nameex
        self.__data = uf
        self.__operation_counter += 1
        return self

    def group_entities(
            self,
            linear_size: int | None = None,  # starts to group the chunk into linear_size big groups starting at small, use 0 to automatically select the ppn number
            lambda_selector: Callable[[int], int] | None = None,  # lambda function receives entity id, returns group id
            aggr_start_end: Callable = "mean",  # min, max, mean, median
            show_group_at: str = "min",  # min, max, median: which p of the group shall be used
            custom_name_extension: str | None = None
    ):
        if linear_size is not None and lambda_selector is not None:
            m.error("Only linear_size parameter or lambda_selector are possible simultaneously.")
            return

        add_name = ""
        if linear_size == 0 or linear_size is None and lambda_selector is None:
            linear_size = self.td.ppn_n
            add_name = f"g{self.__operation_counter}:node({linear_size}) "

        if linear_size is not None:
            lambda_selector = (lambda x: x // linear_size)
            if add_name == "":
                add_name = f"g{self.__operation_counter}:lin({linear_size}) "
        else:
            add_name = f"g{self.__operation_counter}:lambda "
        if custom_name_extension is None:
            self.__name_extension += add_name
        elif custom_name_extension != "":
            self.__name_extension = f"{custom_name_extension} "

        d = self.get_data()
        temp = d.copy()

        # Apply grouping ids to temp col
        temp["group"] = temp["p"].apply(lambda_selector)
        temp["counter"] = 1
        temp = temp.groupby(["idx", "group", "is_start"]).agg(
            {"start": aggr_start_end,
             "end": aggr_start_end,
             "p": show_group_at,
             "counter": "count",
             "buf_size": "unique",
             "callid": "unique",
             "comm_size": "unique",
             "region": "unique"
             }).reset_index()
        # todo add functionality to allow median as show_group_at, must not have value which is not a valid p
        temp = pd.merge(temp, d, on=["idx", "p", "is_start"], suffixes=(None, "_r"), validate="1:1")
        if len(temp["counter"].unique()) != 1:
            m.warning("Note that the grouping function created groups of different sizes!")
        temp["context"] += temp["counter"].apply(lambda x: f"g{self.__operation_counter}:c{x}")
        # Check if all datapoints have groupable values
        lam_check_unique_array_val = lambda x: (x[0] if len(x) == 1 else None)
        temp["buf_size"] = temp["buf_size"].apply(lam_check_unique_array_val)
        temp["callid"] = temp["callid"].apply(lam_check_unique_array_val)
        temp["comm_size"] = temp["comm_size"].apply(lam_check_unique_array_val)
        temp["region"] = temp["region"].apply(lam_check_unique_array_val)
        if temp[["buf_size", "callid", "comm_size", "region"]].isnull().values.any():
            m.warning("Note that data was grouped where buf_size, callid, comm_size or region columns had different values. (affected values now NaN)")

        temp = temp.drop(["start_r", "end_r", "buf_size_r", "callid_r", "comm_size_r", "region_r", "counter"], axis=1)
        self.__data = temp
        self.__operation_counter += 1
        return self

    # Filters the data, so only the selected datapoints will be shown. Calculations which require all data, like the
    #  mean of an idx will still be calculated over all data to avoid wrong data.
    def filter_entities(
            self,
            entity_selection_list: list[int] | None = None,
            entity_selection_lambda: Callable[[int], bool] | None = None,
            additional_selection: Filter = Filter.NOTHING,
            filter_start: bool = True,
            filter_end: bool = True,
            remove_duplicates: bool = True,
            keep_selection_and_drop_unselected: bool = True,
            custom_name_extension: str | None = None):
        """
        :param custom_name_extension: pass None (default) to automatically generate name, or pass custom name
        :param entity_selection_lambda: lambda function which can decide which entities shall be selected
            lambda functions receives the entity id for each entity and returns a boolean.
        :param entity_selection_list: list of entities which shall be selected.
        :param additional_selection: Contains a selection of entities which will additionally be used
            additional selection will be executed on the current dataset. if it was previously already filtered, the
            results might differ from the same calculations on the original data.
        :param filter_end: if true, the end-values will be filtered
        :param filter_start: if true, the start-values will be filtered
        :param remove_duplicates: in case of multiple min/max values, only one will be chosen.
        :param keep_selection_and_drop_unselected: if True, selected entities will be kept, otherwise dismissed
            only applies to selection list and lambda, additional selection will always be shown and never dismissed
        :return: None
        """
        whitelist = None
        lam_func = None
        if type(entity_selection_list) is list:
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

        if custom_name_extension is None:
            self.__name_extension += f"ef{self.__operation_counter}:entity "
        elif custom_name_extension != "":
            self.__name_extension += f"{custom_name_extension} "
        if filter_start:
            self.__filter_entities_helper(whitelist, lam_func, additional_selection, remove_duplicates,
                                          keep_selection_and_drop_unselected, True)
        if filter_end:
            self.__filter_entities_helper(whitelist, lam_func, additional_selection, remove_duplicates,
                                          keep_selection_and_drop_unselected, False)
        self.__operation_counter += 1
        m.debug("filtering done")
        m.debug(f"final point length: {len(self.__data)}")
        return

    def __filter_entities_helper(self, whitelist, lam_func, additional, remove_duplicates, keep, filter_start):
        key = ("start" if filter_start else "end")
        uf = self.get_data()
        filtered = uf[uf["is_start"] == (not filter_start)].copy()
        uf = uf[(uf["is_start"] == filter_start)]
        idxes = uf["idx"].unique()

        #  first: median, min, max, first, last
        filter_opts = [
            dict(filter=Filter.MEDIAN, agg_key=key, agg_oper="median", filter_name="median"),
            dict(filter=Filter.MIN, agg_key=key, agg_oper="min", filter_name="min"),
            dict(filter=Filter.MAX, agg_key=key, agg_oper="max", filter_name="max"),
            dict(filter=Filter.FIRST, agg_key="p", agg_oper="min", filter_name="first"),
            dict(filter=Filter.LAST, agg_key="p", agg_oper="max", filter_name="last"),
        ]
        for x in filter_opts:
            if additional & x["filter"]:
                aggr = uf.groupby(['idx']).agg({x["agg_key"]: x["agg_oper"]}).reset_index()
                if x["filter"] == Filter.MEDIAN:
                    # special median calcs
                    median_aggr = pd.DataFrame(columns=aggr.columns)
                    for y in idxes:
                        con = uf[(uf["idx"] == y) & (uf[x["agg_key"]] == aggr[aggr["idx"] == y][x["agg_key"]].values[0])][["idx", x["agg_key"]]].drop_duplicates()
                        if len(con) == 0:
                            # no exact median found, need to take 2 border elements
                            smaller = uf[
                                (uf["idx"] == y) & (uf[x["agg_key"]] < aggr[aggr['idx'] == y][x["agg_key"]].values[0])
                                ][x["agg_key"]].max()
                            larger = uf[
                                (uf["idx"] == y) & (uf[x["agg_key"]] > aggr[aggr['idx'] == y][x["agg_key"]].values[0])
                                ][x["agg_key"]].min()
                            median_aggr = pd.concat([median_aggr, pd.DataFrame([[y, smaller]], columns=median_aggr.columns)])
                            median_aggr = pd.concat([median_aggr, pd.DataFrame([[y, larger]], columns=median_aggr.columns)])
                        else:
                            median_aggr = pd.concat([con, median_aggr])
                    aggr = median_aggr
                temp = pd.merge(aggr, uf, on=["idx", x["agg_key"]])
                if remove_duplicates:
                    temp = temp.drop_duplicates(subset=["idx", x["agg_key"]])
                remove = temp[["idx", "p"]]
                temp["context"] += f"ef{self.__operation_counter}:{x['filter_name']} "
                #print(f"before:{len(uf)}")
                uf = uf.merge(remove, on=["idx", "p"], how="left", indicator=True)
                uf = uf[uf["_merge"] == "left_only"].drop(columns="_merge")
                #print(f"after:{len(uf)}")
                filtered = pd.concat([filtered, temp])

        # second: list
        if whitelist is not None:
            selector = uf["p"].isin(whitelist)
            if not keep:
                selector = ~selector
            temp = uf[selector].copy()
            remove = temp[["idx", "p"]]
            temp["context"] += f"f{self.__operation_counter}:wl "
            uf = uf.merge(remove, on=["idx", "p"], how="left", indicator=True)
            uf = uf[uf["_merge"] == "left_only"].drop(columns="_merge")
            filtered = pd.concat([filtered, temp])

        # third: lambda
        if lam_func is not None:
            selector = uf["p"].apply(lam_func)
            if not keep:
                selector = ~selector
            temp = uf[selector].copy()
            temp["context"] += f"ef{self.__operation_counter}:lambda "
            filtered = pd.concat([filtered, temp])

        self.__data = filtered
        return


class ChunkList(list):
    def copy(self) -> Self:
        c = ChunkList([])
        for a in self:
            c.append(a.copy())
        return c

    def each_time_starts_zero_at_first_mean(self):
        for a in self:
            a.time_starts_zero_at_first_mean()
        return self

    def each_time_starts_zero_at_first_value(self):
        for a in self:
            a.time_starts_zero_at_first_value()
        return self

    def each_reset_filters_and_groups(self):
        for a in self:
            a.reset_filters_and_groups()
        return self

    def each_filter_entities(
            self,
            entity_selection_list: list[int] | None = None,
            entity_selection_lambda: Callable[[int], bool] | None = None,
            additional_selection: Filter = Filter.NOTHING,
            filter_start: bool = True,
            filter_end: bool = True,
            remove_duplicates: bool = True,
            keep_selection_and_drop_unselected: bool = True,
            custom_name_extension: str | None = None):
        for a in self:
            a.filter_entities(entity_selection_list, entity_selection_lambda, additional_selection, filter_start, filter_end, remove_duplicates, keep_selection_and_drop_unselected, custom_name_extension)
        return self

    def each_group_entities(
            self,
            linear_size: int | None = None,  # starts to group the chunk into linear_size big groups starting at small, use 0 to automatically select the ppn number
            lambda_selector: Callable[[int], int] | None = None,  # lambda function receives entity id, returns group id
            aggr_start_end: Callable = "mean",  # min, max, mean, median
            show_group_at: str = "min",  # min, max, median: which p of the group shall be used
            custom_name_extension: str | None = None
    ):
        for a in self:
            a.group_entities(linear_size, lambda_selector, aggr_start_end, show_group_at, custom_name_extension)
        return self

    def each_filter_column(self, column_name: str, filter_lambda: Callable[[any], bool], custom_name_extension: str | None = None):
        for a in self:
            a.filter_column(column_name, filter_lambda, custom_name_extension)
        return self

    def each_filter_rows(self, filter_lambda: Callable[[any], bool], custom_name_extension: str | None = None):
        for a in self:
            a.filter_rows(filter_lambda, custom_name_extension)
        return self

    def sort_by_duration(self, *, reverse=False):
        super().sort(key=lambda c: c.get_execution_duration(), reverse=reverse)
        return self

    def __getitem__(self, index):
        if isinstance(index, slice):
            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else len(self)
            step = index.step if index.step is not None else 1

            # Handle negative indices for start and stop
            if start < 0:
                start += len(self)
            if stop < 0:
                stop += len(self)

            # Ensure that start and stop are within the bounds
            start = max(start, 0)
            stop = min(stop, len(self))

            sliced_chunk_list = ChunkList()
            for i in range(start, stop, step):
                sliced_chunk_list.append(self[i])
            return sliced_chunk_list
        else:
            return super().__getitem__(index)
