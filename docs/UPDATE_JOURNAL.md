# Mealy Development Journal

## Version 0.3 – Dataset Setup
- Downloaded Food-101 dataset
- Organised dataset in data/raw directory
- Analysed dataset structure
- Prepared for data exploration notebook

## Version 0.2 – Environment Setup
- Checked Python compatibility: system default is Python 3.14.3, but TensorFlow 2.x
  requires Python 3.9–3.12; installed Python 3.12.13 from Fedora 43 repos
- Created virtual environment at `venv/` using Python 3.12.13
- Upgraded pip (26.0.1), setuptools (82.0.1), wheel (0.46.3)
- Installed ML and CV libraries:
  - TensorFlow 2.21.0, Keras 3.13.2
  - NumPy 2.4.4, Pandas 3.0.2, SciPy 1.17.1
  - Scikit-learn 1.8.0
  - OpenCV 4.13.0, Pillow 12.2.0
  - Matplotlib 3.10.8, Seaborn 0.13.2
  - JupyterLab 4.5.6
- Generated `requirements.txt` (133 packages, fully pinned)
- Environment ready for dataset and model development

## Version 0.1 – Project Setup
- Created project directory structure
- Added documentation files
- Added project logo
- Initialized Git repository
- Connected repository to GitHub
