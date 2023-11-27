rm -rf data1/geth
rm -rf data2/geth
rm -rf data3/geth
./geth init --datadir data1 ./config/genesis.json
./geth init --datadir data2 ./config/genesis.json
./geth init --datadir data3 ./config/genesis.json