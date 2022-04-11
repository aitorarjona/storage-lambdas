package main

import (
	"errors"
	"io"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type sleepGetHandler struct {
	s3client      *s3.Client
	s3endpoint    string
	s3credentials *aws.Credentials
	httpClient    *http.Client
}

func (h *sleepGetHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Println("--- start sleep get ---")
	var err error
	t0 := time.Now()
	bucket := r.Header.Get("amz-s3proxy-bucket")
	key := r.Header.Get("amz-s3proxy-key")
	if bucket == "" || key == "" {
		log.Fatal(errors.New("Bucket and key headers required"))
	}

	var sleepTime int
	values := r.URL.Query()
	if values.Has("time") {
		sleepTime, err = strconv.Atoi(values.Get("time"))
	} else {
		sleepTime = 5
	}
	if err != nil {
		panic(err)
	}
	log.Printf("Sleeping for %d seconds...\n", sleepTime)
	time.Sleep(time.Second * time.Duration(sleepTime))
	log.Println("Ok")

	done := false
	var getObjectRes *s3.GetObjectOutput
	for !done {
		getObjectRes, err = h.s3client.GetObject(r.Context(), &s3.GetObjectInput{Bucket: &bucket, Key: &key})
		if err != nil {
			log.Println(err)
			log.Println("retrying...")
		} else {
			done = true
		}
	}

	defer getObjectRes.Body.Close()

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", *getObjectRes.ContentType)
	// w.Header().Set("Content-Length", strconv.Itoa(int(objRes.ContentLength)))
	w.Header().Set("Transfer-Encoding", "chunked")

	io.Copy(w, getObjectRes.Body)
	elapsed := time.Since(t0)
	log.Printf("--- end sleep get (took %v) ---\n", elapsed)
}
