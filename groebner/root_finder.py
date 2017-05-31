import numpy as np
from multi_power import MultiPower
from groebner_class import Groebner
import itertools

'''
This class represents the ring A = C[x_1,...,x_n]/I as a vector space over C,
and contains the tools necessary to find the points of the variety of the
ideal generated by the given Groebner basis.
'''
class RootFinder(object):
    '''
    attributes
    ----------
    self.Groebner : Groebner object
        provides methods for calculating a Groebner basis and for
        dividing a polynomial by a set of other polynomials
    self.GB : list
        polynomials in Groebner basis
    self.vectorBasis : list
        tuples representing monomials in the vector space basis
    self.dimension : int
        dimension of the vector space

    primary methods
    ---------------
    makeVectorBasis(self, GB)
        Calculates a basis for C[x_1,...,x_n]/I as a vector space over C
        where I is the ideal generated by GB, a Groebner basis.
    coordinateVector(self, reducedPoly)
        Calculates the coordinate vector of the given polynomial's coset in
        C[x_1,...,x_n]/I. The argument must be a polynomial that has been
        reduced by the Groebner basis already.
    '''
    def __init__(self, G):
        '''
        parameters
        ----------
        G : Groebner object or list
            groebner object that represents a Groebner Basis for the ideal
            OR
            a list of polynomials that make up a Groebner basis
        '''
        if type(G) is list:
            self.Groebner = Groebner(G)
            self.GB = G
        else:
            self.Groebner = G
            self.GB = G.solve()

        self.vectorBasis = self.makeVectorBasis(self.GB)
        self.vectorSpaceDimension = len(self.vectorBasis)

    def makeVectorBasis(self, GB):
        '''
        parameters
        ----------
        GB: list
            polynomial objects that make up a Groebner basis for the ideal

        return
        ------
        basis : list
            tuples representing the monomials in the vector space basis
        '''
        LT_G = [f.lead_term for f in GB]
        possibleVarDegrees = [range(max(tup)) for tup in zip(*LT_G)]
        possibleMonomials = itertools.product(*possibleVarDegrees)
        basis = []

        for mon in possibleMonomials:
            divisible = False
            for LT in LT_G:
                if (self.divides(LT, mon)):
                     divisible = True
                     break
            if (not divisible):
                basis.append(mon)

        return basis

    def multOperatorMatrix(self, poly):
        dim = self.vectorSpaceDimension
        multOperatorMatrix = np.zeros((dim, dim))

        for i in range(dim):
            monomial = self.vectorBasis[i]
            poly_ = poly.mon_mult(monomial)
            poly_ = self.getRemainder(poly_)

            multOperatorMatrix[:,i] = self.coordinateVector(poly_)

        return multOperatorMatrix

    def coordinateVector(self, reducedPoly):
        '''
        parameters
        ----------
        reducedPoly : polynomial object
            the polynomial for which to find the coordinate vector of its coset

        return
        ------
        coordinateVector : list
            the coordinate vector of the given polynomial's coset in
            A = C[x_1,...x_n]/I as a vector space over C
        '''
        # reverse the array since self.vectorBasis is in increasing order
        # and monomialList() gives a list in decreasing order
        reducedPolyTerms = reducedPoly.monomialList()[::-1]
        assert(len(reducedPolyTerms) <= self.vectorSpaceDimension)

        coordinateVector = [0] * self.vectorSpaceDimension
        for monomial in reducedPolyTerms:
            coordinateVector[self.vectorBasis.index(monomial)] = \
                reducedPoly.coeff[monomial]

        return coordinateVector

    def divides(self, mon1, mon2):
        '''
        parameters
        ----------
        mon1 : tuple
            contains the exponents of the monomial divisor
        mon2 : tuple
            contains the exponents of the monomial dividend

        return
        ------
        boolean
            true if mon1 divides mon2, false otherwise
        '''
        return all(np.subtract(mon2, mon1) >= 0)

    def reduce_poly(self, poly):
        """
        Divides a polynomial by the Groebner basis using the standard
        multivariate division algorithm and returns the remainder
        """
        change = True
        while change:
            change = False
            for other in self.old_polys:
                if poly.lead_term == None or other.lead_term == None:
                    continue #one of them is empty
                if other != poly and all([i-j >= 0 for i,j in zip(poly.lead_term,other.lead_term)]):
                    #print(poly.coeff)
                    #print(other.coeff)
                    monomial = tuple(np.subtract(poly.lead_term,other.lead_term))
                    new = other.mon_mult(monomial)

                    lcm = np.maximum(poly.coeff.shape, new.coeff.shape)

                    poly_pad = np.subtract(lcm, poly.coeff.shape)
                    poly_pad[np.where(poly_pad<0)]=0
                    pad_poly = self.pad_back(poly_pad, poly)

                    new_pad = np.subtract(lcm, new.coeff.shape)
                    new_pad[np.where(new_pad<0)]=0
                    pad_new = self.pad_back(new_pad,new)

                    new_coeff = pad_poly.coeff-(poly.lead_coeff/other.lead_coeff)*pad_new.coeff
                    new_coeff[np.where(abs(new_coeff) < 1.e-10)]=0 #Get rid of floating point errors to make more stable
                    poly.__init__(new_coeff)
                    #print(poly.coeff)
                    change = True
                    pass
                pass
            pass
        return poly

    def getRemainder(self, poly):
        '''
        parameters
        ----------
        polynomial : polynomial object, either power or chebychev
            the polynomial to be divided by the Groebner basis

        return
        ------
        polynomial object
            the unique remainder of poly divided by self.GB
        '''
        return self.Groebner.reduce_poly(poly, self.GB)
