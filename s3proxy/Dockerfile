# Multistage - Builder
FROM maven:3.6.3-jdk-11-slim as s3proxy-builder
LABEL maintainer="Andrew Gaul <andrew@gaul.org>"

WORKDIR /opt/s3proxy
COPY src/ /opt/s3proxy/src/
COPY pom.xml /opt/s3proxy/pom.xml

RUN mvn package -DskipTests

# Multistage - Image
FROM openjdk:11-jre-slim
LABEL maintainer="Andrew Gaul <andrew@gaul.org>"

WORKDIR /opt/s3proxy

COPY \
    --from=s3proxy-builder \
    /opt/s3proxy/target/s3proxy \
    /opt/s3proxy/src/main/resources/s3_endpoint_hack.sh \
    /opt/s3proxy/

EXPOSE 8080
CMD chmod u+x /opt/s3proxy/s3_endpoint_hack.sh \
    && bash /opt/s3proxy/s3_endpoint_hack.sh \
    && java -DLOG_LEVEL="${LOG_LEVEL}" -jar /opt/s3proxy/s3proxy --properties /opt/s3proxy/s3proxy.properties

