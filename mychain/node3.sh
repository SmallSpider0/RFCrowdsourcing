./geth \
    --port "30305" \
    --datadir ./data3  \
    --networkid 7777 \
    --http --http.api eth,web3,net,debug --http.addr "0.0.0.0" \
    --http.port 8547 --http.corsdomain "*"  --http.vhosts "*" \
    --authrpc.port 8553 \
    --mine \
    --miner.etherbase "0x34A1FEa23C319258563e3809fE8F5Eb0F756b8D2" \
    --allow-insecure-unlock  \
    --unlock "0x34A1FEa23C319258563e3809fE8F5Eb0F756b8D2" \
    --password "./tmp/password.txt" \
    --bootnodes "enode://bf7b1433654cb77817fe079f63b9b295f96c2317ce0642cf3335eabeb1ff4e9ceb230900c5681f40eda02a39c8fba668b627354499b80561e83274ea44ad0759@127.0.0.1:30303"
    
    