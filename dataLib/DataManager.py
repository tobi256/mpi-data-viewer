from dataLib.Messenger import Messenger as m
from dataLib.TimingData import TimingData
from dataLib.Chunk import ChunkList
from typing import List


class DataManager:
    def __init__(self):
        self.timings = {}

    def read_timing(self, file_path: str, name: str = "hallo") -> None:
        d = TimingData._create(file_path, name)
        self.timings[name] = d

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


