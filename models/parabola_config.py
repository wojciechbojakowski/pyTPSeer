from dataclasses import dataclass, field
import numpy as np
from typing import Optional
from models.sampling_mode import SamplingMode

@dataclass
class ParabolaConfig:
    name:  str
    A:     float
    Q:     float
    E_min: float
    E_max: float

    sampling_mode: SamplingMode

    rotation_parameter: float = 0.0 #In experiment it is not global parameter, it theory it is

    cached_line_x: Optional[np.ndarray] = field(default=None, repr=False)
    cached_line_y: Optional[np.ndarray] = field(default=None, repr=False)
    
    cached_spec_E: Optional[np.ndarray] = field(default=None, repr=False)
    cached_spec_dNdE: Optional[np.ndarray] = field(default=None, repr=False)

    cached_tof_t: np.ndarray = None
    cached_tof_signal: np.ndarray = None

    def update(self, line_x=None, line_y=None, spec_E=None, spec_dNdE=None, tof_t=None, tof_signal=None):
        if line_x is not None: 
            self.cached_line_x = line_x
        if line_y is not None: 
            self.cached_line_y = line_y
        if spec_E is not None: 
            self.cached_spec_E = spec_E
        if spec_dNdE is not None: 
            self.cached_spec_dNdE = spec_dNdE
        if tof_t is not None: 
            self.cached_tof_t = tof_t
        if tof_signal is not None: 
            self.cached_tof_signal = tof_signal


    def update_rot(self, rot):
        if rot is not None:
            self.rotation_parameter=rot

    def clear_cache(self):
        self.cached_line_x = None
        self.cached_line_y = None
        self.cached_spec_E = None
        self.cached_spec_dNdE = None
        self.cached_tof_t = None
        self.cached_tof_signal = None