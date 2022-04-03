#!/bin/bash

python3.8 -m grpc_tools.protoc --proto_path="./modelservice" --python_out="./modelservice" --grpc_python_out="./modelservice" modelservice/modelservice.proto
sed -i 's/import modelservice_pb2 as modelservice__pb2/from modelservice import modelservice_pb2 as modelservice__pb2/g' modelservice/modelservice_pb2_grpc.py