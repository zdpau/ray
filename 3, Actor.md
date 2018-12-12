https://blog.csdn.net/u011254180/article/details/80352304 （有人翻译了）

# Actors
Ray中的远程功能应该被认为是功能性和无副作用。仅限于远程功能的情况下，我们可以为我们提供分布式功能编程（Restricting ourselves only to remote functions gives us distributed functional programming），这对于许多使用情况非常有用，但在实践中会受到一些限制。

Ray与演员一起扩展了数据流模型。 一个演员本质上是一个有状态的工作者（或服务）。 当一个新的actor被实例化时，一个新的worker被创建，并且该actor的方法被安排在该特定的worker上，并且可以访问并改变该worker的状态。
## Defining and creating an actor
考虑下面的简单例子。 ray.remote装饰器指示Counter类的实例将是actors。
```
@ray.remote
class Counter(object):
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1
        return self.value
```
为了实际创建一个actor，我们可以通过调用Counter.remote（）来实例化这个类。
```
a1 = Counter.remote()
a2 = Counter.remote()
```
当actor实例化时，会发生以下事件。

选择集群中的一个节点，并在该节点上（由该节点上的本地调度程序）创建一个worker进程，以便运行在该actor上调用的方法。
在该worker上创建一个Counter对象，并运行Counter构造函数。
## Using an actor
我们可以通过调用其方法来调度actor的任务。
```
a1.increment.remote()  # ray.get returns 1
a2.increment.remote()  # ray.get returns 1
```
当调用a1.increment.remote（）时，会发生以下事件。

1，创建一个任务。

2，该任务直接分配给driver的本地调度程序负责该actor的本地调度程序。因此，此调度过程绕过全局调度程序。

3，返回一个对象ID。

然后，我们可以调用ray.get来获取实际值。

同样，对a2.increment.remote（）的调用将生成一个计划在第二个Counter actor上的任务。由于这两个任务在不同的角色上运行，他们可以并行执行（请注意，只有actor method将被安排在actor角色上，常规的远程函数不会）。

另一方面，在同一个Counter actor上调用的方法按照它们被调用的顺序依次执行。因此它们可以相互共享状态，如下所示。
```
# Create ten Counter actors.
counters = [Counter.remote() for _ in range(10)]

# Increment each Counter once and get the results. These tasks all happen in
# parallel.
results = ray.get([c.increment.remote() for c in counters])
print(results)  # prints [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

# Increment the first Counter five times. These tasks are executed serially
# and share state.
results = ray.get([counters[0].increment.remote() for _ in range(5)])
print(results)  # prints [2, 3, 4, 5, 6]
```
## A More Interesting Actor Example
一个常见的模式是使用actors来封装由外部库或服务管理的可变状态。

Gym为许多模拟环境提供了一个界面，用于测试和培训强化学习代理。 这些模拟器是有状态的，使用这些模拟器的任务必须改变它们的状态。 我们可以使用actor来封装这些模拟器的状态。
```
import gym

@ray.remote
class GymEnvironment(object):
    def __init__(self, name):
        self.env = gym.make(name)
        self.env.reset()

    def step(self, action):
        return self.env.step(action)

    def reset(self):
        self.env.reset()
```
然后，我们可以实例化一个actor，并按如下方式安排该actor的任务。
```
pong = GymEnvironment.remote("Pong-v0")
pong.step.remote(0)  # Take action 0 in the simulator.
```
## Using GPUs on actors
一个常见的用例是包含一个神经网络的ａｃｔｏｒ。例如，假设我们已经导入了Tensorflow并创建了一个构建神经网络的方法。
```
import tensorflow as tf

def construct_network():
    x = tf.placeholder(tf.float32, [None, 784])
    y_ = tf.placeholder(tf.float32, [None, 10])

    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))
    y = tf.nn.softmax(tf.matmul(x, W) + b)

    cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))
    train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)
    correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(y_,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    return x, y_, train_step, accuracy
```
然后我们可以按如下方式为这个网络定义一个actor。
```
import os

# Define an actor that runs on GPUs. If there are no GPUs, then simply use
# ray.remote without any arguments and no parentheses.
@ray.remote(num_gpus=1)
class NeuralNetOnGPU(object):
    def __init__(self):
        # Set an environment variable to tell TensorFlow which GPUs to use. Note
        # that this must be done before the call to tf.Session.
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join([str(i) for i in ray.get_gpu_ids()])
        with tf.Graph().as_default():
            with tf.device("/gpu:0"):
                self.x, self.y_, self.train_step, self.accuracy = construct_network()
                # Allow this to run on CPUs if there aren't any GPUs.
                config = tf.ConfigProto(allow_soft_placement=True)
                self.sess = tf.Session(config=config)
                # Initialize the network.
                init = tf.global_variables_initializer()
                self.sess.run(init)

```
为了表明一个演员需要一个GPU，我们将num_gpus = 1传递给ray.remote。 请注意，为了实现这一点，Ray必须已经开始使用某些GPU，例如，通过ray.init（num_gpus = 2）。 否则，当您尝试使用NeuralNetOnGPU.remote（）实例化GPU版本时，会引发异常，说明系统中没有足够的GPU。

