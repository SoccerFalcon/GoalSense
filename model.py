import os
from pathlib import Path

from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
import torch
import torchvision.models as models
import torch.nn as nn
from torchvision.transforms import v2

PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_WEIGHTS_PATH = PROJECT_ROOT / "model_weights.safetensors"

preprocess: v2.Compose = v2.Compose([
               v2.Resize((224,224)),
               v2.ConvertImageDtype(torch.float32),
               v2.Normalize(mean=[0.43216, 0.394666, 0.37645],
                            std=[0.22803, 0.22145, 0.216989]),
             ])

def load_model():
  # Download model weights from Hugging Face if they don't exist
  if not os.path.exists(MODEL_WEIGHTS_PATH):
    hf_hub_download(
      repo_id="SoccerFalcon/GoalPredictor",
      filename="model_weights.safetensors",
      local_dir=PROJECT_ROOT,
    )

  model = models.video.r3d_18(weights=None)
  model.fc = nn.Linear(in_features=512, out_features=2)

  state_dict = load_file(MODEL_WEIGHTS_PATH)
  model.load_state_dict(state_dict)

  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  model.to(device)
  model.eval()
  return model, device

# returns confidence of class 1 (goal)
def predict(model, clip, device):
  with torch.no_grad():
    clip = clip.permute(1, 0, 2, 3) # (T, C, H, W)
    clip = preprocess(clip)
    clip = clip.permute(1, 0, 2, 3) # (C, T, H, W)
    clip = clip.unsqueeze(0).to(device)  # Add batch dimension

    output = model(clip)
  return torch.softmax(output, dim=1)[0, 1].item()
