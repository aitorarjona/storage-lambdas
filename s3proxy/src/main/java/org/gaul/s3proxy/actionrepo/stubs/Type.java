package org.gaul.s3proxy.actionrepo.stubs;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Type {
    private String name;
    private String mimeType;
    private List<Method> methods;
    private List<Attribute> attributes;
    private String extends_;
    private Map<String, Method> methodMap;

    public Type(String name, String mimeType, List<Method> methods, List<Attribute> attributes, String extends_) {
        this.name = name;
        this.mimeType = mimeType;
        this.methods = methods;
        this.attributes = attributes;
        this.extends_ = extends_;

        this.methodMap = new HashMap<>();
        for (Method method : methods) {
            methodMap.put(method.getName(), method);
        }
    }

    public Type() {
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getMimeType() {
        return mimeType;
    }

    public void setMimeType(String mimeType) {
        this.mimeType = mimeType;
    }

    public List<Method> getMethods() {
        return methods;
    }

    public void setMethods(List<Method> methods) {
        this.methodMap = new HashMap<>();
        for (Method method : methods) {
            methodMap.put(method.getName(), method);
        }
        this.methods = methods;
    }

    public List<Attribute> getAttributes() {
        return attributes;
    }

    public void setAttributes(List<Attribute> attributes) {
        this.attributes = attributes;
    }

    public String getExtends() {
        return extends_;
    }

    public void setExtends(String extends_) {
        this.extends_ = extends_;
    }

    public Method getMethod(String name) {
        return this.methodMap.get(name);
    }

    @Override
    public String toString() {
        return "Type{" +
                "name='" + name + '\'' +
                ", mimeType='" + mimeType + '\'' +
                ", methods=" + methods +
                ", attributes=" + attributes +
                ", extends_='" + extends_ + '\'' +
                ", methodMap=" + methodMap +
                '}';
    }
}
