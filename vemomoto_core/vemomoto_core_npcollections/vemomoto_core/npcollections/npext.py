'''
Created on 05.07.2016

@author: Samuel
'''
import os
import warnings
import copy
from itertools import repeat, starmap, chain as  iterchain

import numpy as np
from scipy.sparse import csr_matrix

try:
    import autograd.numpy as ag
except ImportError:
    ag = np
try:
    from sharedmem import sharedmem as sh
except ImportError:
    sh = np
    
from vemomoto_core.tools.iterext import Repeater, EmptyList

from .npextc import pointer_sum, pointer_sum_chosen, \
    pointer_sum_chosen_rows, pointer_sum_chosen_rows_fact, pointer_prod, \
    pointer_sum_row_prod

def as_dtype(arr, dtype):
    if arr.dtype == dtype:
        return arr
    return arr.astype(dtype)

def sparsepower(arr, b):
    tmp = np.empty_like(arr.data)
    np.exp(np.multiply(np.log(arr.data, tmp), b, tmp), tmp)
    result = copy.copy(arr)
    result.data = tmp
    return result            

def sparsesum(arr):
    indptr = as_dtype(arr.indptr, np.int64)
    result = pointer_sum(arr.data, indptr)
    return result

def sparseprod(arr):
    indptr = as_dtype(arr.indptr, np.int64)
    result = pointer_prod(arr.data, indptr)
    return result


def sparsepowersum(arr, b):
    tmp = np.empty_like(arr.data)
    np.exp(np.multiply(np.log(arr.data, tmp), b, tmp), tmp)
    indptr = as_dtype(arr.indptr, np.int64)
    result = pointer_sum(tmp, indptr)
    return result

def sparsesum_chosen(arr, indices):
    indptr = as_dtype(arr.indptr, np.int64)
    indicesindptr = as_dtype(indices.indptr, np.int64)
    if not indices.dtype == np.int64:
        if not indices.dtype == np.int:
            raise ValueError("Index array must be an integer array")
        indicesdata = indices.data.astype(np.int64)
    else:
        indicesdata = indices.data
    return pointer_sum_chosen(arr.data, indptr, indicesdata, 
                              indicesindptr)

def sparsesum_chosen_rows(arr, indices, rows):
    indptr = as_dtype(arr.indptr, np.int64)
    indicesindptr = as_dtype(indices.indptr, np.int64)
    if not indices.dtype == np.int64:
        if not indices.dtype == np.int:
            raise ValueError("Index array must be an integer array")
        indicesdata = indices.data.astype(np.int64)
    else:
        indicesdata = indices.data
    if not rows.dtype == np.int64:
        if not rows.dtype == int:
            raise ValueError("Row array must be an integer array")
        rowdata = rows.astype(np.int64)
    else:
        rowdata = rows
    return pointer_sum_chosen_rows(arr.data, indptr, indicesdata, 
                                   indicesindptr, rowdata)

def sparsesum_chosen_rows_fact(arr, indices, rows, factor):
    indptr = as_dtype(arr.indptr, np.int64)
    indicesindptr = as_dtype(indices.indptr, np.int64)
    if not indices.dtype == np.int64:
        if not indices.dtype == np.int:
            raise ValueError("Index array must be an integer array")
        indicesdata = indices.data.astype(np.int64)
    else:
        indicesdata = indices.data
    if not rows.dtype == np.int64:
        if not rows.dtype == int:
            raise ValueError("Row array must be an integer array")
        rowdata = rows.astype(np.int64)
    else:
        rowdata = rows
    return pointer_sum_chosen_rows_fact(arr.data, indptr, indicesdata, 
                                        indicesindptr, rowdata, factor.data)

def sparsesum_row_prod(arr1, columns1, rows1, rowsColumns, 
                       arr2, rows2):
    arr1indptr = as_dtype(arr1.indptr, np.int64)
    columns1indptr = as_dtype(columns1.indptr, np.int64)
    arr2indptr = as_dtype(arr2.indptr, np.int64)
    if not columns1.dtype == np.int64:
        if not columns1.dtype == np.int:
            raise ValueError("columns1 must be an integer array")
        columns1data = columns1.data.astype(np.int64)
    else:
        columns1data = columns1.data
    if not rows1.dtype == np.int64:
        if not rows1.dtype == int:
            raise ValueError("rows1 must be an integer array")
        rows1data = rows1.astype(np.int64)
    else:
        rows1data = rows1
    if not rows2.dtype == np.int64:
        if not rows2.dtype == int:
            raise ValueError("rows2 must be an integer array")
        rows2data = rows2.astype(np.int64)
    else:
        rows2data = rows2
    if not rowsColumns.dtype == np.int64:
        if not rowsColumns.dtype == int:
            raise ValueError("rowsColumns must be an integer array")
        rowsColumnsdata = rowsColumns.astype(np.int64)
    else:
        rowsColumnsdata = rowsColumns
    return pointer_sum_row_prod(arr1.data, arr1indptr, columns1data, 
                                columns1indptr, rowsColumnsdata,
                                rows1data, arr2.data, arr2indptr,
                                rows2data)


