CURRENT_DIR=$(dirname "$0")
export IPFS_PATH=$CURRENT_DIR/data
nohup bin/ipfs daemon > ../logs/ipfs 2>&1 &
