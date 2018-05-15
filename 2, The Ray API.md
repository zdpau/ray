# starting ray
ray有两种主要的使用方式。首先，您可以启动所有相关的Ray进程，并在单个脚本的范围内全部关闭它们。其次，您可以连接并使用现有的Ray群集。
### 在脚本中启动和停止集群
一个用例是在您调用ray.init时启动所有相关的Ray进程，并在脚本退出时关闭它们。这些进程包括本地和全局调度程序，对象存储和对象管理器，Redis服务器等。

**注意**：这种方法仅限于一台机器。

可以用下面的：
```
ray.init()
```
如果机器上有可用的GPU，则应使用num_gpus参数来指定。同样，您也可以使用num_cpus指定CPU的数量。
```
ray.init(num_cpus=20, num_gpus=2)
```
默认情况下，Ray将使用psutil.cpu_count（）来确定CPU的数量。Ray也会尝试自动确定GPU的数量。
与其考虑每个节点上的“worker”的进程数量，我们更愿意考虑每个节点上CPU和GPU资源的数量，并提供无限的worker pool的幻想(the illusion of an infinite pool of workers)。根据资源的可用性将任务分配给工人，以避免争用，而不是基于可用工作进程的数量。
### 连接到现有群集
一旦Ray群集启动，您需要连接的唯一东西就是群集中Redis服务器的地址。在这种情况下，您的脚本不会启动或关闭任何进程。集群及其所有进程可以在多个脚本和多个用户之间共享。要做到这一点，您只需要知道群集的Redis服务器的地址。这可以通过如下命令完成。
```
ray.init(redis_address="12.345.67.89:6379")
```
在这种情况下，您不能在ray.init中指定num_cpus或num_gpus，因为该信息在启动群集时传递到群集中，而不是在脚本启动时传递。

查看有关如何在多个节点上启动Ray群集的说明。
> ray.init(redis_address=None, node_ip_address=None, object_id_seed=None, num_workers=None, driver_mode=0, redirect_worker_output=False, redirect_output=True, num_cpus=None, num_gpus=None, resources=None, num_custom_resource=None, num_redis_shards=None, redis_max_clients=None, plasma_directory=None, huge_pages=False, include_webui=True, object_store_memory=None, use_raylet=False)
连接到现有的Ray群集或启动并连接到它。

该方法处理两种情况。一个Ray集群已经存在，我们只需将该driver附加到它，或者我们启动与Ray集群关联的所有进程并附加到新启动的集群。

参数：
* node_ip_address（str） - 我们所在节点的IP地址。
* redis_address（str） - 要连接到的Redis服务器的地址。如果未提供此地址，则此命令将启动Redis，全局调度程序，本地调度程序，a plasma store, a plasma manager和一些worker。它还会在Python退出时终止这些进程。
* object_id_seed（int） - 用于播种确定性的对象ID生成。可以在同一作业的多次运行中使用相同的值，以便以一致的方式生成对象ID。但是，相同的ID不应该用于不同的工作。
* num_workers（int） - 要启动的工人数量。这仅在未提供redis_address的情况下提供。
* driver_mode（bool） - 启动driver的模式。这应该是ray.SCRIPT_MODE，ray.PYTHON_MODE和ray.SILENT_MODE之一。
* redirect_worker_output - 如果应将工作进程的stdout和stderr重定向到文件，则为true。
* num_cpus（int） - 用户希望所有本地调度程序配置的cpus数
* num_gpus（int） - 用户希望所有本地调度程序配置的gpus数。
* resource - 将资源名称映射到可用资源数量的字典
* num_redis_shards - 除主Redis分片以外的Redis分片数。
* redis_max_clients - 如果提供，请尝试使用此maxclients号码配置Redis。
* plasma_directory - 将创建Plasma存储器映射文件的目录。
* huge_pages - 布尔标志，指示是否启动具有hugetlbfs支持的Object Store。需要plasma_directory。
* include_webui - 布尔标志，指示是否启动Web UI，这是一个Jupyter笔记本。
* object_store_memory - 用来启动对象存储器的内存量（以字节为单位）。
* use_raylet - 如果应该使用新的Raylet代码路径，则为true。这还不支持。

