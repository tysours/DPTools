#!/usr/bin/env bash

#dptools train ../input/data
#dptools train -p 00_iteration0/01_train ../input/data

#dptools train -e -p 00_iteration0/01_train ../input/data
#grep seed 00_*/01*/0*/in.json # check to make sure ensemble seeds are different

#dptools train -es -p 00_iteration0/01_train ../input/data # will fail if HPC stuff not configured
