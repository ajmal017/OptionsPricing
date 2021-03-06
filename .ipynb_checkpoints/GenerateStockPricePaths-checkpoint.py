#!/usr/bin/env python
# coding: utf-8

# In[2]:


import numpy as np
import pandas as pd


# In[ ]:


"""Class that provides methods to generate stock price paths according to different processes.
Euler method is implemented to simulate continuous processes thanks to discretinised versions."""

class GenerateStockPricePaths():
    
    """S0: initial price of asset
       vol: volatility
       rf: risk free rate
       N: number of paths
       steps: number of steps
       T: horizon given in years"""
    
    def __init__(self,S0,vol,rf,N = 10000,steps = 252,T = 1):
        self.S0 = S0
        self.vol = vol
        self.rf = rf
        self.N = N
        self.steps = steps
        self.T = T
    
    @property
    
    def S0(self):
        return self.__S0
    
    @property
    
    def vol(self):
        return self.__vol
    
    @property
    
    def rf(self):
        return self.__rf
    
    @property
    
    def N(self):
        return self.__N
    
    @property
    
    def steps(self):
        return self.__steps
    
    @property
    
    def T(self):
        return self.__T
    
    @S0.setter
    
    def S0(self, S0):
        self.__S0 = S0
        
    @vol.setter
    
    def vol(self, vol):
        self.__vol = vol
        
    @rf.setter
    
    def rf(self, rf):
        self.__rf = rf
        
    @N.setter
    
    def N(self, N):
        self.__N = N
    
    @steps.setter
    
    def steps(self, steps):
        self.__steps = steps
        
    @T.setter
    
    def T(self, T):
        self.__T = T
        
    """Generate paths using Black-Scholes without jumps.
       Monte-Carlo simulation combined with Antithetic sampling
       to reduce error convergence.
       Returns: stock price paths (DF)."""
    
    def BSPaths(self):
        dt = self.T/self.steps
        logS0 = np.log(self.S0)
        epsMatrix1 = np.random.normal(size=(int(self.N/2),self.steps))
        epsMatrix2 = -epsMatrix1
        dlogSMatrix1 = (self.rf-self.vol**2/2)*dt+self.vol*np.sqrt(dt)*epsMatrix1
        dlogSMatrix2 = (self.rf-self.vol**2/2)*dt+self.vol*np.sqrt(dt)*epsMatrix2
        pathsMatrix = np.zeros(shape=(self.N,self.steps))
        pathsMatrix[:,0] = logS0
        for i in range(1, self.steps):
            pathsMatrix[:int(self.N/2),i] = pathsMatrix[:int(self.N/2),i-1]+dlogSMatrix1[:,i]
            pathsMatrix[int(self.N/2):,i] = pathsMatrix[int(self.N/2):,i-1]+dlogSMatrix2[:,i]
        pathsMatrix = np.exp(pathsMatrix)
        return pd.DataFrame(pathsMatrix)
    
    
    """Plot paths generated by the method above."""
    
    def plotBSPaths(self):
        for i in range(self.N):    
            self.BSPaths().iloc[i,:].plot(figsize = (15,7), legend = None, grid = True,
                                  title = "Stock price paths generated by Black-Scholes SDE.")
    
    
    """Generate paths using Heston model without jumps.
       Returns: volatility paths (DF) and stock price paths (DF)."""
    
    def HestonPaths(self, kappa, eta, theta, rho, vol0):
        
        """Method that requires parameters for volatility process.
           kappa = speed of mean reversion
           eta = level mean reversion
           theta = vol-of vol
           rho = correlation vol-asset
           vol0 = initial vol of asset"""
        
        dt = self.T/self.steps

        def twoBrownianMotionCorrelated(correlation,simulations,nsteps):
            """Function that generate dim normal random variables
               that have a rho correlation.
               Tool used: Cholesky decomposition."""
            covariance = np.array(([1,correlation],[correlation,1]))
            cholesky = np.linalg.cholesky(covariance)
            epsMatrix1 = np.zeros(shape = (simulations, nsteps))
            epsMatrix2 = np.zeros(shape = (simulations, nsteps))
            for i in range(nsteps):
                normal = np.random.normal(size=(2,simulations))
                helper = np.dot(cholesky,normal)
                epsMatrix1[:,i] = helper[0,:]
                epsMatrix2[:,i] = helper[1,:]
            return (epsMatrix1, epsMatrix2)

        volPaths = np.zeros(shape=(self.N,self.steps))
        volPaths[:,0] = vol0
        logS = np.zeros(shape=(self.N,self.steps))
        logS[:,0] = np.log(self.S0)
        eps1 = twoBrownianMotionCorrelated(rho,self.N,self.steps)[0]
        eps2 = twoBrownianMotionCorrelated(rho,self.N,self.steps)[1]
        for i in range(1,self.steps):
            volPaths[:,i-1] = np.abs(volPaths[:,i-1])
            volPaths[:,i] = (volPaths[:,i-1])+kappa*(eta-volPaths[:,i-1])*dt+theta*np.sqrt(np.abs(volPaths[:,i-1]))*eps1[:,i]
        dlogSMatrix = (self.rf-volPaths/2)*dt+volPaths*np.sqrt(dt)*eps2
        for i in range(1,self.steps):
            logS[:,i] = logS[:,i-1]+dlogSMatrix[:,i]
        pathsMatrix = np.exp(logS)
        return (pd.DataFrame(volPaths),pd.DataFrame(pathsMatrix))
    
    
    
    """Plot stock price paths generated in the method above."""
    
    def plotHestonPaths(self, kappa, eta, theta, rho, vol0):
        for i in range(self.N):    
            self.HestonPaths(kappa, eta, theta, rho, vol0)[1].iloc[i,:].plot(figsize = (15,7), legend = None, grid = True,
                                  title = "Stock price paths generated by Heston SDE.")
            
       
    
    """Plot volatility paths and paths generated by the method above.""" 
    
    def plotHestonVolatilityPaths(self, kappa, eta, theta, rho, vol0): 
        for i in range(self.N):    
            self.HestonPaths(kappa, eta, theta, rho, vol0)[0].iloc[i,:].plot(figsize = (15,7), legend = None, grid = True,
                                  title = "Volatility paths paths generated by Heston SDE.")
    
    
    
    """Generate stock price paths according to Merton Jump diffusion model."""
    
    def MertonJDPaths(self, mu, delta, l):
        dt = self.T/self.steps
        logS0 = np.log(self.S0)
        epsMatrix1 = np.random.normal(size=(self.N,self.steps))
        epsMatrix2 = np.random.normal(size=(self.N,self.steps))
        jumpPart = np.exp(mu+delta*epsMatrix2-1)*np.random.poisson(l*dt,size=(self.N,self.steps))
        dlogSMatrix = (self.rf-self.vol**2/2)*dt+self.vol*np.sqrt(dt)*epsMatrix1
        pathsMatrix = np.zeros(shape=(self.N,self.steps))
        pathsMatrix[:,0] = logS0
        for i in range(1, self.steps):
            pathsMatrix[:,i] = pathsMatrix[:,i-1]+dlogSMatrix[:,i]+jumpPart[:,i]
        pathsMatrix = np.exp(pathsMatrix)
        return pd.DataFrame(pathsMatrix)
    
    
    """Plot paths generated by the method above."""
    
    def plotMertonJDPaths(self, mu, delta, l):
        for i in range(self.N):    
            self.MertonJDPaths(mu, delta, l).iloc[i,:].plot(figsize = (15,7), legend = None, grid = True,
                                  title = "Stock price paths generated by Merton Jump diffusion SDE.")
    
    
    """Method that generates stock price paths according to Bates model.
       Bates model is an extension of Heston model that incorporates a jump as in Merton Jump diffusion model.
       """
    
    def BatesPaths(self, kappa, eta, theta, rho, vol0, mu, delta, l):
        dt = self.T/self.steps
        def twoBrownianMotionCorrelated(correlation,simulations,nsteps):
            """Function that generate dim normal random variables
               that have a rho correlation.
               Tool used: Cholesky decomposition."""
            covariance = np.array(([1,correlation],[correlation,1]))
            cholesky = np.linalg.cholesky(covariance)
            epsMatrix1 = np.zeros(shape = (simulations, nsteps))
            epsMatrix2 = np.zeros(shape = (simulations, nsteps))
            for i in range(nsteps):
                normal = np.random.normal(size=(2,simulations))
                helper = np.dot(cholesky,normal)
                epsMatrix1[:,i] = helper[0,:]
                epsMatrix2[:,i] = helper[1,:]
            return (epsMatrix1, epsMatrix2)

        volPaths = np.zeros(shape=(self.N,self.steps))
        volPaths[:,0] = vol0
        logS = np.zeros(shape=(self.N,self.steps))
        logS[:,0] = np.log(self.S0)
        eps1 = twoBrownianMotionCorrelated(rho,self.N,self.steps)[0]
        eps2 = twoBrownianMotionCorrelated(rho,self.N,self.steps)[1]
        eps3 = np.random.normal(size=(self.N,self.steps))
        jumpPart = np.exp(mu+delta*eps3-1)*np.random.poisson(l*dt,size=(self.N,self.steps))
        for i in range(1,self.steps):
            volPaths[:,i-1] = np.abs(volPaths[:,i-1])
            volPaths[:,i] = (volPaths[:,i-1])+kappa*(eta-volPaths[:,i-1])*dt+theta*np.sqrt(np.abs(volPaths[:,i-1]))*eps1[:,i]
        dlogSMatrix = (self.rf-volPaths/2)*dt+volPaths*np.sqrt(dt)*eps2
        for i in range(1,self.steps):
            logS[:,i] = logS[:,i-1]+dlogSMatrix[:,i]+jumpPart[:,i]
        pathsMatrix = np.exp(logS)
        return (pd.DataFrame(volPaths),pd.DataFrame(pathsMatrix))
    
    
    """Plot paths generated by the method above."""
    
    def plotBatesPaths(self, kappa, eta, theta, rho, vol0, mu, delta, l):
        for i in range(self.N):    
            self.BatesPaths(kappa, eta, theta, rho, vol0, mu, delta, l)[1].iloc[i,:].plot(figsize = (15,7), legend = None, grid = True,
                                  title = "Stock price paths generated by Bates SDE.")

