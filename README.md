<p align="center">
    <h1 align="center"><a href="https://localizoo.com/crocodl/"><img src="assets/croco_white.png" height="230"></a></h1>
    <br>
    <h1 align="center">CroCoDL: Cross-device Collaborative Dataset for Localization</h1>
  <p align="center">
    <a href="https://hermannblum.net/">Hermann&nbsp;Blum</a><sup>1,3</sup>
    ·
    <a href="https://github.com/alemercurio">Alessandro&nbsp;Mercurio</a><sup>1</sup>
    ·
    <a href="https://joshuaoreilly.com/">Joshua&nbsp;O’Reilly</a><sup>1</sup>
    ·
    <a href="https://ch.linkedin.com/in/timengelbracht/de">Tim&nbsp;Engelbracht</a><sup>1</sup>
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


## 0 Overview

This repository hosts the source code for CroCoDL, the first dataset to contain sensor recordings from real-world robots, phones, and mixed-reality headsets, covering a total of 10 challenging locations to benchmark cross-device and human-robot visual registra-tion. The contributions of this work are:
1. The (to the best of our knowledge) largest real-world cross-device visual localization dataset, focusing on diverse capture setups and environments.
2. A novel benchmark on cross-device visual registration that shows considerable limitations of current state-of-the-art methods.
3. Integration of the sensor streams of Boston Dynamic’s Spot robot into LaMAR’s pseudo-GTpipeline. We will release the code for the data pre-processing and the required changes to the pipeline. 

Here is a quick breakdown of the repository:

```
crocodile-benchmark/                                 
├── assets/                   # README.md images
├── lamar/                    # Benchmarking pipeline code
├── pipelines/                # End to end pipelines for processing data
├── run_scripts/              # Convenience bash scripts for running pipelines
├── scantools/                # Processing pipeline code
├── scripts/                  # Convenience external module installation bash scripts
├── RAW-DATA.md               # Information about raw data format
├── CAPTURE.md                # Information about capture format
├── DATA.md                   # Information about data release structure
├── Dockerfile                # Docker container installation folder
└── location_release.xlsx     # Sheet containing inormation about data release locations            
```

## 1 Getting started

Setting up of our pipeline is similar to setting up <a href="https://localizoo.com/crocodl/">Lamar</a> with added dependencies. You can choose to set it up either locally, or using docker. Local installation has been tested with:

