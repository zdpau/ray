https://bair.berkeley.edu/blog/2018/01/09/ray/

随着机器学习算法和技术的进步，越来越多的机器学习应用程序需要多台机器，并且必须利用并行性。但是，在集群上进行机器学习的基础设施仍然是临时的。虽然确实存在针对特定用例（例如，参数服务器或超参数搜索）和AI之外的高质量分布式系统的良好解决方案（例如，Hadoop或Spark），但是在边界开发算法的从业者通常从头开始构建他们自己的系统基础设施。这相当于许多多余的努力。

例如，采用概念上简单的算法，如进化策略进行强化学习。该算法大约有十几行伪代码，其Python实现并不需要太多。但是，在更大的机器或集群上有效地运行算法需要更多的软件工程。作者的实现涉及数千行代码，必须定义通信协议，消息序列化和反序列化策略以及各种数据处理策略。

Ray的目标之一是让从业者能够将在笔记本电脑上运行的原型算法转变为高性能的分布式应用程序，该应用程序可以在集群（或单个多核机器）上高效运行，而且代码行相对较少。这样的框架应该包括手动优化系统的性能优势，而无需用户推理调度，数据传输和机器故障。