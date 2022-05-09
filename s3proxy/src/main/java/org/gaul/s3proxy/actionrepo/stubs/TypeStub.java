package org.gaul.s3proxy.actionrepo.stubs;

import java.util.List;

public class TypeStub {
    private String name;
    private String mimeType;
    private List<MethodStub> methodStubs;
    private List<AttributeStub> attributeStubs;
    private String extend;

    public TypeStub(String name, String mimeType, List<MethodStub> methodStubs, List<AttributeStub> attributeStubs, String extend) {
        this.name = name;
        this.mimeType = mimeType;
        this.methodStubs = methodStubs;
        this.attributeStubs = attributeStubs;
        this.extend = extend;
    }

    public TypeStub() {
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

    public List<MethodStub> getMethods() {
        return methodStubs;
    }

    public void setMethods(List<MethodStub> methodStubs) {
        this.methodStubs = methodStubs;
    }

    public List<AttributeStub> getAttributes() {
        return attributeStubs;
    }

    public void setAttributes(List<AttributeStub> attributeStubs) {
        this.attributeStubs = attributeStubs;
    }

    public String getExtend() {
        return extend;
    }

    public void setExtend(String extend) {
        this.extend = extend;
    }

    @Override
    public String toString() {
        return "TypeStub{" +
                "name='" + name + '\'' +
                ", mimeType='" + mimeType + '\'' +
                ", methodStubs=" + methodStubs +
                ", attributeStubs=" + attributeStubs +
                ", extend='" + extend + '\'' +
                '}';
    }
}
