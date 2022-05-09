package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class ModuleStub {

    private String module;
    private String image;
    private String host;
    private int port;
    private List<ActionStub> actionStubs;

    public ModuleStub(String module, String image, String host, int port, List<ActionStub> actionStubs) {
        this.module = module;
        this.image = image;
        this.host = host;
        this.port = port;
        this.actionStubs = actionStubs;
    }

    public ModuleStub() {
    }

    public String getModule() {
        return module;
    }

    public void setModule(String module) {
        this.module = module;
    }

    public String getImage() {
        return image;
    }

    public void setImage(String image) {
        this.image = image;
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

    public List<ActionStub> getActions() {
        return actionStubs;
    }

    public void setActions(List<ActionStub> actionStubs) {
        this.actionStubs = actionStubs;
    }

}
