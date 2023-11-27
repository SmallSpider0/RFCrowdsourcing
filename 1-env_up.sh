cd tmp
find "IPFS_downloads" -mindepth 1 ! -name ".gitkeep" -exec rm -f {} \;
find "IPFS_uploads" -mindepth 1 ! -name ".gitkeep" -exec rm -f {} \;
cd ../envs/mychain && ./1-node1.sh && ./1-node2.sh  && ./1-node3.sh
cd ../ipfs && ./1-start.sh