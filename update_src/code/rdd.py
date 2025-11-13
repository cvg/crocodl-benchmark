import sys
from pathlib import Path

from ..utils.base_model import BaseModel

rdd_path = Path(__file__).parent / "../../third_party/rdd"
sys.path.append(str(rdd_path))
from RDD.RDD import build
from RDD.utils import read_config
import torch
config_path = rdd_path / 'configs/default.yaml'
config = read_config(config_path)
config['weights'] = str(rdd_path / 'weights/RDD-v2.pth')

class RDD(BaseModel):
    default_conf = {
        "model_name": "rdd",
        "max_keypoints": 8192,
    }
    
    required_inputs = ["image"]
    
    def _init(self, conf):
        conf.pop("name")
        self.conf = conf
        RDD_model = build(config)
        self.model = RDD_model
        self.model.eval()
        self.model.set_softdetect(top_k=self.conf["max_keypoints"], scores_th=0.01)

    def _forward(self, data):
        
        self.model = self.model.to(data["image"].device)
        self.model.device = data["image"].device
        if self.conf.get('combine', False):
            features = self.model.extract_combine(data["image"], model='aliked')
            # only keep top_k keypoints
            if features[0]['scores'].numel() > self.conf["max_keypoints"]:
                
                idxs = torch.topk(features[0]['scores'], self.conf["max_keypoints"]).indices
                features[0]['keypoints'] = features[0]['keypoints'][idxs]
                features[0]['scores'] = features[0]['scores'][idxs]
                features[0]['descriptors'] = features[0]['descriptors'][idxs]
            
        else:
            features = self.model.extract(data["image"])
        return {
            "keypoints": [f["keypoints"] for f in features],
            "keypoint_scores": [f["scores"] for f in features],
            "descriptors": [f["descriptors"].t() for f in features],
        }