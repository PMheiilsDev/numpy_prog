
from math import * 
import numpy as np
import os

def help():
    print()
    print("E_mat(n) returns identity Matrix (n x n) \n")

    print("mat_inv( mat ) return the inverse of mat \n")

    print("mat_det( mat ) get determinat of mat \n")

    print("mat_times( mat1, mat2 ) return the matrix mat1*mat2 \n")

    print("mat_solve( mat, vec ) solves for v in mat * v = vec \n")

    print("vec_cross( vec1, vec2 ) return the crossproduct \n")

def E_mat(n):
    return np.identity(n)

def mat_inv( mat ):
    return np.linalg.inv( mat )

def mat_det( mat ):
    return np.linalg.det( mat )

def mat_times( mat1, mat2 ):
    return np.dot( mat1, mat2 )

def mat_solve( mat, vec ):
    return np.linalg.solve( mat, vec )

def vec_cross( vec1, vec2 ):
    return np.cross( vec1, vec2 )

def vec_add( vec1, vec2 ):
    return np.add(vec1, vec2 ) 

def vec_neg( vec ):
    new_vec = []
    for i in vec:
        new_vec.append(-i)
    return new_vec


eps0 = 8.854188e-12


def clear():
    os.system("cls")
    return None
    

# clear function
clear_prot = []
def clear_var( cls=False ):
    list_of_keys = list(globals().keys())
    for i,t in enumerate(list_of_keys):
        if t in clear_prot:
            continue
        else:
            print ("del", t)
            del globals()[t]
    if cls:
        clear()
    
# save things not to be cleared
clear_prot = list(globals().keys())
