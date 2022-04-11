package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class Modules {
    private List<Module> modules;

    public Modules(List<Module> modules) {
        this.modules = modules;
    }

    public Modules() {
    }

    public List<Module> getModules() {
        return modules;
    }

    public void setModules(List<Module> modules) {
        this.modules = modules;
    }
}
