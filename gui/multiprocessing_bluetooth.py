import os
from multiprocessing import Pool


macAdresses=('F1:E5:A8:F0:96:80', 'E4:69:61:26:E6:23')

def run_process(adress):
    os.system('python peripheral.py {}'.format(adress))
    
if __name__ == '__main__':
    pool = Pool()
    pool.map(run_process, macAdresses)
    pool.close()
    pool.join()