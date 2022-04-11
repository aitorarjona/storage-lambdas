package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

const UNSIGNED_PAYLOAD_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

func main() {
	s3endpoint := os.Getenv("S3_ENDPOINT")
	s3accessKeyId := os.Getenv("S3_ACCESS_KEY_ID")
	s3secretAccessKey := os.Getenv("S3_SECRET_ACCESS_KEY")
	target := os.Getenv("TARGET")
	fmt.Println("S3_ENDPOINT", s3endpoint)
	fmt.Println("S3_ACCESS_KEY_ID", s3accessKeyId[:5]+strings.Repeat("X", len(s3accessKeyId[5:])))
	fmt.Println("S3_SECRET_ACCESS_KEY", s3secretAccessKey[:5]+strings.Repeat("X", len(s3secretAccessKey[5:])))
	fmt.Println("TARGET", target)
	staticResolver := aws.EndpointResolverFunc(func(service, region string) (aws.Endpoint, error) {
		return aws.Endpoint{
			PartitionID:       "aws",
			URL:               s3endpoint,
			HostnameImmutable: true,
		}, nil
	})
	cfg := aws.Config{
		Credentials:      credentials.NewStaticCredentialsProvider(s3accessKeyId, s3secretAccessKey, ""),
		EndpointResolver: staticResolver,
	}
	s3client := s3.NewFromConfig(cfg)

	credsProvider := credentials.NewStaticCredentialsProvider(s3accessKeyId, s3secretAccessKey, "")
	creds, err := credsProvider.Retrieve(context.Background())
	if err != nil {
		log.Fatal(err)
	}

	httpClient := http.Client{}

	http.Handle("/preprocess", &noopPutHandler{s3client: s3client})
	http.Handle("/apply/noop", &noopGetHandler{
		s3client:      s3client,
		s3endpoint:    s3endpoint,
		s3credentials: &creds,
		httpClient:    &httpClient,
	})
	http.Handle("/apply/gunzip", &gunzipGetHandler{
		s3client:      s3client,
		s3endpoint:    s3endpoint,
		s3credentials: &creds,
		httpClient:    &httpClient,
	})
	http.Handle("/apply/sleep", &sleepGetHandler{
		s3client:      s3client,
		s3endpoint:    s3endpoint,
		s3credentials: &creds,
		httpClient:    &httpClient,
	})
	log.Println("Listen and serving at", target)
	log.Fatal(http.ListenAndServe(target, nil))
}
