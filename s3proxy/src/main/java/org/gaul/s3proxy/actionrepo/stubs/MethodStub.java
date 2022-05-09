package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class MethodStub {
    private String name;
    private String returns;
    private List<String> args;

    public MethodStub(String name, String returns, List<String> args) {
        this.name = name;
        this.returns = returns;
        this.args = args;
    }

    public MethodStub() {
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getReturns() {
        return returns;
    }

    public void setReturns(String returns) {
        this.returns = returns;
    }

    public List<String> getArgs() {
        return args;
    }

    public void setArgs(List<String> args) {
        this.args = args;
    }

    @Override
    public String toString() {
        return "Method{" +
                "name='" + name + '\'' +
                ", returns='" + returns + '\'' +
                ", args=" + args +
                '}';
    }
}
