package org.gaul.s3proxy.actionrepo.stubs;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class Module {
    private String module;
    private Gateway gateway;
    private List<String> mimeTypes;
    private LinkedHashMap<String, List<Action>> actions;
    private Boolean preprocess;

    public Module() {
    }

    public Module(String module, Gateway gateway, List<String> mimeTypes, LinkedHashMap<String, List<Action>> actions,
                  Boolean preprocess) {
        this.module = module;
        this.gateway = gateway;
        this.mimeTypes = mimeTypes;
        this.actions = actions;
        this.preprocess = preprocess;
    }

    public String getModule() {
        return module;
    }

    public void setModule(String module) {
        this.module = module;
    }

    public Gateway getGateway() {
        return gateway;
    }

    public void setGateway(Gateway gateway) {
        this.gateway = gateway;
    }

    public List<String> getMimeTypes() {
        return mimeTypes;
    }

    public void setMimeTypes(List<String> mimeTypes) {
        this.mimeTypes = mimeTypes;
    }

    public Map<String, List<Action>> getActions() {
        return actions;
    }

    public void setActions(LinkedHashMap<String, List<Action>> actions) {
        this.actions = actions;
    }

    public Boolean getPreprocess() {
        return preprocess;
    }

    public void setPreprocess(Boolean preprocess) {
        this.preprocess = preprocess;
    }
}
