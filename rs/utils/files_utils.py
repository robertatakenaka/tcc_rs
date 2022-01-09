
import os
import csv
import numpy as np


def create_folder(*args):
    path = os.path.join(*args)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def write_file(file_path, content, mode="w"):
    with open(file_path, mode) as fp:
        fp.write(content)


def read_file(file_path):
    with open(file_path, "r") as fp:
        return fp.read()


def read_csv_file(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yield row


def write_array(file_path, arr):
    np.save(file_path, arr, allow_pickle=True, fix_imports=True)


def read_array(file_path):
    return np.load(file_path, mmap_mode="r")