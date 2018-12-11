https://bair.berkeley.edu/blog/2018/01/09/ray/

https://blog.csdn.net/Uwr44UOuQcNsUQb60zk2/article/details/79029868 (有人翻译了，蛋疼)

随着机器学习算法和技术的进步，越来越多的机器学习应用程序需要多台机器，并且必须利用并行性。但是，在集群上进行机器学习的基础设施仍然是临时的。虽然确实存在针对特定用例（例如，参数服务器或超参数搜索）和AI之外的高质量分布式系统的良好解决方案（例如，Hadoop或Spark），但是在边界开发算法的从业者通常从头开始构建他们自己的系统基础设施。这相当于许多多余的努力。

例如，采用概念上简单的算法，如进化策略进行强化学习。该算法大约有十几行伪代码，其Python实现并不需要太多。但是，在更大的机器或集群上有效地运行算法需要更多的软件工程。作者的实现涉及数千行代码，必须定义通信协议，消息序列化和反序列化策略以及各种数据处理策略。

Ray的目标之一是让从业者能够将在笔记本电脑上运行的原型算法转变为高性能的分布式应用程序，该应用程序可以在集群（或单个多核机器）上高效运行，而且代码行相对较少。这样的框架应该包括手动优化系统的性能优势，而无需用户推理调度，数据传输和机器故障。

## 人工智能的开源框架
与深度学习框架的关系：Ray与TensorFlow，PyTorch和MXNet等深度学习框架完全兼容，在许多应用程序中使用一个或多个深度学习框架和Ray是很自然的（例如，我们的强化学习库使用TensorFlow和PyTorch严重）。

与其他分布式系统的关系：目前使用了许多流行的分布式系统，但其中大多数都没有考虑到AI应用程序而构建，缺乏支持和表达AI应用程序的API所需的性能。今天的分布式系统缺少以下功能（以各种组合）：
* 支持毫秒级任务和每秒数百万个任务
* 嵌套并行（在任务中并行化任务，例如，在超参数搜索中的并行模拟）（参见下图）
* 在运行时动态确定的任意任务依赖性（例如，以避免等待慢工作者）
* 在共享可变状态下操作的任务（例如，神经网络权重或模拟器）
* 支持异构资源（CPU，GPU等）

![avatar](https://bair.berkeley.edu/static/blog/ray/task_hier.png)

嵌套并行性的一个简单示例。 一个应用程序运行两个并行实验（每个实验都是一个长期运行的任务），每个实验都运行许多并行模拟（每个实验也是一项任务）。

使用Ray有两种主要方式：通过其较低级别的API和更高级别的库。 较高级别的库构建在较低级别的API之上。 目前，这些包括Ray RLlib，一个可扩展的强化学习库和Ray.tune，一个高效的分布式超参数搜索库。

## Ray低级API
Ray API的目标是使表达非常通用的计算模式和应用程序变得自然而不局限于像MapReduce这样的固定模式。

### 动态任务图
Ray应用程序或作业中的基础原语是动态任务图。 这与TensorFlow中的计算图非常不同。 而在TensorFlow中，计算图表示神经网络并且在单个应用程序中执行多次，在Ray中，任务图表示整个应用程序并且仅执行一次。 任务图预先不知道。 它在应用程序运行时动态构建，并且一个任务的执行可以触发创建更多任务。

![avatar](https://bair.berkeley.edu/static/blog/ray/task_graph.png)
一个示例计算图。白色椭圆表示任务，蓝色框表示对象。箭头表示任务依赖于对象或任务创建对象。

任意Python函数可以作为任务执行，它们可以任意依赖于其他任务的输出。这在下面的示例中说明。
```
# Define two remote functions. Invocations of these functions create tasks
# that are executed remotely. 定义两个远程功能。 这些函数的调用创建了远程执行的任务。

@ray.remote
def multiply(x, y):
    return np.dot(x, y)

@ray.remote
def zeros(size):
    return np.zeros(size)

# Start two tasks in parallel. These immediately return futures and the
# tasks are executed in the background.并行启动两个任务。 这些立即返回futures，任务在后台执行。
x_id = zeros.remote((100, 100))
y_id = zeros.remote((100, 100))

# Start a third task. This will not be scheduled until the first two
# tasks have completed. 开始第三项任务。 在前两个任务完成之前，不会安排此操作。
z_id = multiply.remote(x_id, y_id)

# Get the result. This will block until the third task completes.
z = ray.get(z_id)
```

### Actors
仅使用上述远程功能和任务无法完成的一件事是让多个任务在相同的共享可变状态下运行。 这出现在机器学习的多个上下文中，其中共享状态可以是模拟器的状态，神经网络的权重或者完全不同的东西。 Ray使用actor抽象来封装多个任务之间共享的可变状态。 这是一个如何使用Atari模拟器完成此操作的玩具示例。
```
import gym

@ray.remote
class Simulator(object):
    def __init__(self):
        self.env = gym.make("Pong-v0")
        self.env.reset()

    def step(self, action):
        return self.env.step(action)

# Create a simulator, this will start a remote process that will run
# all methods for this actor.创建一个模拟器，这将启动一个远程进程，该进程将运行此actor的所有方法。
simulator = Simulator.remote()

observations = []
for _ in range(4):
    # Take action 0 in the simulator. This call does not block and
    # it returns a future.在模拟器中执行操作0。 此调用不会阻止，它会返回future。
    observations.append(simulator.step.remote(0))
```
虽然简单，但actor可以非常灵活的方式使用。 例如，actor可以封装模拟器或神经网络策略，它可以用于分布式培训（与参数服务器一样）或用于实时应用程序中的策略服务。

![avatar](https://bair.berkeley.edu/static/blog/ray/param_actor.png)
左：为多个客户端进程提供预测/操作的actor。右：多个参数服务器参与者使用多个工作进程执行分布式培训。

### Parameter server example
参数服务器可以实现为Ray actor，如下所示:
```
@ray.remote
class ParameterServer(object):
    def __init__(self, keys, values):
        # These values will be mutated, so we must create a local copy.
        # 这些值将被突变，因此我们必须创建一个本地副本。
        values = [value.copy() for value in values]
        self.parameters = dict(zip(keys, values))

    def get(self, keys):
        return [self.parameters[key] for key in keys]

    def update(self, keys, values):
        # This update function adds to the existing values, but the update
        # function can be defined arbitrarily.
        # 此更新功能添加到现有值，但更新功能可以任意定义。
        for key, value in zip(keys, values):
            self.parameters[key] += value
```
要实例化参数服务器，请执行以下操作。
```
parameter_server = ParameterServer.remote(initial_keys, initial_values)
```
To create four long-running workers that continuously retrieve and update the parameters, do the following.
要创建四个持续检索和更新参数的长时间运行的工作程序，请执行以下操作。
```
@ray.remote
def worker_task(parameter_server):
    while True:
        keys = ['key1', 'key2', 'key3']
        # Get the latest parameters.
        values = ray.get(parameter_server.get.remote(keys))
        # Compute some parameter updates.
        updates = …
        # Update the parameters.
        parameter_server.update.remote(keys, updates)

# Start 4 long-running tasks.
for _ in range(4):
    worker_task.remote(parameter_server)
```


