package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class Action {
    private String name;
    private List<String> parameters;

    public Action(String name, List<String> parameters) {
        this.name = name;
        this.parameters = parameters;
    }

    public Action() {
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<String> getParameters() {
        return parameters;
    }

    public void setParameters(List<String> parameters) {
        this.parameters = parameters;
    }
}
