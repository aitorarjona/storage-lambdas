package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	v4 "github.com/aws/aws-sdk-go-v2/aws/signer/v4"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/google/uuid"
)

const PARAMS_FILE = "params.json"

type params struct {
	Benchmark         string            `json:"benchmark"`
	S3Endpoint        string            `json:"s3endpoint"`
	S3EndpointScheme  string            `json:"s3endpointScheme"`
	S3AccessKeyId     string            `json:"s3accessKeyId"`
	S3SecretAccessKey string            `json:"s3secretAccessKey"`
	S3Bucket          string            `json:"s3bucket"`
	PayloadSize       int               `json:"payloadSize"`
	NumberKeys        int               `json:"numberKeys"`
	Action            string            `json:"action"`
	Parameters        map[string]string `json:"parameters"`
}

type keys struct {
	Keys []string `json:"keys"`
}

type result struct {
	Start   int64 `json:"start"`
	End     int64 `json:"end"`
	Elapsed int64 `json:"elapsed"`
	TTFB    int64 `json:"ttfb"`
}

func write(httpClient *http.Client, params *params, creds *aws.Credentials, payload []byte, key string, sha string, resChan chan result) {
	url := url.URL{
		Scheme: params.S3EndpointScheme,
		Host:   params.S3Endpoint,
		Path:   filepath.Join(params.S3Bucket, key),
	}
	fmt.Println(url.String())

	payloadReader := bytes.NewReader(payload)
	req, err := http.NewRequest("PUT", url.String(), payloadReader)
	if err != nil {
		log.Fatal(err)
	}

	req.ContentLength = int64(params.PayloadSize)
	req.Header.Add("Content-Type", "application/octet-stream")
	req.Header.Add("x-amz-content-sha256", sha)
	signer := v4.NewSigner()
	signer.SignHTTP(context.Background(), *creds, req, sha, "s3", "us-east-1", time.Now())

	start := time.Now()
	res, err := httpClient.Do(req)
	end := time.Now()
	if err != nil {
		log.Fatal(err)
	}
	elapsed := end.Sub(start)
	fmt.Println(elapsed)

	fmt.Println(res.Status)
	fmt.Println(res.Header)
	resBody, err := io.ReadAll(res.Body)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(string(resBody))

	resChan <- result{
		Start:   start.UnixNano(),
		End:     end.UnixNano(),
		Elapsed: elapsed.Nanoseconds(),
	}
}

func read(httpClient *http.Client, params *params, creds *aws.Credentials,
	key string, sha string, resChan chan result) {
	url := url.URL{
		Scheme: params.S3EndpointScheme,
		Host:   params.S3Endpoint,
		Path:   filepath.Join(params.S3Bucket, key),
	}

	if params.Action != "" {
		urlQuery := url.Query()
		urlQuery.Add("query", params.Action)
		for k, v := range params.Parameters {
			urlQuery.Add(k, v)
		}
		url.RawQuery = urlQuery.Encode()
	}

	fmt.Println(url.String())
	payloadReader := bytes.NewReader([]byte{})
	req, err := http.NewRequest("GET", url.String(), payloadReader)
	if err != nil {
		log.Fatal(err)
	}

	firstByte := make([]byte, 1)

	signer := v4.NewSigner()
	signer.SignHTTP(context.Background(), *creds, req, sha, "s3", "us-east-1", time.Now())

	start := time.Now()
	res, err1 := httpClient.Do(req)
	_, err2 := req.Body.Read(firstByte)
	ttfb := time.Now()
	bodyRes, err3 := io.ReadAll(res.Body)
	end := time.Now()
	if err1 != nil {
		log.Fatal(err)
	}
	if err2 != nil {
		log.Fatal(err)
	}
	if err3 != nil {
		log.Fatal(err)
	}
	allBody := []byte{}
	allBody = append(allBody, firstByte...)
	allBody = append(allBody, bodyRes...)
	fmt.Println("Status", res.Status)
	fmt.Println("Content-Length", res.ContentLength)
	fmt.Println("TransferEncoding", res.TransferEncoding)
	fmt.Println("Headers", res.Header)
	fmt.Println("Body len", len(allBody))

	elapsed := end.Sub(start)
	ttfbElpased := ttfb.Sub(start)
	fmt.Println("Time elpased", elapsed)
	fmt.Println("TTFB", ttfbElpased)

	resChan <- result{
		Start:   start.UnixNano(),
		End:     end.UnixNano(),
		Elapsed: elapsed.Nanoseconds(),
		TTFB:    ttfbElpased.Nanoseconds(),
	}
}

