<p align="center">
  <h1 align="center"><img src="assets/CroCo1.png" height="250"><br>CroCoDL: Cross-device Collaborative Dataset for Localization</h1>
  <p align="center">
    <a href="https://hermannblum.net/">Hermann&nbsp;Blum</a><sup>1,3</sup>
    ·
    <a href="https://github.com/alemercurio">Alessandro&nbsp;Mercurio</a><sup>1</sup>
    ·
    <a href="https://joshuaoreilly.com/">Joshua&nbsp;O’Reilly</a><sup>1</sup>
    ·
    <a href="https://scholar.google.com/citations?user=Ig5T__8AAAAJ&hl=de">Tim&nbsp;Engelbracht</a><sup>1</sup>
    ·
    <a href="https://dsmn.ml/">Mihai&nbsp;Dusmanu</a><sup>2</sup>
    ·
    <a href="https://www.microsoft.com/en-us/research/people/mapoll/">Marc&nbsp;Pollefeys</a><sup>1,2</sup>
    ·
    <a href="https://zuriabauer.com/">Zuria&nbsp;Bauer</a><sup>1</sup>
  </p>
  <p align="center">
    <sup>1</sup>ETH Zürich &nbsp;&nbsp;
    <sup>2</sup>Microsoft &nbsp;&nbsp;
    <sup>3</sup>Lamar Institute / Uni Bonn
  </p>
  <h2 align="center">CVPR 2025</h2>
  <h3 align="center">
    <a href="https://localizoo.com/crocodl/">WEBSITE</a> | 
    <a href="https://openaccess.thecvf.com/content/CVPR2025/html/Blum_CroCoDL_Cross-device_Collaborative_Dataset_for_Localization_CVPR_2025_paper.html"> PAPER</a>
  </h3>
  <div align="center"></div>
</p>
<p align="center">
    <a href="https://localizoo.com/crocodl/"><img src="assets/CrocoTeaser.png" alt="Logo" width="80%"></a>
    <br>
    <em>CroCoDL: the first dataset to contain sensor recordings from real-world robots, phones, and mixed-reality headsets, covering a total of 10 challenging locations to benchmark cross-device and human-robot visual registra- tion.</em>
</p>

##

This repository hosts the source code for CroCoDL, the first dataset to contain sensor recordings from real-world robots, phones, and mixed-reality headsets, covering a total of 10 challenging locations to benchmark cross-device and human-robot visual registra-tion. The contributions of this work are:
1. The (to the best of our knowledge) largest real-world cross-device visual localization dataset, focusing on diverse capture setups and environments.
2. A novel benchmark on cross-device visual registration that shows considerable limitations of current state-of-the-art methods.
3. Integration of the sensor streams of Boston Dynamic’s Spot robot into LaMAR’s pseudo-GTpipeline. We will release the code for the data pre-processing and the required changes to the pipeline.

## 0 Overview

TODO:

## 1 Getting started

Setting up of our pipeline is similar to setting up <a href="https://localizoo.com/crocodl/">Lamar</a> with added dependencies. You can choose to set it up either locally, or using docker. Local installation has been tested with:

1. Ubuntu 20.04 and Cuda 12.1
2. Ubuntu 22.03 and Cuda XX.X (lamar machine)

### 1.1 Installation GPU

#### 1.1.1 Clone the repository:
```
git clone git@github.com:cvg/crocodl-benchmark.git
cd crocodl-benchmark
```
#### 1.1.2 Install virtual environment:
```
conda create -n croco python=3.10 pip
conda activate croco
```
We have used conda, however, you could also choose venv.

#### 1.1.3 Install external dependencies:
Depending on whether you would like to use exclusively benchmarking pipeline or processing pipeline, you can run:
```
chmod +x ./scripts/*
./scripts/install_all_dependencies.sh
```
for processing pipeline, or:
```
chmod +x ./scripts/*
./scripts/install_benchmarking_dependencies.sh
```
for benchmarking dependencies only. Full package of dependencies, installed by install_all_dependencies.sh, is (in order):

  1. [Ceres Solver 2.1](https://ceres-solver.googlesource.com/ceres-solver/+/refs/tags/2.1.0)
  2. [Colmap 3.8](https://colmap.github.io/install.html)
  3. [hloc 1.4](https://github.com/cvg/Hierarchical-Localization)
  4. [raybender](https://github.com/cvg/raybender)
  5. [pcdmeshing](https://github.com/cvg/pcdmeshing)

You can install these manually too using provided scripts inside ./scripts/install_{name_of_the_package}.


#### 1.1.4 Additional python dependencies:
Last two are only required by processing pipeline, and are not installed by install_benchmarking_dependencies. Now, additional python dependencies need to be installed. You can do this by running: 
```
python -m pip install -e .
```
for benchmarking pipeline only. If you wish to use processing too, also run:
```
python -m pip install -e .[scantools]
```

<<<<<<< HEAD
#### 1.1.5 Contribution dependencies:
Lastly, if you wish to contribute run:

```
python -m pip install -e .[dev]
```

### 1.2 Installation Docker

The Dockerfile provided in this project has multiple stages, two of which are:
`scantools` and `lamar`. For processing and benchamrking, respectively. You can build these images using:

#### 1.2.1 Build the 'scantools' stage:
```
docker build --target scantools -t croco:scantools -f Dockerfile ./
```
#### 1.2.2 Build the 'lamar' stage:
```
docker build --target lamar -t croco:lamar -f Dockerfile ./
```

## 3 Functionalities

TODO:

### Processing pipeline

### Running GPU

### Running Docker

## 4 Data

TODO:

### 5.1 Raw Data

### 5.2 Capture Data

### 5.3 Dataset Overview

## 5 CroCoDL team

<p align="center">
    <img src="assets/cvg_logo_horizontal-1.svg" alt="cvg" height="50"> &nbsp;&nbsp;&nbsp;&nbsp;
    <img src="assets/logo_text.svg" alt="robot" height="50"> 
</p>
<p align="center">
    <img src="assets/eth_logo_kurz_pos.svg" alt="eth" height="50"> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <img src="assets/UNI_Bonn_Logo_Kompakt.jpg" alt="bonn" height="50"> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <img src="assets/Microsoft_logo_(2012).svg.png" alt="mc" height="50"> 
</p>
## BibTex citation

Please consider citing our work if you use any code from this repo or ideas presented in the paper:

```
@InProceedings{Blum_2025_CVPR,
    author    = {Blum, Hermann and Mercurio, Alessandro and O'Reilly, Joshua and Engelbracht, Tim and Dusmanu, Mihai and Pollefeys, Marc and Bauer, Zuria},
    title     = {CroCoDL: Cross-device Collaborative Dataset for Localization},
    booktitle = {Proceedings of the Computer Vision and Pattern Recognition Conference (CVPR)},
    month     = {June},
    year      = {2025},
    pages     = {27424-27434}
}
```