#models/tps_parameters.py
from dataclasses import dataclass

@dataclass
class TPSParameters:
    B_field:    float = 0.2
    E_field:    float = 2600.0
    Zm1:        float = 0.0205
    Zm2:        float = 0.0985
    Ze1:        float = 0.106
    Ze2:        float = 0.189
    d1:         float = 0.0021
    d2:         float = 0.012
    Zd:         float = 0.269
    pin_d:      float = 0.157
    pin_target: float = 1.0

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                try:
                    setattr(self, key, float(value))
                except ValueError:
                    raise ValueError(f"Parameter '{key}' must be Number!")
        
        self.validate()

    def validate(self):
        if self.Zm2 <= self.Zm1:
            raise ValueError("Zm2 must be bigger than Zm1!")
            
        if self.Ze2 <= self.Ze1:
            raise ValueError("Ze2 must be bigger than Ze1!")
            
        if self.pin_d <= 0 or self.pin_target <= 0:
            raise ValueError("Size of p-hole and distance from it must be non negative!")
            
        if self.d1 <= 0 or self.d2 <= 0:
            raise ValueError("Distance between must be bigger than 0!")