"""
def sparsepowersum2D(arr, b):
    tmp = np.empty((b.size, arr.data.size))
    np.exp(np.multiply(np.log(arr.data), b, tmp), tmp)
    return np.vstack([pointer_sum(tmp[i],arr.indptr) for i in range(b.size)]).T
"""
def sparsepowersum2D(arr, b):
    tmp = np.empty((b.size, arr.data.size))
    np.exp(np.multiply(np.log(arr.data), b, tmp), tmp)
    #l = np.log(arr.data)
    #np.multiply(l, b, tmp)
    #np.exp(tmp, tmp)
    if not type(arr.indptr) == np.int64:
        indptr = arr.indptr.astype(np.int64)
    else:
        indptr = arr.indptr
    indptr = (indptr[1:] + np.arange(b.size)[:,None]*arr.size).ravel()
    indptr = np.insert(indptr, 0, 0)
    return pointer_sum(tmp.ravel(), indptr).reshape((b.size, arr.shape[0])).T


def convert_R_pos(x):
    if x < 0:
        return ag.exp(x)
    else: 
        return x+1

def convert_R_pos_reverse(x):
    if x < 1:
        return ag.log(x)
    else: 
        return x-1
    
def convert_R_0_1(x):
    return ag.arctan(x)/np.pi+0.5

def convert_R_0_1_reverse(x):
    return np.tan((x+0.5)*np.pi)

def fields_view(arr, fields):
    #d2 = [(name, arr.dtype.fields[name][0]) for name in fields]
    return np.ndarray(arr.shape, np.dtype({name:arr.dtype.fields[name] 
                                           for name in fields}), 
                      arr, 0, arr.strides)

def remove_fields(a, names):
    """
    `a` must be a numpy structured array.
    `names` is the collection of field names to remove.

    Returns a view of the array `a` (not a copy).
    """
    dt = a.dtype
    keep_names = [name for name in dt.names if name not in names]
    return fields_view(a, keep_names)

def add_alias(arr, original, alias):
    """
    Adds an alias to the field with the name original to the array arr.
    Only one alias per field is allowed.
    """
    
    if arr.dtype.names is None:
        raise TypeError("arr must be a structured array. Use add_name instead.")
    descr = arr.dtype.descr
    
    try:
        index = arr.dtype.names.index(original)
    except ValueError:
        raise ValueError("arr does not have a field named '" + str(original) 
                         + "'")
    
    if type(descr[index][0]) is tuple:
        raise ValueError("The field " + str(original) + 
                         " already has an alias.")
    
    descr[index] = ((alias, descr[index][0]), descr[index][1])
    try:
        arr.dtype = np.dtype(descr)
    except TypeError:
        arr = arr.astype(descr)
    return arr

def add_names(arr, names, sizes=None):
    """
    Adds a name to the data of an unstructured array.
    """
    
    if arr.dtype.names is not None:
        raise TypeError("arr must not be a structured array. "
                        + "Use add_alias instead.")
    
    dt = str(arr.dtype)
    if type(names) is str:
        if arr.ndim > 1: 
            sizeStr = str(arr.shape[-1])
        else:
            sizeStr = ''
        descr = [(names, sizeStr + dt)]
    else:
        if len(names) == arr.shape[-1]:
            descr = [(name, dt) for name in names]
        elif sizes is None:
            raise ValueError("If the length of the names array does not match "
                             + "the length of the first dimension of arr, "
                             + "then the sizes of the fields must be given.")
        elif len(sizes) == len(names):
            if sum(sizes) == arr.shape[-1]:
                descr = [(name, str(sizes[i])+dt) for i, name 
                         in enumerate(names)]
            else:
                raise ValueError("The entries in names must sum to the size "
                                 + "of the first dimension of arr.")
        else:
            raise ValueError("The lengths of the size array and the names "
                             + "array must match.")
            
    arr.dtype = np.dtype(descr)
    return arr

def add_fields(array, names, dtypes, fillVal = None):
        
        if type(names) == str or not hasattr(names, "__iter__"):
            names = [names,]
        else:
            names = list(names)
        
        if type(dtypes) == str or not hasattr(dtypes, "__iter__"):
            dtypes = Repeater(dtypes)
        
        
        for name in names:
            if name in array.dtype.names:
                raise ValueError("A field with name '" + str(name)
                                 + "' does already exist.")
        
        descr = ([d for d in array.dtype.descr if d[0] != ''] 
                 + list(zip(names, dtypes)))
        
        newArr = np.empty(array.shape, dtype=descr)  
        
        newArr[list(array.dtype.names)] = array 
        
        if fillVal is None:
            fillVal = np.zeros(1, dtype=descr)
        elif type(fillVal) == np.ndarray:
            fillVal = add_names(np.expand_dims(fillVal, fillVal.ndim), names)
        elif hasattr(fillVal, "__iter__"):
            fillVal = tuple(fillVal)
        
        newArr[names] = fillVal
        
        return newArr

def merge_arrays(arrays):
    newArr = np.empty(arrays[0].shape, dtype=sum((arr.dtype.descr for 
                                                  arr in arrays), []))
    for arr in arrays:
        for name in arr.dtype.names:
            newArr[name] = arr[name]
    return newArr

def list_to_csr_matrix(array, dtype="double"):
    lengths = [len(i) for i in array]
    indptr = np.zeros(len(lengths)+1)
    indptr[1:] = lengths
    if not np.max(indptr):
        return csr_matrix((len(lengths), 0), dtype=dtype)
    np.cumsum(indptr, out=indptr)
    return csr_matrix((list(iterchain(*array)), 
                       list(iterchain(*(range(l) for l in lengths))),
                       indptr), dtype=dtype)

def csr_list_to_csr_matrix(array, dtype="double"):
    list_arr = [row.data for row in array]
    return list_to_csr_matrix(list_arr, dtype)
    