**Return**：有关启动的进程的地址信息。
### 定义远程功能
远程功能用于创建任务。要定义一个远程函数，@ ray.remote装饰器放置在函数定义上。

然后可以用f.remote调用该函数。调用该函数将创建一个任务，该任务将由Ray群集中的某个工作进程调度并执行。该调用将返回一个代表任务的最终返回值的对象ID（本质上是未来）。具有对象ID的任何人都可以检索其值，而不管执行任务的位置（请参阅从对象ID获取值）。

任务执行时，其输出将被序列化为一串字节并存储在对象存储中。

请注意，远程函数的参数可以是值或对象ID。
```
@ray.remote
def f(x):
    return x + 1

x_id = f.remote(0)
ray.get(x_id)  # 1

y_id = f.remote(x_id)
ray.get(y_id)  # 2
```
如果你想要一个远程函数返回多个对象ID，你可以通过将num_return_vals参数传递给远程装饰器来实现。
```
@ray.remote(num_return_vals=2)
def f():
    return 1, 2

x_id, y_id = f.remote()
ray.get(x_id)  # 1
ray.get(y_id)  # 2
```
```
ray.remote(*args, **kwargs)
```
这个装饰器用于定义远程函数并定义参与者。

参数：
* num_return_vals（int） - 对此函数的调用应返回的对象ID的数量。
* num_cpus（int） - 执行此函数所需的CPU数量。 
* num_gpus（int） - 执行此函数所需的GPU数量。
* 资源 - 将资源名称映射到所需资源数量的字典。
* max_calls（int） - 在需要重新启动worker之前可以在worker上运行的此类任务的最大数量。
* checkpoint_interval（int） - 在actor状态的检查点之间运行的任务数。
### 从对象ID获取值
通过调用对象ID上的ray.get，可以将对象ID转换为对象。请注意，ray.get接受单个对象ID或对象ID列表。
```
@ray.remote
def f():
    return {'key1': ['value']}

# Get one object ID.
ray.get(f.remote())  # {'key1': ['value']}

# Get a list of object IDs.
ray.get([f.remote() for _ in range(2)])  # [{'key1': ['value']}, {'key1': ['value']}]
```
#### Numpy arrays
Numpy数组比其他数据类型更有效，因此**尽可能使用numpy数组**。

作为序列化对象一部分的任何numpy数组都不会被复制出对象存储。它们将保留在对象存储中，并且所得到的反序列化对象将只是一个指向对象存储内存中相关位置的指针。

由于对象存储中的对象是不可变的，这意味着如果您想要对由远程函数返回的numpy数组进行变异，则必须先将其复制。
```
ray.get(object_ids, worker=<ray.worker.Worker object>)
```
*从对象存储中获取远程对象或远程对象的列表。

此方法阻塞，直到对象ID对应的对象在本地对象存储中可用。如果此对象不在本地对象存储中，则它将从具有该对象的对象存储中运送（一旦创建该对象）。如果object_ids是一个列表，则将返回列表中每个对象所对应的对象。

> 参数：object_ids - 要获取的对象的对象ID或要获取的对象ID的列表。 
  返回：一个Python对象或一个Python对象列表。
### Putting objects in the object store将对象放入对象存储区
对象放置在对象存储中的主要方式是由任务返回。但是，也可以使用ray.put直接在对象存储中放置对象。
```
x_id = ray.put(1)
ray.get(x_id)  # 1
```
使用ray.put的主要原因是您想要将相同的大对象传递给多个任务。通过首先执行ray.put，然后将生成的对象ID传递给每个任务，大对象只会复制到对象存储中一次，而当我们直接传入对象时，它将被复制多次。
```
import numpy as np

@ray.remote
def f(x):
    pass

x = np.zeros(10 ** 6)

# Alternative 1: Here, x is copied into the object store 10 times.
[f.remote(x) for _ in range(10)]

# Alternative 2: Here, x is copied into the object store once.
x_id = ray.put(x)
[f.remote(x_id) for _ in range(10)]
```
请注意，在几种情况下，ray.put在hood(引擎罩)下被调用。
* 它被任务返回的值调用。 通常需要根据不同任务何时完成来调整正在执行的计算。
* 它被调用到任务的参数上，除非参数是Python基元(primitives)，如整数或短字符串，列表，元组或字典。
```
ray.put(value, worker=<ray.worker.Worker object>)
```
> 将对象存储在对象存储中。 
> 参数：value - 要存储的Python对象。 
> 返回：分配给此值的对象ID。
### Waiting for a subset of tasks to finish
通常需要根据不同任务何时完成来调整正在执行的计算。例如，如果一组任务每个都需要不同的时间长度，并且可以按照任意顺序处理它们的结果，那么只需按照它们完成的顺序处理结果就很有意义。在其他设置中，放弃可能不需要结果的失败任务是有意义的。

