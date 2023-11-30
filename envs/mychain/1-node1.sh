nohup bin/geth \
    --port "40303" \
    --datadir ./data1  \
    --networkid 7777 \
    --http --http.api eth,web3,net,debug,admin --http.addr "0.0.0.0" \
    --http.port 18545 --http.corsdomain "*"  --http.vhosts "*" \
    --authrpc.port 18551 \
    --miner.etherbase "0x9A82f98d6083c30632A22a9e93a9dfA8B054C929" \
    --mine --allow-insecure-unlock  \
    --unlock "0x9A82f98d6083c30632A22a9e93a9dfA8B054C929" \
    --password "./config/password.txt" \
    > ../logs/bc_node1 2>&1 &