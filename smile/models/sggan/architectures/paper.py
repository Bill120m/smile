import functools

import tensorflow as tf

from smile.ops import get_normalization_fn


# TODO: Change initializer? Not specified in paper.

def conv(x, d, k, s, use_bias=False, padding="same"):
    return tf.layers.conv2d(
        x,
        kernel_size=(k, k),
        strides=(s, s),
        filters=d,
        activation=None,
        kernel_initializer=tf.truncated_normal_initializer(stddev=0.02),
        use_bias=use_bias,
        padding=padding)


def dconv(x, d, k, s, use_bias=False):
    return tf.layers.conv2d_transpose(
        x,
        kernel_size=(k, k),
        strides=(s, s),
        filters=d,
        activation=None,
        kernel_initializer=tf.truncated_normal_initializer(stddev=0.02),
        use_bias=use_bias,
        padding="same")


def res_block(x, d, k, norm, activation):
    # TODO: reflect pad?
    x_orig = x
    x = activation(norm(conv(x, d, k, 1)))
    x = norm(conv(x, d, k, 1))
    return x + x_orig


def encoder(x, is_training, **hparams):

    activation = tf.nn.relu
    norm = get_normalization_fn("instancenorm", is_training)

    # TODO: norm or activation first? Paper says relu then norm, code the opposite

    net = x
    net = norm(activation(conv(net, 64, 7, 1)))
    net = norm(activation(conv(net, 128, 4, 2)))
    net = norm(activation(conv(net, 256, 4, 2)))

    return net


def bottleneck(z, is_training, **hparams):

    activation = tf.nn.relu
    norm = get_normalization_fn("instancenorm", is_training)

    # TODO: norm or activation first in resblock?
    # TODO: One or two convs in resblock?

    net = z
    net = res_block(net, 256, 3, norm, activation)
    net = res_block(net, 256, 3, norm, activation)
    net = res_block(net, 256, 3, norm, activation)
    net = res_block(net, 256, 3, norm, activation)
    net = res_block(net, 256, 3, norm, activation)
    net = res_block(net, 256, 3, norm, activation)

    return net


def decoder(z, x_orig, n_attributes, is_training, **hparams):

    activation = tf.nn.relu
    norm = get_normalization_fn("instancenorm", is_training)

    net = z
    net = norm(activation(dconv(net, 128, 4, 2)))

    def decoder_head():
        h = norm(activation(dconv(net, 64, 4, 2)))
        h = tf.concat((h, x_orig))
        h = tf.nn.tanh(conv(h, 3, 7, 1))
        return h

    return tuple(decoder_head() for _ in range(n_attributes))


def classifier_discriminator_shared(x, is_training, **hparams):

    activation = functools.partial(tf.nn.leaky_relu, alpha=0.2)

    net = x
    net = activation(conv(net, 64, 5, 2))
    net = activation(conv(net, 128, 5, 2))
    net = activation(conv(net, 256, 5, 2))
    net = activation(conv(net, 512, 5, 2))
    net = activation(conv(net, 512, 5, 2))
    net = activation(conv(net, 1024, 5, 2))

    return net


def classifier_private(h, n_attributes, is_training, **hparams):
    logits = conv(h, n_attributes, 2, 1, padding="valid")
    # TODO: Reshape?
    return logits


def discriminator_private(h, is_training, **hparams):
    logits = conv(h, 1, 3, 1)
    # TODO: Reshape?
    return logits
