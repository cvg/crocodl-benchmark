export EXTERNAL_DIR=./external

# cp update_src/code/rdd.py $EXTERNAL_DIR/hloc/hloc/extractors/rdd.py
cp update_src/code/aliked.py $EXTERNAL_DIR/hloc/hloc/extractors/aliked.py
cp update_src/code/extract_features.py $EXTERNAL_DIR/hloc/hloc/extract_features.py

# cp update_src/code/match_features.py $EXTERNAL_DIR/hloc/hloc/match_features.py
# cp update_src/code/lightglue_hloc.py $EXTERNAL_DIR/hloc/hloc/matchers/lightglue.py

# bash update_src/setup_rdd.sh

echo "=== Update src code successfully! ==="