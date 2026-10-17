"""Notebook-wide admission includes installation, hashing and model startup."""
import math
import time


class SessionWindow:
    def __init__(self,started,*,limit_seconds=10800,finalization_seconds=900,clock=time.monotonic):
        if (not isinstance(started,(int,float)) or isinstance(started,bool) or not math.isfinite(started)
                or type(limit_seconds) is not int or limit_seconds<=0 or type(finalization_seconds) is not int
                or not 0<=finalization_seconds<limit_seconds):
            raise ValueError('Invalid Notebook window')
        self.started,self.limit,self.finalization,self.clock=started,limit_seconds,finalization_seconds,clock

    def admission(self,slot_seconds):
        if not isinstance(slot_seconds,(int,float)) or isinstance(slot_seconds,bool) or not math.isfinite(slot_seconds) or slot_seconds<=0:
            raise ValueError('Invalid complete slot')
        elapsed=self.clock()-self.started
        if not math.isfinite(elapsed) or elapsed<0:raise ValueError('Invalid monotonic clock origin')
        remaining=max(0,self.limit-elapsed)
        return dict(elapsed_seconds=elapsed,remaining_seconds=remaining,slot_seconds=slot_seconds,
            finalization_reserved=self.finalization,allow=remaining>=slot_seconds+self.finalization,
            scope='Notebook setup origin, including install/hash/server startup')
