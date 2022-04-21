package org.gaul.s3proxy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import redis.clients.jedis.HostAndPort;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPoolConfig;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.UnifiedJedis;

public class RedisPoolConnector extends UnifiedJedis {
    private static final Logger logger = LoggerFactory.getLogger(RedisPoolConnector.class);
    private final JedisPool jedisPool;

    public RedisPoolConnector(String hosts, String password) {
        HostAndPort hostAndPort;
        if (hosts.contains(":")) {
            String[] hostSplit = hosts.split(":");
            hostAndPort = new HostAndPort(hostSplit[0], Integer.parseInt(hostSplit[1]));
        } else {
            hostAndPort = new HostAndPort(hosts, 6379);
        }
        JedisPoolConfig poolConfig = new JedisPoolConfig();
        poolConfig.setMaxTotal(128);
        poolConfig.setMaxIdle(16);
        this.jedisPool = new JedisPool(poolConfig, hostAndPort.getHost(), hostAndPort.getPort(), 250, password);
        logger.info("Created Jedis single-node client");
    }

    @Override
    public String get(String key) {
        try (Jedis jedis = jedisPool.getResource()) {
            String val = jedis.get(key);
            jedis.close();
            return val;
        }
    }

    @Override
    public String hget(String key, String field) {
//        logger.debug("hget " + key + " " + field);
        try (Jedis jedis = jedisPool.getResource()) {
            String val = jedis.hget(key, field);
            jedis.close();
            return val;
        }
    }

    @Override
    public long hset(String key, String field, String value) {
//        logger.debug("hset " + key + " " + field);
        try (Jedis jedis = jedisPool.getResource()) {
            long val = jedis.hset(key, field, value);
            jedis.close();
            return val;
        }
    }
}
