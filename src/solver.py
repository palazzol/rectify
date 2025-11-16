from numpy import array, diag, zeros, arctan2, pi, sqrt, finfo, count_nonzero, delete, vstack
from numpy.linalg import svd, norm
from pynnex import with_emitters, emitter, listener

class PointConstraint:
    def __init__(self, image_x, image_y, world_x, world_y, weight):
        self.image_x = image_x
        self.image_y = image_y
        self.world_x = world_x
        self.world_y = world_y
        self.weight  = weight

@with_emitters
class SVDSolver:
    def __init__(self) -> None:
        self.constraints = []

    @emitter
    def emitcreateconstraint(self):
        pass

    @emitter
    def emitdestroyconstraint(self):
        pass

    def CreateConstraint(self, image_x, image_y, world_x, world_y, weight=1.0, emit=True):
        c = PointConstraint(image_x, image_y, world_x, world_y, weight)
        self.constraints.append(c)
        if emit:
            self.emitcreateconstraint.emit(c)
        return c
    
    def DestroyConstraint(self, c, emit=True):
        if emit:
            self.emitdestroyconstraint.emit(c)
        self.constraints.remove(c)

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
            
    def BuildMatrix(self):
        # Build A and b
        m = len(self.constraints)*2
        A = zeros((m,6))
        b = zeros((m,1))
        for i in range(0,len(self.constraints)):
            c = self.constraints[i]
            xp, yp = c.world_x, c.world_y
            xd, yd = c.image_x, c.image_y
            A[2*i,  :] = c.weight*array([ xd, yd, 1., 0., -xd*xp, -yd*xp])
            b[2*i,  0] = c.weight*array([xp-xd])
            A[2*i+1,:] = c.weight*array([yd, -xd, 0., 1., -xd*yp, -yd*yp])
            b[2*i+1,0] = c.weight*array([yp-yd])
        return A,b

    def ComputeSolution(self):
        A,b = self.BuildMatrix()
        x,r,t = self.compute_solution(A, b)
        print(f'r={r}')

        if t == 2:
            print('Least Squares Solution:')
        elif t == 1:
            print('Preferred Solution:')
        else:
            print('Minimum Norm Solution:')
        #print(f'x=\n{x}')

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