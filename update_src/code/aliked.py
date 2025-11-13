import torch
from lightglue import ALIKED

from ..utils.base_model import BaseModel


class Aliked(BaseModel):
    default_conf = {
        "model_name": "aliked-n16",
        "max_num_keypoints": 4096,
        "detection_threshold": 0.01,
        "nms_radius": 2,
    }
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def _init(self, conf):
        self.net = ALIKED(**conf)
        
    def _forward(self, data):
        results = self.net(data)
        results['descriptors'] = results['descriptors'].permute(0, 2, 1)
        return results