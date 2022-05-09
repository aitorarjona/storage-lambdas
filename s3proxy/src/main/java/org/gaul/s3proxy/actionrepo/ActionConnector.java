package org.gaul.s3proxy.actionrepo;

import org.gaul.s3proxy.actionrepo.stubs.ActionStub;
import org.gaul.s3proxy.actionrepo.stubs.ModuleStub;

public class ActionConnector {
    private final ActionStub actionStub;
    private final ModuleStub moduleStub;
    private final ActionType actionType;

    public ActionConnector(ModuleStub moduleStub, ActionStub actionStub) {
        this.moduleStub = moduleStub;
        this.actionStub = actionStub;
        if (actionStub.getKind() != null) {
            this.actionType = actionStub.getKind().compareToIgnoreCase("stateful") == 0 ?
                    ActionType.STATEFUL :
                    ActionType.STATELESS;
        } else {
            this.actionType = ActionType.STATEFUL;
        }
    }

    public ActionStub getActionStub() {
        return actionStub;
    }

    public ModuleStub getModuleStub() {
        return moduleStub;
    }


    public ActionType getActionType() {
        return actionType;
    }

    @Override
    public String toString() {
        return "ActionConnector{" +
                "action=" + actionStub +
                ", module=" + moduleStub +
                '}';
    }
}
