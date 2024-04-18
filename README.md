# mpi-data-viewer

## dataLib

### TimingData

TimingData is a wrapper for an MPI performance log file. 
It saves the meta information like the cores and nodes were used.
It provides access to the whole dataset or subsets of it.
It may drop the Dataframe to free memory for other data. It can be instructed to load the data again.

### DataManager

DataManager organizes a set of TimingData objects and enables operations over all or some of its TimingData objects.

### Messenger

Messenger is a helper class to provide consistent messaging. 
Set `Messenger.min_level` to a higher value to restrict the printed messages:
- 0: debug
- 1: info
- 2: warning
- 3: error
- 4: critical