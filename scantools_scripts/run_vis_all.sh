#!/usr/bin/env bash

yes | ./scantools_scripts/docker_run_vis_map_query_matrix.sh
yes | ./scantools_scripts/docker_run_vis_map_query.sh
yes | ./scantools_scripts/docker_run_vis_trajectories.sh
yes | ./scantools_scripts/docker_run_vis_map_query_renders.sh