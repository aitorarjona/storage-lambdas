package org.gaul.s3proxy.shit;

import io.pravega.client.ByteStreamClientFactory;
import io.pravega.client.ClientConfig;
import io.pravega.client.EventStreamClientFactory;
import io.pravega.client.admin.StreamManager;
import io.pravega.client.byteStream.ByteStreamWriter;
import io.pravega.client.stream.EventStreamWriter;
import io.pravega.client.stream.EventWriterConfig;
import io.pravega.client.stream.ScalingPolicy;
import io.pravega.client.stream.StreamConfiguration;
import io.pravega.client.stream.impl.UTF8StringSerializer;

import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

public class StreamWriterExample {

    public final String scope;
    public final String streamName;
    public final URI controllerURI;

    public StreamWriterExample(String scope, String streamName, URI controllerURI) {
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

        ClientConfig clientConfig = ClientConfig.builder().controllerURI(controllerURI).build();
        ByteStreamClientFactory clientFactory = ByteStreamClientFactory.withScope(scope, clientConfig);

        ByteStreamWriter writer = clientFactory.createByteStreamWriter(streamName);
        try {
            for (int i = 0; i < 10; i++) {
                System.out.println("writing stream");
                writer.write("hello xd".getBytes(StandardCharsets.UTF_8));
                writer.flush();
                TimeUnit.SECONDS.sleep(2);
            }
//            writer.close();
            writer.closeAndSeal();
        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
            throw new RuntimeException(e);
        }

        clientFactory.close();
    }

    public static void main(String[] args) {
        final URI controllerURI = URI.create(Constants.DEFAULT_CONTROLLER_URI);
        StreamWriterExample writer = new StreamWriterExample(Constants.DEFAULT_SCOPE, "byteStream", controllerURI);

        writer.run();
    }
}
