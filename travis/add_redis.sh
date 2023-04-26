sudo apt -y install redis

# enable auth for Redis
REDIS_SR3_PASSWORD=$(openssl rand -hex 6)
cat << EOF | sudo tee -a /etc/redis/redis.conf
user sr3 on >${REDIS_SR3_PASSWORD} ~* +@all
user default off
EOF

## Enable TLS for Redis
# This won't work for our testing, as there's no easy way to let the Python Redis client
#   accept self-signed certs. Still nice to know how to do it though.
# Generate CA key
sudo openssl genrsa -out /etc/redis/tls_ca.key 4096
sudo openssl req \
    -x509 -new -nodes -sha256 \
    -key /etc/redis/tls_ca.key \
    -days 3650 \
    -subj '/O=Redis Test/CN=Certificate Authority' \
    -out /etc/redis/tls_ca.crt
# Generate service key
sudo openssl genrsa -out /etc/redis/tls_redis.key 2048
# Generate service cert, signed by the above CA key
sudo openssl req \
    -new -sha256 \
    -key /etc/redis/tls_redis.key \
    -subj '/O=Redis Test/CN=Server' | \
    sudo openssl x509 \
        -req -sha256 \
        -CA /etc/redis/tls_ca.crt \
        -CAkey /etc/redis/tls_ca.key \
        -CAserial /etc/redis/tls_ca.txt \
        -CAcreateserial \
        -days 365 \
        -out /etc/redis/tls_redis.crt
# Generate service Diffie-Hellman parameters
sudo openssl dhparam -out /etc/redis/tls_redis.dh 2048
# set ownership of the certs/keys
sudo chown redis:redis /etc/redis/tls*
# add options to config file
cat << EOF | sudo tee -a /etc/redis/redis.conf
tls-cert-file /etc/redis/tls_redis.crt 
tls-key-file /etc/redis/tls_redis.key 
tls-ca-cert-file /etc/redis/tls_ca.crt 
tls-dh-params-file /etc/redis/tls_redis.dh 
tls-port 6380 
tls-auth-clients no
EOF


check_wsl=$(ps --no-headers -o comm 1)

# Start Redis Service
if [[ $(($check_wsl == "init" )) ]]; then
	sudo service redis-server restart
else
	sudo systemctl restart redis-server
fi

# Install Python modules
pip3 install redis python-redis-lock

# Set redis defaults for sr3
cat >> ~/.config/sr3/default.conf << EOF
retry_driver redis
redisqueue_serverurl redis://sr3:${REDIS_SR3_PASSWORD}@localhost:6379/0?ssl_cert_reqs=none&ssl_ca_certs=/etc/redis/tls_ca.crt
EOF