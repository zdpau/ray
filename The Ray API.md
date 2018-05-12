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
