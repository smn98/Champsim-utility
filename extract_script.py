import os
import codecs
import argparse
import pandas as pd
import re
import time
from scipy.stats.mstats import gmean
import sys
import socket

import warnings

warnings.filterwarnings("ignore")
    # Code that may raise warnings
# Warnings are enabled again outside the context manager


def initializeDataframe():
    dataPoints = pd.read_csv("dataPoints.csv")
    caches = ['L0D', 'L1D', 'L2C', 'LLC']
    df.at[0,'Benchmarks'] = ""
    
    for index, dataPoint in dataPoints.iterrows():
        if not dataPoint['cache']:
            df.at[0, dataPoint['name']] = 0
        # extracts statistics for each cache
        if dataPoint['cache']:
            for cache in caches:
                df.at[0, f"{cache} {dataPoint['name']}"] = 0
    df.drop(index=0, inplace=True)

def extractData(filename, path):
    file = codecs.open(f"{path}/{filename}", "r", encoding="utf-8", errors='ignore')
    trace = '.'.join(filename.split('.')[0:2])

    currentIndex = len(df.index)
    df.at[currentIndex, 'Benchmarks'] = trace

    dataPoints = pd.read_csv("dataPoints.csv")
    caches = ['L0D', 'L1D', 'L2C', 'LLC']

    for line in file:
        for index, dataPoint in dataPoints.iterrows():
            # extracts overall statistics (not specific to any cache)
            if not dataPoint['cache'] and re.search(dataPoint['searchText'], line):
                # print(dataPoint['name'])
                df.at[currentIndex, dataPoint['name']] = float(line.split()[dataPoint['fieldNumber']-1])
            # extracts statistics for each cache
            if dataPoint['cache'] and re.search(dataPoint['searchText'], line):
                for cache in caches:
                    if re.search(f"{cache} {dataPoint['searchText']}", line):
                        if dataPoint['name'] == "Dropped prefetches" and len(line.split()) <= (dataPoint['fieldNumber'] - 1):
                            dataPoint['fieldNumber'] = 10
                        if len(line.split()) > (dataPoint['fieldNumber'] - 1):
                            df.at[currentIndex, f"{cache} {dataPoint['name']}"] = float(line.split()[dataPoint['fieldNumber']-1])

def calculateDerivedAttributes():
    cache = "L0D"
    if args.prefetcher.split('-')[1] != 'no': #L1D prefetcher
        cache = "L1D"
    elif args.prefetcher.split('-')[2] != 'no': #L2C prefetcher
        cache = "L2C"

    # Add derived attributes here
    df["Prefetcher Accuracy"] = df[f"{cache} Timely prefetches"] / df[f"{cache} Prefetch fills"] * 100
    df["Prefetcher Accuracy(With Late)"] = (df[f"{cache} Timely prefetches"] + df[f"{cache} Late prefetches"]) / df[f"{cache} Prefetch fills"] * 100
    df["Percent of Late prefetches"] = df[f"{cache} Late prefetches"] / df[f"{cache} Prefetch fills"] * 100
    df["Percent of Timely prefetches"] = df[f"{cache} Timely prefetches"] / df[f"{cache} Prefetch fills"] * 100
    df["Prefetches issued per kilo instructions"] = df[f"{cache} Prefetches issued to lower level"] / (int(args.nsim) * 1000)
    # df["Percent of Commit Late prefetches"] = df[f"{cache} Commit late prefetches"] / df[f"{cache} Prefetch fills"] * 100
    # df["Percent of Commit Late MSHR prefetches"] = df[f"{cache} Commit late mshr prefetches"] / df[f"{cache} Prefetch fills"] * 100
    # df["Prefetch missed opportunity per kilo instruction"] = df[f"{cache} Missed opportunity"] / (int(args.nsim) * 1000)
    # if args.environment.split('-')[-1] == "gm":
    #     df["Prefetcher Coverage"] = 1 - (df[f"L2C Load access"]/df[f"L0D Load access"]) 
    # else:
    #     df["Prefetcher Coverage"] = 1 - (df[f"L2C Load access"]/df[f"L1D Load access"]) 

