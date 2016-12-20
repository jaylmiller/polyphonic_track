import numpy as np
import matplotlib.pyplot as plt
import pickle
from utilities_globals import data_to_dict_matrix
import sys

DATAFILE = 'fretdata.p'
data = pickle.load(open('fretdata.p', 'rb'))
matrix = data_to_dict_matrix(data)


plt.imshow(matrix)
plt.show()
sys.exit()