package main

import (
	"bytes"
	"context"
	"io"
	"log"
	"sync"

	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

const BUFF_SZ = 10 * 1024 * 1024 // 10 MiB

type OutputWriter struct {
	bucket      string
	key         string
	contentType string
	buff        *bytes.Buffer
	buffSz      uint32
	uploadId    *string
	partNo      int32
	parts       []types.CompletedPart
	s3Client    *s3.Client
	lock        *sync.Mutex
	wg          *sync.WaitGroup
	etag        *string
}

func NewOutputWriter(bucket string, key string, contentType string, s3client *s3.Client) *OutputWriter {
	res, err := s3client.CreateMultipartUpload(context.Background(),
		&s3.CreateMultipartUploadInput{
			Bucket:      &bucket,
			Key:         &key,
			ContentType: &contentType,
		},
	)
	if err != nil {
		log.Fatal(err)
	}

	w := &OutputWriter{
		bucket:      bucket,
		key:         key,
		contentType: contentType,
		buff:        bytes.NewBuffer(make([]byte, BUFF_SZ)),
		uploadId:    res.UploadId,
		parts:       make([]types.CompletedPart, 0),
		s3Client:    s3client,
		lock:        &sync.Mutex{},
		wg:          &sync.WaitGroup{},
	}
	w.buff.Reset()

	return w
}

func (w *OutputWriter) Write(data []byte) (int, error) {
	inSz := len(data)
	processed := 0

	for processed < inSz {
		space := BUFF_SZ - w.buff.Len()
		upLimit := processed + space
		if upLimit > inSz {
			upLimit = inSz
		}
		n, err := w.buff.Write(data[processed:upLimit])
		if err != nil {
			log.Fatal(err)
		}
		processed += n

		if w.buff.Len() == BUFF_SZ {
			bodyBuff := make([]byte, BUFF_SZ)
			n, err = w.buff.Read(bodyBuff)
			if err != nil {
				log.Fatal((err))
			}
			log.Println("upload part of size", n)
			res, err := w.s3Client.UploadPart(
				context.Background(),
				&s3.UploadPartInput{
					Bucket:     &w.bucket,
					Key:        &w.key,
					PartNumber: w.partNo,
					UploadId:   w.uploadId,
					Body:       bytes.NewReader(bodyBuff[:n]),
				},
			)
			if err != nil {
				log.Fatal(err)
			}
			objPart := types.CompletedPart{
				PartNumber: w.partNo,
				ETag:       res.ETag,
			}
			w.parts = append(w.parts, objPart)
			w.partNo++
			w.buff.Reset()
		}

	}

	return processed, nil
}

func (w *OutputWriter) Close() {
	leftSz := BUFF_SZ - w.buff.Len()
	if leftSz > 0 {
		bodyBuff := make([]byte, BUFF_SZ)
		n, err := w.buff.Read(bodyBuff)
		if err == nil {
			log.Println("upload part of size", n)
			res, err := w.s3Client.UploadPart(
				context.Background(),
				&s3.UploadPartInput{
					Bucket:     &w.bucket,
					Key:        &w.key,
					PartNumber: w.partNo,
					UploadId:   w.uploadId,
					Body:       bytes.NewReader(bodyBuff[:n]),
				},
			)
			if err != nil {
				log.Fatal(err)
			}
			objPart := types.CompletedPart{
				PartNumber: w.partNo,
				ETag:       res.ETag,
			}
			w.parts = append(w.parts, objPart)
			w.buff.Reset()
		}
		if err != nil && err != io.EOF {
			log.Fatal(err)
		}
	}

	multipartUpload := &types.CompletedMultipartUpload{
		Parts: w.parts,
	}
	completedRes, err := w.s3Client.CompleteMultipartUpload(
		context.Background(),
		&s3.CompleteMultipartUploadInput{
			Bucket:          &w.bucket,
			Key:             &w.key,
			UploadId:        w.uploadId,
			MultipartUpload: multipartUpload,
		},
	)
	if err != nil {
		log.Fatal(err)
	}
	w.etag = completedRes.ETag
}

func (w *OutputWriter) Etag() string {
	return *w.etag
}