def calculateDerivedFromBaseline():
    if args.baseline:    
        cache = "L0D"
        if args.prefetcher.split('-')[0] == 'no': #L1D prefetcher
            cache = "L1D"

        if not os.path.isfile(f"../results-{socket.gethostname()}/{args.benchmark}/no-no-no-{args.baseline}.csv"):
            command = f"python3 extractor.py -b {args.benchmark} -p no-no-no -e {args.baseline} -n {args.nsim}"
            print("Extracting baseline.")
            os.system(command)
        
        # print(f"Reading csv: ../results-{socket.gethostname()}/{args.benchmark}/no-no-no-{args.baseline}.csv")
        baseline = pd.read_csv(f"../results-{socket.gethostname()}/{args.benchmark}/no-no-no-{args.baseline}.csv")

        if not os.path.isfile(f"../results-{socket.gethostname()}/{args.benchmark}/no-no-no-{args.baseline}.csv"):
            command = f"python3 extractor.py -b {args.benchmark} -p no-no-no -e no-no-non_secure -n {args.nsim}"
            print("Extracting non-secure baseline.")
            os.system(command)
        
        # print(f"Reading csv: ../results-{socket.gethostname()}/{args.benchmark}/no-no-no-non_secure.csv")
        non_secure_baseline = pd.read_csv(f"../results-{socket.gethostname()}/{args.benchmark}/no-no-no-no-no-non_secure.csv")

        # if not (args.prefetcher.split('-')[0] != "no" and args.baseline.split('-')[-1] != "gm"):
        #     print("Calculating Coverage")
        #     df["Covered"] = baseline[f"{cache} Load miss"] - df[f"{cache} Load miss"]
        #     df["Normal Coverage"] = (baseline[f"{cache} Load miss"] - df[f"{cache} Load miss"]) * 100 / baseline[f"{cache} Load miss"]
        # else:
        #     df["Normal Coverage"] = 0
        
        df["Speedup"] = df["IPC"]/baseline["IPC"]
        df["Speedup Non-secure"] = df["IPC"]/non_secure_baseline["IPC"]

    else:
        # df["Prefetcher Coverage"] = 0
        df["Speedup"] = 0
    
def calculateAverages():
    # Mean
    df.fillna(0, inplace=True)
    df.replace(0,0.000001,inplace=True)
    
    currentIndex = len(df.index)
    df.loc[currentIndex]= df.mean(numeric_only=True, axis=0)
    df.at[currentIndex,'Benchmarks'] = "Mean"

    # Geomean
    df.loc[currentIndex+1] = pd.concat([pd.DataFrame(['Geomean']),pd.DataFrame(gmean(df.loc[:,df.columns != 'Benchmarks'], axis=0))]).reset_index(drop = True).T.values.tolist()[0]
    # steps to create Geomean:
    # 1. Use gmean function of scipy to get geomean of across all columns.
    # 2. Change it to dataframe.
    # 3. Concat Geomean string to the first column of the dataframe.
    # 4. Change it to list and add it to the main dataframe.

def main():
    startTime = time.time()

    initializeDataframe()

    for filename in sorted(os.listdir(path)):
        extractData(filename, path)

    df.fillna(0, inplace=True)

    calculateDerivedAttributes()
    
    calculateDerivedFromBaseline()

    calculateAverages()

    df.to_csv(f"../results-{socket.gethostname()}/{args.benchmark}/{args.prefetcher}-{args.environment}.csv", index=False)

    print(f"Out csv: ../results-{socket.gethostname()}/{args.benchmark}/{args.prefetcher}-{args.environment}.csv")


    print("Elapsed time: %s secs" % (time.time() - startTime))
    print(" ")

if __name__ == '__main__':
    df = pd.DataFrame()
    parser = argparse.ArgumentParser(
                        prog = 'Extractor',
                        description = 'Extracts all datapoints for all traces of a given benchmark',
                        epilog = 'Use it well.')

    parser.add_argument('-b','--benchmark', metavar='spec', required=True,
                        help='Name of benchmark')
    parser.add_argument('-p','--prefetcher', metavar='ip_stride', required=True,
                        help='Name of prefetcher')
    parser.add_argument('-e','--environment', metavar='gm', required=True,
                        help='Environment to be used')
    parser.add_argument('-s','--baseline', metavar='no-no-no-non_secure',
                        help='L0D prefetcher-L1D prefetcher-Baseline environment')

    parser.add_argument('-n','--nsim', metavar='10', required=True,
                        help='Number of simulation instructions(in millions)')

    args = parser.parse_args()
    path = f"../results-{socket.gethostname()}/{args.benchmark}/{args.prefetcher}/{args.environment}/results_{args.nsim}M"

    user_input = print(f"{path}\nWorking on the above parent directory.\n")
    # if user_input.lower() == 'n':
        # print("terminating.")
        # sys.exit()

    main()