class csr_matrix_nd(object):
    HighDimAccessError = NotImplementedError("Access to subarrays of "
                                             + "dimension higher "
                                             + "than 1 is not yet "
                                             + "supported.")
    def __init__(self, listMatrix, dtype="double"):
        listMatrix[~listMatrix.astype(bool)] = EmptyList()
        self.data = list_to_csr_matrix(listMatrix.flatten(), dtype=dtype)
        self.shapeFactor = np.array(listMatrix.shape)
        self.shapeFactor[:-1] = self.shapeFactor[1:]
        self.shapeFactor[-1] = 1
        np.multiply.accumulate(self.shapeFactor[::-1], 
                               out=self.shapeFactor[::-1])
        self.ndim = listMatrix.ndim+1
    
        
    def __getitem__(self, index):
        if len(index) == self.ndim:
            return self.data[np.sum(index[:-1]*self.shapeFactor), index[-1]]
        elif len(index) == self.ndim-1:
            return self.data[np.sum(index*self.shapeFactor)]
        else: 
            raise self.HighDimAccessError
    
    def __setitem__(self, index, value):
        if len(index) == self.ndim:
            self.data[np.sum(index[:-1]*self.shapeFactor), index[-1]] = value
        elif len(index) == self.ndim-1:
            self.data[np.sum(index*self.shapeFactor)] = value
        else: 
            raise self.HighDimAccessError

