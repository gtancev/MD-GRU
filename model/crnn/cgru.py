import logging
from copy import deepcopy

import tensorflow as tf
from tensorflow.python.ops import variable_scope as vs

from helper import argget, check_if_kw_empty, compile_arguments
from model import batch_norm
from model.crnn import CRNNCell


class CGRUCell(CRNNCell):
    """Convolutional gated recurrent unit.

    This class processes n-d data along the last dimension using a gated recurrent unit, which uses n-1 d convolutions
    on its path along that last dimension to gather context from input and last state to produce the new state.
    Property defaults contains defaults for all properties of a CGRUCell that are the same for one MDGRU.
    param: add_x_bn: Enables batch normalization on inputs for gates
    param: add_h_bn: Enables batch normalization on last state for gates
    param: add_a_bn: Enables batch normalization for the candidate (both input and last state)
    param: resgrux: Enables residual learning on weighted input
    param: resgruh: Enables residual learning on weighted previous output / state
    param: use_dropconnect_on_state: Should dropconnect be used also for the candidate computation?
    """
    _defaults = {
        "add_x_bn": False,
        "add_h_bn": False,
        "add_a_bn": False,
        "resgrux": False,
        "resgruh": False,
        "put_r_back": False,
        "use_dropconnect_on_state": False,
        "min_mini_batch": False,
        "istraining": tf.constant(True),
        "gate": tf.nn.sigmoid,
    }

    def __init__(self, *w, **kw):
        super(CGRUCell, self).__init__(*w, **kw)
        cgru_kw, kw = compile_arguments(CGRUCell, transitive=False, **kw)
        for k, v in cgru_kw.items():
            setattr(self, k, v)

        filter_shape_h_candidate = self.filter_size_h + [self._num_units] * 2
        filter_shape_h_gates = deepcopy(filter_shape_h_candidate)
        filter_shape_h_gates[-1] *= 2
        filter_shape_x_candidate = self.filter_size_x + [self.myshapes[0][-1], self._num_units]
        filter_shape_x_gates = deepcopy(filter_shape_x_candidate)
        filter_shape_x_gates[-1] *= 2

        self.dc_h_factor_gates = self._get_dropconnect(filter_shape_h_gates, self.dropconnecth,
                                                       "mydropconnecthgates")
        self.dc_h_factor_candidate = self._get_dropconnect(filter_shape_h_candidate, self.dropconnecth,
                                                           "mydropconnecthcandidate")
        self.dc_x_factor_gates = self._get_dropconnect(filter_shape_x_gates, self.dropconnectx,
                                                       "mydropconnectxgates")
        self.dc_x_factor_candidate = self._get_dropconnect(filter_shape_x_candidate, self.dropconnectx,
                                                           "mydropconnectxcandidate")

    def __call__(self, inputs, state, scope=None):
        """Perform one timestep of this cGRU.

        :param inputs: Input at timestep t.
        :param state: State at timestep t-1.
        :param scope: Optional named scope.
        :return: State at timestep t.
        """
        with vs.variable_scope(scope or type(self).__name__):
            with vs.variable_scope("Gates"):  # Reset gate and update gate.
                # We start with bias of 1.0 to not reset and not update.
                zrx, zrh, zrb = self._convlinear([inputs, state], self._num_units * 2, True, 1.0,
                                                 dropconnectx=self.dropconnectx, dropconnecth=self.dropconnecth,
                                                 dropconnectxmatrix=self.dc_x_factor_gates,
                                                 dropconnecthmatrix=self.dc_h_factor_gates,
                                                 strides=self.strides, orthogonal_init=False)
            # Perform batch norm on x and/or h of the gates if needed.
            if self.add_x_bn:
                zrx = batch_norm(zrx, "bnx", self.istraining, bias=None, m=self.min_mini_batch)
            if self.add_h_bn:
                zrh = batch_norm(zrh, "bnh", self.istraining, bias=None, m=self.min_mini_batch)
            # Add skip connections for input x and/or state h of the gates if needed.
            with vs.variable_scope('resgru'):
                if self.resgrux:
                    ntiles = self._num_units // inputs.get_shape().as_list()[-1]
                    if ntiles * inputs.get_shape().as_list()[-1] != self._num_units:
                        logging.getLogger('model').error(
                            '{}*{} is smaller than the actual number of outputs. (needs to be multiple){}'
                                .format(ntiles, inputs.get_shape().as_list()[-1], self._num_units))
                    else:
                        zrx = tf.tile(inputs, [1, ntiles * 2]) + zrx
                if self.resgruh:
                    zrh = tf.tile(state, [1, 2]) + zrh
            # Separate and activate update gate z and reset gate r
            z, r = tf.split(zrx + zrh + zrb, 2, axis=len(inputs.get_shape()) - 1)
            z, r = self.gate(z), self.gate(r)
            # Compute candidate \tilde{h}
            with vs.variable_scope("Candidate"):  # Proposal or Candidate.
                if self.put_r_back:
                    state *= r
                usedx = self.dropconnectx if self.use_dropconnect_on_state else None
                usedh = self.dropconnecth if self.use_dropconnect_on_state else None
                htx, hth, htb = self._convlinear([inputs, state],
                                                 self._num_units, True,
                                                 dropconnectxmatrix=self.dc_x_factor_candidate,
                                                 dropconnecthmatrix=self.dc_h_factor_candidate,
                                                 dropconnectx=usedx, dropconnecth=usedh,
                                                 strides=self.strides)
                if self.put_r_back:
                    htwb = htx + hth
                else:
                    htwb = htx + r * hth
            # Perform batch norm on candidate if needed.
            if self.add_a_bn:
                htwb = batch_norm(htwb, "bna", self.istraining, bias=None, m=self.min_mini_batch)
            # Update state/output.
            new_h = z * state + (1 - z) * self.crnn_activation(htwb + htb)
        return new_h, new_h
