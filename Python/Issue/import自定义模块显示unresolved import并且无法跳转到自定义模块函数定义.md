# Issue: 

1. import自定义模块显示unresolved import
2. 无法跳转到自定义模块函数定义
---
  
  
# Evironment:
1. code tool：vscode
2. language: python
---

# Reason:

> *vscode仅会把工作目录根目录里面的包加载进来，如果引用的包(或文件)在根目录的子目录下面，使用import后就会提示unresolved import,并且不会触发对应的代码提示，也无法跳转到对应的方法定义。*
---
# Solution:
1. launch.json里面最后一条配置后面加入
```json        
    "env": {"PYTHONPATH":"${workspaceRoot}"},
    "envFile":"${workspaceFolder}/.env"
```

2. 在根目录下面建立一个.env文件，文件内部填写自定义模块的相对位置：
```yml
    PYTHONPATH=./mymodule
```