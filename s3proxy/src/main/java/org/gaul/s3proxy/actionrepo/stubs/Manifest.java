package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class Manifest {
    private List<Module> modules;
    private List<Type> types;

    public Manifest(List<Module> modules, List<Type> types) {
        this.modules = modules;
        this.types = types;
    }

    public Manifest() {
    }

    public List<Module> getModules() {
        return modules;
    }

    public void setModules(List<Module> modules) {
        this.modules = modules;
    }

    public List<Type> getTypes() {
        return types;
    }

    public void setTypes(List<Type> types) {
        this.types = types;
    }
}
