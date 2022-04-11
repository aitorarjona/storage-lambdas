FROM golang:1.17-buster AS build

WORKDIR /app

COPY go.mod ./
COPY go.sum ./
RUN go mod download

COPY . ./
RUN go build

FROM ubuntu:20.04

WORKDIR /app
COPY --from=build /app/devmod /app/devmod
COPY s3_endpoint_hack.sh s3_endpoint_hack.sh
RUN chmod u+x s3_endpoint_hack.sh devmod

CMD bash s3_endpoint_hack.sh