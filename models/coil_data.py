from dataclasses import dataclass
from typing import Dict

@dataclass
class CoilStat:
    value: float
    label: 'QLabel' = None
    unit: str = ""

@dataclass
class AxisControl:
    type: str
    value: int
    slider: 'QSlider' = None
    combo: 'QComboBox' = None
    label: 'QLabel' = None

class CoilData:
    def __init__(self):
        self.stats = {
            f'coil_{i}': {
                'name': f'Coil {i}',
                'pwm': CoilStat(0, unit='%'),
                'current': CoilStat(0, unit='A')
            } for i in range(1, 7)
        }
        self.controls = {
            'buttons': ['Reset', 'Set'],
            'axes': {
                axis: AxisControl('Helmholtz', 0)
                for axis in ['X', 'Y', 'Z']
            }
        }