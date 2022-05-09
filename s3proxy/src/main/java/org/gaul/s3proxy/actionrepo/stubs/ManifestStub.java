package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class ManifestStub {
    private List<ModuleStub> moduleStubs;
    private List<TypeStub> typeStubs;
    private List<TriggerStub> triggerStubs;

    public ManifestStub(List<ModuleStub> moduleStubs, List<TypeStub> typeStubs, List<TriggerStub> triggerStubs) {
        this.moduleStubs = moduleStubs;
        this.typeStubs = typeStubs;
        this.triggerStubs = triggerStubs;
    }

    public ManifestStub() {
    }

    public List<ModuleStub> getModules() {
        return moduleStubs;
    }

    public void setModules(List<ModuleStub> moduleStubs) {
        this.moduleStubs = moduleStubs;
    }

    public List<TypeStub> getTypes() {
        return typeStubs;
    }

    public void setTypes(List<TypeStub> typeStubs) {
        this.typeStubs = typeStubs;
    }

    public List<TriggerStub> getTriggers() {
        return triggerStubs;
    }

    public void setTriggers(List<TriggerStub> triggerStubs) {
        this.triggerStubs = triggerStubs;
    }
}
