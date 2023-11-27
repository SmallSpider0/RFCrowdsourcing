ENODE=$(./geth --exec "admin.nodeInfo.enode" attach "data1/geth.ipc")
ENODE_CLEANED=$(echo $ENODE | tr -d '"')

nohup ./geth \
    --port "30304" \
    --datadir ./data2  \
    --networkid 7777 \
    --http --http.api eth,web3,net,debug,admin --http.addr "0.0.0.0" \
    --http.port 8546 --http.corsdomain "*"  --http.vhosts "*" \
    --authrpc.port 8552 \
    --mine \
    --miner.etherbase "0x5475288c5F7bC49DD6D7155A090a23d67f449595" \
    --allow-insecure-unlock  \
    --unlock "0x5475288c5F7bC49DD6D7155A090a23d67f449595" \
    --password "./config/password.txt" \
    --bootnodes $ENODE_CLEANED \
    > ../logs/bc_node2 2>&1 &