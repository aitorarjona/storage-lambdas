package main

import (
	"encoding/json"
	"errors"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type putResponse struct {
	Etag string `json:"etag"`
}

type noopPutHandler struct {
	s3client *s3.Client
}

func (h *noopPutHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Println("--- start noop put ---")
	t0 := time.Now()
	bucket := r.Header.Get("amz-s3proxy-bucket")
	key := r.Header.Get("amz-s3proxy-key")
	if bucket == "" || key == "" {
		log.Fatal(errors.New("Bucket and key headers required"))
	}

	contentType := r.Header.Get("Content-Type")
	if contentType == "" {
		contentType = "application/octet-stream"
	}
	writer := NewOutputWriter(bucket, key, contentType, h.s3client)

	defer r.Body.Close()
	io.Copy(writer, r.Body)
	writer.Close()
	elapsed := time.Since(t0)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(putResponse{Etag: writer.Etag()})
	log.Printf("--- end noop put (took %v) ---\n", elapsed)
}
