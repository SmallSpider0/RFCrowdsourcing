find "envs/logs" -mindepth 1 ! -name ".gitkeep" -exec rm -f {} \;
cd envs/ipfs && ./0-init.sh
cd ../mychain && ./0-init.sh