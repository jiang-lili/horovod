// Copyright 2017 Uber Technologies, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// =============================================================================

// automatically generated by the FlatBuffers compiler, do not modify


#ifndef FLATBUFFERS_GENERATED_MPIMESSAGE_HOROVOD_TENSORFLOW_WIRE_H_
#define FLATBUFFERS_GENERATED_MPIMESSAGE_HOROVOD_TENSORFLOW_WIRE_H_

#include "flatbuffers/flatbuffers.h"

namespace horovod {
namespace tensorflow {
namespace wire {

struct MPIRequest;

struct MPIResponse;

enum MPIDataType {
  MPIDataType_TF_MPI_UINT8 = 0,
  MPIDataType_TF_MPI_INT8 = 1,
  MPIDataType_TF_MPI_UINT16 = 2,
  MPIDataType_TF_MPI_INT16 = 3,
  MPIDataType_TF_MPI_INT32 = 4,
  MPIDataType_TF_MPI_INT64 = 5,
  MPIDataType_TF_MPI_FLOAT32 = 6,
  MPIDataType_TF_MPI_FLOAT64 = 7,
  MPIDataType_MIN = MPIDataType_TF_MPI_UINT8,
  MPIDataType_MAX = MPIDataType_TF_MPI_FLOAT64
};

inline const char **EnumNamesMPIDataType() {
  static const char *names[] = {
    "TF_MPI_UINT8",
    "TF_MPI_INT8",
    "TF_MPI_UINT16",
    "TF_MPI_INT16",
    "TF_MPI_INT32",
    "TF_MPI_INT64",
    "TF_MPI_FLOAT32",
    "TF_MPI_FLOAT64",
    nullptr
  };
  return names;
}

inline const char *EnumNameMPIDataType(MPIDataType e) {
  const size_t index = static_cast<int>(e);
  return EnumNamesMPIDataType()[index];
}

enum MPIRequestType {
  MPIRequestType_ALLREDUCE = 0,
  MPIRequestType_ALLGATHER = 1,
  MPIRequestType_BROADCAST = 2,
  MPIRequestType_MIN = MPIRequestType_ALLREDUCE,
  MPIRequestType_MAX = MPIRequestType_BROADCAST
};

inline const char **EnumNamesMPIRequestType() {
  static const char *names[] = {
    "ALLREDUCE",
    "ALLGATHER",
    "BROADCAST",
    nullptr
  };
  return names;
}

inline const char *EnumNameMPIRequestType(MPIRequestType e) {
  const size_t index = static_cast<int>(e);
  return EnumNamesMPIRequestType()[index];
}

enum MPIResponseType {
  MPIResponseType_ALLREDUCE = 0,
  MPIResponseType_ALLGATHER = 1,
  MPIResponseType_BROADCAST = 2,
  MPIResponseType_ERROR = 3,
  MPIResponseType_DONE = 4,
  MPIResponseType_SHUTDOWN = 5,
  MPIResponseType_MIN = MPIResponseType_ALLREDUCE,
  MPIResponseType_MAX = MPIResponseType_SHUTDOWN
};

inline const char **EnumNamesMPIResponseType() {
  static const char *names[] = {
    "ALLREDUCE",
    "ALLGATHER",
    "BROADCAST",
    "ERROR",
    "DONE",
    "SHUTDOWN",
    nullptr
  };
  return names;
}

inline const char *EnumNameMPIResponseType(MPIResponseType e) {
  const size_t index = static_cast<int>(e);
  return EnumNamesMPIResponseType()[index];
}

struct MPIRequest FLATBUFFERS_FINAL_CLASS : private flatbuffers::Table {
  enum {
    VT_REQUEST_RANK = 4,
    VT_REQUEST_TYPE = 6,
    VT_TENSOR_TYPE = 8,
    VT_TENSOR_NAME = 10,
    VT_ROOT_RANK = 12,
    VT_DEVICE = 14,
    VT_TENSOR_SHAPE = 16
  };
  int32_t request_rank() const {
    return GetField<int32_t>(VT_REQUEST_RANK, 0);
  }
  MPIRequestType request_type() const {
    return static_cast<MPIRequestType>(GetField<int8_t>(VT_REQUEST_TYPE, 0));
  }
  MPIDataType tensor_type() const {
    return static_cast<MPIDataType>(GetField<int8_t>(VT_TENSOR_TYPE, 0));
  }
  const flatbuffers::String *tensor_name() const {
    return GetPointer<const flatbuffers::String *>(VT_TENSOR_NAME);
  }
  int32_t root_rank() const {
    return GetField<int32_t>(VT_ROOT_RANK, 0);
  }
  int32_t device() const {
    return GetField<int32_t>(VT_DEVICE, 0);
  }
  const flatbuffers::Vector<int64_t> *tensor_shape() const {
    return GetPointer<const flatbuffers::Vector<int64_t> *>(VT_TENSOR_SHAPE);
  }
  bool Verify(flatbuffers::Verifier &verifier) const {
    return VerifyTableStart(verifier) &&
           VerifyField<int32_t>(verifier, VT_REQUEST_RANK) &&
           VerifyField<int8_t>(verifier, VT_REQUEST_TYPE) &&
           VerifyField<int8_t>(verifier, VT_TENSOR_TYPE) &&
           VerifyField<flatbuffers::uoffset_t>(verifier, VT_TENSOR_NAME) &&
           verifier.Verify(tensor_name()) &&
           VerifyField<int32_t>(verifier, VT_ROOT_RANK) &&
           VerifyField<int32_t>(verifier, VT_DEVICE) &&
           VerifyField<flatbuffers::uoffset_t>(verifier, VT_TENSOR_SHAPE) &&
           verifier.Verify(tensor_shape()) &&
           verifier.EndTable();
  }
};

struct MPIRequestBuilder {
  flatbuffers::FlatBufferBuilder &fbb_;
  flatbuffers::uoffset_t start_;
  void add_request_rank(int32_t request_rank) {
    fbb_.AddElement<int32_t>(MPIRequest::VT_REQUEST_RANK, request_rank, 0);
  }
  void add_request_type(MPIRequestType request_type) {
    fbb_.AddElement<int8_t>(MPIRequest::VT_REQUEST_TYPE, static_cast<int8_t>(request_type), 0);
  }
  void add_tensor_type(MPIDataType tensor_type) {
    fbb_.AddElement<int8_t>(MPIRequest::VT_TENSOR_TYPE, static_cast<int8_t>(tensor_type), 0);
  }
  void add_tensor_name(flatbuffers::Offset<flatbuffers::String> tensor_name) {
    fbb_.AddOffset(MPIRequest::VT_TENSOR_NAME, tensor_name);
  }
  void add_root_rank(int32_t root_rank) {
    fbb_.AddElement<int32_t>(MPIRequest::VT_ROOT_RANK, root_rank, 0);
  }
  void add_device(int32_t device) {
    fbb_.AddElement<int32_t>(MPIRequest::VT_DEVICE, device, 0);
  }
  void add_tensor_shape(flatbuffers::Offset<flatbuffers::Vector<int64_t>> tensor_shape) {
    fbb_.AddOffset(MPIRequest::VT_TENSOR_SHAPE, tensor_shape);
  }
  MPIRequestBuilder(flatbuffers::FlatBufferBuilder &_fbb)
        : fbb_(_fbb) {
    start_ = fbb_.StartTable();
  }
  MPIRequestBuilder &operator=(const MPIRequestBuilder &);
  flatbuffers::Offset<MPIRequest> Finish() {
    const auto end = fbb_.EndTable(start_, 7);
    auto o = flatbuffers::Offset<MPIRequest>(end);
    return o;
  }
};

inline flatbuffers::Offset<MPIRequest> CreateMPIRequest(
    flatbuffers::FlatBufferBuilder &_fbb,
    int32_t request_rank = 0,
    MPIRequestType request_type = MPIRequestType_ALLREDUCE,
    MPIDataType tensor_type = MPIDataType_TF_MPI_UINT8,
    flatbuffers::Offset<flatbuffers::String> tensor_name = 0,
    int32_t root_rank = 0,
    int32_t device = 0,
    flatbuffers::Offset<flatbuffers::Vector<int64_t>> tensor_shape = 0) {
  MPIRequestBuilder builder_(_fbb);
  builder_.add_tensor_shape(tensor_shape);
  builder_.add_device(device);
  builder_.add_root_rank(root_rank);
  builder_.add_tensor_name(tensor_name);
  builder_.add_request_rank(request_rank);
  builder_.add_tensor_type(tensor_type);
  builder_.add_request_type(request_type);
  return builder_.Finish();
}

inline flatbuffers::Offset<MPIRequest> CreateMPIRequestDirect(
    flatbuffers::FlatBufferBuilder &_fbb,
    int32_t request_rank = 0,
    MPIRequestType request_type = MPIRequestType_ALLREDUCE,
    MPIDataType tensor_type = MPIDataType_TF_MPI_UINT8,
    const char *tensor_name = nullptr,
    int32_t root_rank = 0,
    int32_t device = 0,
    const std::vector<int64_t> *tensor_shape = nullptr) {
  return horovod::tensorflow::wire::CreateMPIRequest(
      _fbb,
      request_rank,
      request_type,
      tensor_type,
      tensor_name ? _fbb.CreateString(tensor_name) : 0,
      root_rank,
      device,
      tensor_shape ? _fbb.CreateVector<int64_t>(*tensor_shape) : 0);
}

struct MPIResponse FLATBUFFERS_FINAL_CLASS : private flatbuffers::Table {
  enum {
    VT_RESPONSE_TYPE = 4,
    VT_TENSOR_NAME = 6,
    VT_ERROR_MESSAGE = 8,
    VT_DEVICES = 10,
    VT_TENSOR_SIZES = 12
  };
  MPIResponseType response_type() const {
    return static_cast<MPIResponseType>(GetField<int8_t>(VT_RESPONSE_TYPE, 0));
  }
  const flatbuffers::String *tensor_name() const {
    return GetPointer<const flatbuffers::String *>(VT_TENSOR_NAME);
  }
  const flatbuffers::String *error_message() const {
    return GetPointer<const flatbuffers::String *>(VT_ERROR_MESSAGE);
  }
  const flatbuffers::Vector<int32_t> *devices() const {
    return GetPointer<const flatbuffers::Vector<int32_t> *>(VT_DEVICES);
  }
  const flatbuffers::Vector<int64_t> *tensor_sizes() const {
    return GetPointer<const flatbuffers::Vector<int64_t> *>(VT_TENSOR_SIZES);
  }
  bool Verify(flatbuffers::Verifier &verifier) const {
    return VerifyTableStart(verifier) &&
           VerifyField<int8_t>(verifier, VT_RESPONSE_TYPE) &&
           VerifyField<flatbuffers::uoffset_t>(verifier, VT_TENSOR_NAME) &&
           verifier.Verify(tensor_name()) &&
           VerifyField<flatbuffers::uoffset_t>(verifier, VT_ERROR_MESSAGE) &&
           verifier.Verify(error_message()) &&
           VerifyField<flatbuffers::uoffset_t>(verifier, VT_DEVICES) &&
           verifier.Verify(devices()) &&
           VerifyField<flatbuffers::uoffset_t>(verifier, VT_TENSOR_SIZES) &&
           verifier.Verify(tensor_sizes()) &&
           verifier.EndTable();
  }
};

struct MPIResponseBuilder {
  flatbuffers::FlatBufferBuilder &fbb_;
  flatbuffers::uoffset_t start_;
  void add_response_type(MPIResponseType response_type) {
    fbb_.AddElement<int8_t>(MPIResponse::VT_RESPONSE_TYPE, static_cast<int8_t>(response_type), 0);
  }
  void add_tensor_name(flatbuffers::Offset<flatbuffers::String> tensor_name) {
    fbb_.AddOffset(MPIResponse::VT_TENSOR_NAME, tensor_name);
  }
  void add_error_message(flatbuffers::Offset<flatbuffers::String> error_message) {
    fbb_.AddOffset(MPIResponse::VT_ERROR_MESSAGE, error_message);
  }
  void add_devices(flatbuffers::Offset<flatbuffers::Vector<int32_t>> devices) {
    fbb_.AddOffset(MPIResponse::VT_DEVICES, devices);
  }
  void add_tensor_sizes(flatbuffers::Offset<flatbuffers::Vector<int64_t>> tensor_sizes) {
    fbb_.AddOffset(MPIResponse::VT_TENSOR_SIZES, tensor_sizes);
  }
  MPIResponseBuilder(flatbuffers::FlatBufferBuilder &_fbb)
        : fbb_(_fbb) {
    start_ = fbb_.StartTable();
  }
  MPIResponseBuilder &operator=(const MPIResponseBuilder &);
  flatbuffers::Offset<MPIResponse> Finish() {
    const auto end = fbb_.EndTable(start_, 5);
    auto o = flatbuffers::Offset<MPIResponse>(end);
    return o;
  }
};

inline flatbuffers::Offset<MPIResponse> CreateMPIResponse(
    flatbuffers::FlatBufferBuilder &_fbb,
    MPIResponseType response_type = MPIResponseType_ALLREDUCE,
    flatbuffers::Offset<flatbuffers::String> tensor_name = 0,
    flatbuffers::Offset<flatbuffers::String> error_message = 0,
    flatbuffers::Offset<flatbuffers::Vector<int32_t>> devices = 0,
    flatbuffers::Offset<flatbuffers::Vector<int64_t>> tensor_sizes = 0) {
  MPIResponseBuilder builder_(_fbb);
  builder_.add_tensor_sizes(tensor_sizes);
  builder_.add_devices(devices);
  builder_.add_error_message(error_message);
  builder_.add_tensor_name(tensor_name);
  builder_.add_response_type(response_type);
  return builder_.Finish();
}

inline flatbuffers::Offset<MPIResponse> CreateMPIResponseDirect(
    flatbuffers::FlatBufferBuilder &_fbb,
    MPIResponseType response_type = MPIResponseType_ALLREDUCE,
    const char *tensor_name = nullptr,
    const char *error_message = nullptr,
    const std::vector<int32_t> *devices = nullptr,
    const std::vector<int64_t> *tensor_sizes = nullptr) {
  return horovod::tensorflow::wire::CreateMPIResponse(
      _fbb,
      response_type,
      tensor_name ? _fbb.CreateString(tensor_name) : 0,
      error_message ? _fbb.CreateString(error_message) : 0,
      devices ? _fbb.CreateVector<int32_t>(*devices) : 0,
      tensor_sizes ? _fbb.CreateVector<int64_t>(*tensor_sizes) : 0);
}

}  // namespace wire
}  // namespace tensorflow
}  // namespace horovod

#endif  // FLATBUFFERS_GENERATED_MPIMESSAGE_HOROVOD_TENSORFLOW_WIRE_H_
