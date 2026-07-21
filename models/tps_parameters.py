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
        

    def import_from_txt(self, path:str):
        try:
           with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")] 
            vals = [float(val) for val in lines]
            
            if len(vals) < 12:
                raise ValueError(f"Oczekiwano co najmniej 12 linii parametrów w pliku, znaleziono {len(vals)}.")

            #alpha=vals[0],
            self.B_field=vals[1]
            self.E_field=vals[2]
            self.Zm1=vals[3]
            self.Zm2=vals[4]
            self.Ze1=vals[5]
            self.Ze2=vals[6]
            self.d1=vals[7]
            self.d2=vals[8]
            self.Zd=vals[9]
        
        except Exception as e:
            print(f"No file found at the specified path. Error: {e}")
            return None