class FlexibleArray(object):
    '''
    classdocs
    '''

    def __init__(self, nparray, copy=True, 
                 dtype=None, recArray=True, extentionFactor=2, 
                 pseudoShared=False):
        '''
        Constructor
        '''
        if pseudoShared:
            if not os.name == 'posix':
                warnings.warn("Sharing the memory is only possible on Unix-"
                              + "based systems. Thus, the memory will not be "
                              + "shared now.")
                pseudoShared = False
                
        self.pseudoShared = pseudoShared
        
        if (type(nparray) == int or type(nparray) == tuple or
                type(nparray) == list):
            if pseudoShared: 
                nparray = sh.full(nparray, 0, dtype=dtype)
            else:
                nparray = np.zeros(nparray, dtype=dtype)
            considerAll = False
        else:
            considerAll = True
        
        self.space = nparray.shape[0]
        
        if not pseudoShared:
            self.array = nparray.copy() if copy else nparray
        else:
            self.array = sh.copy(nparray)
        
        self.isStructured = not self.array.dtype.names is None
        if recArray:
            self.array = np.rec.array(self.array, copy=False)
        
        self.isRecArray = type(self.array) == np.recarray
        self.deleted = set()
        self.extentionFactor = extentionFactor
        
        self.__set_zero_item()
        
        self.aliases = []
        if considerAll:
            if pseudoShared:
                self.considered = sh.full(self.space, True, dtype=bool)
            else:
                self.considered = np.ones(self.space, dtype=bool)
            self.size = self.space
        else:
            if pseudoShared:
                self.considered = sh.full(self.space, False, dtype=bool)
            else:
                self.considered = np.zeros(self.space, dtype=bool)
            self.size = 0
        
        self.changeIndex = 0
    
    def __set_zero_item(self):
        if self.isStructured:
            self.zeroitem = tuple(0 for _ in self.array.dtype.names)
        else:
            self.zeroitem = np.array(0, dtype=self.array.dtype)
            
    def add(self, data=None, **keywordData):
        if data is None:
            if self.isStructured:
                data = keywordData
                keywordData = None
            else: 
                data = self.zeroitem
                keywordData = None
        if len(self.deleted):
            index = self.deleted.pop()
            try:
                self._set_item_by_keywords(index, data, keywordData, True)
                self.considered[index] = True
            except ValueError as e:
                self.deleted.add(index)
                raise e
        else:
            if self.size == self.space: self.expand()
            index = self.size
            self._set_item_by_keywords(index, data, keywordData, True)
            #self.considered[index] = self.size + 1
            self.considered[index] = True
            self.size += 1
        return index
    
    def quick_add(self, **keywordData):
        deletedExists = len(self.deleted)
        if deletedExists:
            index = self.deleted.pop()
            self.array[index] = self.zeroitem
        else:
            if self.size == self.space: self.expand()
            index = self.size
            
        try:
            [self.array[key].__setitem__(index, val) 
                    for key, val in keywordData.items()]
        except ValueError as e:
            if deletedExists: 
                self.deleted.add(index)
            raise e
        
        self.considered[index] = True
        self.size += 1
        return index
    
    def quick_add_tuple(self, data):
        deletedExists = len(self.deleted)
        if deletedExists:
            index = self.deleted.pop()
            self.array[index] = self.zeroitem
        else:
            if self.size == self.space: self.expand()
            index = self.size
            
        try:
            self.array[index] = data
        except ValueError as e:
            if deletedExists: 
                self.deleted.add(index)
            raise e
        
        self.considered[index] = True
        self.size += 1
        return index
    
    def __delitem__(self, index): 
        if index is None:
            return
        size = self.size
        try:
            if index < 0:
                index += size
        except TypeError:
            raise TypeError("Can only delete a complete row. "
                            + "Therefore, index must be an intereger.")
        if index < 0 or index >= size:
            raise IndexError("Index " + str(index) + " out of range " 
                             + str(size))
        if index == size-1:
            self.size -= 1
        else:
            self.deleted.add(index)
        self.considered[index] = False
    
    def expand(self, newlines=None):
        if newlines is None:
            newlines = int(np.ceil(self.space * (self.extentionFactor - 1)))
        
        self.space += newlines
        #print("EXPAND from", self.space, "to", self.space+newlines)
        newshape = list(self.array.shape)
        
        if not self.pseudoShared:
            newshape[0] = self.space
            
            try:
                self.array.resize(newshape, refcheck=False)
                #print("FlexArr expand array SUCCESSFUL")
            except ValueError:
                arr = self.array
                newshape[0] = newlines
                self.array = np.concatenate((arr, np.zeros(newshape, 
                                                           dtype=arr.dtype)))
                if self.isRecArray:
                    self.array = np.rec.array(self.array, copy=False)
                #print("FlexArr expand array FAILED")
            try:    
                self.considered.resize(self.space, refcheck=False)
                #print("FlexArr expand considered SUCCESSFUL")
            except ValueError:
                self.considered = np.concatenate((self.considered, 
                                                  np.zeros(newlines, 
                                                           dtype=bool)))
                #print("FlexArr expand considered FAILED")
        else:
            oldLen = arr.shape[0]
            newshape[0] = newlines + oldLen
            self.array = sh.empty(newshape, dtype=arr.dtype)
            self.array[:oldLen] = arr
            self.array[oldLen:] = 0
            
            considered = self.considered
            self.considered = sh.empty(newshape[0], dtype=bool)
            self.considered[:oldLen] = considered
            self.considered[oldLen:] = False
            if self.isRecArray:
                self.array = np.rec.array(self.array, copy=False)
        
        self.changeIndex += 1
    
    def get_array(self):
        if len(self.deleted):
            return self.array[:self.size][self.considered[:self.size]]
        else:
            return self.array[:self.size]
    
    def __len__(self):
        return self.size - len(self.deleted)
    
    def __getitem__(self, index):
        if index is None:
            return
        try:
            indexErr = index >= self.size
            considered = self.considered[index]
        except TypeError:
            indexErr = index[-1] >= self.size
            considered = self.considered[index[0]]
        
        if indexErr:
            raise IndexError("Index " + str(index) + " out of range " 
                             + str(self.size))
        if not considered:
            raise KeyError("The specified element does not exist.")
        return self.array[index]
    
    def __setitem__(self, index, value=None, clear=False, **keywordData):
        
        try:
            if index < 0:
                index += self.size
            indexErr = index >= self.size or index < 0
        except TypeError:
            if index[0] < 0:
                index = list(index)
                index[0] += self.size
            indexErr = index[0] >= self.size or index[0] < 0
        
        if indexErr:
            raise IndexError("Index " + str(index) + " out of range " 
                             + str(self.size))
        
        if value is None:
            value = keywordData
            keywordData = None
        self._set_item_by_keywords(index, value, keywordData, clear)
        try:
            self.deleted.remove(index)
            self.considered[index] = True
        except KeyError:
            pass
        
    def _set_item_by_keywords(self, index, value, keywordData=None, 
                               clear=False):
        if self.isStructured:
            if clear: 
                self.array[index] = self.zeroitem
            if type(value) == dict:
                if keywordData is not None:
                    keywordData = {**value, **keywordData}
                else:
                    keywordData = value
            elif type(value) is np.ndarray and value.dtype.names is not None:
                [self.array[key].__setitem__(index, val) 
                            for key, val in zip(value, value.dtype.names)]
            else:
                self.array[index] = value
            if keywordData is not None and len(keywordData):
                [self.array[key].__setitem__(index, val) 
                        for key, val in keywordData.items()]
        else:
            self.array[index] = value
    
    def exists(self, *indices):
        try:
            return self.considered[list(indices)].all()
        except IndexError:
            return False
        
    def add_fields(self, names, dtypes, fillVal = None):
        
        array = self.array
        
        if type(names) == str or not hasattr(names, "__iter__"):
            names = (names,)
        
        if type(dtypes) == str or not hasattr(dtypes, "__iter__"):
            dtypes = Repeater(dtypes)
        
        for name in names:
            if name in array.dtype.names:
                raise ValueError("A field with name '" + str(name)
                                 + "' does already exist.")
        
        descr = list(zip(names, dtypes))
        
        if self.pseudoShared:
            newArr = sh.empty(array.shape, dtype=array.dtype.descr + descr)  
        else:
            newArr = np.empty(array.shape, dtype=array.dtype.descr + descr)  
        
        view = fields_view(newArr, array.dtype.names)
        view[:] = array 
        
        simpleFill = True
        if fillVal is None:
            fillVal = np.zeros(1, dtype=descr)
        elif type(fillVal) == np.ndarray:
            fillVal = add_names(np.expand_dims(fillVal, fillVal.ndim), names)
        elif hasattr(fillVal, "__iter__"):
            for name, value in zip(names, fillVal):
                newArr[name] = value
            simpleFill = False
        
        if simpleFill:
            view = fields_view(newArr, names)
            view[self.considered] = fillVal
        
        if self.isRecArray:
            self.array = np.rec.array(newArr, copy=False)
        else:
            self.array = newArr
        
        self.__set_zero_item()
        self.changeIndex += 1
    
    def remove_fields(self, names):
        self.array = remove_fields(self.array, names)
        if self.isRecArray:
            self.array = np.rec.array(self.array, copy=False)
        self.__set_zero_item()
        self.changeIndex += 1
        
    def __iter__(self):
        return FlexibleArrayIterator(self)
    
    def __str__(self):
        return self.get_array().__str__()
    
    def __repr__(self):
        return (str(type(self)) + " object with " + str(len(self)) 
                + " rows occupying the space of " + str(self.space) 
                + " rows. Data: \n" + self.get_array().__repr__())
    
    def get_array_indices(self, column, equalCondition):
        return np.where(self.array[column][:self.size][self.considered[:self.size]] 
                        == equalCondition)[0]
                        
    def extend(self, newRows):
        newRowNumber = self.size - self.space + newRows.shape[0]
        if newRowNumber > 0:
            self.expand(newRowNumber)
        
        start = self.size 
        stop = self.size+newRows.shape[0]
        self.array[start:stop] = newRows
        self.considered[start:stop] = True
        self.size = stop
        
    def is_contiguous(self):
        return (self.considered[:self.size] == True).all()
    
    
    def make_contiguous(self):
        
        if self.is_contiguous():
            return [], []
        
        newLen = len(self)
        
        emptySpaces = np.nonzero(~self.considered[:newLen])[0]
        fill = np.nonzero(self.considered[:self.size])[0][-len(emptySpaces):]
        self.array[emptySpaces] = self.array[fill]
        self.considered[fill] = True
        
        self.deleted.clear()
        self.size = newLen
        
        return fill, emptySpaces
        
        
    
    def cut(self):
        # I do not implement pseudoShared anymore. 
        # If required this can be added and the assertion deleted.
        assert not self.pseudoShared
        
        self.space = self.size
        newshape = list(self.array.shape)
        newshape[0] = self.space
        try:
            self.array.resize(newshape, refcheck=False)
            #print("FlexArr cut array SUCCESSFUL")
        except ValueError:
            self.array = np.resize(self.array, newshape)
            #print("FlexArr cut array FAILED")
        
        try:
            self.considered.resize(self.space, refcheck=False)
            #print("FlexArr cut considered SUCCESSFUL")
        except ValueError:
            self.considered = np.resize(self.considered, self.space)
            #print("FlexArr cut considered FAILED")
        self.changeIndex += 1
        
    
    
