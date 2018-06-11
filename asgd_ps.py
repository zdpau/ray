from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import time

import ray
import model

parser = argparse.ArgumentParser(description="Run the asynchronous parameter "
                                             "server example.")
parser.add_argument("--num-workers", default=4, type=int,
                    help="The number of workers to use.")
parser.add_argument("--redis-address", default=None, type=str,
                    help="The Redis address of the cluster.")


@ray.remote
class ParameterServer(object):
    def __init__(self, keys, values):
        values = [value.copy() for value in values]
        self.weights = dict(zip(keys, values))

    def push(self, keys, values):
        for key, value in zip(keys, values):
            self.weights[key] += value

    def pull(self, keys):
        return [self.weights[key] for key in keys]


@ray.remote
def worker_task(ps, worker_index, batch_size=50):
    mnist = model.download_mnist_retry(seed=worker_index)

    net = model.SimpleCNN()
    keys = net.get_weights()[0]

    while True:
        weights = ray.get(ps.pull.remote(keys))
        net.set_weights(keys, weights)

        xs, ys = mnist.train.next_batch(batch_size)
        gradients = net.compute_update(xs, ys)
        ps.push.remote(keys, gradients)


if __name__ == "__main__":
    args = parser.parse_args()

    ray.init(redis_address=args.redis_address)

    net = model.SimpleCNN()
    all_keys, all_values = net.get_weights()
    ps = ParameterServer.remote(all_keys, all_values)

    worker_tasks = [worker_task.remote(ps, i) for i in range(args.num_workers)]

    mnist = model.download_mnist_retry()

    i = 0
    while True:
        current_weights = ray.get(ps.pull.remote(all_keys))
        net.set_weights(all_keys, current_weights)
        test_xs, test_ys = mnist.test.next_batch(1000)
        accuracy = net.compute_accuracy(test_xs, test_ys)
        print("Iteration {}: accuracy is {}".format(i, accuracy))
        i += 1
        time.sleep(1)
