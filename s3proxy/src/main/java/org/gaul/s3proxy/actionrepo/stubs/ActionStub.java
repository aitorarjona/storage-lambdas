package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class ActionStub {
    private String name;
    private List<String> types;
    private String kind;

    public ActionStub(String name, List<String> types, String kind) {
        this.name = name;
        this.types = types;
        this.kind = kind;
    }

    public ActionStub() {
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<String> getTypes() {
        return types;
    }

    public void setTypes(List<String> types) {
        this.types = types;
    }

    public String getKind() {
        return kind;
    }

    public void setKind(String kind) {
        this.kind = kind;
    }
}
