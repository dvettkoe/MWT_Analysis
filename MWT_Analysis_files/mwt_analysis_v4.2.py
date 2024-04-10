import tkinter as tk
import os
from tkinter import ttk
from tkinter import filedialog
import tkinter.font as font
import pandas as pd
import numpy as np
from pathlib import Path

### Changelog ###
# v1-3 (by Dennis Vettkötter):
#       Software for Crawling Analysis of MWT data. Parameter for Chore.jar are fixed for standard data output.
#       Batch processing of multiple assays with one go.
#       GUI for easier acces to select data folder and track progress of analysis.
# v4 (by Dennis Vettkötter 24.10.2022):
#       Incorporated Chore.jar to folder of python script. No need to select Chore.jar anymore. Removed selection in GUI
#       Removed merging of experiments, as single data should be shown anyways.
#       Added reversal analysis.
# v4.1 (by Dennis Vettkötter 01.11.2022):
#       Added "moving" average for reversal analysis (separate excel sheet) by rounding time values of reversal events
#       and calculating mean of reversal events at same time points.
# v4.2 (by Dennis Vettkötter 02.11.2022):
#       Added normalization of reversal events by normalizing through number of animals tracked at respective time point
#
#
#

gui = tk.Tk()
gui.geometry("540x85")
gui.title("MWT Analysis")
gui.iconbitmap('mwt_analysis_ico2.ico')