1. Ubuntu 20.04 and Cuda 12.1
2. Ubuntu 22.04 and Cuda XX.X (lamar machine)

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
Depending on whether you would like to use exclusively use benchmarking pipeline or processing pipeline also, you can run:
```
chmod +x ./scripts/*
./scripts/install_all_dependencies.sh
```
for both processing and benchmarking pipelines, or:
```
chmod +x ./scripts/*
./scripts/install_benchmarking_dependencies.sh
```
for benchmarking dependencies only. Full package of dependencies, installed by install_all_dependencies.sh, is (in order):

  1. [Ceres Solver 2.1](https://ceres-solver.googlesource.com/ceres-solver/+/refs/tags/2.1.0) (processing and benchmarking)
  2. [Colmap 3.8](https://colmap.github.io/install.html) (processing and benchmarking)
  3. [hloc 1.4](https://github.com/cvg/Hierarchical-Localization) (processing and benchmarking)
  4. [raybender](https://github.com/cvg/raybender) (processing)
  5. [pcdmeshing](https://github.com/cvg/pcdmeshing) (processing)

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
In this section we will list available scripts and describe how to run our pipeline on both GPU and Docker. For simplicity, we will list only script you are directly running using bash scripts. To understand folder structure better, you may have a look at our [data](DATA.md) section.

### 3.1 Processing pipeline
Processing transforms raw data sessions into capture format, aligns capture sessions to ground truth scan, aligns sessions cross device, creates map and query split and finaly prunes query sessions. In the order of processing here is the list of run_{script_name}.py scripts that we are running to process data:

### *Raw data to Capture format*
  1) [`scantools/run_merge_bagfiles.py`](scantools/run_merge_bagfiles.py) - Combines Nuc and Orin bagfiles into a single, merged bagfile.  
    Output: `{session_id}-{scene_name}.bag` for each pair of Nuc and Orin bagfiles given by the input txt file. Scene names are needed for further processing that is custom for each location.

  2) [`scantools/run_spot_to_capture.py`](scantools/run_spot_to_capture.py) - Processes all merged bagfiles from a folder into a capture format spot sessions.  
    Output: `sessions/spot_{session_id}/` capture format folder for each session in input folder.

  3) [`scantools/run_phone_to_capture.py`](scantools/run_phone_to_capture.py) - Processes all raw iOS sessions into a capture format.  
    Output: `sessions/ios_{session_id}/` capture format folder for each phone session inside input folder.

  4) [`scantools/run_navvis_to_capture.py`](scantools/run_navvis_to_capture.py) - Processes given raw NavVis session into a capture format.  
    Output: `sessions/{navvis_session_id}/` capture format folder of the NavVis scan.

  5) [`scantools/run_combine_navvis_sessions.py`](scantools/run_combine_navvis_sessions.py) - Combines and aligns multiple NavVis sessions in capture format into a single NavVis session.  
    Output: `sessions/{navvis_session_id_1}+...+{navvis_session_id_m}/` capture format folder of the combined NavVis scan.

  6) [`scantools/run_meshing.py`](scantools/run_meshing.py) - Creates meshes from pointclouds of the NavVis scan. Also simplifies meshes for visualization.  
    Output: `sessions/{navvis_session_id_1}+...+{navvis_session_id_m}/proc/meshes/*` for the given NavVis scan in capture format.

  7) [`scantools/run_rendering.py`](scantools/run_rendering.py) - Renders meshes and calculates depth maps.  
    Output: `sessions/{navvis_session_id_1}+...+{navvis_session_id_m}/raw_data/{session_id_i}/renderer/` depth map for images of the given NavVis scan mesh.

  8) [`pipelines/pipeline_scans.py`](pipelines/pipeline_scans.py) - Combines scripts 4–7 into a single pipeline for end-to-end processing of NavVis scans into capture format.  
    Output: `sessions/{navvis_session_id_1}+...+{navvis_session_id_m}/` capture format folder of the combined NavVis scan.

### *Sessions alignment and cross-session refinement*
  1) [`scantools/run_sequence_aligner.py`](scantools/run_sequence_aligner.py) - Aligns a given session to the ground truth NavVis scan.  
    Output: `sessions/{session_id}/proc/` folder with alignment trajectories and `registration/{session_id}/` folders with image features, matches, and correspondences.

  2) [`scantools/run_joint_refinement.py`](scantools/run_joint_refinement.py) - Refines alignment trajectory of the given sessions by co-alignment.  
    Output: `registration/{session_id}/{covisible_session_id}/` with matches/correspondences, and updated aligned trajectories in `registration/{session_id}/trajectory_refined.txt`.

  3) [`pipelines/pipeline_sequences.py`](pipelines/pipeline_sequences.py) - Combines 1 and 2 into a pipeline for aligning sessions listed in `.txt` files.  
    Output: `sessions/{session_id}/` and `registration/{session_id}/` with alignment information.


### *Map/Query processing*
  1) [`scantools/run_combine_sequences.py`](scantools/run_combine_sequences.py) - Combines multiple capture sessions into a single capture session.  
    Output: `{combined_session_id}/` folder with combined sessions in capture format.

  2) [`scantools/run_map_query_split_manual.py`](scantools/run_map_query_split_manual.py) - Creates map and query splits using 1 and `.txt` inputs in `location/*.txt`. Also transforms map sessions such that they are randomized.
    Output: `{combined_session_id}/` folder with map/query split in capture format for all selected devices, transformation applied in `transformations.txt`and visualizations in `visualizations/` of all intermediate steps.

  3) [`scantools/run_query_pruning.py`](scantools/run_query_pruning.py) - Prunes query trajectories of all devices such that all parts of the locations are covered in each query trajectory and subsamples them to achieve equal desnity overall.
    Output: `{map/query_session_id}/proc/keyframes_*.txt` containing all the keyframes selected by the algorithm in each of its steps (original, after pruning annd after subsampling) and visualizations in `visualizations/` of all intermediate steps along with a configuration file `query_pruning_config.txt` used for pruning.

