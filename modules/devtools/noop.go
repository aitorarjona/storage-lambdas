package main

import (
	"bytes"
	"context"
	"errors"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	v4 "github.com/aws/aws-sdk-go-v2/aws/signer/v4"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type noopGetHandler struct {
	s3client      *s3.Client
	s3endpoint    string
	s3credentials *aws.Credentials
	httpClient    *http.Client
}

func (h *noopGetHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Println("--- start noop get ---")
	t0 := time.Now()
	bucket := r.Header.Get("amz-s3proxy-bucket")
	key := r.Header.Get("amz-s3proxy-key")
	if bucket == "" || key == "" {
		log.Fatal(errors.New("Bucket and key headers required"))
	}

	url := h.s3endpoint + "/" + bucket + "/" + key
	req, err := http.NewRequest("GET", url, bytes.NewReader([]byte{}))
	if err != nil {
		log.Fatal(err)
	}
	signer := v4.NewSigner()
	signer.SignHTTP(context.Background(), *h.s3credentials, req, UNSIGNED_PAYLOAD_SHA, "s3", "us-east-1", time.Now())

	res, err := h.httpClient.Do(req)
	if res.StatusCode != 200 {
		log.Println(res.Status)
		body, _ := io.ReadAll(res.Body)
		log.Println(string(body))
		panic("error")
	}
	if err != nil {
		log.Fatal(err)
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", res.Request.Header.Get("Content-Type"))
	// w.Header().Set("Content-Length", strconv.Itoa(int(objRes.ContentLength)))
	w.Header().Set("Transfer-Encoding", "chunked")

	defer res.Body.Close()
	io.Copy(w, res.Body)
	elapsed := time.Since(t0)
	log.Printf("--- end noop get (took %v) ---\n", elapsed)
}
