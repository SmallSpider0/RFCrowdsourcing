nohup ./geth \
    --port "30304" \
    --datadir ./data2  \
    --networkid 7777 \
    --http --http.api eth,web3,net,debug --http.addr "0.0.0.0" \
    --http.port 8546 --http.corsdomain "*"  --http.vhosts "*" \
    --authrpc.port 8552 \
    --mine \
    --miner.etherbase "0x5475288c5F7bC49DD6D7155A090a23d67f449595" \
    --allow-insecure-unlock  \
    --unlock "0x5475288c5F7bC49DD6D7155A090a23d67f449595" \
    --password "./tmp/password.txt" \
    --bootnodes "enode://bf7b1433654cb77817fe079f63b9b295f96c2317ce0642cf3335eabeb1ff4e9ceb230900c5681f40eda02a39c8fba668b627354499b80561e83274ea44ad0759@127.0.0.1:30303" \
    > ../logs/bc_node2 2>&1 &