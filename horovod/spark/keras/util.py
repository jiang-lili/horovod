# Copyright 2019 Uber Technologies, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import io

from distutils.version import LooseVersion

import h5py
import numpy as np
import tensorflow as tf

from horovod.runner.common.util import codec

from horovod.spark.common import constants, params
from horovod.spark.keras import optimizer, remote


BARE_KERAS = 'keras'
TF_KERAS = 'tf_keras'

_HAS_AUTOGRAPH = LooseVersion(tf.__version__) >= LooseVersion('1.15')


class TFKerasUtil(object):
    type = TF_KERAS

    @staticmethod
    def fit_fn(epochs):
        def fn(model, train_data, val_data, steps_per_epoch, validation_steps, callbacks, verbose):
            return model.fit(
                train_data,
                validation_data=val_data,
                steps_per_epoch=steps_per_epoch,
                validation_steps=validation_steps,
                callbacks=callbacks,
                verbose=verbose,
                epochs=epochs)
        return fn

    @staticmethod
    def make_dataset_fn(feature_columns, label_columns, sample_weight_col, metadata,
                        input_shapes, label_shapes, output_names, batch_size):
        # Check if any of the columns are only SparseVector
        has_sparse_col = any(metadata[col]['is_sparse_vector_only']
                             for col in label_columns + feature_columns)

        reshape = TFKerasUtil._reshape_fn(
            sample_weight_col, feature_columns, label_columns, metadata)

        prep_data_tf_keras = TFKerasUtil._prep_data_fn(
            has_sparse_col, sample_weight_col, feature_columns,
            label_columns, input_shapes, label_shapes, output_names)

        def fn(reader, shuffle_buffer_size, is_batch_reader, shuffle=False):
            from petastorm.tf_utils import make_petastorm_dataset

            dataset = make_petastorm_dataset(reader)
            if is_batch_reader:
                dataset = dataset.apply(tf.data.experimental.unbatch())

            if shuffle:
                dataset = dataset.shuffle(shuffle_buffer_size)

            # Decompress sparse data if necessary
            if has_sparse_col:
                dataset = dataset.batch(1).map(reshape)

            dataset = dataset.batch(batch_size).map(prep_data_tf_keras)
            return dataset
        return tf.autograph.experimental.do_not_convert(fn) if _HAS_AUTOGRAPH else fn

    @staticmethod
    def get_horovod():
        return TFKerasUtil.horovod_fn()()

    @staticmethod
    def horovod_fn():
        def fn():
            import horovod.tensorflow.keras as hvd
            return hvd
        return fn

    @staticmethod
    def keras():
        return TFKerasUtil.keras_fn()()

    @staticmethod
    def keras_fn():
        def fn():
            import tensorflow.keras as tf_keras
            return tf_keras
        return fn

    @staticmethod
    def serialize_optimizer(*args, **kwargs):
        return optimizer.serialize_tf_keras_optimizer(*args, **kwargs)

    @staticmethod
    def deserialize_optimizer(*args, **kwargs):
        return optimizer.deserialize_tf_keras_optimizer(*args, **kwargs)

    @staticmethod
    def serialize_model(*args, **kwargs):
        def serialize_keras_model(x):
            return _serialize_keras_model(x, TFKerasUtil.keras().models.save_model)

        return serialize_keras_model(*args, **kwargs)

    @staticmethod
    def deserialize_model(*args, **kwargs):
        return _deserialize_keras_model(*args, **kwargs)

    @staticmethod
    def serialize_param_value(*args, **kwargs):
        def _serialize_param(x, y):
            return _serialize_param_value(x, y,
                                          serialize_model_fn=TFKerasUtil.serialize_model,
                                          serialize_opt_fn=TFKerasUtil.serialize_optimizer)

        return _serialize_param(*args, **kwargs)

    @staticmethod
    def _reshape_fn(sample_weight_col, feature_columns, label_columns, metadata):
        CUSTOM_SPARSE = constants.CUSTOM_SPARSE
        custom_sparse_to_dense = _custom_sparse_to_dense_fn()

        def reshape(row):
            new_row = {}
            if sample_weight_col:
                new_row[sample_weight_col] = getattr(row, sample_weight_col)

            for col in feature_columns + label_columns:
                v = getattr(row, col)
                intermediate_format = metadata[col]['intermediate_format']
                if intermediate_format == CUSTOM_SPARSE:
                    reshaped_v = tf.reshape(v, [metadata[col]['max_size'] * 2 + 1])
                    v = custom_sparse_to_dense(reshaped_v, metadata[col]['shape'])

                new_row[col] = v
            return new_row

        return reshape

    @staticmethod
    def _prep_data_fn(has_sparse_col, sample_weight_col, feature_columns, label_columns,
                      input_shapes, label_shapes, output_names):
        def _get_from_dict(row, col):
            return row[col]

        def _get_from_named_tuple(row, col):
            return getattr(row, col)

        if has_sparse_col:
            get_col_from_row_fn = _get_from_dict
        else:
            get_col_from_row_fn = _get_from_named_tuple

        num_inputs = len(feature_columns)
        num_labels = len(label_columns)

        def as_tuple(v):
            return tuple(v) if len(v) > 1 else v[0]

        def prep(row):
            if sample_weight_col:
                sample_weight = get_col_from_row_fn(row, sample_weight_col)
                return (
                    tuple(
                        tf.reshape(get_col_from_row_fn(row, feature_columns[i]), input_shapes[i])
                        for i
                        in range(num_inputs)),
                    as_tuple([
                        tf.reshape(get_col_from_row_fn(row, label_columns[j]), label_shapes[j]) for
                        j
                        in range(num_labels)]),
                    {name: tf.reshape(sample_weight, [-1]) for name in output_names}
                )
            else:
                return (
                    tuple(
                        tf.reshape(get_col_from_row_fn(row, feature_columns[i]), input_shapes[i])
                        for i
                        in range(num_inputs)),
                    as_tuple([
                        tf.reshape(get_col_from_row_fn(row, label_columns[j]), label_shapes[j]) for
                        j
                        in range(num_labels)])
                )

        return prep


