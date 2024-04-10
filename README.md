# MWT_Analysis
A custom python-based program for the bulk processing of Multi-Worm Tracker data by applying set parameters for Choreography to each file. Users can specify if crawling speed should be normalized by a chosen time interval.

1. Users need to generate data is described in https://www.nature.com/articles/nmeth.1625
2. Copy the file "Chore.jar" from the above linked publication into the folder of the python script.
3. Start MWT analysis and select folder containing data files
4. Optional: User can toggle normalization of crawling speed analysis.

    Input time point when normalization should start (Normalize from ...(s)) and time interval for how many seconds should be used as a mean value for normalization (for ...(s))

5. MWT Analysis will output an XLSX file for each folder in the source folder file for further data analysis