### *Visualization*
  1) [`scantools/run_visualize_trajectories.py`](scantools/run_visualize_trajectories.py) - Visualizes all available trajectories for selected devices.
    Output: `visualizations/trajectories/trajectory_{device}.png`.

  2) [`scantools/run_visualize_map_query.py`](scantools/run_visualize_map_query.py) - Visualizes all map and query overlap for selected devices.
    Output: `visualizations/map_query/trajectory_{device}.png`.

  3) [`scantools/run_visualize_map_query_matrix.py`](scantools/run_visualize_map_query_matrix.py) - Visualizes matrix of map and query devices for all selected devices.
    Output: `visualizations/map_query/matrix_{device_list}.png`.

  4) [`scantools/run_visualize_map_query_renders.py`](scantools/run_visualize_map_query_renders.py) - Visualizes comparison of renders and raw images in all map/query session that are avialable. It also saves a video of these images stiched together.
    Output: `visualizations/renders/{device}_{map/query}/*png` and `visualizations/render_videos/{device}_{map/query}.mp4`

### 3.2 Benchmarking pipeline
After fully processing the pipeline and confirming with visualizations you can now run the benchmarking pipeline. In this case you can choose whether to choose original keyframes, the ones generated after pruning or the ones generated after subsampling. These could be found in the corresponding `{map/query_session_id}/proc/keyframes_*.txt`, where the start can be: `original`, `_pruned` or `_pruned_subsampled`.

  1) [`lamar/run.py`](lamar/run.py) - Runs the benchmarking  for the given pair of map and query capture sessions.
    Output: `benchmarking/` folder containing all intermediate data for benchmarking, features matches etc.

  2) [`lamar/run_read_benchmarking_output.py`](lamar/run_read_benchmarking_output.py) - Creates confusion matrix out of .txt file generated by [`scantools/run_benchmarking.sh`](run_scripts/run_benchmarking.sh). You can read more here: [`run_scripts/run_benchmarking.sh`](run_scripts/run_benchmarking.sh).

### 3.3 Running on GPU
In case you are running our pipeline locally, you can use these given example bash scripts with arguments:

  1) [`run_scripts/run_merge_spot.sh`](run_scripts/run_merge_spot.sh) - Runs [`scantools/run_merge_bagfiles.py`](scantools/run_merge_bagfiles.py) locally.  

  2) [`run_scripts/run_spot_to_capture.sh`](run_scripts/run_spot_to_capture.sh) - Runs [`scantools/run_spot_to_capture.py`](scantools/run_spot_to_capture.py) 
  locally.  

  3) [`run_scripts/run_phone_to_capture.sh`](run_scripts/run_phone_to_capture.sh) - Runs [`scantools/run_phone_to_capture.py`](scantools/run_phone_to_capture.py) locally.  

  4) [`run_scripts/run_process_navvis.sh`](run_scripts/run_process_navvis.sh) - Runs [`pipelines/pipeline_scans.py`](pipelines/pipeline_scans.py) locally.  

  5) [`run_scripts/run_align_sessions.sh`](run_scripts/run_align_sessions.sh) - Runs [`pipelines/pipeline_sequences.py`](pipelines/pipeline_sequences.py) locally.  

  6) [`run_scripts/run_map_query_split.sh`](run_scripts/run_map_query_split.sh) - Runs [`scantools/run_map_query_split_manual.py`](scantools/run_map_query_split_manual.py) locally.  

  7) [`run_scripts/run_query_pruning.sh`](run_scripts/run_query_pruning.sh) - Runs [`scantools/run_query_pruning.py`](scantools/run_query_pruning.py) locally.

  8) [`run_scripts/run_vis_trajectories.sh`](run_scripts/run_vis_trajectories.sh) - Runs [`scantools/run_visualize_trajectories.py`](scantools/run_visualize_trajectories.py) locally.

  9) [`run_scripts/run_vis_map_query.sh`](run_scripts/run_vis_map_query.sh) - Runs [`scantools/run_visualize_map_query.py`](scantools/run_visualize_map_query.py) locally.

  10) [`run_scripts/run_vis_map_query_matrix.sh`](run_scripts/run_vis_map_query_matrix.sh) - Runs [`scantools/run_visualize_map_query_matrix.py`](scantools/run_visualize_map_query_matrix.py) for all device combinations locally.

  11) [`run_scripts/run_vis_map_query_renders.sh`](run_scripts/run_vis_map_query_renders.sh) - Runs [`scantools/run_visualize_map_query_renders.py`](scantools/run_visualize_map_query_renders.py) for all available map/query sessions locally.

  12) [`run_scripts/run_benchmarking.sh`](run_scripts/run_benchmarking.sh) - Runs [`lamar/run.py`](lamar/run.py) locally.

  13) [`run_scripts/run_read_benchmarking_output.py`](lamar/run_read_benchmarking_output.py) - In case you saved output to a .txt file, as suggested by [`run_scripts/run_benchmarking.sh`](run_scripts/run_benchmarking.sh), this script runs [`lamar/run_read_benchmarking_output.py`](lamar/run_read_benchmarking_output.py) locally and creates confusion matrix for all generated output.


