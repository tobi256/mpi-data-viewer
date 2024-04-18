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

    def data_loaded(self):
        return not self.__data is None

    # reads the data from 'file' and creates the header from 'header_line'
    def __read_data_stream(self, file: IO[str], header_line: str):
        try:
            header = [x.strip() for x in header_line.split('\t')]
            self.__data = pd.read_csv(file, delimiter='\t', names=header)
        except IOError as e:
            self.__data = None
            m.error(f"Error while reading file")

    # loads data but skips the parameters on top of file
    def load_data(self):
        if not self.data_loaded():
            try:
                with open(self.file_path, 'r') as file:
                    for line in file:
                        if line[0:2] != '#@':
                            break
                    self.__read_data_stream(file, line)
            except IOError as e:
                m.error(f"Could not read file {self.file_path}")
                m.debug(f"File error: {e}")

    def drop_data(self):
        self.__data = None

    def get_raw_data_frame(self):
        self.load_data()
        return self.__data

    # creates and returns a new TimingData object
    @staticmethod
    def create(file_path: str, name: str | None = None):
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
                td.__read_data_stream(file, line)
                return td
        except IOError as e:
            m.error(f"Could not read file {file_path}")
            m.debug(f"File error: {e}")
        except (TypeError, ValueError) as e:
            m.error(f"Could not parse file {file_path}")
            m.debug(f"Parse error: {e}")
        return None




