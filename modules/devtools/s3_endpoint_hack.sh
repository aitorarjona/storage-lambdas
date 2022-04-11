echo $HOSTNAME
if [[ "$HOSTNAME" == *"storage"* ]]; then
  export S3_ENDPOINT="http://$HOSTIP:9000"
fi
echo $S3_ENDPOINT
./devmod