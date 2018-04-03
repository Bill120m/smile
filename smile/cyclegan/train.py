import argparse
import datetime
from pathlib import Path
from typing import List

import tensorflow as tf

from smile.cyclegan import CycleGAN
from smile.cyclegan.architectures import celeb
from smile.cyclegan.input import celeb_input_fn


tf.logging.set_verbosity(tf.logging.INFO)


def run_training(model_dir: Path,
                 X_paths: List[Path],
                 Y_paths: List[Path],
                 **hparams):

    model_dir.mkdir(parents=True, exist_ok=True)

    cycle_gan = CycleGAN(
        celeb_input_fn(X_paths, batch_size=hparams["batch_size"]),
        celeb_input_fn(Y_paths, batch_size=hparams["batch_size"]),
        celeb.generator,
        celeb.discriminator,
        **hparams)

    summary_writer = tf.summary.FileWriter(str(model_dir))

    with tf.train.MonitoredTrainingSession(checkpoint_dir=str(model_dir), save_summaries_secs=30) as sess:
        while not sess.should_stop():
            cycle_gan.train_step(sess, summary_writer)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--model-dir", required=False, help="directory for checkpoints etc")
    arg_parser.add_argument("-X", nargs="+", required=True, help="tfrecord files for first image domain")
    arg_parser.add_argument("-Y", nargs="+", required=True, help="tfrecord files for second image domain")
    arg_parser.add_argument("--batch-size", required=True, type=int, help="batch size")
    args = arg_parser.parse_args()

    hparams = {
        "batch_size": args.batch_size,
        "lambda_cyclic": 5.0,
        "use_history": False
    }

    ROOT_RUNS_DIR = Path("runs")
    if args.model_dir is None:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
        model_description = "_".join(f"{k}={hparams[k]}" for k in sorted(hparams.keys()))
        model_dir = ROOT_RUNS_DIR / Path(f"cyclegan_{timestamp}_{model_description}")
    else:
        model_dir = Path(args.model_dir)

    run_training(model_dir, args.X, args.Y, **hparams)

    # TODO: also see https://arxiv.org/pdf/1611.05507.pdf
    # TODO: Preprocess data to extract only face?
    # TODO: Add attention?
    # TODO: Try wgan-gp loss?
