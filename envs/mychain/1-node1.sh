nohup ./geth \
    --port "30303" \
    --datadir ./data1  \
    --networkid 7777 \
    --http --http.api eth,web3,net,debug,admin --http.addr "0.0.0.0" \
    --http.port 8545 --http.corsdomain "*"  --http.vhosts "*" \
    --authrpc.port 8551 \
    --miner.etherbase "0x9A82f98d6083c30632A22a9e93a9dfA8B054C929" \
    --mine --allow-insecure-unlock  \
    --unlock "0x9A82f98d6083c30632A22a9e93a9dfA8B054C929" \
    --password "./config/password.txt" \
    > ../logs/bc_node1 2>&1 &

# wait for node started
sleep 5