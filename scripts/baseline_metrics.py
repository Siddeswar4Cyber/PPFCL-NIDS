"""Binary IDS metrics with explicit absent-class and threshold-tie behavior."""
import math
import numpy as np
from sklearn.metrics import confusion_matrix, average_precision_score, roc_auc_score


def validate(y,p):
    y=np.asarray(y); p=np.asarray(p,dtype=np.float64)
    if y.ndim!=1 or p.shape!=y.shape or len(y)==0: raise ValueError('Invalid shapes or empty input')
    if not np.isin(y,[0,1]).all() or not np.isfinite(p).all() or ((p<0)|(p>1)).any(): raise ValueError('Invalid labels/probabilities')
    return y,p


def threshold_for_fpr(y,p,target=0.01):
    y,p=validate(y,p)
    if not 0<=target<1: raise ValueError('FPR target must be in [0,1)')
    benign=np.sort(p[y==0])[::-1]
    if len(benign)==0: return None
    allowed=int(math.floor(target*len(benign)))
    return float(np.nextafter(benign[allowed],np.inf))


def evaluate(y,p,labels,universe,threshold=0.5):
    y,p=validate(y,p); labels=np.asarray(labels)
    if labels.shape!=y.shape: raise ValueError('Family labels do not align')
    if not math.isfinite(threshold): raise ValueError('Nonfinite threshold')
    predicted=p>=threshold
    tn,fp,fn,tp=map(int,confusion_matrix(y,predicted,labels=[0,1]).ravel())
    divide=lambda a,b: a/b if b else 0.0
    f1=divide(2*tp,2*tp+fp+fn); f1benign=divide(2*tn,2*tn+fp+fn)
    families={}
    for label in universe:
        mask=labels==label; n=int(mask.sum())
        families[label]={'support':n,'binary_attack_recall':float(predicted[mask].mean()) if n and label!='benign' else None}
    both=len(np.unique(y))==2
    return {'threshold':float(threshold),'rows':len(y),'attack_prevalence':float(y.mean()),'accuracy':divide(tp+tn,len(y)),
        'attack_precision':divide(tp,tp+fp),'attack_recall':divide(tp,tp+fn),'attack_f1':f1,'binary_macro_f1':(f1+f1benign)/2,
        'benign_fpr':divide(fp,fp+tn) if fp+tn else None,'average_precision':float(average_precision_score(y,p)) if both else None,
        'roc_auc':float(roc_auc_score(y,p)) if both else None,'confusion':{'tn':tn,'fp':fp,'fn':fn,'tp':tp},'attack_family_recall':families,
        'zero_division_policy':'precision/recall/F1=0 for undefined denominator; absent family recall=null; AUC=null without both classes'}
