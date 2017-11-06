import tensorflow as tf


def generator(X, is_training):
    weight_initializer = tf.truncated_normal_initializer(stddev=0.02)

    def conv7_stride1_k(inputs, k):
        """7x7, 1 strided convolution with k filters and batch norm before activation."""
        padded = tf.pad(inputs, [[0, 0], [3, 3], [3, 3], [0, 0]], "reflect")
        return tf.layers.conv2d(
            padded,
            kernel_size=(7, 7),
            strides=(1, 1),
            filters=k,
            activation=None,
            kernel_initializer=weight_initializer,
            use_bias=False,
            padding="valid")

    def conv3_stride2_k(inputs, k):
        """3x3, 2 strided convolution with k filters and batch norm before activation."""
        return tf.layers.conv2d(
            inputs,
            kernel_size=(3, 3),
            strides=(2, 2),
            filters=k,
            activation=None,
            kernel_initializer=weight_initializer,
            use_bias=False,
            padding="same")

    def res_block(inputs, k):
        # Layer 1.
        padded1 = tf.pad(inputs, [[0, 0], [1, 1], [1, 1], [0, 0]], "reflect")
        conv1 = tf.layers.conv2d(
            padded1,
            kernel_size=(3, 3),
            strides=(1, 1),
            filters=k,
            activation=None,
            kernel_initializer=weight_initializer,
            use_bias=False,
            padding="valid")
        normalized1 = tf.contrib.layers.instance_norm(conv1)
        relu1 = tf.nn.relu(normalized1)

        # Layer 2.
        padded2 = tf.pad(relu1, [[0, 0], [1, 1], [1, 1], [0, 0]], "reflect")
        conv2 = tf.layers.conv2d(
            padded2,
            kernel_size=(3, 3),
            strides=(1, 1),
            filters=k,
            activation=None,
            kernel_initializer=weight_initializer,
            use_bias=False,
            padding="valid")
        normalized2 = tf.contrib.layers.instance_norm(conv2)
        return inputs + normalized2

    def deconv3_stride2_k(inputs, k):
        """3x3. 2 strided deconvolution (transposed convolution) with k filters."""
        return tf.layers.conv2d_transpose(
            inputs,
            kernel_size=(3, 3),
            strides=(2, 2),
            filters=k,
            activation=None,
            kernel_initializer=weight_initializer,
            use_bias=False,
            padding="same")

    relu = tf.nn.relu
    norm = tf.contrib.layers.instance_norm

    # Net definition.
    net = X
    net = relu(norm(conv7_stride1_k(net, 32)))
    net = relu(norm(conv3_stride2_k(net, 64)))
    net = relu(norm(conv3_stride2_k(net, 128)))
    for i in range(6):
        net = res_block(net, 128)
    net = relu(norm(deconv3_stride2_k(net, 64)))
    net = relu(norm(deconv3_stride2_k(net, 32)))
    net = tf.nn.tanh(conv7_stride1_k(net, 3))

    return net


def discriminator(X, is_training):
    weight_initializer = tf.truncated_normal_initializer(stddev=0.02)

    def conv4_stride2_k(inputs, k):
        return tf.layers.conv2d(
            inputs,
            kernel_size=(4, 4),
            strides=(2, 2),
            filters=k,
            activation=None,
            kernel_initializer=weight_initializer,
            use_bias=False,
            padding="same")

    lrelu = tf.nn.leaky_relu
    norm = tf.contrib.layers.instance_norm

    # Net definition.
    net = X
    net = lrelu(conv4_stride2_k(net, 64))
    net = lrelu(norm(conv4_stride2_k(net, 128)))
    net = lrelu(norm(conv4_stride2_k(net, 256)))
    net = lrelu(norm(conv4_stride2_k(net, 512)))
    net = tf.layers.conv2d(
        net,
        kernel_size=(4, 4),
        strides=(1, 1),
        filters=1,
        activation=None,
        padding="same")

    # Note: The discriminator returns a tensor T of shape (?, x, y, 1)
    # where each T_(i,j) corresponds to the discriminator's output for one
    # larger patch of the input image.
    # See https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix/issues/39

    return net
