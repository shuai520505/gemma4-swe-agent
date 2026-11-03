"""Prespecified paired reporting; no experiment outcomes are fabricated."""
from math import comb

def cdf(k,n,p):
    return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(k+1))

def cp(k,n,alpha=.05):
    if n==0:return [None,None]
    if not 0<=k<=n:raise ValueError('Invalid binomial count')
    def bisect(fn,target,increasing):
        lo,hi=0.,1.
        for _ in range(90):
            m=(lo+hi)/2
            if (fn(m)<target)==increasing:lo=m
            else:hi=m
        return (lo+hi)/2
    lower=0. if k==0 else bisect(lambda p:1-cdf(k-1,n,p),alpha/2,True)
    upper=1. if k==n else bisect(lambda p:cdf(k,n,p),alpha/2,False)
    return [lower,upper]

def paired(n00,n01,n10,n11):
    # 01 = S0 failure/EGRD success; 10 = S0 success/EGRD failure.
    if any(not isinstance(k,int) or k<0 for k in [n00,n01,n10,n11]):raise ValueError('Nonnegative integer cells required')
    n=n00+n01+n10+n11;discord=n01+n10
    if not n:return {'n':0,'absolute_difference':None,'relative_difference':None,'mcnemar_exact_p':None}
    b=cp(n01,n,.025);c=cp(n10,n,.025)
    return {'n':n,'paired_cells':{'00':n00,'01':n01,'10':n10,'11':n11},'S0_successes':n10+n11,'EGRD_successes':n01+n11,'absolute_difference':(n01-n10)/n,'relative_difference':(n01-n10)/(n10+n11) if n10+n11 else None,'S0_CP95':cp(n10+n11,n),'EGRD_CP95':cp(n01+n11,n),'difference_exact_conservative95':[b[0]-c[1],b[1]-c[0]],'discordant_pairs':discord,'discordance_EGRD_win_CP95':cp(n01,discord),'mcnemar_exact_p':min(1.,2*cdf(min(n01,n10),discord,.5)) if discord else 1.,'interval_method':'Bonferroni union bound of two exact 97.5% Clopper-Pearson discordant-cell proportion intervals; conservative joint >=95%, not a Wald interval'}
