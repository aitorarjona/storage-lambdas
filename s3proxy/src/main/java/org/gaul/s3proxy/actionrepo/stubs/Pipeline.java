package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class Pipeline {
    private String name;
    private List<String> pipeline;

    public Pipeline(String name, List<String> pipeline) {
        this.name = name;
        this.pipeline = pipeline;
    }

    public Pipeline() {

    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<String> getPipeline() {
        return pipeline;
    }

    public void setPipeline(List<String> pipeline) {
        this.pipeline = pipeline;
    }

    @Override
    public String toString() {
        return "Pipeline{" +
                "name='" + name + '\'' +
                ", pipeline=" + pipeline +
                '}';
    }
}