class BareKerasUtil(object):
    type = BARE_KERAS

    @staticmethod
    def fit_fn(epochs):
        def fn(model, train_data, val_data, steps_per_epoch, validation_steps, callbacks, verbose):
            return model.fit_generator(
                train_data,
                validation_data=val_data,
                steps_per_epoch=steps_per_epoch,
                validation_steps=validation_steps,
                callbacks=callbacks,
                verbose=verbose,
                epochs=epochs)

        return fn

    @staticmethod
    def make_dataset_fn(feature_columns, label_columns, sample_weight_col, metadata,
                        input_shapes, label_shapes, output_names, batch_size):
        batch_generator = BareKerasUtil._batch_generator_fn(
            feature_columns, label_columns, sample_weight_col,
            input_shapes, label_shapes, batch_size, metadata)

        def fn(reader, shuffle_buffer_size, shuffle=False):
            return batch_generator(reader, shuffle_buffer_size)

        return fn

    @staticmethod
    def get_horovod():
        return BareKerasUtil.horovod_fn()()

    @staticmethod
    def horovod_fn():
        def fn():
            import horovod.keras as hvd
            return hvd
        return fn

    @staticmethod
    def keras():
        return BareKerasUtil.keras_fn()()

    @staticmethod
    def keras_fn():
        def fn():
            import keras
            return keras
        return fn

    @staticmethod
    def serialize_optimizer(*args, **kwargs):
        return optimizer.serialize_bare_keras_optimizer(*args, **kwargs)

    @staticmethod
    def deserialize_optimizer(*args, **kwargs):
        return optimizer.deserialize_bare_keras_optimizer(*args, **kwargs)

    @staticmethod
    def serialize_model(*args, **kwargs):
        def serialize_keras_model(x):
            return _serialize_keras_model(x, BareKerasUtil.keras().models.save_model)

        return serialize_keras_model(*args, **kwargs)

    @staticmethod
    def deserialize_model(*args, **kwargs):
        return _deserialize_keras_model(*args, **kwargs)

    @staticmethod
    def serialize_param_value(*args, **kwargs):
        def _serialize_param(x, y):
            return _serialize_param_value(x, y,
                                          serialize_model_fn=BareKerasUtil.serialize_model,
                                          serialize_opt_fn=BareKerasUtil.serialize_optimizer)

        return _serialize_param(*args, **kwargs)

    @staticmethod
    def _batch_generator_fn(feature_columns, label_columns, sample_weight_col,
                            input_shapes, label_shapes, batch_size, metadata):
        prepare_data_bare_keras = BareKerasUtil._prepare_data_fn(metadata)

        cols = feature_columns + label_columns
        if sample_weight_col:
            cols.append(sample_weight_col)

        def batch_generator(reader, shuffle_buffer_size, shuffle=False):
            while True:
                num_rows_read_sofar = 0
                data = None
                while num_rows_read_sofar < shuffle_buffer_size:
                    # Each call to next reads one row group at a time. reader is an infinite
                    # generator and never ends
                    row_group_data = next(reader)
                    if not data:
                        data = {col: getattr(row_group_data, col) for col in cols}
                    else:
                        for col in cols:
                            data[col] = np.concatenate((data[col],
                                                        getattr(row_group_data, col)))
                    num_rows_read_sofar += row_group_data[0].shape[0]

                # Create a permutation of len of data and use it to shuffle each numpy array
                perm = np.random.permutation(num_rows_read_sofar) \
                    if shuffle else list(range(num_rows_read_sofar))

                inputs = [prepare_data_bare_keras(data[col][perm], col, shape) for col, shape
                          in zip(feature_columns, input_shapes)]
                labels = [prepare_data_bare_keras(data[col][perm], col, shape) for col, shape
                          in zip(label_columns, label_shapes)]

                num_outputs = len(label_columns)
                sample_weights = None
                if sample_weight_col:
                    sample_weights = data[sample_weight_col][perm]

                batch_count = int(len(inputs[0]) / batch_size)
                for i in range(0, batch_count):
                    if sample_weight_col:
                        # We use the same sample weight for all the outputs of the sample
                        sample_weight = sample_weights[i * batch_size:(i + 1) * batch_size]
                        sample_weight_for_batch = [sample_weight for i in range(num_outputs)]

                        yield (
                            [input[i * batch_size:(i + 1) * batch_size] for input in inputs],
                            [label[i * batch_size:(i + 1) * batch_size] for label in labels],
                            sample_weight_for_batch)
                    else:
                        yield (
                            [input[i * batch_size:(i + 1) * batch_size] for input in inputs],
                            [label[i * batch_size:(i + 1) * batch_size] for label in labels])

        return batch_generator

    @staticmethod
    def _prepare_data_fn(metadata):
        convert_custom_sparse_to_dense = BareKerasUtil._convert_custom_sparse_to_dense_fn()
        CUSTOM_SPARSE = constants.CUSTOM_SPARSE

        def prepare_data(rows, col, shape):
            intermediate_format = metadata[col]['intermediate_format']
            if intermediate_format != CUSTOM_SPARSE:
                return rows.reshape(shape)

            dense_rows = []
            shape_1d = metadata[col]['shape']
            for row in rows:
                dense_row = convert_custom_sparse_to_dense(row, shape_1d)
                dense_rows.append(dense_row)
            return np.array(dense_rows).reshape(shape)
        return prepare_data

    @staticmethod
    def _convert_custom_sparse_to_dense_fn():
        def convert_custom_sparse_to_dense(row, shape):
            size = int(row[0])
            dense_row = np.zeros(shape)
            dense_row[row[1:size + 1].astype(int)] = row[size + 1:2 * size + 1]
            return dense_row
        return convert_custom_sparse_to_dense


