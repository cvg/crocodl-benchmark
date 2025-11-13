# QUICK START

## Step 0 - Setup
Setting up of our pipeline is similar to setting up [Lamar](https://lamar.ethz.ch/) with added dependencies. You can choose to set it up either locally, or using docker. Local installation has been tested with: Ubuntu 20.04 and Cuda 12.1.

### 0.1 OPTION 1: Installation GPU

#### 0.1.1 Clone the repository:

```bash
git clone git@github.com:cvg/crocodl-benchmark.git
cd crocodl-benchmark
```

#### 0.1.2 Install virtual environment:

```bash
conda create -n croco python=3.10 pip
conda activate croco
conda install -c conda-forge libstdcxx-ng
```

We have used conda, however, you could also choose venv.

#### 0.1.3 Install external dependencies:

For the challenge you will only need benchmarking dependencies. These can be installed as follows:

```bash
sudo apt-get update
sudo apt-get install git-lfs
```

```bash
chmod +x ./scripts/*
chmod +x ./benchmark_scripts/*
./scripts/install_benchmarking_dependencies.sh
```

This will install:

1. [Ceres Solver 2.1](https://ceres-solver.googlesource.com/ceres-solver/+/refs/tags/2.1.0) (processing and benchmarking)\
2. [Colmap 3.8](https://colmap.github.io/install.html) (processing and benchmarking)\
3. [hloc 1.4](https://github.com/PetarLukovic/Hierarchical-Localization) (processing and benchmarking)

You can install these manually too using provided scripts inside [here](https://github.com/cvg/crocodl-benchmark/tree/main/scripts).

#### 0.1.4 Additional python dependencies:
Now, additional python dependencies need to be installed. You can do this by running:

```bash
python -m pip install -e .
```

### 0.2 OPTION 2: Build the Docker 'lamar' stage
If you would like to run the benchmark code using Docker container, you simply run following command:

Setup **Docker CUDA** by following this:

```
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
```

```bash
docker build --target lamar -t croco:lamar -f Dockerfile ./
```

### 0.3 Update hloc source:

```bash
bash ./update_src.sh
```


### 0.4 Environmental variables:
Before running any code, you should set environmental variables. You can do this with:

```bash
export CAPTURE_DIR="path/to/capture"
```

Capture directory has to end with **capture/** folder. Some of the scripts require more arguments, so we strongly advise to have a look at them before running and change them if needed. All the arguments are explained inside each bash script and corresponding docustrings in python files.

## Step 1 - Download
We provide a simple script to download all challenge data at once using git. The script will create the necessary folder structure such that data is ready out of the box. For the code to run smoothly, you should use given folder structure. Firstly, to download challenge data you can run:

```bash
pip install huggingface_hub
pip install hf_transfer
```

```bash
./benchmark_scripts/run_download_data.sh --arche
```

you can alter the path of the dataset as you wish, however, final folder has to be named capture/. Challenge data comes in the same folder as regular, full release, data but with removed ground truth and consisting only of maps and queries for all devices. For the challenge we provide two locations: **HYDRO** and **SUCCULENT**. Once the data is downloaded, you can run benchmarking on it!

## Step 2 - Benchmarking
To start the benchmarking you will use the following script:

```bash
./benchmark_scripts/run_benchmarking.sh > output.txt 2>&1
```

or

```bash
# if use tmux:
newgrp docker
```

```bash 
./benchmark_scripts/docker_run_benchmarking.sh > output.txt 2>&1
```

if you wish to run in Docker container. You can remove printing out to a `.txt` file, however, output might get too long to read in the CLI. You can either use the methods already available in lamar or implement your own. Make sure to update the flags in the `run_benchmarking.sh` script accordingly when you want to run different methods.

Step 3 - Results file generation
Finally, you can run the script to zip all the results. Your estimated poses are buried deeply inside of benchmarking output folder (by default set to $CAPTURE_DIR/{location}/benchmarking_ps, but you can change it inside of benchmark_scripts/run_benchmarking.sh or benchmark_scripts/docker_run_benchmarking.sh), so we made a quick script to generate the submission .zip file. You can run it as follows:

```bash
./benchmark_scripts/run_combine_results.sh
```
or

```bash
./benchmark_scripts/docker_run_combine_results.sh
```