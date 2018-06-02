本文档将介绍如何使用actors来实现简单的同步和异步参数服务器。要运行该应用程序，首先安装一些依赖项。
```
pip install tensorflow
```
你可以查看这个例子(链接)的代码。 这些示例可以运行如下。
```
# Run the asynchronous parameter server.
python ray/examples/parameter_server/async_parameter_server.py --num-workers=4

# Run the synchronous parameter server.
python ray/examples/parameter_server/sync_parameter_server.py --num-workers=4
```
请注意，这些示例使用分布式的actor操作符，这些操作符仍被视为实验性的。
## Asynchronous Parameter Server
异步参数服务器本身作为一个actor来实现，它expose了push和pull方法。
```
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
```
然后我们定义一个工作任务，它将参数服务器作为参数并向其提交任务。代码的结构如下所示。
```
@ray.remote
def worker_task(ps):
    while True:
        # Get the latest weights from the parameter server.
        weights = ray.get(ps.pull.remote(keys))

        # Compute an update.
        ...

        # Push the update to the parameter server.
        ps.push.remote(keys, update)
```
然后我们可以创建一个参数服务器并开始如下训练。
```
ps = ParameterServer.remote(keys, initial_values)
worker_tasks = [worker_task.remote(ps) for _ in range(4)]
```
## synchronous Parameter Server
参数服务器被实现为actor，它expose了方法apply_gradients和get_weights。通过根据worker的数量缩放学习速率来应用恒定线性缩放规则。（The parameter server is implemented as an actor, which exposes the methods apply_gradients and get_weights. A constant linear scaling rule is applied by scaling the learning rate by the number of workers.）
```
@ray.remote
class ParameterServer(object):
    def __init__(self, learning_rate):
        self.net = model.SimpleCNN(learning_rate=learning_rate)

    def apply_gradients(self, *gradients):
        self.net.apply_gradients(np.mean(gradients, axis=0))
        return self.net.variables.get_flat()

    def get_weights(self):
        return self.net.variables.get_flat()
```
worker是expose方法compute_gradients的actor。(Workers are actors which expose the method compute_gradients.)
```
@ray.remote
class Worker(object):
    def __init__(self, worker_index, batch_size=50):
        self.worker_index = worker_index
        self.batch_size = batch_size
        self.mnist = input_data.read_data_sets("MNIST_data", one_hot=True,
                                               seed=worker_index)
        self.net = model.SimpleCNN()

    def compute_gradients(self, weights):
        self.net.variables.set_flat(weights)
        xs, ys = self.mnist.train.next_batch(self.batch_size)
        return self.net.compute_gradients(xs, ys)
```
在给定参数服务器当前权重的情况下，计算梯度之间进行交替训练，并使用所产生的梯度更新参数服务器的权重。
```
while True:
    gradients = [worker.compute_gradients.remote(current_weights)
                 for worker in workers]
    current_weights = ps.apply_gradients.remote(*gradients)
```
这两个示例都使用单个actor服务器，但是他们可以很容易地扩展为跨多个参与者分解参数。(shard the parameters across multiple actors.)
