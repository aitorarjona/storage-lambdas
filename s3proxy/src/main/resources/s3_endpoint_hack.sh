echo $HOSTNAME
cat /opt/s3proxy/configmap/s3proxy.properties >> /opt/s3proxy/s3proxy.properties
if [[ "$HOSTNAME" == *"storage"* ]]; then
  sed -i "s|jclouds.endpoint=.*|jclouds.endpoint=http://$HOSTIP:9000|g" /opt/s3proxy/s3proxy.properties
fi
cat /opt/s3proxy/s3proxy.properties