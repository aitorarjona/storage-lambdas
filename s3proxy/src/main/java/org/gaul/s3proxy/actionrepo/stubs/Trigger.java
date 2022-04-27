package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class Trigger {
    private String method;
    private List<String> pipeline;
    private Condition condition;

    public Trigger(String method, List<String> pipeline, Condition condition) {
        this.method = method;
        this.pipeline = pipeline;
        this.condition = condition;
    }

    public Trigger() {
    }

    public String getMethod() {
        return method;
    }

    public void setMethod(String method) {
        this.method = method;
    }

    public List<String> getPipeline() {
        return pipeline;
    }

    public void setPipeline(List<String> pipeline) {
        this.pipeline = pipeline;
    }

    public Condition getCondition() {
        return condition;
    }

    public void setCondition(Condition condition) {
        this.condition = condition;
    }

    @Override
    public String toString() {
        return "Trigger{" +
                "method='" + method + '\'' +
                ", pipeline=" + pipeline +
                ", condition=" + condition +
                '}';
    }
}
