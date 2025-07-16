# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from horovod.common.util import check_extension

check_extension('horovod.mxnet', 'HOROVOD_WITH_MXNET',
                __file__, 'mpi_lib')

from horovod.mxnet.functions import allgather_object, broadcast_object
from horovod.mxnet.mpi_ops import allgather
from horovod.mxnet.mpi_ops import allreduce, allreduce_
from horovod.mxnet.mpi_ops import alltoall
from horovod.mxnet.mpi_ops import broadcast, broadcast_
from horovod.mxnet.mpi_ops import init, shutdown
from horovod.mxnet.mpi_ops import is_initialized, start_timeline, stop_timeline
from horovod.mxnet.mpi_ops import size, local_size, rank, local_rank
from horovod.mxnet.mpi_ops import mpi_threads_supported, mpi_enabled, mpi_built
from horovod.mxnet.mpi_ops import gloo_enabled, gloo_built
from horovod.mxnet.mpi_ops import nccl_built, ddl_built, ccl_built, cuda_built, rocm_built

import mxnet as mx
import types
import warnings


# This is where Horovod's DistributedOptimizer wrapper for MXNet goes
class DistributedOptimizer(mx.optimizer.Optimizer):
    def __init__(self, optimizer, gradient_predivide_factor=1.0):
        if gradient_predivide_factor != 1.0 and rocm_built():
            raise ValueError('gradient_predivide_factor not supported yet with ROCm')

        self._optimizer = optimizer
        # Normalizing rescale_grad by Horovod size, which is equivalent to
        # performing average in allreduce, has better performance.
        self._optimizer.rescale_grad *= (gradient_predivide_factor / size())
        self._gradient_predivide_factor = gradient_predivide_factor

    def __getattr__(self, item):
        return getattr(self._optimizer, item)

    def create_state_multi_precision(self, index, weight):
        return self._optimizer.create_state_multi_precision(index, weight)

    def _do_allreduce(self, index, grad):
        if size() == 1: return

        if isinstance(index, (tuple, list)):
            for i in range(len(index)):
                allreduce_(grad[i], average=False,
                           name=str(index[i]), priority=-i,
                           prescale_factor=1.0 / self._gradient_predivide_factor)
        else:
            allreduce_(grad, average=False, name=str(index),
                       prescale_factor=1.0 / self._gradient_predivide_factor)

    def update(self, index, weight, grad, state):
        self._do_allreduce(index, grad)
        self._optimizer.update(index, weight, grad, state)

    def update_multi_precision(self, index, weight, grad, state):
        self._do_allreduce(index, grad)
        self._optimizer.update_multi_precision(index, weight, grad, state)

    def set_learning_rate(self, lr):
        self._optimizer.set_learning_rate(lr)

    def set_lr_mult(self, args_lr_mult):
        self._optimizer.set_lr_mult(args_lr_mult)

    def set_wd_mult(self, args_wd_mult):
        self._optimizer.set_wd_mult(args_wd_mult)


# DistributedTrainer, a subclass of MXNet gluon.Trainer.
# There are two differences between DistributedTrainer and Trainer:
# 1. DistributedTrainer calculates gradients using Horovod allreduce
#    API while Trainer does it using kvstore push/pull APIs;
# 2. DistributedTrainer performs allreduce(summation) and average
#    while Trainer only performs allreduce(summation).
class DistributedTrainer(mx.gluon.Trainer):
    """The distributed trainer for data parallel training.

    Arguments:
        params: dict of parameters to train
        optimizer: mx.optim.Optimizer. the choice of optimizer
        optimizer_params: hyper-parameter of the chosen optimizer
        gradient_predivide_factor: gradient_predivide_factor splits the averaging
              before and after the sum. Gradients are scaled by
              1.0 / gradient_predivide_factor before the sum and
              gradient_predivide_factor / size after the sum.
        prefix: the prefix of the parameters this trainer manages.
              If multiple trainers are used in the same program,
              they must be specified by different prefixes to avoid tensor name collision.
    """
    def __init__(self, params, optimizer, optimizer_params=None,
                 gradient_predivide_factor=1.0, prefix=None):
        if gradient_predivide_factor != 1.0 and rocm_built():
            raise ValueError('gradient_predivide_factor not supported yet with ROCm')
        if isinstance(optimizer, DistributedOptimizer):
            optimizer = optimizer._optimizer
            warnings.warn("DistributedTrainer does not take DistributedOptimizer "
                          "as its optimizer. We have unwrapped it for you.")

        super(DistributedTrainer, self).__init__(
            params, optimizer, optimizer_params=optimizer_params, kvstore=None)

        # _scale is used to check and set rescale_grad for optimizer in Trainer.step()
        # function. Normalizing it by Horovod size, which is equivalent to performing
        # average in allreduce, has better performance. 
        self._scale *= (gradient_predivide_factor / size())
        self._gradient_predivide_factor = gradient_predivide_factor
        assert prefix is None or isinstance(prefix, str)
        self._prefix = prefix if prefix else ""

    def _allreduce_grads(self):
        if size() == 1: return

        # In MXNet 2.0, param.name is no longer unique.
        # Meanwhile, since horovod requires Python 3.6, there is no need to sort
        # self._params as enumerating a python dict is always deterministic.
        for i, param in enumerate(self._params):
            if param.grad_req != 'null':
                allreduce_(param.list_grad()[0], average=False,
                           name=self._prefix + str(i), priority=-i,
                           prescale_factor=1.0 / self._gradient_predivide_factor)


# Wrapper to inject Horovod broadcast after parameter initialization
def _append_broadcast_init(param, root_rank, name):
    init_impl = getattr(param, '_init_impl')
    def wrapped_init_impl(self, *args, **kwargs):
        init_impl(*args, **kwargs)
        broadcast_(self.data(), root_rank=root_rank, name=name)
    return wrapped_init_impl


def broadcast_parameters(params, root_rank=0, prefix=None):
    """Broadcasts the parameters from root rank to all other processes.
    Typical usage is to broadcast the `Module.get_params()` or the
    `Block.collect_params()`.

    Arguments:
        params: One of the following:
            - dict of parameters to broadcast
            - ParameterDict to broadcast
        root_rank: The rank of the process from which parameters will be
                   broadcasted to all other processes.
        prefix: The prefix of the parameters to broadcast.
              If multiple `broadcast_parameters` are called in the same program,
              they must be specified by different prefixes to avoid tensor name collision.
    """
    if size() == 1: return

    tensors = []
    names = []
    assert prefix is None or isinstance(prefix, str)
    prefix = prefix if prefix else ""
    try:
        from mxnet.gluon.parameter import ParameterDict
        valid_types = (dict, ParameterDict)
    except ImportError:
        valid_types = (dict,)
    if isinstance(params, valid_types):
        for name, p in sorted(params.items()):
            try:
                if isinstance(p, mx.gluon.parameter.Parameter):
                    tensors.append(p.data())
                else:
                    tensors.append(p)
                names.append(prefix + str(name))
            except mx.gluon.parameter.DeferredInitializationError:
                # Inject wrapper method with post-initialization broadcast to
                # handle parameters with deferred initialization
                # we use the key of params instead of param.name, since
                # param.name is no longer unique in MXNet 2.0
                new_init = _append_broadcast_init(p, root_rank, prefix + str(name))
                p._init_impl = types.MethodType(new_init, p)
    else:
        raise ValueError('invalid params of type: %s' % type(params))

    # Run broadcasts.
    for tensor, name in zip(tensors, names):
        broadcast_(tensor, root_rank, name=name)
