# ray
## Tutorial
### 要使用Ray，您需要了解以下内容： 
* Ray如何异步执行任务以实现并行性。 
* Ray如何使用对象ID来表示不可变的远程对象。
## Overview
### Ray是一个基于Python的分布式执行引擎。可以在单台机器上运行相同的代码以实现高效的多处理，并且可将其用于大型计算的群集。使用Ray时，涉及几个过程。
* 多个 **worker** 进程执行任务并将结果存储在对象库中。每个worker都是一个独立的过程。
* 每个节点的一个 **对象存储（object store)** 将不可变对象存储在共享内存中，并允许worker在最小复制和反序列化的情况下有效地共享同一节点上的对象。
* 每个节点的一个 **本地调度程序(local scheduler)** 将任务分配给同一节点上的worker。 
* **全局调度程序（global scheduler)** 从本地调度程序接收任务并将其分配给其他本地调度程序。
* **driver**是用户控制的Python进程。例如，如果用户正在运行脚本或使用Python shell，那么driver是运行脚本或shell的Python进程。driver与worker类似，可以将任务提交到本地调度程序并从对象存储区获取对象，但不同之处在于本地调度程序不会将任务分配给要执行的driver。
* **Redis**服务器维护系统的大部分状态。例如，它会跟踪哪些对象在哪些机器上以及任务规范（而不是数据）上。它也可以直接用于调试目的查询。
## Immutable remote objects
#### 在Ray中，我们可以创建和计算对象。我们将这些对象称为远程对象，并使用对象ID(object IDs)来引用它们。远程对象存储在对象存储(object stores)中，并且集群中每个节点都有一个对象存储。在集群设置中，我们可能实际上不知道每个对象所在的机器。
#### 对象ID本质上是一个唯一的ID，可用于引用远程对象。如果您熟悉期货，我们的对象ID在概念上相似。
#### 我们假设远程对象是不可变的。也就是说，它们的值在创建后无法更改。这允许远程对象被复制到多个对象存储中，而不需要同步副本。
## Put and Get
#### 可以使用ray.get和ray.put命令在Python对象和对象ID之间进行转换，如下例所示。
#### 命令ray.put（x）将由worker process或driver process运行（driver process是运行脚本的进程）。它需要一个Python对象并将其复制到本地对象存储区（这里的本地方式表示在同一个节点上）。一旦对象被存储在对象存储中，它的值就不能被改变。
#### 另外，ray.put（x）返回一个对象ID，它本质上是一个可以用来引用新创建的远程对象的ID。如果我们用x_id = ray.put（x）将对象ID保存到变量中，那么我们可以将x_id传递给远程函数，并且这些远程函数将对相应的远程对象进行操作。
#### 命令`ray.get（x_id）`接受一个对象ID并从相应的远程对象创建一个Python对象。
#### 
#### 
#### 
#### 
#### 
#### 