class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify="left",
                      background="#ffffe0", relief="solid", borderwidth=1,
                      font=("tahoma", "10", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


def Choreography():
    progress_analyze_value = 0
    progress_analyze_list = []
    chore_root = chorePath.get()
    data_root = dataPath.get() + "/"
    for subdir, dirs, files in os.walk(data_root):
        for file in files:
            if file.endswith(".summary") == True:
                progress_analyze_list.append(file)
    progress_analyze_steps = 100 / len(progress_analyze_list)
    for subdir, dirs, files in os.walk(data_root):
        for file in files:
            if file.endswith(".summary") == True:
                os.system("java -jar " + chore_root + " --header -p 0.017 -s 1 -T 1 --shadowless -S --plugin Reoutline::exp --plugin Respine -o tfnNpss#s*SlwMmm*kPcDbdrC --plugin MeasureReversal::all --plugin SpinesForward --plugin Eigenspine::graphic::data " + subdir)
                progress_analyze_value += progress_analyze_steps
                progressbar_analyze['value'] = progress_analyze_value
                progressbar_analyze.update()

def rev_analysis():
    data_root = dataPath.get() + "/"
    for subdir, dirs, files in os.walk(data_root):
        if "data_output" in dirs:
            dirs.remove("data_output")
        if data_root in dirs:
            dirs.remove(data_root)
        if subdir != data_root:
            subname = os.path.basename(subdir)
            with open(subdir + "/" + subname + "_" + "reversals.txt", 'w') as rev_file:
                for file in files:
                    if file.endswith(".rev") == True:
                        rev_events = open(os.path.join(subdir, file), "r")
                        rev_file.write(rev_events.read())
            rev_file.close()

def format_data():
    progress_analyze_value=0
    progress_analyze_list=[]
    data_root = dataPath.get() + "/"
    Path(data_root + "/data_output").mkdir(parents=True, exist_ok=True)
    output_root = data_root + "/data_output/"
    rev_column_list = ['object_id', 'rev_time', 'rev_distance', 'rev_duration']
    for subdir, dirs, files in os.walk(data_root):
        for file in files:
            if file.endswith(".dat") == True:
                progress_analyze_list.append(file)
    progress_analyze_steps=100/len(progress_analyze_list)
    for subdir, dirs, files in os.walk(data_root):
        subname = os.path.basename(subdir)
        if os.path.exists(subdir + "/" + subname + "_" + "reversals.txt") == True:
            reversals = open(subdir + "/" + subname + "_" + "reversals.txt", 'r')
        for file in files:
            if file.endswith(".dat") == True:
                column_list=['time','frame','number','goodnumber','persistence','speed','speed_number','speed_std','angular','length','width','Morphwidth','midline','midline_std','kink','pathlen','curve','id','bias','direction','crab','Custom']
                df = pd.read_csv(os.path.join(subdir, file), sep="\s+", names=column_list,encoding='utf-8', quotechar='"', decimal=",")
                index = df.index
                number_of_rows = len(index)
                rtime = list(range(1,number_of_rows+1))
                df.insert(loc=0, column='rTime', value=rtime)
                np.seterr(divide='ignore', invalid='ignore')
                col_pathlen_arr = df['pathlen'].to_numpy()
                col_goodnumber_arr = df['goodnumber'].to_numpy()
                pathlenPerWorm_arr = col_pathlen_arr / col_goodnumber_arr
                df["pathlenPerWorm"] = pathlenPerWorm_arr
                df2 = df[["rTime", "speed", "speed_std", "speed_number"]]

                df4 = pd.read_csv(reversals, delim_whitespace=True, names=rev_column_list, encoding='utf-8',
                                  quotechar='"', decimal=",")

                # calculate mean of reversal raw data and round rev_times to whole seconds. Add count of rev_events
                df5 = df4
                df5 = df5.round({'rev_time': 0})
                df5 = df5.sort_values(by=['rev_time'])
                df5['rev_events'] = df5.groupby('rev_time')['rev_time'].transform('count')
                df5 = df5.drop(["object_id"], axis=1)
                df5 = df5.groupby('rev_time').agg(['mean', 'sem'])
                df5.columns = df5.columns.map('_'.join)
                df5 = df5.drop(['rev_events_sem'], axis=1)
                df5.rename(columns={'rev_events_mean': 'rev_events'},
                           inplace=True)
                df5 = df5.reset_index()

                # creating empty data frame for duration of analyzed experiment
                df6 = pd.DataFrame({'rev_time': [x for x in range(df2.rTime.min(), df2.rTime.max() + 1)]})

                # combining mean reversal dataframe with exp duration data frame to fill missing time points

                df7 = pd.merge(left=df5, right=df6, on='rev_time', how='outer').fillna(0).sort_values(by='rev_time')
                df7 = df7.reset_index()
                df7 = df7.drop(["index"], axis=1)
                df7["norm_rev_events"] = df7['rev_events'].div(df['goodnumber'], axis=0)
                df7['number_tracked_animals'] = df['goodnumber']

                # binning with bin width 10
                df8 = df4
                df8 = df8.round({'rev_time': -1})
                df8 = df8.sort_values(by=['rev_time'])
                df8['rev_events'] = df8.groupby('rev_time')['rev_time'].transform('count')
                df8 = df8.drop(["object_id"], axis=1)
                df8 = df8.groupby('rev_time').agg(['mean', 'sem'])
                df8.columns = df8.columns.map('_'.join)
                df8 = df8.drop(['rev_events_sem'], axis=1)
                df8.rename(columns={'rev_events_mean': 'rev_events'},
                           inplace=True)
                df8 = df8.reset_index()

                # binning of number of tracked animals
                df11 = df.round({'rTime': -1})
                df11 = df11.groupby('rTime').mean()
                df11 = df11.reset_index()

                # create empty dataframe with 10s steps from beginning to end of experiment
                df9 = pd.DataFrame({'rev_time': [x for x in range(df.rTime.min() - 1, df.rTime.max() + 10, 10)]})

                # combining both binning dataframes
                df10 = pd.merge(left=df8, right=df9, on='rev_time', how='outer').fillna(0).sort_values(by='rev_time')
                df10 = df10.reset_index()
                df10 = df10.drop(["index"], axis=1)
                df10["norm_rev_events"] = df10['rev_events'].div(df11['goodnumber'], axis=0)
                df10['number_tracked_animals'] = df11['goodnumber']

                filename = file.strip(".dat")
                subname = os.path.basename(subdir)
                with pd.ExcelWriter(output_root + subname + "_" + filename + ".xlsx") as writer:
                    df.to_excel(writer, sheet_name='Sheet_name_1')
                    df2.to_excel(writer, sheet_name='speed')
                    df4.to_excel(writer, sheet_name='reversals')
                    df7.to_excel(writer, sheet_name='reversal_means')
                    df10.to_excel(writer, sheet_name='reversal_10s_bins')
                progress_analyze_value += progress_analyze_steps
                progressbar_analyze['value'] = progress_analyze_value
                progressbar_analyze.update()
    return

def startFormatData():
    data_root = dataPath.get() + "/"
    for subdir, dirs, files in os.walk(data_root):
        for file in files:
            if file.endswith(".dat") == True:
                format_data()
                break
    return

def normalization():
    rev_analysis()
    progress_analyze_value = 0
    progress_analyze_list = []
    data_root = dataPath.get() + "/"
    Path(data_root + "/data_output").mkdir(parents=True, exist_ok=True)
    output_root = data_root + "/data_output/"
    norm_from = int(normalizefrom.get())-1
    norm_to = int(normalizefrom.get())+int(normalizefor.get())-1
    rev_column_list = ['object_id', 'rev_time', 'rev_distance', 'rev_duration']
    for subdir, dirs, files in os.walk(data_root):
        for file in files:
            if file.endswith(".dat") == True:
                progress_analyze_list.append(file)
    progress_analyze_steps = 100 / len(progress_analyze_list)
    for subdir, dirs, files in os.walk(data_root):
        subname = os.path.basename(subdir)
        if os.path.exists(subdir + "/" + subname + "_" + "reversals.txt") == True:
            reversals = open(subdir + "/" + subname + "_" + "reversals.txt", 'r')
        for file in files:
            if file.endswith(".dat") == True:
                column_list = ['time', 'frame', 'number', 'goodnumber', 'persistence', 'speed', 'speed_number',
                               'speed_std', 'angular', 'length', 'width', 'Morphwidth', 'midline', 'midline_std',
                               'kink', 'pathlen', 'curve', 'id', 'bias', 'direction', 'crab', 'Custom']
                df = pd.read_csv(os.path.join(subdir, file), sep="\s+", names=column_list, encoding='utf-8',
                                 quotechar='"', decimal=",")
                index = df.index
                number_of_rows = len(index)
                rtime = list(range(1, number_of_rows + 1))
                df.insert(loc=0, column='rTime', value=rtime)
                np.seterr(divide='ignore', invalid='ignore')
                col_pathlen_arr = df['pathlen'].to_numpy()
                col_goodnumber_arr = df['goodnumber'].to_numpy()
                pathlenPerWorm_arr = col_pathlen_arr / col_goodnumber_arr
                df["pathlenPerWorm"] = pathlenPerWorm_arr

                df2 = df[["rTime", "speed", "speed_std", "speed_number"]]

                mean_arr = df["speed"].iloc[norm_from:norm_to].to_numpy()
                speed_arr = df["speed"].to_numpy()
                normalized_arr = speed_arr / mean_arr.mean()
                df3 = pd.DataFrame()
                df3["rTime"] = df["rTime"]
                df3["norm_speed"] = normalized_arr
                df3["norm_std"] = df["speed_std"] / mean_arr.mean()
                df3["speed_number"] = df["speed_number"]
                df3["-"] = ""
                df3["normalized by"] = mean_arr.mean()
                df3["normalized by"] = df3["normalized by"].drop_duplicates()
                df3["normalized from"] = normalizefrom.get() + " s"
                df3["normalized from"] = df3["normalized from"].drop_duplicates()
                df3["normalized for"] = normalizefor.get() + " s"
                df3["normalized for"] = df3["normalized for"].drop_duplicates()

                df4 = pd.read_csv(reversals, delim_whitespace=True, names=rev_column_list, encoding='utf-8',
                                 quotechar='"', decimal=",")

                #calculate mean of reversal raw data and round rev_times to whole seconds. Add count of rev_events
                df5 = df4
                df5 = df5.round({'rev_time': 0})
                df5 = df5.sort_values(by=['rev_time'])
                df5['rev_events'] = df5.groupby('rev_time')['rev_time'].transform('count')
                df5 = df5.drop(["object_id"], axis=1)
                df5 = df5.groupby('rev_time').agg(['mean','sem'])
                df5.columns = df5.columns.map('_'.join)
                df5 = df5.drop(['rev_events_sem'], axis=1)
                df5.rename(columns={'rev_events_mean': 'rev_events'},
                       inplace=True)
                df5 = df5.reset_index()

                #creating empty data frame for duration of analyzed experiment
                df6 = pd.DataFrame({'rev_time':[x for x in range(df3.rTime.min(), df3.rTime.max()+1)]})

                #combining mean reversal dataframe with exp duration data frame to fill missing time points

                df7 = pd.merge(left=df5, right=df6, on='rev_time', how='outer').fillna(0).sort_values(by='rev_time')
                df7 = df7.reset_index()
                df7 = df7.drop(["index"], axis=1)
                df7["norm_rev_events"] = df7['rev_events'].div(df['goodnumber'] ,axis=0)
                df7['number_tracked_animals'] = df['goodnumber']

                # binning with bin width 10
                df8 = df4
                df8 = df8.round({'rev_time': -1})
                df8 = df8.sort_values(by=['rev_time'])
                df8['rev_events'] = df8.groupby('rev_time')['rev_time'].transform('count')
                df8 = df8.drop(["object_id"], axis=1)
                df8 = df8.groupby('rev_time').agg(['mean','sem'])
                df8.columns = df8.columns.map('_'.join)
                df8 = df8.drop(['rev_events_sem'], axis=1)
                df8.rename(columns={'rev_events_mean': 'rev_events'},
                       inplace=True)
                df8 = df8.reset_index()

                #binning of number of tracked animals
                df11 = df.round({'rTime': -1})
                df11 = df11.groupby('rTime').mean()
                df11 = df11.reset_index()

                #create empty dataframe with 10s steps from beginning to end of experiment
                df9 = pd.DataFrame({'rev_time':[x for x in range(df3.rTime.min()-1, df3.rTime.max()+10, 10)]})

                #combining both binning dataframes
                df10 = pd.merge(left=df8, right=df9, on='rev_time', how='outer').fillna(0).sort_values(by='rev_time')
                df10 = df10.reset_index()
                df10 = df10.drop(["index"], axis=1)
                df10["norm_rev_events"] = df10['rev_events'].div(df11['goodnumber'], axis=0)
                df10['number_tracked_animals'] = df11['goodnumber']

                filename = file.strip(".dat")
                subname = os.path.basename(subdir)
                with pd.ExcelWriter(output_root + subname + "_" + filename + ".xlsx") as writer:
                    df.to_excel(writer, sheet_name='Sheet_name_1')
                    df2.to_excel(writer, sheet_name='speed')
                    df3.to_excel(writer, sheet_name='normalized_speed')
                    df4.to_excel(writer, sheet_name='reversals')
                    df7.to_excel(writer, sheet_name='reversal_means')
                    df10.to_excel(writer, sheet_name='reversal_10s_bins')
                progress_analyze_value += progress_analyze_steps
                progressbar_analyze['value'] = progress_analyze_value
                progressbar_analyze.update()
    return


def Chore_Analysis():
    analyze_done.grid_remove()
    chore_root = chorePath.get()
    data_root = dataPath.get() + "/"
    if check.get() == 1:
        if chore_root.endswith("Chore.jar") == True or chore_root.endswith("chore.jar") == True:
            Choreography()
            progress_analyze_value = 0
            progressbar_analyze['value'] = progress_analyze_value
            progressbar_analyze.update()
            normalization()
            analyze_done.grid(column=2, row=4, sticky="w")
        else:
            normalization()
            analyze_done.grid(column=2, row=4, sticky="w")
    else:
        if chore_root.endswith("Chore.jar") == True or chore_root.endswith("chore.jar") == True:
            Choreography()
            progress_analyze_value = 0
            progressbar_analyze['value'] = progress_analyze_value
            progressbar_analyze.update()
            format_data()
            analyze_done.grid(column=2, row=4, sticky="w")
        else:
            format_data()
            analyze_done.grid(column=2, row=4, sticky="w")
    return


# def merge_strains():  # Old merging code. Omitted because single data points should be shown.
#     progress_merge_value = 0
#     strains_entry = strainsEntry.get()
#     strain_list = strains_entry.split(",")
#     merge_root = mergePath.get() + "/"
#     Path(merge_root + "data_merged").mkdir(parents=True, exist_ok=True)
#     merged_root = merge_root + "data_merged/"
#     progress_merge_steps = 100 / len(strain_list)
#     for subdir, dirs, files in os.walk(merge_root):
#         for strain in strain_list:
#             data_list = []
#             df = pd.DataFrame()
#             for file in files:
#                 if file.find(strain) >= 0 and file.endswith('.xlsx'):
#                     data_list.append(file)
#                     df = df.append(pd.read_excel(os.path.join(subdir, file)), ignore_index=True)
#             df.head()
#             df['persistence'] = df['persistence'].mul(df['goodnumber'] ,axis=0)
#             df['speed'] = df['speed'].mul(df['speed_number'] ,axis=0)
#             df['speed_std'] = df['speed_std'].mul(df['speed_number'] ,axis=0)
#             df.iloc[:, 11:]=df.iloc[:, 11:].mul(df['goodnumber'] ,axis=0)
#             df = df.groupby('rTime').sum('number').fillna(0).reset_index()
#             df['time'] = df['time']/len(data_list)
#             df['frame'] = df['frame']/len(data_list)
#             df['persistence'] = df['persistence'].div(df['goodnumber'] ,axis=0)
#             df['speed'] = df['speed'].div(df['speed_number'], axis=0)
#             df['speed_std'] = df['speed_std'].div(df['speed_number'], axis=0)
#             df.iloc[:, 11:] = df.iloc[:, 11:].div(df['goodnumber'], axis=0)
#             df.drop(df.iloc[:,1:2], axis = 1, inplace = True)
#             selected_columns = df[["rTime", "speed", "speed_std", "speed_number"]]
#             df2 = selected_columns.copy()
#             df2['speed_std'] = df2['speed_std'].div(np.sqrt(df2['speed_number']))
#             df2.rename(columns={'speed_std': 'speed_sem'}, inplace=True)
#             with pd.ExcelWriter(merged_root + strain + '_merged.xlsx') as writer:
#                 df.to_excel(writer, sheet_name='Sheet_name_1')
#                 df2.to_excel(writer, sheet_name='speed')
#             progress_merge_value += progress_merge_steps
#             progressbar_merge['value'] = progress_merge_value
#             progressbar_merge.update()
#     merge_done.grid(column=2, row=11, sticky="w")
#     return



def getDataPath():
    data_selected = filedialog.askdirectory()
    dataPath.set(data_selected)

def getChorePath():
    chore_selected = filedialog.askopenfile(title="Select Chore.jar")
    chorePath.set(chore_selected.name)

def getMergePath():
    merge_selected = filedialog.askdirectory()
    mergePath.set(merge_selected)


def doStuff():
    folder = dataPath.get()
    print("Doing stuff with folder", folder)

# chore_info = "For new data insert directory of 'Chore.jar'.\n" \
#              "If Chore is not selected, the script will check\n" \
#              "for existing '*.dat' files in the data directory \n" \
#              "and output the data in xlsx format for further \n" \
#              "analysis."
#
# strains_info = "Specify strain names seperated by commas. Do not use spaces after comma!\n" \
#                "Eg. 'strain x,strain-y,strain_z'"

norm_info = "Check if data should be normalized.\n" \
            "Specify starting time (\"from\") and duration (\" for \") \n" \
            "as time period used for normalization."

myFont = font.Font(family='Cambria', size=10, weight="bold")
headerFont = font.Font(size=10, weight="bold")
analyzeFont = font.Font(size=9, weight="bold")

chorePath = tk.StringVar()
chorePath.set(os.path.dirname(__file__) + "/Chore.jar")
dataPath = tk.StringVar()
mergePath = tk.StringVar()
# strains = StringVar()


# infobutton = tk.Button(gui, text = 'i', font=myFont, bg='white', fg='blue', bd=0)
# CreateToolTip(infobutton, text = chore_info)
# infobutton.grid(row=1,column=3, padx=5)

header_analysis = tk.Label(gui, text= "Analyze data", font=headerFont)
header_analysis.grid(row=0,column = 1)

# choreLabel = tk.Label(gui ,text="Select Chore.jar")
# choreLabel.grid(row=1,column = 0, sticky="w")
# choreEntry = tk.Entry(gui,textvariable=chorePath)
# choreEntry.grid(row=1,column=1, ipadx=100, padx =2)
# btnBrowse1 = ttk.Button(gui, text="Browse",command=getChorePath)
# btnBrowse1.grid(row=1,column=2)

dataLabel = tk.Label(gui ,text="Select Data folder")
dataLabel.grid(row=2,column = 0, sticky="w")
dataEntry = tk.Entry(gui, textvariable=dataPath)
dataEntry.grid(row=2,column=1, ipadx=100, padx=2)
btnBrowse2 = ttk.Button(gui, text="Browse",command=getDataPath)
btnBrowse2.grid(row=2,column=2)

norm_infobutton = tk.Button(gui, text = 'i', font=myFont, bg='white', fg='blue', bd=0)
CreateToolTip(norm_infobutton, text = norm_info)
norm_infobutton.grid(row=4,column=0, sticky='w')

check = tk.IntVar()
normalizeCheck = tk.Checkbutton(gui, text="Normalize from", variable=check)
normalizeCheck.grid(row=4, column=0, sticky='w', padx=12)

normalizefrom = tk.StringVar()
normalizefor = tk.StringVar()


normalizeLabel = tk.Label(gui, text= "       (s) for         (s)")
normalizeLabel.grid(row=4, column=1, sticky='w')
normalizeEntryfrom = tk.Entry(gui, textvariable=normalizefrom, width=3)
normalizeEntryfrom.grid(row=4, column=1, sticky='w')
normalizeEntryfor = tk.Entry(gui, textvariable=normalizefor, width=3)
normalizeEntryfor.grid(row=4, column=1, sticky='w', padx=58)


startbtn = tk.Button(gui ,text="Start analysis", font=analyzeFont, command=Chore_Analysis)
startbtn.grid(row=4,column=1)

progressbar_analyze = ttk.Progressbar(gui, length=100)
progressbar_analyze.grid(column=1, row=4, sticky="e")

analyze_done = tk.Label(gui, text="Done!", font=analyzeFont)


l0 = tk.Label(gui, text=' ')
l0.grid(column=0, row=5)
#
# ttk.Separator(gui, orient="horizontal").grid(column=0, row=6, columnspan=3, padx=15, sticky='ew')
#
# l1 = tk.Label(gui, text=' ')
# l1.grid(column=0, row=7)
#
# header_analysis = tk.Label(gui, text= "Merge data", font=headerFont)
# header_analysis.grid(row=8,column = 1)
#
# mergeLabel = tk.Label(gui ,text="Select Merge folder")
# mergeLabel.grid(row=9,column = 0, sticky="w")
# mergeEntry = tk.Entry(gui, textvariable=mergePath)
# mergeEntry.grid(row=9,column=1, ipadx=100, padx=2)
# btnBrowseMerge = ttk.Button(gui, text="Browse",command=getMergePath)
# btnBrowseMerge.grid(row=9,column=2)
#
# strainsLabel = tk.Label(gui ,text="Specify strains:")
# strainsLabel.grid(row=10,column = 0, sticky="w")
# strainsEntry = tk.Entry(gui)
# strainsEntry.grid(row=10,column=1, ipadx=100, padx=2)
#
# infobutton2 = tk.Button(gui, text = 'i', font=myFont, bg='white', fg='blue', bd=0)
# CreateToolTip(infobutton2, text =strains_info)
# infobutton2.grid(row=10,column=3, padx=5)
#
# startbtn2 = tk.Button(gui ,text="Merge files", font=analyzeFont, command=merge_strains)
# startbtn2.grid(row=11,column=1)
#
# progressbar_merge = ttk.Progressbar(gui, length=100)
# progressbar_merge.grid(column=1, row=11, sticky="e")
#
# merge_done = tk.Label(gui, text="Done!", font=analyzeFont)

gui.mainloop()