class FlexibleArrayDict(FlexibleArray):
    
    def __init__(self, nparray, fancyIndices=None, **flexibleArrayArgs):
        super().__init__(nparray, **flexibleArrayArgs)
        if hasattr(fancyIndices, "__iter__"):
            self.indexDict = {iD:index for index, iD 
                              in enumerate(fancyIndices)}
            if not len(self.indexDict) == self.size:
                raise ValueError("There must be as many distinct keys "
                                 + "as elements!")
        else:
            self.indexDict = {i:i for i in range(self.size)}
    
    def add(self, index, data=None, **keywordData):
        if index in self.indexDict:
            raise KeyError("The given index does already exist.")
        internalIndex = FlexibleArray.add(self, data, **keywordData)
        self.indexDict[index] = internalIndex
        return internalIndex
    
    def quick_add(self, index, **keywordData):
        if index in self.indexDict:
            raise KeyError("The given index does already exist.")
        internalIndex = FlexibleArray.quick_add(self, **keywordData)
        self.indexDict[index] = internalIndex
        return internalIndex
    
    def quick_add_tuple(self, index, data):
        if index in self.indexDict:
            raise KeyError("The given index does already exist.")
        internalIndex = FlexibleArray.quick_add_tuple(self, data)
        self.indexDict[index] = internalIndex
        return internalIndex
    
    def __delitem__(self, index): 
        FlexibleArray.__delitem__(self, self.indexDict.pop(index))
        
    def get_item_count(self):
        return len(self.indexDict)
    
    def __getitem__(self, index):
        return self.array[self.indexDict[index]]
        #return FlexibleArray.__getitem__(self, self.indexDict[index])
    
    def __setitem__(self, index, value=None, clear=False, **keywordData):
        try:
            internalIndex = self.indexDict[index]
            keyExists = True
        except KeyError:
            internalIndex = FlexibleArray.add(self, value, **keywordData)
            self.indexDict[index] = internalIndex
            keyExists = False
        
        if keyExists:
            if value is None:
                value = keywordData
                keywordData = None
            self._set_item_by_keywords(internalIndex, value, 
                                        keywordData, clear)
        return internalIndex
    
    def get(self, index, *default):
        internalIndex = self.indexDict.get(index, None)
        if internalIndex is None:
            if default:
                return default[0]
            internalIndex = self.add(index)
        return FlexibleArray.__getitem__(self, internalIndex)
            
    def exists(self, *indices):
        indexDict = self.indexDict
        return all(index in indexDict for index in indices)
     
    def extend(self, newRows):
        raise NotImplementedError("This method is still to be implemented.")
        #FlexibleArray.extend(self, newRows)
    def getColumnView(self, column):
        return FlexibleArrayDictColumnView.new(self, column)

class FlexibleArrayDictColumnView(FlexibleArrayDict, object):
    @staticmethod
    def new(flexibleArray, column):
        self = copy.copy(flexibleArray)
        self.__class__ = FlexibleArrayDictColumnView
        self.array = self.array[column]
        return self
    def extend(self):
        raise AttributeError("The view is immutable.")
    def __setitem__(self, index, value=None, clear=False, **keywordData):
        raise AttributeError("The view is immutable.")
    def __delitem__(self, index):
        raise AttributeError("The view is immutable.")
    def add(self, data=None, **keywordData):
        raise AttributeError("The view is immutable.")
    def quick_add(self, **keywordData):
        raise AttributeError("The view is immutable.")
    def remove_fields(self, names):
        raise AttributeError("The view is immutable.")
    def add_fields(self, names, dtypes, fillVal=None):
        raise AttributeError("The view is immutable.")
    def expand(self, newlines=None):
        raise AttributeError("The view is immutable.")