func main() {
	paramsFile, err := os.Open(PARAMS_FILE)
	defer paramsFile.Close()
	if err != nil {
		log.Fatal(err)
	}
	paramsData, err := io.ReadAll(paramsFile)
	params := params{}
	err = json.Unmarshal(paramsData, &params)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(params)

	credsProvider := credentials.NewStaticCredentialsProvider(params.S3AccessKeyId, params.S3SecretAccessKey, "")
	creds, err := credsProvider.Retrieve(context.Background())
	if err != nil {
		log.Fatal(err)
	}

	httpClient := http.Client{}

	execId := uuid.New().String()[:4]

	switch params.Benchmark {
	case "write":
		keyList := make([]string, params.NumberKeys)
		payload := make([]byte, params.PayloadSize)
		_, err = rand.Read(payload)
		if err != nil {
			log.Fatal(err)
		}

		hash := sha256.New()
		hash.Write(payload)
		sha := hex.EncodeToString(hash.Sum(nil))
		fmt.Println(sha)

		resultChan := make(chan result, params.NumberKeys)
		for i := 0; i < params.NumberKeys; i++ {
			key := uuid.New().String()
			write(&httpClient, &params, &creds, payload, key, sha, resultChan)
			keyList[i] = key
			// go write(&httpClient, &params, &creds, payload, sha, resultChan)
		}

		results := make([]result, params.NumberKeys)
		for i := 0; i < params.NumberKeys; i++ {
			res := <-resultChan
			results[i] = res
		}

		resultsFile, err := os.OpenFile(fmt.Sprintf("write_results_%s.json", execId), os.O_CREATE|os.O_WRONLY, 0666)
		defer resultsFile.Close()
		if err != nil {
			log.Fatal(err)
		}
		resultsJson, err := json.Marshal(results)
		if err != nil {
			log.Fatal((err))
		}
		resultsFile.Write(resultsJson)

		keysStruct := keys{Keys: keyList}
		keysFile, err := os.OpenFile("keys.json", os.O_CREATE|os.O_WRONLY, 0666)
		defer keysFile.Close()
		if err != nil {
			log.Fatal(err)
		}
		keysJson, err := json.Marshal(keysStruct)
		if err != nil {
			log.Fatal((err))
		}
		keysFile.Write(keysJson)

	case "read":
		keysFile, err := os.Open("keys.json")
		if err != nil {
			log.Fatal(err)
		}
		keysFileContent, err := io.ReadAll(keysFile)
		if err != nil {
			log.Fatal(err)
		}
		keysStruct := keys{}
		err = json.Unmarshal(keysFileContent, &keysStruct)
		if err != nil {
			log.Fatal(err)
		}

		keys := keysStruct.Keys

		hash := sha256.New()
		hash.Write([]byte{})
		sha := hex.EncodeToString(hash.Sum(nil))
		fmt.Println(sha)

		resultChan := make(chan result, len(keys))
		for _, key := range keys {
			read(&httpClient, &params, &creds, key, sha, resultChan)
		}

		results := make([]result, params.NumberKeys)
		for i := 0; i < params.NumberKeys; i++ {
			res := <-resultChan
			results[i] = res
		}

		resultsFile, err := os.OpenFile(fmt.Sprintf("read_results_%s.json", execId), os.O_CREATE|os.O_WRONLY, 0666)
		defer resultsFile.Close()
		if err != nil {
			log.Fatal(err)
		}
		resultsJson, err := json.Marshal(results)
		if err != nil {
			log.Fatal((err))
		}
		resultsFile.Write(resultsJson)

	default:
		panic(errors.New(fmt.Sprintf("Unknown action %s", params.Action)))
	}
}
