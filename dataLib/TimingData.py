from datetime import datetime
from typing import IO
from dataLib.Messenger import Messenger as m
import pandas as pd


# TimingData stores the data of one Timing Log.
# It may drop the data momentarily, but can fetch it again
class TimingData:
    def __init__(
            self,
            name: str,
            time: datetime,
            procs_exec_n: int,
            procs_samp_n: int,
            nodes_n: int,
            ppn_n: int,
            timestamps_n: int,
            file_path: str):
        self.time = time
        self.procs_exec_n = procs_exec_n
        self.procs_samp_n = procs_samp_n
        self.nodes_n = nodes_n
        self.ppn_n = ppn_n
        self.timestamps_n = timestamps_n
        self.name = name
        self.file_path = file_path
        self.__data = None
        self.__line_start = 0  # the first dataline which is loaded (if __data not None)
        self.__line_end = 0  # the last line +1 (like python [0:1024] -> line 0-1023 are loaded)
        self.drop_lock_registry = []  # if not empty, data must not be dropped

    def _register_locking_chunk(self, item):
        if item.td == self:
            if item not in self.drop_lock_registry:
                self.drop_lock_registry.append(item)
                m.debug(f"TimingData {self.name} drop-registry count increased: {len(self.drop_lock_registry)}")
        else:
            m.error("Can not register Chunk")

    def _deregister_locking_chunk(self, item):
        if item not in self.drop_lock_registry:
            m.warning("Chunk not registered in this TimingData")
        else:
            self.drop_lock_registry.remove(item)
            m.debug(f"TimingData {self.name} drop-registry count decreased: {len(self.drop_lock_registry)}")

    # both ends here are inclusive for idx and p. (p[0,0] -> only p = 0, idx[1,3] -> idx = 1,2,3)
    def create_chunk(self, idx_start: int = 0, idx_end: int | None = None, p_start: int = 0, p_end: int | None = None, standalone: bool = False):
        if idx_end is None:
            idx_end = self.timestamps_n - 1
        elif idx_end < 0:
            idx_end += self.timestamps_n
        if p_end is None:
            p_end = self.procs_exec_n - 1  # todo think about what happens if sampled != exec
        elif p_end < 0:
            p_end += self.procs_exec_n

        if idx_start < 0 or idx_end >= self.timestamps_n or p_start < 0 or p_end >= self.procs_exec_n:
            m.error("Invalid index for chunk creation")
            return None
        c = Chunk(self, idx_start, idx_end, p_start, p_end)
        self._load_range(idx_start, idx_end)
        self._register_locking_chunk(c)
        if standalone:
            c.make_standalone()
        return c

    def __idx_to_line(self, idx, start: bool):
        if idx < 0:
            idx += self.timestamps_n
        return (idx if start else idx+1) * self.procs_samp_n

    def __idxs_to_lines(self, idx_start, idx_end):
        if idx_end is None:
            idx_end = self.timestamps_n - 1
        start = self.__idx_to_line(idx_start, True)
        end = self.__idx_to_line(idx_end, False)
        if start > end:
            m.critical(f"{self.name} invalid idx values")
        return start, end

    def _data_loaded(self, idx_start: int = 0, idx_end: int | None = None):
        start, end = self.__idxs_to_lines(idx_start, idx_end)
        return self.__data is not None and start >= self.__line_start and end <= self.__line_end

    # reads the data from 'file' and creates the header from 'header_line'
    def __read_data_stream(self, file: IO[str], header_line: str, line_count: int | None = None):
        try:
            header = [x.strip() for x in header_line.split('\t')]
            self.__data = pd.read_csv(file, delimiter='\t', names=header, nrows=line_count)
        except IOError as e:
            self.__data = None
            m.error(f"Error while reading file")

    # loads idx range given (both inclusive, end -1 is last element), skips headers
    def _load_range(self, idx_start: int = 0, idx_end: int | None = None):
        if not self._data_loaded(idx_start, idx_end):
            try:
                with open(self.file_path, 'r') as file:
                    for line in file:
                        if line[0:2] != '#@':
                            break
                    header = line
                    start, end = self.__idxs_to_lines(idx_start, idx_end)
                    for x in range(0, start):
                        file.readline()
                    m.info(f"TimingData {self.name} reading idx {idx_start} - {idx_end if idx_end is not None else "end"}. (lines [{start}:{end}])")
                    self.__read_data_stream(file, header, end-start)
                    self.__line_start = start
                    self.__line_end = end
            except IOError as e:
                m.error(f"Could not read file {self.file_path}")
                m.debug(f"File error: {e}")

    # loads data but skips the parameters on top of file
    def _load_all_data(self):
        self._load_range()

    def _drop_data(self):
        if len(self.drop_lock_registry) == 0:
            m.info(f"TimingData {self.name} dropped its dataframe.")
            self.__data = None

    def get_loaded_dataframe(self):
        return self.__data

    def get_complete_raw_data_frame(self):
        self._load_all_data()
        return self.__data

    def temp_print_df(self):
        print(self.__data)

    # creates and returns a new TimingData object
    @staticmethod
    def _create(file_path: str, name: str | None = None, read_all: bool = False):
        args = {
            "time": None,
            "nprocs": None,
            "nnodes": None,
            "ppn": None,
            "num_timestamps": None,
            "nb_processes_sampled": None,
        }
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    if line[0:2] != '#@':
                        break
                    line_split = line[3:].strip().split("=")
                    if len(line_split) != 2 or line_split[0] not in args.keys() or args[line_split[0]] is not None:
                        raise TypeError(f"Unable to parse {line}")
                    args[line_split[0]] = line_split[1]
                if None in args.values():
                    raise TypeError(f"Missing parameter.")
                td = TimingData(
                    file_path if name is None else name,
                    datetime.strptime(args["time"], "%Y-%m-%d %H:%M:%S"),
                    int(args["nprocs"]),
                    int(args["nb_processes_sampled"]),
                    int(args["nnodes"]),
                    int(args["ppn"]),
                    int(args["num_timestamps"]),
                    file_path)
                if read_all:
                    td.__read_data_stream(file, line)
                return td
        except IOError as e:
            m.error(f"Could not read file {file_path}")
            m.debug(f"File error: {e}")
        except (TypeError, ValueError) as e:
            m.error(f"Could not parse file {file_path}")
            m.debug(f"Parse error: {e}")
        return None


# import has to be at end to avoid circular import
from dataLib.Chunk import Chunk