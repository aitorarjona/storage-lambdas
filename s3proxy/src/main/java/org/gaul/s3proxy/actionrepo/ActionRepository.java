package org.gaul.s3proxy.actionrepo;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.gaul.s3proxy.actionrepo.exceptions.ActionHandlerException;
import org.gaul.s3proxy.actionrepo.stubs.Action;
import org.gaul.s3proxy.actionrepo.stubs.Module;
import org.gaul.s3proxy.actionrepo.stubs.Modules;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ActionRepository {
    private static final Logger logger = LoggerFactory.getLogger(ActionRepository.class);
    private final Map<String, Module> preprocessActionMap;
    private final Map<String, Map<String, ActionConnector>> consumeActionMap;

    private ActionRepository(Map<String, Module> putActions,
                             Map<String, Map<String, ActionConnector>> getActions) {
        this.preprocessActionMap = putActions;
        this.consumeActionMap = getActions;
    }

    public static ActionRepository fromYAML(File file) throws IOException {
        logger.debug("Loading actions from YAML file " + file.getPath());
        ObjectMapper om = new ObjectMapper(new YAMLFactory());
        om.findAndRegisterModules();

        Modules modules = om.readValue(file, Modules.class);

        Map<String, Module> putActions = new HashMap<String, Module>();
        Map<String, Map<String, ActionConnector>> getActions = new HashMap<String, Map<String, ActionConnector>>();

        for (Module mod : modules.getModules()) {

            for (String mimeType : mod.getMimeTypes()) {
                logger.info("Preprocess action for type " + mimeType + " in module " + mod.getModule());
                putActions.put(mimeType, mod);
            }

            for (Map.Entry<String, List<Action>> tup : mod.getActions().entrySet()) {
                for (Action act : tup.getValue()) {
                    ActionConnector ac = new ActionConnector(mod, act.getName(), act.getParameters());

                    switch (tup.getKey()) {
                        case "GET":
                            for (String mimeType : mod.getMimeTypes()) {
                                if (!getActions.containsKey(mimeType)) {
                                    getActions.put(mimeType, new HashMap<String, ActionConnector>());
                                }
                                logger.info("Consume action " + act.getName() + " for type " + mimeType + " in module" +
                                        " " + mod.getModule());
                                getActions.get(mimeType).put(act.getName(), ac);
                            }
                            break;
                        default:
                            throw new IOException("puta");
                    }

                }
            }
        }

        return new ActionRepository(putActions, getActions);
    }

    public Module getPreprocessAction(String mimeType) throws ActionHandlerException {
        if (this.preprocessActionMap.containsKey(mimeType)) {
            return this.preprocessActionMap.get(mimeType);
        } else {
            logger.info(mimeType + " does not have preprocess action handler");
            throw new ActionHandlerException();
        }
    }

    public ActionConnector getConsumeAction(String mimeType, String actionName) throws ActionHandlerException {
        if (this.consumeActionMap.containsKey(mimeType)) {
            Map<String, ActionConnector> actions = this.consumeActionMap.get(mimeType);
            if (actions.containsKey(actionName)) {
                return actions.get(actionName);
            } else {
                logger.info(mimeType + " does not have action " + actionName);
                throw new ActionHandlerException();
            }
        } else {
            logger.info(mimeType + " does not have any action handler");
            throw new ActionHandlerException();
        }
    }
}
