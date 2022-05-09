package org.gaul.s3proxy.actionrepo;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.gaul.s3proxy.actionrepo.exceptions.ActionHandlerException;
import org.gaul.s3proxy.actionrepo.stubs.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.apache.commons.lang3.tuple.ImmutablePair;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

public class ActionRepository {
    private static final Logger logger = LoggerFactory.getLogger(ActionRepository.class);
    private final Map<ImmutablePair<String, String>, ActionConnector> repo;

    private ActionRepository(Map<ImmutablePair<String, String>, ActionConnector> repo) {
        this.repo = repo;
    }

    private static ActionRepository build(ManifestStub manifest) {
        Map<String, TypeStub> typesMap = new HashMap<>();
        Map<ImmutablePair<String, String>, ActionConnector> repo = new HashMap<>();

        for (TypeStub typ : manifest.getTypes()) {
            logger.info(typ.toString());
            typesMap.put(typ.getName(), typ);
        }

        int basePort = 8000;
        for (ModuleStub mod : manifest.getModules()) {
            if (mod.getHost() == null) {
                mod.setHost("127.0.0.1");
            }
            if (mod.getPort() == 0) {
                mod.setPort(basePort++);
            }
            for (ActionStub act : mod.getActions()) {
                for (String actionType : act.getTypes()) {
                    TypeStub type = typesMap.get(actionType);
                    ImmutablePair<String, String> tup = new ImmutablePair<>(type.getMimeType(), act.getName());
                    ActionConnector ac = new ActionConnector(mod, act);
                    logger.info("{}: {} ({})", tup, ac.getActionType(), mod.getModule());
                    repo.put(tup, ac);
                }
            }
        }

        return new ActionRepository(repo);
    }

    public static ActionRepository fromYAML(File file) throws IOException {
        logger.debug("Loading actions from YAML file " + file.getPath());
        ObjectMapper om = new ObjectMapper(new YAMLFactory());
        om.findAndRegisterModules();

        ManifestStub manifestStub = om.readValue(file, ManifestStub.class);
        return ActionRepository.build(manifestStub);
    }

    public static ActionRepository fromYAML(InputStream stream) throws IOException {
        logger.debug("Loading actions from stream");
        ObjectMapper om = new ObjectMapper(new YAMLFactory());
        om.findAndRegisterModules();

        ManifestStub manifestStub = om.readValue(stream, ManifestStub.class);
        return ActionRepository.build(manifestStub);
    }

    public ActionConnector getAction(String mimeType, String actionName) throws ActionHandlerException {
        ImmutablePair<String, String> tup = new ImmutablePair<>(mimeType, actionName);
        if (repo.containsKey(tup)) {
            return repo.get(tup);
        } else {
            throw new ActionHandlerException();
        }
    }

}
