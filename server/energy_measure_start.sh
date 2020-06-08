#!/bin/bash

MSR_PKG_ENERGY_STATUS="0x611"
# CPU energy counter
MSR_DRAM_ENERGY_STATUS="0x619"
# Energy Status Units(ESU)
ESU=`echo "ibase=16; 1/2^$(rdmsr -X 0x606 -f 12:8)" | bc -l`
# Calculate number od CPU energy status
# counter incremants during sampling period


meas_start=$(rdmsr -X $MSR_PKG_ENERGY_STATUS);

#echo "energy measure start = $meas_start"
echo $meas_start > energy.txt
