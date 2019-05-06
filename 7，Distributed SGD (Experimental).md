Ray includes an implementation of synchronous distributed stochastic gradient descent (SGD), which is competitive in performance with implementations in Horovod and Distributed TensorFlow.

Ray SGD is built on top of the Ray task and actor abstractions to provide seamless integration into existing Ray applications.

Ray包括同步分布随机梯度下降（SGD）的实现，它在性能上与Horovod和分布式张量流的实现具有竞争力。

RAY SGD构建在RAY任务和actor抽象之上，以提供与现有RAY应用程序的无缝集成。

Under the hood, Ray SGD will create replicas of your model onto each hardware device (GPU) allocated to workers (controlled by num_workers). Multiple devices can be managed by each worker process (controlled by devices_per_worker). Each model instance will be in a separate TF variable scope. The DistributedSGD class coordinates the distributed computation and application of gradients to improve the model.

There are two distributed SGD strategies available for use:
strategy="simple": Gradients are averaged centrally on the driver before being applied to each model replica. This is a reference implementation for debugging purposes.
strategy="ps": Gradients are computed and averaged within each node. Gradients are then averaged across nodes through a number of parameter server actors. To pipeline the computation of gradients and transmission across the network, we use a custom TensorFlow op that can read and write to the Ray object store directly.

在hood下，RaySGD将在分配给工人（由num_worker控制）的每个硬件设备（GPU）上创建模型的副本。每个工作进程可以管理多个设备（由devices_per_worker控制）。每个模型实例将在单独的TF变量范围内。分布式SGD类协调了梯度的分布式计算和应用，以改进模型。

**有两种分布式SGD策略可供使用：**
>* strategy=“simple”：在应用于每个模型副本之前，在driver上对梯度进行平均。这是用于调试的参考实现。
>* strategy=“ps”：在每个节点内计算和平均梯度。然后通过一些参数服务器actors在节点间平均梯度。为了在网络上传输梯度计算和传输，我们使用一个定制的TensorFlow op，它可以直接读写到Ray object store。

Note that when num_workers=1, only local allreduce will be used and the choice of distributed strategy is irrelevant.

请注意，当num_workers = 1时，将仅使用本地allreduce，并且分布式策略的选择无关紧要。
