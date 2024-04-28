from dataLib.Messenger import Messenger as m
from dataLib.TimingData import TimingData
from dataLib.Chunk import ChunkList
from typing import List
import os
import re


class DataManager:
    def __init__(self):
        self.timings = {}
        self.auto_increment = 0

    def read_timing(self, file_path: str, name: str) -> None:
        d = TimingData._create(file_path, name)
        self.timings[name] = d

    # reads all files in given folder where the file pattern matches.
    # The TimingData is named like naming, where the ? is replaced with the auto increment number of the data manager.
    def read_timing_folder(self, folder_path: str, file_pattern: str = "timings_.*\\.dat", naming: str = "data?"):
        if not os.path.exists(folder_path):
            m.error("Invalid folder path!")
            return
        if not os.path.isdir(folder_path):
            m.error("expected folder path!")
            return
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if re.fullmatch(file_pattern, f)]

        for x in files:
            if os.path.isfile(x):
                self.read_timing(x, naming.replace("?", str(self.auto_increment)))
                self.auto_increment += 1

    def get_timing_data(self, name: str) -> None | TimingData:
        if name in self.timings.keys():
            return self.timings[name]
        m.warning("No Timing Data with that name: {name}")
        return None

    def create_chunks(self, names: None | List[str] = None, idx_start: int = 0, idx_end: int | None = None, p_start: int = 0, p_end: int | None = None, standalone: bool = False):
        if names is None:
            names = self.timings.keys()

        # todo add warnings, if data does not match
        res = ChunkList([])
        for x in names:
            res.append(self.timings[x].create_chunk(idx_start, idx_end, p_start, p_end, standalone))

        return res


