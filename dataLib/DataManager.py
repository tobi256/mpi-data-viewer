from dataLib.Messenger import Messenger as m
from dataLib.TimingData import TimingData



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
