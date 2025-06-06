## 使用方法

将被测 jar 包（可以多个）放到 jar 目录下，然后在根目录运行 main.py 。

## 注意事项

1. 可以更改 main.py 中的 SERIAL 和  LENGTH 参数调整测试组数和每组长度。
2. 需要使用课程组提供的投喂程序（datainput_student_win64.exe）。
3. hw7 测评机增加了高并发和 GUI 界面，使用方法与前相同。可以在 main.py 中修改 MAX_THREAD 来调整并发线程数量，建议取值20附近。
4. hw7 的 gen.py 支持切换公测模式和互测模式。支持dense（密集），frequent（频繁调度），random（随机），uniform（均匀）等四种数据生成策略，按照命令行提示选择即可。