### 3.4 Running in Docker
In case you are running our pipeline on Docker, you can use these given example bash scripts with arguments:

  1) [`run_scripts/docker_run_merge_spot.sh`](run_scripts/docker_run_merge_spot.sh) - Runs [`scantools/run_merge_bagfiles.py`](scantools/run_merge_bagfiles.py) in a Docker container.  

  2) [`run_scripts/docker_run_spot_to_capture.sh`](run_scripts/docker_run_spot_to_capture.sh) - Runs [`scantools/run_spot_to_capture.py`](scantools/run_spot_to_capture.py) in a Docker container.  

  3) [`run_scripts/docker_run_phone_to_capture.sh`](run_scripts/docker_run_phone_to_capture.sh) - Runs [`scantools/run_phone_to_capture.py`](scantools/run_phone_to_capture.py) in a Docker container. 

  4) [`run_scripts/docker_run_process_navvis.sh`](run_scripts/docker_run_process_navvis.sh) - Runs [`pipelines/pipeline_scans.py`](pipelines/pipeline_scans.py) in a Docker container.  

  5) [`run_scripts/docker_run_align_sessions.sh`](run_scripts/docker_run_align_sessions.sh) - Runs [`pipelines/pipeline_sequences.py`](pipelines/pipeline_sequences.py) in a Docker container.  

  6) [`run_scripts/docker_run_map_query_split.sh`](run_scripts/docker_run_map_query_split.sh) - Runs [`scantools/run_map_query_split_manual.py`](scantools/run_map_query_split_manual.py) in a Docker container. 

  7) [`run_scripts/docker_run_query_pruning.sh`](run_scripts/docker_run_query_pruning.sh) - Runs [`scantools/run_query_pruning.py`](scantools/run_query_pruning.py) in a Docker container.

  8) [`run_scripts/docker_run_vis_trajectories.sh`](run_scripts/docker_run_vis_trajectories.sh) - Runs [`scantools/run_visualize_trajectories.py`](scantools/run_visualize_trajectories.py) in a Docker container.

  9) [`run_scripts/docker_run_vis_map_query.sh`](run_scripts/docker_run_vis_map_query.sh) - Runs [`scantools/run_visualize_map_query.py`](scantools/run_visualize_map_query.py) in a Docker container.

  10) [`run_scripts/docker_run_vis_map_query_matrix.sh`](run_scripts/docker_run_vis_map_query_matrix.sh) - Runs [`scantools/run_visualize_map_query_matrix.py`](scantools/run_visualize_map_query_matrix.py) for all device combinations loin a Docker containercally.

  11) [`run_scripts/docker_run_vis_map_query_renders.sh`](run_scripts/run_vis_map_query_renders.sh) - Runs [`scantools/run_visualize_map_query_renders.py`](scantools/run_visualize_map_query_renders.py) for all available map/query sessions in a Docker container.

  12) [`run_scripts/docker_run_benchmarking.sh`](run_scripts/run_benchmarking.sh) - Runs [`lamar/run.py`](lamar/run.py) in a Docker container.

  13) [`run_scripts/docker_run_read_benchmarking_output.py`](lamar/docker_run_read_benchmarking_output.py) - In case you saved output to a .txt file, as suggested by [`run_scripts/docker_run_benchmarking.sh`](run_scripts/docker_run_benchmarking.sh), this script runs [`lamar/run_read_benchmarking_output.py`](lamar/run_read_benchmarking_output.py) in a Docker container and creates confusion matrix for all generated output.

## 4 Data

If you want to read more about data we provide, and how to download it you can have a look [here](DATA.md).

## 5 CroCoDL team

<p align="center"> <img src="assets/croco_team.png" alt="team" height="200"> </p>

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
