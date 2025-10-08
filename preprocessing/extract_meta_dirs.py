"""
extract photo meta for all subdirectories
call functions from the extract_metadata_fun.py script
"""

from preprocessing.functions.extract_metadata_fun import extract_metadata_from_directory
import os, glob

dir_in = r'D:\GoogleDrive\Projects_ongoing\snapshotWI\data\combined'
dir_out = r'D:\GoogleDrive\Projects_ongoing\snapshotWI\data\combined_meta'
dirs = glob.glob(f'{dir_in}/*/')
# dirs = dirs[4:]

for d in dirs:
    last_dir = os.path.basename(os.path.dirname(d))
    print(last_dir)
    fn_csv = f'{dir_out}/{last_dir}_meta.csv'
    extract_metadata_from_directory(d, fn_csv)

