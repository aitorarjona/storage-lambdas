package org.gaul.s3proxy.actionrepo.stubs;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class Module {

    private String module;
    private String image;
    private String host;
    private int port;
    private List<Action> actions;
    private List<Trigger> triggers;
    private List<Pipeline> pipelines;

    public Module(String module, String image, String host, int port, List<Action> actions, List<Trigger> triggers,
                  List<Pipeline> pipelines) {
        this.module = module;
        this.image = image;
        this.host = host;
        this.port = port;
        this.actions = actions;
        this.triggers = triggers;
        this.pipelines = pipelines;
    }

    public Module() {
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

    public List<Action> getActions() {
        return actions;
    }

    public void setActions(List<Action> actions) {
        this.actions = actions;
    }

    public List<Trigger> getTriggers() {
        return triggers;
    }

    public void setTriggers(List<Trigger> triggers) {
        this.triggers = triggers;
    }

    public List<Pipeline> getPipelines() {
        return pipelines;
    }

    public void setPipelines(List<Pipeline> pipelines) {
        this.pipelines = pipelines;
    }

    @Override
    public String toString() {
        return "Module{" +
                "module='" + module + '\'' +
                ", image='" + image + '\'' +
                ", host='" + host + '\'' +
                ", port=" + port +
                ", actions=" + actions +
                ", triggers=" + triggers +
                ", pipelines=" + pipelines +
                '}';
    }
}
