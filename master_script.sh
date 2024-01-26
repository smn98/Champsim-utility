#!/bin/bash
set -e

MODE=$1
BUILD=$2
L0D_PREF=$3
L1D_PREF=$4
L2C_PREF=$5
ENV=$6
BENCH=$7
N_WARM=$8
N_SIM=$9
BASELINE=${10}

echo $HOSTNAME

if [ "$#" -lt 10 ]; then
    echo "Illegal number of parameters"
    echo "Usage: ./start.sh [MODE] [BUILD_FLAG] [L0D_PREF] [L1D_PREF] [L2C_PREF] [ENV] [BENCHMARK] [N_WARM] [N_SIM] [BASELINE]"
    exit 1
fi
    
if [ $BUILD -eq 1 ]
then
    ./build-test.sh ${ENV} ${L0D_PREF} ${L1D_PREF} ${L2C_PREF}
else
    echo "Skipping build..."
fi

if [ "$MODE" = "build" ]
then
    echo "closing.."
    exit 1
else
    if [ "$MODE" = "test" ]
    then
        ./run-test.sh ${ENV} ${L0D_PREF} ${L1D_PREF} ${L2C_PREF} ${BENCH} ../results-${HOSTNAME}/test/${L0D_PREF}-${L1D_PREF}-${L2C_PREF}-${ENV} ${N_WARM} ${N_SIM}
    elif [ "$MODE" = "upload" ]
    then
        python3 extractor.py -b ${BENCH} -p ${L0D_PREF}-${L1D_PREF}-${L2C_PREF} -e ${ENV} -n ${N_SIM} -s ${BASELINE}
        python3 uploader.py -b ${BENCH} -p ${L0D_PREF}-${L1D_PREF}-${L2C_PREF} -e ${ENV}
    else
        ./run_suite.sh ${ENV} ${L0D_PREF} ${L1D_PREF} ${L2C_PREF} ${BENCH} ../results-${HOSTNAME}/${BENCH}/${L0D_PREF}-${L1D_PREF}-${L2C_PREF}/${ENV} ${N_WARM} ${N_SIM}
        wait
        python3 extractor.py -b ${BENCH} -p ${L0D_PREF}-${L1D_PREF}-${L2C_PREF} -e ${ENV} -n ${N_SIM} -s ${BASELINE}
        python3 uploader.py -b ${BENCH} -p ${L0D_PREF}-${L1D_PREF}-${L2C_PREF} -e ${ENV}
    fi
fi