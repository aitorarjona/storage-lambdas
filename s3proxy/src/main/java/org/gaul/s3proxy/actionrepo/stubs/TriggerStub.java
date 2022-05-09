package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class TriggerStub {
    private String method;
    private List<String> pipeline;
    private ConditionStub conditionStub;

    public TriggerStub(String method, List<String> pipeline, ConditionStub conditionStub) {
        this.method = method;
        this.pipeline = pipeline;
        this.conditionStub = conditionStub;
    }

    public TriggerStub() {
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

    public ConditionStub getCondition() {
        return conditionStub;
    }

    public void setCondition(ConditionStub conditionStub) {
        this.conditionStub = conditionStub;
    }

    @Override
    public String toString() {
        return "Trigger{" +
                "method='" + method + '\'' +
                ", pipeline=" + pipeline +
                ", condition=" + conditionStub +
                '}';
    }
}
