package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class Action {
    private String name;
    private List<String> types;
    private List<String> args;

    public Action(String name, List<String> mimeTypes, List<String> args) {
        this.name = name;
        this.types = mimeTypes;
        this.args = args;
    }

    public Action() {
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

    public List<String> getArgs() {
        return args;
    }

    public void setArgs(List<String> args) {
        this.args = args;
    }

    @Override
    public String toString() {
        return "Action{" +
                "name='" + name + '\'' +
                ", types=" + types +
                ", args=" + args +
                '}';
    }
}
