cd data && find . -mindepth 1 ! -name "config" -exec rm -rf {} +
mv config config_tmp
cd .. && CURRENT_DIR=$(dirname "$0") && export IPFS_PATH=$CURRENT_DIR/data && bin/ipfs init
mv data/config_tmp data/config