class FlexibleArrayIterator(object):
    
    def __init__(self, flexibleArray):
        self.flexibleArray = flexibleArray
        self.relevantIndices = np.nonzero(flexibleArray.considered)[0]
        self.i = 0

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        flexibleArray = self.flexibleArray
        try:
            i = self.i
            self.i += 1
            return flexibleArray.array[i]
        except IndexError:
            raise StopIteration()


def get_chunks(arr, key=None, returnKeys=False):
    if key is None:
        key = arr 
    elif not (hasattr(key, "__iter__") and not type(key) == str):
        key = arr[key]
    
    splits = np.nonzero(key!=np.roll(key, 1))[0]
    if not len(splits):
        if returnKeys:
            return [key[0]], [arr]
        else: 
            return [arr]
    splittedArr = np.split(arr, splits[1:])
    
    if returnKeys:
        return key[splits], splittedArr
    return splittedArr

def in1d(a, b, rtol=1e-6, atol=0):
    #if not len(a):
    #    return np.array([], dtype=bool)
    #if not len(b):
    #    return np.zeros_like(a, dtype=bool)
    b = np.unique(b)
    intervals = np.empty(2*b.size, float)
    intervals[::2] = b
    intervals[1::2] = b * (1+rtol) + atol
    overlaps = intervals[:-1] >= intervals[1:]
    overlaps[1:] = overlaps[1:] | overlaps[:-1]
    keep = np.concatenate((~overlaps, [True]))
    intervals = intervals[keep]
    return np.searchsorted(intervals, a, side='right') & 1 == 1

def in1d2d(a, b, rtol=1e-6, atol=0):
    if not a.shape[0] == b.shape[0]:
        raise ValueError("The arrays must have the same first dimension")
    if not a.size or not b.size:
        return np.zeros(a.shape, dtype=bool)
    return np.array(list(starmap(in1d, zip(a, b, repeat(rtol),  repeat(atol)))),
                    ndmin=2, dtype=bool)


def binary_ceil(arr, digits):
    out = arr.copy()
    v = out.view(np.uint64)
    v |= np.uint64(2**digits-1)
    return out    

def binary_floor(arr, digits):
    out = arr.copy()
    v = out.view(np.uint64)
    v &= ~np.uint64(2**digits-1)
    return out

def get_precision_binary_digits(rTol):
    return int(np.round(np.log2(rTol)+53))

"""
def searchsorted2d(a, b):
    m, n = a.shape
    max_num = np.maximum(a.max() - a.min(), b.max() - b.min()) + 1
    r = max_num*np.arange(a.shape[0])[:,None]
    p = np.searchsorted( (a+r).ravel(), (b+r).ravel() ).reshape(m,-1)
    return p - n*(np.arange(m)[:,None])

def get_common_element2d(a, b):
    # Sort each row of a and b in-place
    a.sort(1)
    b.sort(1)

    # Use 2D searchsorted row-wise between a and b
    idx = searchsorted2d(a,b)

    # "Clip-out" out of bounds indices
    idx[idx==a.shape[1]] = 0

    # Get mask of valid ones i.e. matches
    mask = np.take_along_axis(a,idx,axis=1) == b

    # Use argmax to get first match as we know there's at most one match
    match_val = np.take_along_axis(b,mask.argmax(1)[:,None],axis=1)

    # Finally use np.where to choose between valid match 
    # (decided by any one True in each row of mask)
    return np.where(mask.any(1)[:,None], match_val, np.nan)
"""

