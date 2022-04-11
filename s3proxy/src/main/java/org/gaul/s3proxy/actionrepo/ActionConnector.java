package org.gaul.s3proxy.actionrepo;

import org.gaul.s3proxy.actionrepo.stubs.Module;

import java.util.List;

public class ActionConnector {
    private Module module;
    private String name;
    private List<String> parameters;

    public ActionConnector(Module module, String name, List<String> parameters) {
        this.module = module;
        this.name = name;
        this.parameters = parameters;
    }

    public Module getModule() {
        return module;
    }

    public void setModule(Module module) {
        this.module = module;
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
