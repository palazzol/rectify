from numpy import array, diag, zeros, arctan2, pi, sqrt, finfo, count_nonzero, delete, vstack
from numpy.linalg import svd, norm
from scipy.optimize import least_squares
from pynnex import with_emitters, emitter, listener

class DeltaXConstraint:
    def __init__(self, image_x1, image_y1, image_x2, image_y2, world_dx, weight):
        self.image_x1 = image_x1
        self.image_y1 = image_y1
        self.image_x2 = image_x2
        self.image_y2 = image_y2
        self.world_dx = world_dx
        self.weight  = weight

class DeltaYConstraint:
    def __init__(self, image_x1, image_y1, image_x2, image_y2, world_dy, weight):
        self.image_x1 = image_x1
        self.image_y1 = image_y1
        self.image_x2 = image_x2
        self.image_y2 = image_y2
        self.world_dy = world_dy
        self.weight  = weight

@with_emitters
class NLLSSolver:
    def __init__(self):
        self.dxconstraints = []
        self.dyconstraints = []

    @emitter
    def emitcreateconstraint(self):
        pass

    @emitter
    def emitdestroyconstraint(self):
        pass

    def CreateDXConstraint(self, image_x1, image_y1, image_x2, image_y2, world_dx, weight=1.0, emit=True):
        c = DeltaXConstraint(image_x1, image_y1, image_x2, image_y2, world_dx, weight)
        self.dxconstraints.append(c)
        if emit:
            self.emitcreateconstraint.emit(c)
        return c
    
    def CreateDYConstraint(self, image_x1, image_y1, image_x2, image_y2, world_dy, weight=1.0, emit=True):
        c = DeltaYConstraint(image_x1, image_y1, image_x2, image_y2, world_dy, weight)
        self.dyconstraints.append(c)
        if emit:
            self.emitcreateconstraint.emit(c)
        return c

    def DestroyConstraint(self, c, emit=True):
        if c in self.dxconstraints:
            if emit:
                self.emitdestroyconstraint.emit(c)
            self.dxconstraints.remove(c)
        elif c in self.dyconstraints:
            if emit:
                self.emitdestroyconstraint.emit(c)
            self.dyconstraints.remove(c)

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
        for dxc in self.dxconstraints:
            r[i] = self.FunctionFx(dxc.image_x1, dxc.image_y1, x) - self.FunctionFx(dxc.image_x2, dxc.image_y2, x) - dxc.world_dx
            i += 1
        for dyc in self.dyconstraints:
            r[i] = self.FunctionFy(dyc.image_x1, dyc.image_y1, x) - self.FunctionFy(dyc.image_x2, dyc.image_y2, x) - dyc.world_dy
            i += 1
        return r
    
    def ComputeSolution(self):
        # m = number of rows, number of constraints
        self.m = len(self.dxconstraints) + len(self.dyconstraints)
        # n = number of params, 2+2+2 = 6
        self.n = 6
        x0 = [1, 0, 0, 0, 0, 0]
        res = least_squares(self.FunctionG, x0)
        
        x = res.x
        r = res.fun
        print(f'r={r}')

        print('NL Least Squares Solution:')
        print(f'x=\n{x}')

        # Compute transformation matrix, for printing
        T = zeros((3,3))
        T[0,0] = x[0]+1.
        T[0,1] = x[1]
        T[0,2] = x[2]
        T[1,0] = -x[1]
        T[1,1] = x[0]+1.
        T[1,2] = x[3]
        T[2,0] = x[4]
        T[2,1] = x[5]
        T[2,2] = 1.
        print(f'T=\n{T}')
        return T