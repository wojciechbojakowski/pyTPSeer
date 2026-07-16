# models/sampling_mode.py
# python is stupid for not having normal enums like C
from enum import Enum

class SamplingMode(Enum):
    LINEAR = (0, "Liniowe (Linear)")
    QUADRATIC = (1, "Kwadratowe (Quadratic)")
    POWER = (2, "Potęgowe (Power)")

    def __init__(self, code: int, label: str):
        self.code = code     
        self.label = label    

    def __str__(self):
        """Automatic GUI text return"""
        return self.label

    @classmethod
    def from_label(cls, label: str):
        for mode in cls:
            if mode.label == label:
                return mode
        return cls.QUADRATIC #DEFAULT