# GoalSense
 
> Real-time threat level overlay for soccer broadcasts, powered by a fine-tuned R3D-18 video neural network.

## Table of Contents
* [Jump to Overview](#overview)
* [Jump to Technical Details](#technical-details)
* [Jump to Requirements](#requirements)
* [Jump to Installation](#installation)
* [Jump to Usage](#usage)
* [Jump to Known Limitations](#known-limitations)
* [Jump to Current Status and Roadmap](#current-status-and-roadmap)
* [Jump to Acknowledgements](#acknowledgements)
 
## Overview
 
GoalSense is an end-to-end computer vision project spanning dataset pipeline construction, video model fine-tuning, and a real-time desktop application.
The app sits as an overlay on your screen while you watch a soccer match and continuously outputs a threat level corresponding to
how threatening the current moment of play is. A high score means the model has identified patterns associated with imminent goals: attacking positioning, ball movement toward goal, defensive disorganisation. A low score means routine play
 
The model is trained to answer: *given a clip of the last 3 seconds of broadcast footage, does a goal occur within 8 seconds from the start of the clip?* The resulting score is used as a danger indicator rather than a literal probability.


## Technical Details
 
### Data Pipeline

- **Clip extraction:** Custom pipeline extracting 3-second clips (sampled to 16 frames) from footage from 50 soccer matches, labelled by whether a goal occurs within 8 seconds of the clip start
- **Dataset:** ~7,000 clips across 50 matches, split by game to prevent data leakage, with a 1:4 goal-to-no-goal ratio
- **Augmentation:** Random horizontal flip and colour jitter applied during training to improve generalisation across different stadiums and lighting conditions
### Model
 
- **Architecture:** [R3D-18](https://pytorch.org/vision/stable/models/video_resnet.html) — a 3D CNN pretrained on the Kinetics video dataset, designed for temporal video understanding
- **Fine-tuning strategy:** All layers frozen except the final residual block (`layer4`) and the classification head, which were fine-tuned with different learning rates (1e-5 and 1e-4 respectively)
- **Input:** `(3, 16, 224, 224)` tensor — 16 frames sampled evenly from a 3-second window
- **Output:** Binary classification — goal / no goal
- **Loss:** Cross-entropy with class weighting to handle the natural imbalance between goal and non-goal moments
- **Training:** 40 epochs on an RTX 2080 Super
### Results
 
| Metric | Score |
|---|---|
| Accuracy | 96% |
| Precision | 22% |
| Recall | 75% |
 
### Application
 
Built with **PyQt6** for the overlay UI and **mss** for fast screen capture. The app runs a background `QThread` that continuously captures frames from a user-defined screen region, maintains a rolling 3-second frame buffer, samples 16 frames, and runs inference.
Results are emitted as Qt signals.
 
 
## Requirements
 
- Windows 10 or 11
- Python 3.10+
- NVIDIA GPU strongly recommended
- CUDA 12.6 (if using GPU)
 
## Installation
 
### 1. Clone the repository
 
```bash
git clone https://github.com/SoccerFalcon/GoalSense.git
cd GoalSense
```
 
### 2. Create and activate a virtual environment
 
```bash
python -m venv .venv
. .venv/Scripts/activate
```
 
### 3. Install PyTorch
 
**a) If you have an NVIDIA GPU (recommended):**
 
Go to [pytorch.org/get-started/locally](https://pytorch.org/get-started/locally/) and select the correct settings for your configuration to get the right install command. Inference is faster if using some version of Cuda for your compute platform.

 
**b) Otherwise: CPU only (not recommended for real-time use):**
 
```bash
pip install torch torchvision
```
 
### 4. Install remaining dependencies
 
```bash
pip install -r requirements.txt
```
> Note: If using CUDA, make sure to run the custom installation for PyTorch from step 3a first before doing step 4. If you do step 4 first, add the flag --force-reinstall to the command you get from step 3a.
 
### 5. Model weights
 
Model weights are hosted on HuggingFace and will be downloaded automatically on first run.
 
 
## Usage
 
```bash
python main.py
```
 
1. Launch the app while watching a soccer broadcast on your screen (Could be from any source, or even a highlight video on a platform like YouTube).
2. The app launches with a landing screen displaying the title of the app.
3. Hit the "Select Region" button.
4. The landing screen goes away, and your screen should become covered with a dim overlay.
5. From here, you can click and drag to define a rectangular region of your screen. Select the region of your screen that
   your soccer broadcast is showing on.
8. Press the "Confirm" button in the lower right corner.
9. The live overlay appears showing the threat level in real time.
10. Press "Change Region" at any time to redefine the capture area.
11. Close the window to exit.
---

> Note: The app captures the rectangular region of the screen that you define exactly as it is shown, even if the broadcast is moved from that location or covered up by another window, the app will capture the originally defined rectangle.
Make sure to keep the broadcast unobstructed on the screen, and redefine the region if its location on the screen moves, in order for accurate results.
 
## Known Limitations
 
- **Broadcast footage only** — Trained exclusively on professional broadcast camera angles. Performance will degrade on phone recordings, wide-angle cameras, or non-standard perspectives.
- **Multiple Monitors** — If using on a setup with multiple monitors, the broadcast must be located on the primary monitor
- **Cutaways and replays** — Model predictions are not accurate on cutaways or replays, only on actual match footage.
- **Lighting and compression** — Heavily compressed streams or unusual stadium lighting may reduce prediction quality.
- **Not a betting tool** — This is a personal research project. Predictions are probabilistic and will frequently be wrong.
 
## Current Status and Roadmap
 
GoalSense is an actively developed project. The current model works end-to-end but tends to overpredict goals. It catches most genuine danger moments but also fires on some non-threatening play. The data pipeline and application are complete; the focus now is on improving model quality.
 
Planned improvements:
 
- Expanding beyond 50 matches to improve generalisation
- Tuning hyperparameters to achieve better performace
- Calibrating the decision boundary to reduce false positives
 
## Acknowledgements

- [PyTorch](https://pytorch.org/) and [torchvision](https://pytorch.org/vision/) for the model and training framework
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the UI
- [mss](https://python-mss.readthedocs.io/) for screen capture
 
