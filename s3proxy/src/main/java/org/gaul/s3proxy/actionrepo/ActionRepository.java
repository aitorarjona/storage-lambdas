package org.gaul.s3proxy.actionrepo;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.gaul.s3proxy.actionrepo.exceptions.ActionHandlerException;
import org.gaul.s3proxy.actionrepo.stubs.*;
import org.gaul.s3proxy.actionrepo.stubs.Module;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

public class ActionRepository {
    private static final Logger logger = LoggerFactory.getLogger(ActionRepository.class);
    private final Map<String, ActionConnector> actionMap;
    private final Map<String, Type> mimeTypesMap;

    private ActionRepository(Map<String, ActionConnector> actionMap, Map<String, Type> MIMETypesMap) {
        this.actionMap = actionMap;
        this.mimeTypesMap = MIMETypesMap;
    }

    public static ActionRepository fromYAML(File file) throws IOException {
        logger.debug("Loading actions from YAML file " + file.getPath());
        ObjectMapper om = new ObjectMapper(new YAMLFactory());
        om.findAndRegisterModules();

        Manifest manifest = om.readValue(file, Manifest.class);

        Map<String, ActionConnector> actionMap = new HashMap<>();
        Map<String, Type> MIMETypesMap = new HashMap<>();

        for (Type typ : manifest.getTypes()) {
            logger.info(typ.toString());
            MIMETypesMap.put(typ.getMimeType(), typ);
        }

        int basePort = 8000;
        for (Module mod : manifest.getModules()) {
            for (Action act : mod.getActions()) {
                if (mod.getHost() == null) {
                    mod.setHost("127.0.0.1");
                }
                if (mod.getPort() == 0) {
                    mod.setPort(basePort++);
                }
                ActionConnector ac = new ActionConnector(mod, act);
                logger.info(ac.toString());
                actionMap.put(act.getName(), ac);
            }
        }

        return new ActionRepository(actionMap, MIMETypesMap);
    }

    public ActionConnector getAction(String mimeType, String actionName) throws ActionHandlerException {
        if (mimeTypesMap.containsKey(mimeType)) {
            Type type = mimeTypesMap.get(mimeType);
            Method method = type.getMethod(actionName);
            if (method != null) {
                return actionMap.get(actionName);
            } else {
                throw new ActionHandlerException();
            }
        } else {
            throw new ActionHandlerException();
        }
    }

}
