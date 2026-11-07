from numpy import array, diag, zeros, arctan2, pi, sqrt, finfo, count_nonzero, delete, vstack
from numpy.linalg import svd, norm
from scipy.optimize import least_squares
from PySide6 import QtCore

class XConstraint:
    def __init__(self, image_x, image_y, target_x, weight):
        self.image_x = image_x
        self.image_y = image_y
        self.target_x = target_x
        self.weight  = weight

class YConstraint:
    def __init__(self, image_x, image_y, target_y, weight):
        self.image_x = image_x
        self.image_y = image_y
        self.target_y = target_y
        self.weight  = weight

class NLLSSolver(QtCore.QObject):
    emitcreateconstraint = QtCore.Signal(object)
    emitdestroyconstraint = QtCore.Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.xconstraints: list[XConstraint] = []
        self.yconstraints: list[YConstraint] = []

    def CreateXConstraint(self, image_x, image_y, target_x, weight=1.0, emit=True):
        c = XConstraint(image_x, image_y, target_x, weight)
        self.xconstraints.append(c)
        if emit:
            self.emitcreateconstraint.emit(c)
        return c
    
    def CreateYConstraint(self, image_x, image_y, target_y, weight=1.0, emit=True):
        c = YConstraint(image_x, image_y, target_y, weight)
        self.yconstraints.append(c)
        if emit:
            self.emitcreateconstraint.emit(c)
        return c

    def DestroyConstraint(self, c, emit=True):
        if c in self.xconstraints:
            if emit:
                self.emitdestroyconstraint.emit(c)
            self.xconstraints.remove(c)
        elif c in self.yconstraints:
            if emit:
                self.emitdestroyconstraint.emit(c)
            self.yconstraints.remove(c)

    '''
    # Calculate Rank from Singular Value - code stolen from matrix_rank()
    # Used to avoid calling svd() twice
    def rank_from_S(self, S, A):
        tol = S.max(axis=-1, keepdims=True) * max(A.shape[-2:]) * finfo(S.dtype).eps
        return count_nonzero(S > tol, axis=-1)

    def compute_one_solution(self, A, b):
        U, S, Vh = svd(A, full_matrices=False)
        r = self.rank_from_S(S, A)
        #print(U.shape)
        #print(S.shape)
        #print(Vh.shape)
        D = diag(S)
        Dinv = D.copy()
        for i in range(0,r):
            Dinv[i,i] = 1./Dinv[i,i]

        # Compute solution from the SVD
        x = Vh.transpose()@Dinv@U.transpose()@b
        return x, r

    def try_no_y_skew(self, A, b):
        Anew = delete(A,5,1)
        xnew,rnew = self.compute_one_solution(Anew, b)
        err = norm(Anew@xnew-b)
        xnew = vstack((xnew,array([[0.]])))
        return xnew,rnew,err

    def try_no_x_skew(self, A, b):
        Anew = delete(A,4,1)
        xnew,rnew = self.compute_one_solution(Anew, b)
        err = norm(Anew@xnew-b)
        xnew = vstack((xnew[0:4],array([[0.]]),xnew[4]))
        return xnew,rnew,err

    def try_no_skew(self, A, b):
        Anew = delete(A,range(4,6),1)
        xnew,rnew = self.compute_one_solution(Anew, b)
        err = norm(Anew@xnew-b)
        xnew = vstack((xnew[0:4],array([[0.]]),array([[0.]])))
        return xnew,rnew,err

    def compute_solution(self, A, b):
        TOL = 1.e-8
        x,r = self.compute_one_solution(A, b)
        if r == 6:
            return x,r,2
        # insert logic here - don't skew if you don't need to
        if abs(x[5]) < TOL:
            if abs(x[4]) < TOL:  # already no skew
                return x,r,0
            else:  # only x skew, try to remove it
                xnew,rnew,err = self.try_no_x_skew(A, b)
                if err < TOL:
                    return xnew,rnew,1
                else:
                    return x,r,0
        elif abs(x[4]) < TOL: # only y skew, try to remove it
            xnew,rnew,err = self.try_no_y_skew(A, b)
            if err < TOL:
                return xnew,rnew,1
            else:
                return x,r,0
        else: # skew in y and x, try to remove in order
            xnew,rnew,err = self.try_no_y_skew(A, b)
            if err < TOL: # removed y skew
                x = xnew.copy()
                r = rnew.copy()
                xnew,rnew,err = self.try_no_skew(A, b)
                if err < TOL: # removed all skew
                    return xnew,rnew,1
                else:
                    return x,r,1
            else:
                xnew,rnew,err = self.try_no_x_skew(A, b)
                if err < TOL: # removed x skew
                    return xnew,rnew,1
                else:
                    return x,r,1
    '''

    def FunctionFx(self, image_x, image_y, x):
        return ( x[0]*image_x + x[1]*image_y + x[2] )/( 1 + x[4]*image_x + x[5]*image_y)

    def FunctionFy(self, image_x, image_y, x):
        return (-x[1]*image_x + x[0]*image_y + x[3] )/( 1 + x[4]*image_x + x[5]*image_y)
    
    def FunctionG(self, x):
        r = zeros((self.m,))
        i = 0
        for xc in self.xconstraints:
            r[i] = self.FunctionFx(xc.image_x, xc.image_y, x) - xc.target_x
            i += 1
        for yc in self.yconstraints:
            r[i] = self.FunctionFy(yc.image_x, yc.image_y, x) - yc.target_y
            i += 1
        return r
    
    def ComputeSolution(self):
        # m = number of rows, number of constraints
        self.m = len(self.xconstraints) + len(self.yconstraints)
        # n = number of params, 2+2+2 = 6
        self.n = 6
        x0 = [1, 0, 0, 0, 0, 0]
        res = least_squares(self.FunctionG, x0)
        
        x = res.x
        r = res.fun
        print(f'r={r}')

        print('NL Least Squares Solution:')
        print(f'x=\n{x}')

        # Compute transformation matrix
        # From image coordinates to new image coordinates
        T = zeros((3,3))
        T[0,0] = x[0]
        T[0,1] = x[1]
        T[0,2] = x[2]
        T[1,0] = -x[1]
        T[1,1] = x[0]
        T[1,2] = x[3]
        T[2,0] = x[4]
        T[2,1] = x[5]
        T[2,2] = 1.
        print(f'T=\n{T}')
        return T