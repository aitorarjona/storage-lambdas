package org.gaul.s3proxy.actionrepo;

import org.gaul.s3proxy.actionrepo.stubs.Action;
import org.gaul.s3proxy.actionrepo.stubs.Module;

import java.util.List;

public class ActionConnector {
    private final Action action;
    private Module module;

    public ActionConnector(Module module, Action action) {
        this.module = module;
        this.action = action;
    }

    public Action getAction() {
        return action;
    }

    public Module getModule() {
        return module;
    }

    public void setModule(Module module) {
        this.module = module;
    }

    @Override
    public String toString() {
        return "ActionConnector{" +
                "action=" + action +
                ", module=" + module +
                '}';
    }
}
