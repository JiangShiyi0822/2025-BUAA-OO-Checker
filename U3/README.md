## 使用方法

根目录下运行 main.py 即可。

## 注意事项

1. U3测评机基于随机数据生成的对拍实现。你应当有一个 std.jar 置于根目录下（出于代码保护，这里并不给出），你可以在 jar 目录下放置多个 jar 包，实现多文件输出的对拍。
2. main.py 中可以修改测试组数和每组指令数。generator.py 中可以修改生成各种指令的权重。
3. 本单元测评机实现采用人工搭建主体 + AI补全部分函数的方法实现。其中人工搭建的主体框架已经在根目录中给出。使用者可以根据主体框架灵活调整，实现自己的测评机。