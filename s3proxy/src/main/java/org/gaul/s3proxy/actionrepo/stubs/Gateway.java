package org.gaul.s3proxy.actionrepo.stubs;

public class Gateway {

    private String host;
    private int port;

    public Gateway(String host, int port) {
        this.host = host;
        this.port = port;
    }

    public Gateway() {

    }

    public String getHost() {
        return host;
    }

    public void setHost(String host) {
        this.host = host;
    }

    public int getPort() {
        return port;
    }

    public void setPort(int port) {
        this.port = port;
    }
}