def is_instance_of_bare_keras_optimizer(opt):
    import keras
    return isinstance(opt, keras.optimizers.Optimizer)


def is_instance_of_bare_keras_model(model):
    import keras
    return isinstance(model, keras.models.Model)


def _serialize_keras_model(model, save_model_fn):
    """Serialize model into byte array encoded into base 64."""
    bio = io.BytesIO()
    with h5py.File(bio, 'w') as f:
        save_model_fn(model, f)
    return codec.dumps_base64(bio.getvalue())


def _deserialize_keras_model(model_bytes, load_model_fn):
    deserialize_keras_model = remote._deserialize_keras_model_fn()
    return deserialize_keras_model(model_bytes, load_model_fn)


def _serialize_param_value(param_name, param_val, serialize_model_fn, serialize_opt_fn):
    if param_val is None:
        return param_val

    if param_name in [params.EstimatorParams.backend.name, params.EstimatorParams.store.name]:
        # We do not serialize backend and store. These params have to be regenerated for each
        # run of the pipeline
        return None
    elif param_name == params.EstimatorParams.model.name:
        return serialize_model_fn(param_val)
    if param_name == params.EstimatorParams.optimizer.name:
        return serialize_opt_fn(param_val)
    else:
        return codec.dumps_base64(param_val)


def _custom_sparse_to_dense_fn():
    # TODO(fardin): ask petastorm team about codecs for sparse and dense vectors and see if that is
    # a better solution
    def custom_sparse_to_dense(custom_sparse_vec, dense_shape):
        # original sparse vector:   v = {1:2.0, 3:.4.5, 5:7.1}
        # custom sparse vector:     v = [3, 1, 3, 5, 2.0, 4.5, 7.1]
        # dense vector:             v = [0, 2.0, 0, 4.5, 0, 7.1]

        # Get the first element from custom_sparse_vec. This element is the size of
        # non-zero elements in the original sparse vector.
        sparse_vector_size = tf.cast(tf.gather(custom_sparse_vec, 0, axis=0), tf.int32)
        sparse_vector_size = tf.reshape(sparse_vector_size, [1])

        # get the first sparse_vector_size elements of the custom_sparse_vec which are the
        # indices
        indices_1d = tf.cast(
            tf.slice(custom_sparse_vec, begin=tf.constant([1]), size=sparse_vector_size),
            tf.int64)
        indices_reshaped = tf.reshape(indices_1d,
                                      tf.concat([sparse_vector_size, tf.constant([1])], 0))
        # have to pad the indices to match the expected format by the SparseTensor
        indices = tf.pad(indices_reshaped, [[0, 0], [1, 0]], "CONSTANT")

        # get the second sparse_vector_size elements of the custom_sparse_vec which are
        # the values
        begin_index = sparse_vector_size + tf.constant(1)
        values = tf.slice(custom_sparse_vec, begin=begin_index, size=sparse_vector_size)

        # construct a sparse vector with the indices and values
        dense_shape = [1, dense_shape]
        sparse_tensor = tf.sparse.SparseTensor(indices=indices, values=values,
                                               dense_shape=dense_shape)
        # convert the sparse vector into a dense vector
        return tf.sparse.to_dense(sparse_tensor)

    return custom_sparse_to_dense