当actor创建时，它将有权访问允许通过ray.get_gpu_ids（）使用的GPU的ID的列表。 这是一个整数列表，如[]或[1]或[2,5,6]。 由于我们传入了ray.remote（num_gpus = 1），因此此列表将具有一个长度。

我们可以将这一切放在一起，如下所示。
```
import os
import ray
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

ray.init(num_gpus=8)

def construct_network():
    x = tf.placeholder(tf.float32, [None, 784])
    y_ = tf.placeholder(tf.float32, [None, 10])

    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))
    y = tf.nn.softmax(tf.matmul(x, W) + b)

    cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))
    train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)
    correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(y_,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    return x, y_, train_step, accuracy

@ray.remote(num_gpus=1)
class NeuralNetOnGPU(object):
    def __init__(self, mnist_data):
        self.mnist = mnist_data
        # Set an environment variable to tell TensorFlow which GPUs to use. Note
        # that this must be done before the call to tf.Session.
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join([str(i) for i in ray.get_gpu_ids()])
        with tf.Graph().as_default():
            with tf.device("/gpu:0"):
                self.x, self.y_, self.train_step, self.accuracy = construct_network()
                # Allow this to run on CPUs if there aren't any GPUs.
                config = tf.ConfigProto(allow_soft_placement=True)
                self.sess = tf.Session(config=config)
                # Initialize the network.
                init = tf.global_variables_initializer()
                self.sess.run(init)

    def train(self, num_steps):
        for _ in range(num_steps):
            batch_xs, batch_ys = self.mnist.train.next_batch(100)
            self.sess.run(self.train_step, feed_dict={self.x: batch_xs, self.y_: batch_ys})

    def get_accuracy(self):
        return self.sess.run(self.accuracy, feed_dict={self.x: self.mnist.test.images,
                                                       self.y_: self.mnist.test.labels})


# Load the MNIST dataset and tell Ray how to serialize the custom classes.
mnist = input_data.read_data_sets("MNIST_data", one_hot=True)

# Create the actor.
nn = NeuralNetOnGPU.remote(mnist)

# Run a few steps of training and print the accuracy.
nn.train.remote(100)
accuracy = ray.get(nn.get_accuracy.remote())
print("Accuracy is {}.".format(accuracy))
```
## Passing Around Actor Handles (Experimental)(还在试验中)
actor handle可以传递到其他任务。 要查看此示例，请查看异步参数服务器示例。 为了用一个简单的例子来说明这一点，考虑一个简单的actor定义。 此功能目前是实验性的，并受以下所述的限制。
```
@ray.remote
class Counter(object):
    def __init__(self):
        self.counter = 0

    def inc(self):
        self.counter += 1

    def get_counter(self):
        return self.counter
```
我们可以定义使用actor handle的远程函数（或者actor方法）。
```
@ray.remote
def f(counter):
    while True:
        counter.inc.remote()
```
如果我们实例化一个actor，我们可以将这个handle传递给各种任务。
```
counter = Counter.remote()

# Start some tasks that use the actor.
[f.remote(counter) for _ in range(4)]

# Print the counter value.
for _ in range(10):
    print(ray.get(counter.get_counter.remote()))
```
## Current Actor Limitations
我们正在努力解决以下问题。

1，演员生命周期管理：目前，当一个演员的原演员手柄超出范围时，会在该演员上安排一个任务来杀死演员进程（一旦所有先前任务完成运行，此新任务将运行）。如果最初的actor角色超出了作用域，这可能是一个问题，但角色仍然被已经传递了actor角色的任务使用。

2，返回actor角色：Actor角色当前不能从远程函数或actor角色返回。同样，ray.put不能在actor角色上调用。

3，重建被驱逐的角色对象：如果在由角色方法创建的被驱逐对象上调用ray.get，Ray当前不会重建对象。有关更多信息，请参阅有关容错的文档。

4，失去参与者的确定性重构：如果一个参与者由于节点失败而丢失，则参与者按照初始执行的顺序在新节点上重建。然而，同时安排在演员身上的新任务可能会在重新执行的任务之间执行。如果您的应用程序对状态一致性有严格的要求，这可能会成为问题。
