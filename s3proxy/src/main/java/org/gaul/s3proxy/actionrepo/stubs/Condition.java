package org.gaul.s3proxy.actionrepo.stubs;

public class Condition {
    private String target;
    private String verb;
    private String value;

    public Condition(String header, String verb, String value) {
        this.target = header;
        this.verb = verb;
        this.value = value;
    }

    public Condition() {
    }

    public String getTarget() {
        return target;
    }

    public void setTarget(String target) {
        this.target = target;
    }

    public String getVerb() {
        return verb;
    }

    public void setVerb(String verb) {
        this.verb = verb;
    }

    public String getValue() {
        return value;
    }

    public void setValue(String value) {
        this.value = value;
    }

    @Override
    public String toString() {
        return "Condition{" +
                "target='" + target + '\'' +
                ", verb='" + verb + '\'' +
                ", value='" + value + '\'' +
                '}';
    }
}
