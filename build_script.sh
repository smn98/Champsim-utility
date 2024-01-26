#!/bin/bash
ENV=$1
L0D_PREF=$2
L1D_PREF=$3
L2C_PREF=$4

IFS='-' 
read -ra parts <<< ${ENV} 
IFS=' '

# prefetcher config
case ${parts[0]} in
    "on_commit")
        sed -i 's|// #define ON_COMMIT_PREFETCHING|#define ON_COMMIT_PREFETCHING|g' inc/config.h 
        ;;
    "TSB")
        sed -i 's|// #define TSB|#define TSB|g' inc/config.h 
        ;;
    *)
        ;;
esac

# filter on/off
if [[ ${parts[1]} == "SUF" ]]; then
    sed -i 's|// #define SUF|#define SUF|g' inc/config.h 
else
    # no action
    :
fi

# depending on env 
./build_champsim.sh hashed_perceptron no ${L0D_PREF} ${L1D_PREF} ${L2C_PREF} no no no no lru lru lru lru lru lru lru lru lru 1 ${L0D_PREF}-${L1D_PREF}-${ENV}

case ${parts[0]} in
    "on_commit")
        sed -i 's|#define ON_COMMIT_PREFETCHING|// #define ON_COMMIT_PREFETCHING|g' inc/config.h 
        ;;
    "TSB")
        sed -i 's|#define TSB|// #define TSB|g' inc/config.h 
        ;;
    *)
        ;;
esac

# filter on/off
if [[ ${parts[1]} == "SUF" ]]; then
    sed -i 's|#define SUF|// #define SUF|g' inc/config.h 
else
    :
fi