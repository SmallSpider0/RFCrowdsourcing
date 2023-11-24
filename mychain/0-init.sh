rm -rf data1/geth
rm -rf data2/geth
rm -rf data3/geth
./geth init --datadir data1 ./tmp/genesis.json
./geth init --datadir data2 ./tmp/genesis.json
./geth init --datadir data3 ./tmp/genesis.json