def testAccuracyFA(n):
    from npextc import FlexibleArray as FlexibleArray_c
    from npextc import FlexibleArrayDict as _FlexibleArrayDict_c
    a = np.zeros(10, dtype = {"names":["A", "B"], "formats": ["int", "double"]})
    a["A"] = np.arange(10)
    
    A1 = FlexibleArray(a)
    A2 = FlexibleArray_c(a)
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert (A1.get_array() == A2.get_array()).all()
    for i in range(n):
        A1.add((n, n))
        A2.add((n, n))
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert (A1.get_array() == A2.get_array()).all()
    for i in np.random.choice(np.arange(n), n//2, replace=False):
        del A1[i]
        del A2[i]
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert (A1.considered == A2.considered).all()
    assert (A1.get_array() == A2.get_array()).all()
    for i in range(n//2):
        A1[-i] = (-i, -i/2) 
        A2[-i] = (-i, -i/2) 
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert (A1.get_array() == A2.get_array()).all()
    A1.add_fields(["C"], [object], None)
    A2.add_fields(["C"], [object], None)
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert (A1.get_array() == A2.get_array()).all()
    for i in range(n//2):
        A1.add((i, i/2, []))
        A2.add((i, i/2, []))
    
    A1.cut() 
    A2.cut()
    
    print("len(A1), len(A2)", len(A1), len(A2))
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    
    A1.make_contiguous()
    A2.make_contiguous()
     
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    
    cons = A1.get_array() != A2.get_array()
    
    print(cons)
    print(len(cons))
    print(A1.get_array()[cons])
    print(A2.get_array()[cons])
    print(A1.get_array())
    print(A2.get_array())
    assert (A1.get_array() == A2.get_array()).all()
    
    print("Test Successful!")

def testAccuracyFAD(n):
    print("start")
    from npextc import FlexibleArrayDict as FlexibleArrayDict_c
    a = np.zeros(10, dtype = {"names":["A", "B"], "formats": ["int", "double"]})
    a["A"] = np.arange(10)
    
    A1 = FlexibleArrayDict(a)
    A2 = FlexibleArrayDict_c(a)
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert (A1.get_array() == A2.get_array()).all()
    print("check 1 successful")
    for i in range(10, n):
        A1.add(i, (i, i))
        A2[i] = (i, i)
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert (A1.get_array() == A2.get_array()).all()
    print("check 2 successful")
    for i in np.random.choice(np.arange(n), n//2, replace=False):
        del A1[i]
        del A2[i]
    
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert (A1.considered == A2.considered).all()
    assert (A1.get_array() == A2.get_array()).all()
    assert A1.indexDict.keys() == A2.indexDict.keys()
    print("check 3 successful")
    for i in range(n//2):
        A1[i] = (-i, -i/2) 
        A2[i] = (-i, -i/2) 
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    assert A1.indexDict.keys() == A2.indexDict.keys()
    print("check 4 successful")
    
    for i in A1.indexDict.keys():
        assert A1[i] == A2[i]
    A1.add_fields(["C"], [object], None)
    A2.add_fields(["C"], [object], None)
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    for i in A1.indexDict.keys():
        assert A1[i] == A2[i]
    print("check 5 successful")
    for i in range(n, 3*n//2):
        A1.add(i, (i, i/2, []))
        A2[i] = (i, i/2, [])
    
    A1.cut() 
    A2.cut()
    
    print("len(A1), len(A2)", len(A1), len(A2))
    
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    print("check 6 successful")
    
    A1.make_contiguous()
    A2.make_contiguous()
     
    assert len(A1) == len(A2) 
    assert A1.size == A2.size
    print("check 7 successful")
    
    for i in A1.indexDict.keys():
        assert A1[i] == A2[i]
    print("check 8 successful")
    
    print("Test Successful!")

def fTFA(n, a, rands):
    A1 = FlexibleArrayDict(a)
    for i in range(10, n):
        A1.add(i, (i, i))
    for i in rands:
        del A1[i]
    for i in range(n//2):
        A1[i] = (-i, -i/2) 
    #A1.add_fields(["C"], [object], None)
    #for i in range(n, 3*n//2):
    #    A1.add(i, (i, i/2, []))
    #A1.cut() 
    #A1.make_contiguous()
    
from npextc import FlexibleArrayDict as FlexibleArrayDict_c
def fTFAc(n, a, rands):
    A2 = FlexibleArrayDict_c(a)
    for i in range(10, n):
        A2[i] = (i, i)
    for i in rands:
        del A2[i]
    for i in range(n//2):
        A2[i] = (-i, -i/2) 
    #A2.add_fields(["C"], [object], None)
    #for i in range(n, 3*n//2):
    #    A2[i] = (i, i/2, [])
    #A2.cut()
    #A2.make_contiguous()

def testSpeedFA(n):
    dt = np.dtype({"names":["vertexIndex", "depth", 
                                                 "parentMinHeight", "parent", 
                                                 "extention", "xCost", 
                                                 "successors", "visited",
                                                 "edge", "relevant", 
                                                 "improvableInnerVertex"],
                                      "formats":["int", "double", "double",
                                                 "int", "double", "double",
                                                 "object", "bool",
                                                 "int", "bool", "bool"]})
    
    a = np.zeros(10, dtype = {"names":["A", "B"], "formats": ["int", "double"]})
    a["A"] = np.arange(10)
    rands = np.random.choice(np.arange(n), n//2, replace=False)
    from simprofile import profile
    profile("fTFA(n, a, rands)", globals(), locals())
    profile("fTFAc(n, a, rands)", globals(), locals())

def testFlexBoolArr():     
    a = FlexibleArrayDict_c((2,10), dtype=[("a", "bool"), ("b", "int")])
    a[10] = (False, 2)
    a[2] = [(True, 10),] * 10
    a[10][1] = (True, 3)
    print(a)
    

def testPower_Sum3D():
    from npextc import pointer_sum3D, pointer_sum3DY
    a = np.arange(24, dtype="double").reshape((2,3,4))
    ind = np.array([0,2,3], dtype=np.int64)
    print(a)
    print(pointer_sum3D(a, ind))
    print(pointer_sum3DY(a, ind))



def test_sp_chosen2():
    r = np.array(
        [[  1,   0.,   0.],
         [  10,   0.,   0.],
         [  1e2,   2e2,   0.],
         [  1e3,   0.,   0.],
         [  1e4,   2e4,   0.],
         [  1e5,   2e5,   5e5],
         [  1e6,   0.,   0.]])
    
    r = csr_matrix(r)
    
    ind_data=np.array([0, 0, 1, 0, 0, 1, 0, 1, 1, 0], dtype=np.int64)
    ind_indptr=np.array([ 0,  1,  2,  3,  4,  5,  6,  8,  9, 10], dtype=np.int64)
    ind_indices=np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0], dtype=np.int64)
    ind = csr_matrix((ind_data, ind_indices, ind_indptr), shape=(9, 2))

    t = csr_matrix(np.array([[ 0.51670614,  0.        ,  0.        ],
       [ 0.51670614,  0.        ,  0.        ],
       [ 0.45985727,  0.60151814,  0.        ],
       [ 0.45985727,  0.        ,  0.        ],
       [ 0.60151814,  0.        ,  0.        ],
       [ 0.70783489,  0.        ,  0.        ],
       [ 0.53526877,  0.53526877,  0.        ],
       [ 0.74534979,  0.45286325,  0.24240356],
       [ 0.45286325,  0.        ,  0.        ],
       [ 0.45286325,  0.        ,  0.        ],
       [ 0.53526877,  0.        ,  0.        ],
       [ 0.53526877,  0.        ,  0.        ],
       [ 0.74077252,  0.        ,  0.        ],
       [ 0.74077252,  0.45985727,  0.        ],
       [ 0.52185726,  0.        ,  0.        ],
       [ 0.47016788,  0.        ,  0.        ]]))
    t.data[:] = 1
    
    array = np.array
    int64 = np.int64
    
    pairIndices = array([0, 1, 2, 3, 4, 2, 5, 5, 1, 0, 3, 2, 4, 2, 5, 6], dtype=int64)
    psi = array([0, 1, 2, 3, 4, 5, 6, 7, 1, 0, 3, 2, 4, 5, 7, 8], dtype=int64)
    b =array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15], dtype=int64)
    
    obsProbs = sparsesum_row_prod(r, ind, pairIndices, psi, t, b)
    
    print(obsProbs)
    
    
def test_sp_chosen():
    
    a = list_to_csr_matrix([
        [1,1],
        [1,2,3],
        [2],
        [3,4],
        []], 'double')
    ind = list_to_csr_matrix([
        [0,1],
        [1,2],
        [0],
        [],
        []], np.int64)
    ind2 = list_to_csr_matrix([
        [0,1],
        [],
        [1]], np.int64)
    fact = list_to_csr_matrix([
        [0.5,0.1],
        [],
        [2]])
    fact2 = list_to_csr_matrix([
        [0.5,0.1],
        [3,4],
        [2],
        []])
    
    rows = np.array((1,2,1), dtype=int)
    rows1 = np.array((0,2,1,1), dtype=int)
    rowsColumns = np.array((2,1,0,0), dtype=int)
    rows2 = np.array((2,3,0,1), dtype=int)
    
    
    print(sparsesum_chosen(a, ind))
    print(sparsesum_chosen_rows(a, ind2, rows))
    print(sparsesum_chosen_rows_fact(a, ind2, rows, fact))
    
    print(sparsesum_row_prod(a, ind2, rows1, rowsColumns, fact2, rows2))
    
    rows = np.array([0, 1, 2, 3, 4, 5, 6, 7, 2, 5, 7, 7, 7, 5, 6, 8, 8], dtype=np.int64)
    arr = csr_matrix(np.array([[ 1.04568108,  0.        ,  0.        ],
       [ 1.06762593,  0.        ,  0.        ],
       [ 1.08822421,  1.08233152,  0.        ],
       [ 1.075569  ,  0.        ,  0.        ],
       [ 1.06762654,  0.        ,  0.        ],
       [ 1.0823315 ,  1.09344758,  0.        ],
       [ 1.082332  ,  1.08233231,  1.07556986],
       [ 1.08822386,  1.08233183,  1.09344745],
       [ 1.05798311,  0.        ,  0.        ]]))
    indices = csr_matrix(np.array([[0, 0],
       [0, 0],
       [1, 0],
       [0, 0],
       [0, 0],
       [0, 0],
       [0, 0],
       [0, 0],
       [1, 0],
       [0, 0],
       [0, 1],
       [1, 0],
       [0, 0],
       [0, 0],
       [1, 0],
       [0, 0],
       [0, 0]], dtype=np.int64))
    print(sparsesum_chosen_rows(arr, indices, rows))

if __name__ == "__main__":
    test_sp_chosen2()
    #testPytpcore()
    #testPower_Sum3D()
    #testFlexBoolArr()     
    #testAccuracyFAD(10000)
    #testSpeedFA(1000000)
    
    
    """
    arrs = [bitarray(10) for _ in range(5)]
    print(arrs)
    print(transpose_bitarray(arrs))
    
    
    a = np.zeros(10, dtype = {"names":["A", "B"], "formats": ["int", "double"]})
    a["A"] = np.arange(10)
    A = FlexibleArray(a)
    A.add((3,2))
    print(A.get_array())
    A.add((2.1, .1))
    del A[0]
    print(A.get_array())
    A.add((123,5))
    print(A)
    
    del A[4]
    print(A.make_contiguous())
    print(A)
    
    #"""
    
    """
    b = FlexibleArray((3,5), dtype={"names":["a","b"],"formats":["int", "2double"]})
    b2 = FlexibleArrayDict(5, dtype={"names":["a","b"],"formats":["int", "2double"]})
    b2.add(2, (2, (2,3)))
    print(b2.get_array())
    print(b2.array)
    b3 = b2.getColumnView("b")
    print(b3.get_array())
    print(b3[2])
    print(type(b3[2]))
    #b.expand()
    #print(b.array)
    for i in range(5):
        b.add(a=i, b=(i, i))
    b[0,2] = {"a": 3, "b":5}
        
    print(b.get_array())
    print(b.array)
    """
    """
    arr = np.zeros(10, dtype={"names":["a","b"],"formats":["int", "double"]})
    arr["a"] = [1, 1, 2, 2, 2, 5, 2, 2, 6, 6]
    arr["b"] = np.arange(10)
    for chunk in get_chunks(arr, "a"):
        print(chunk)
    for i, chunk in zip(*get_chunks(arr["b"], arr["a"], True)):
        print(i, set(chunk))
    """