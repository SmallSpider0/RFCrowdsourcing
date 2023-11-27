ENODE=$(./geth --exec "admin.nodeInfo.enode" attach "data1/geth.ipc")
ENODE_CLEANED=$(echo $ENODE | tr -d '"')

nohup ./geth \
    --port "30305" \
    --datadir ./data3  \
    --networkid 7777 \
    --http --http.api eth,web3,net,debug,admin --http.addr "0.0.0.0" \
    --http.port 8547 --http.corsdomain "*"  --http.vhosts "*" \
    --authrpc.port 8553 \
    --mine \
    --miner.etherbase "0x34A1FEa23C319258563e3809fE8F5Eb0F756b8D2" \
    --allow-insecure-unlock  \
    --unlock "0x34A1FEa23C319258563e3809fE8F5Eb0F756b8D2" \
    --password "./config/password.txt" \
    --bootnodes $ENODE_CLEANED \
    > ../logs/bc_node3 2>&1 &