package org.gaul.s3proxy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import redis.clients.jedis.HostAndPort;
import redis.clients.jedis.JedisCluster;
import redis.clients.jedis.UnifiedJedis;

import java.util.HashSet;
import java.util.Set;

public class RedisClusterConnector extends UnifiedJedis {
    private static final Logger logger = LoggerFactory.getLogger(RedisClusterConnector.class);
    private final JedisCluster jedisCluster;

    public RedisClusterConnector(String hosts, String password) {
        String[] hostSplits = hosts.split(",");
        Set<HostAndPort> jedisClusterNodes = new HashSet<HostAndPort>();
        for (String host : hostSplits) {
            HostAndPort hostAndPort;
            if (host.contains(":")) {
                String[] hostParsed = host.split(":");
                hostAndPort = new HostAndPort(hostParsed[0], Integer.parseInt(hostParsed[1]));
            } else {
                hostAndPort = new HostAndPort(host, 6379);
            }
            jedisClusterNodes.add(hostAndPort);
            logger.info("Added redis cluster node " + hostAndPort + " to pool");
        }
        this.jedisCluster = new JedisCluster(jedisClusterNodes, null, password);
        logger.info("Created Jedis cluster client");
    }

    @Override
    public String get(String key) {
        return jedisCluster.get(key);
    }

    @Override
    public String hget(String key, String field) {
        return jedisCluster.hget(key, field);
    }

    @Override
    public long hset(String key, String field, String value) {
        return jedisCluster.hset(key, field, value);
    }
}
