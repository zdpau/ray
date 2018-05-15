# Using Ray with GPUs
GPU对许多机器学习应用程序至关重要。 Ray允许远程函数和actor在ray.remote装饰器中指定他们的GPU要求。
## Starting Ray with GPUs
为了让远程功能和actor使用GPU，Ray必须知道有多少GPU可用。如果您在单台机器上启动Ray，则可以按如下方式指定GPU的数量。
```
ray.init(num_gpus=4)
```
如果你没有传入num_gpus参数，Ray会假定机器上有0个GPU。 

如果您使用ray start命令启动Ray，则可以使用--num-gpus参数指示机器上GPU的数量。
```
ray start --head --num-gpus=4
```
注意：没有什么能够阻止您传递比计算机上GPU的真实数量更大的num_gpus值。 在这种情况下，Ray会像计算机具有您为指定需要GPU的任务所指定的GPU数量那样工作。 只有在这些任务试图实际使用不存在的GPU时才会出现问题。
## Using Remote Functions with GPUs
如果远程功能需要GPU，请指明远程装饰器中所需的GPU数量。
```
@ray.remote(num_gpus=1)
def gpu_method():
    return "This function is allowed to use GPUs {}.".format(ray.get_gpu_ids())
```
在远程函数内部，对ray.get_gpu_ids（）的调用将返回一个整数列表，指示远程函数允许使用哪些GPU。

注意：上面定义的函数gpu_method实际上并不使用任何GPU。 Ray会在一台至少有一个GPU的机器上安排它，并且在它正在执行时为它预留一个GPU，但是它实际上可以使用GPU。 这通常是通过像TensorFlow这样的外部库来完成的。 这是一个实际使用GPU的例子。 请注意，在这个例子中，你需要安装TensorFlow的GPU版本。
```
import os
import tensorflow as tf

@ray.remote(num_gpus=1)
def gpu_method():
    os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, ray.get_gpu_ids()))
    # Create a TensorFlow session. TensorFlow will restrict itself to use the
    # GPUs specified by the CUDA_VISIBLE_DEVICES environment variable.
    tf.Session()
```
注意：实现gpu_method的人无疑可以忽略ray.get_gpu_ids并使用机器上的所有GPU。 Ray并没有阻止这种情况的发生，并且这可能导致太多的工作人员同时使用相同的GPU。 例如，如果未设置CUDA_VISIBLE_DEVICES环境变量，则TensorFlow将尝试使用机器上的所有GPU。
## Using Actors with GPUs
定义使用GPU的actor时，请指明ray.remote装饰器中actor实例所需的GPU数量。
```
@ray.remote(num_gpus=1)
class GPUActor(object):
    def __init__(self):
        return "This actor is allowed to use GPUs {}.".format(ray.get_gpu_ids())
```
当演员被创建时，GPU将在actor的一生中被保留给该演员。

请注意，Ray必须已经启动，GPU的数量至少与您传入ray.remote装饰器的GPU数量一样多。 否则，如果您传入的数字大于传入ray.init的数字，则在实例化actor时会引发异常。

以下是如何通过TensorFlow在演员中使用GPU的示例。
```
@ray.remote(num_gpus=1)
class GPUActor(object):
    def __init__(self):
        self.gpu_ids = ray.get_gpu_ids()
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, self.gpu_ids))
        # The call to tf.Session() will restrict TensorFlow to use the GPUs
        # specified in the CUDA_VISIBLE_DEVICES environment variable.
        self.sess = tf.Session()
```
## Troubleshooting 故障排除
注意：当前，当工作人员执行使用GPU的任务时，该任务可能会在GPU上分配内存，并且在任务完成执行时可能不会释放内存。这可能会导致问题。请看这个链接（见原文）
