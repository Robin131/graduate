import AutoTest.Model.Util as U
from AutoTest.Model.const import FilePath
import os


if __name__ == '__main__':
    ls = os.listdir(FilePath.client_res_path)
    print ls