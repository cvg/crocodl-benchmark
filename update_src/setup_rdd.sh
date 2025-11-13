#!/bin/bash

### Setup env
if [ ! -d "$EXTERNAL_DIR/hloc/third_party/rdd" ]; then
    git clone --recursive https://github.com/xtcpete/rdd $EXTERNAL_DIR/hloc/third_party/rdd
fi

pip uninstall lightglue -y

cp update_src/code/lightglue_rdd.py $EXTERNAL_DIR/hloc/third_party/rdd/third_party/LightGlue/lightglue/lightglue.py

cd $EXTERNAL_DIR/hloc/third_party/rdd || exit

# pip install -r requirements.txt
# cd ./RDD/models/ops
# pip install --no-build-isolation -e .
# cd $EXTERNAL_DIR/hloc/third_party/rdd || exit

### Download weights
if ! command -v gdown &> /dev/null; then
    pip install gdown
fi

mkdir -p weights

if [ ! -f "weights/RDD-v2.pth" ]; then
    gdown --fuzzy "https://drive.google.com/file/d/1UN6jO5vDQCZcPyVOhRv_Qfvs9onzlJMO/view?usp=drive_link" \
        -O weights/RDD-v2.pth
fi

if [ ! -f "weights/RDD-v1.pth" ]; then
    gdown --fuzzy "https://drive.google.com/file/d/1wNrRd_4imZeV6U-l1xjuvJktTTK5-NPX/view?usp=drive_link" \
        -O weights/RDD-v1.pth
fi

if [ ! -f "weights/RDD_lg-v2.pth" ]; then
    gdown --fuzzy "https://drive.google.com/file/d/153bHc-HXj7zT4d1hid-s9erjQ5sU5-aa/view?usp=drive_link" \
        -O weights/RDD_lg-v2.pth
fi

if [ ! -f "weights/RDD_lg-v1.pth" ]; then
    gdown --fuzzy "https://drive.google.com/file/d/1gr8pIFZZFyvsNZlTmU9OuUKu4Vj2IOdP/view?usp=drive_link" \
        -O weights/RDD_lg-v1.pth
fi