为此，我们引入ray.wait基元，该基元获取对象ID列表，并在它们的子集可用时返回。默认情况下，它会阻塞直到有单个对象可用，但可以指定num_returns值以等待不同的数字。如果超时参数被传入，它将会阻塞最多几毫秒，并且可能会返回一个列表数少于num_returns的列表。

ray.wait函数返回两个列表。第一个列表是可用对象的对象ID列表（长度至多为num_returns），而第二个列表是剩余对象ID的列表，所以这两个列表的组合等于传入到ray.wait的列表（直至排序）。
```
import time
import numpy as np

@ray.remote
def f(n):
    time.sleep(n)
    return n

# Start 3 tasks with different durations.
results = [f.remote(i) for i in range(3)]
# Block until 2 of them have finished.
ready_ids, remaining_ids = ray.wait(results, num_returns=2)

# Start 5 tasks with different durations.
results = [f.remote(i) for i in range(3)]
# Block until 4 of them have finished or 2.5 seconds pass.
ready_ids, remaining_ids = ray.wait(results, num_returns=4, timeout=2500)
```
使用这个构造很容易创建一个无限循环，其中执行多个任务，并且每当一个任务完成时，就会启动一个新任务。
```
@ray.remote
def f():
    return 1

# Start 5 tasks.
remaining_ids = [f.remote() for i in range(5)]
# Whenever one task finishes, start a new one.
for _ in range(100):
    ready_ids, remaining_ids = ray.wait(remaining_ids)
    # Get the available object and do something with it.
    print(ray.get(ready_ids))
    # Start a new task.
    remaining_ids.append(f.remote())
```
```
ray.wait(object_ids, num_returns=1, timeout=None, worker=<ray.worker.Worker object>)
```
返回已准备好的ID列表和不是的ID列表。

如果设置了超时，则当请求的ID数量准备就绪或达到超时时，函数返回，以先发生者为准。如果未设置，则该函数将一直等待，直到该对象数量准备就绪，并返回确切数量的object_id。

此方法返回两个列表。第一个列表由对应于存储在对象存储中的对象的对象ID组成。第二个列表对应于其余的对象ID（可能或可能没有准备好）。

参数： 
* object_ids（List [ObjectID]） - 可能或可能未准备好的对象的对象ID的列表。请注意，这些ID必须是唯一的。 
* num_returns（int） - 应返回的对象ID的数量。
* timeout（int） - 返回之前等待的最大时间量（以毫秒为单位）。

返回：
* 准备好的对象ID列表和剩余对象列表 标识。（A list of object IDs that are ready and a list of the remaining object）小写，IDs大写，不知道为什么。
### Viewing errors 查看错误
跟踪整个集群中不同流程中发生的错误可能具有挑战性。有一些机制可以帮助解决这个问题。
1，如果一个任务抛出异常，该异常将被打印在driver进程的后台。
2，如果在创建对象之前父项任务抛出异常的对象标识上调用ray.get，则该异常将由ray.get重新引发。

这些错误也将在Redis中累积，并可通过ray.error_info访问。通常情况下，你不需要这样做，但这是可能的。
```
@ray.remote
def f():
    raise Exception("This task failed!!")

f.remote()  # An error message will be printed in the background.

# Wait for the error to propagate to Redis.
import time
time.sleep(1)

ray.error_info()  # This returns a list containing the error message.
```
ray.error_info（worker = <ray.worker.Worker object>） 返回有关失败任务的信息。
