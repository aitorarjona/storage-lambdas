package org.gaul.s3proxy.actionrepo.stubs;

public class Attribute {
    private String key;
    private String type;
    private boolean required = false;

    public Attribute(String key, String type, boolean required) {
        this.key = key;
        this.type = type;
        this.required = required;
    }

    public Attribute() {
    }

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public boolean isRequired() {
        return required;
    }

    public void setRequired(boolean required) {
        this.required = required;
    }

    @Override
    public String toString() {
        return "Attribute{" +
                "key='" + key + '\'' +
                ", type='" + type + '\'' +
                ", required=" + required +
                '}';
    }
}
