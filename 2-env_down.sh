ps -ef | grep ./geth | grep -v grep | awk '{print $2}' | xargs kill
ps -ef | grep ./ipfs | grep -v grep | awk '{print $2}' | xargs kill
echo "success"