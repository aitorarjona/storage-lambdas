package org.gaul.s3proxy.shit;

import io.pravega.client.ByteStreamClientFactory;
import io.pravega.client.ClientConfig;
import io.pravega.client.EventStreamClientFactory;
import io.pravega.client.admin.ReaderGroupManager;
import io.pravega.client.admin.StreamManager;
import io.pravega.client.byteStream.ByteStreamReader;
import io.pravega.client.stream.*;
import io.pravega.client.stream.impl.UTF8StringSerializer;
import org.yaml.snakeyaml.reader.StreamReader;

import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

public class StreamReaderExample {

    public final String scope;
    public final String streamName;
    public final URI controllerURI;

    public StreamReaderExample(String scope, String streamName, URI controllerURI) {
        this.scope = scope;
        this.streamName = streamName;
        this.controllerURI = controllerURI;
    }

    public void run() {
        StreamManager streamManager = StreamManager.create(controllerURI);
        final boolean scopeIsNew = streamManager.createScope(scope);

        StreamConfiguration streamConfig = StreamConfiguration.builder()
                .scalingPolicy(ScalingPolicy.fixed(1))
                .build();
        final boolean streamIsNew = streamManager.createStream(scope, streamName, streamConfig);

        final String readerGroup = UUID.randomUUID().toString().replace("-", "");
        final ReaderGroupConfig readerGroupConfig = ReaderGroupConfig.builder()
                .stream(Stream.of(scope, streamName))
                .build();
        try (ReaderGroupManager readerGroupManager = ReaderGroupManager.withScope(scope, controllerURI)) {
            readerGroupManager.createReaderGroup(readerGroup, readerGroupConfig);
        }

        ClientConfig clientConfig = ClientConfig.builder().controllerURI(controllerURI).build();
        ByteStreamClientFactory clientFactory = ByteStreamClientFactory.withScope(scope, clientConfig);

        ByteStreamReader streamReader = clientFactory.createByteStreamReader(streamName);

        byte[] res = new byte[1];
        try {
            System.out.format("Reading stream from %s/%s%n", scope, streamName);
            long tailOffset = streamReader.fetchTailOffset();
            System.out.println(tailOffset);
//            streamReader.seekToOffset(tailOffset);
//            long offset = streamReader.getOffset();
//            System.out.println(offset);
            streamReader.read(res);
//            System.out.println(p);
        } catch (IOException e) {
            e.printStackTrace();
        }
        System.out.println(new String(res, StandardCharsets.UTF_8));
    }

    public static void main(String[] args) {
        final URI controllerURI = URI.create(Constants.DEFAULT_CONTROLLER_URI);
        StreamReaderExample reader = new StreamReaderExample(Constants.DEFAULT_SCOPE, "byteStream", controllerURI);

        reader.run();
    }
}
