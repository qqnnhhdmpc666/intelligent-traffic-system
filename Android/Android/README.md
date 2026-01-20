# 智慧交通调度系统 - Android客户端 (兼容版)

## 📱 项目简介

这是智慧交通调度系统的Android客户端兼容版本，专为老版本Android设备和低配置环境设计。

## 🔧 兼容性特性

### 系统要求
- **最低Android版本**: Android 5.0 (API 21)
- **目标Android版本**: Android 11 (API 30)
- **最低内存**: 2GB RAM
- **存储空间**: 50MB

### 技术栈选择
- **开发语言**: Kotlin 1.8.10
- **UI框架**: 传统View系统 (非Jetpack Compose)
- **架构模式**: MVVM + LiveData
- **网络库**: Retrofit 2.9.0 + OkHttp 4.9.3
- **异步处理**: Kotlin Coroutines 1.6.4

### 降低依赖要求
- 使用较低版本的AndroidX库
- 避免使用最新的Jetpack组件
- 简化网络配置和错误处理
- 减少第三方库依赖

## 🚀 功能特性

### 核心功能
1. **首页** - 系统状态监控和快速操作
2. **路径规划** - 同步/异步路径规划功能
3. **实时监控** - 系统运行状态监控
4. **设置** - 应用配置和信息

### 网络功能
- 连接服务器: http://120.53.28.58:3389/
- 支持所有API接口调用
- 自动重试和错误处理
- 网络状态检测

## 📋 项目结构

```
app/src/main/
├── java/com/traffic/client/
│   ├── MainActivity.kt                 # 主Activity
│   ├── data/                          # 数据模型
│   │   ├── ApiService.kt              # API接口定义
│   │   └── DataModels.kt              # 数据模型类
│   ├── network/                       # 网络层
│   │   └── NetworkManager.kt          # 网络管理器
│   ├── repository/                    # 数据仓库
│   │   └── TrafficRepository.kt       # 数据仓库
│   └── ui/                           # UI层
│       ├── fragments/                # Fragment
│       │   ├── HomeFragment.kt       # 首页
│       │   ├── PathPlanningFragment.kt # 路径规划
│       │   ├── MonitorFragment.kt    # 监控
│       │   └── SettingsFragment.kt   # 设置
│       └── viewmodels/               # ViewModel
│           ├── HomeViewModel.kt      # 首页ViewModel
│           └── PathPlanningViewModel.kt # 路径规划ViewModel
├── res/                              # 资源文件
│   ├── layout/                       # 布局文件
│   ├── values/                       # 值资源
│   ├── menu/                         # 菜单资源
│   └── drawable/                     # 图形资源
└── AndroidManifest.xml               # 应用清单
```

## 🛠️ 开发环境

### 必需工具
- Android Studio Arctic Fox (2020.3.1) 或更高版本
- JDK 8 或更高版本
- Android SDK (API 21-30)

### 构建配置
- Gradle: 7.4.2
- Android Gradle Plugin: 7.4.2
- Kotlin: 1.8.10

## 📦 安装和运行

### 1. 导入项目
```bash
# 解压项目文件
unzip TrafficClientApp_Compatible.zip

# 使用Android Studio打开项目
# File -> Open -> 选择TrafficClientApp_Compatible文件夹
```

### 2. 同步依赖
```bash
# 在Android Studio中
# 点击 "Sync Project with Gradle Files"
# 等待依赖下载完成
```

### 3. 配置设备
```bash
# 连接Android设备或启动模拟器
# 确保设备已开启开发者选项和USB调试
```

### 4. 编译运行
```bash
# 在Android Studio中
# 点击 "Run" 按钮或按 Shift+F10
# 选择目标设备并等待安装完成
```

## 🔗 服务器连接

### 默认配置
- **服务器地址**: http://120.53.28.58:3389/
- **连接超时**: 30秒
- **读取超时**: 30秒
- **写入超时**: 30秒

### 支持的API接口
- `GET /` - 获取系统信息
- `GET /health` - 健康检查
- `POST /api/request_path` - 同步路径规划
- `POST /api/request_path_async` - 异步路径规划
- `GET /api/task/{taskId}` - 查询任务状态
- `GET /api/system_stats` - 获取系统统计
- `GET /api/nodes` - 获取节点列表
- `GET /api/roads` - 获取道路列表

## 🎨 界面设计

### 设计原则
- Material Design 2.0 (兼容老版本)
- 蓝色主题色调 (#0D47A1)
- 简洁清晰的布局
- 适配不同屏幕尺寸

### 主要界面
1. **首页**: 系统状态卡片 + 快速操作按钮
2. **路径规划**: 车辆信息输入 + 路线选择 + 结果显示
3. **监控**: 系统监控信息展示
4. **设置**: 应用配置和版本信息

## 🐛 故障排除

### 常见问题

#### 1. 编译错误
```bash
# 清理项目
./gradlew clean

# 重新构建
./gradlew build
```

#### 2. 网络连接失败
- 检查服务器是否正常运行
- 确认网络权限已添加
- 验证服务器地址是否正确

#### 3. 依赖冲突
- 检查build.gradle中的版本号
- 使用Android Studio的依赖分析工具
- 清理并重新同步项目

### 调试技巧
- 使用Logcat查看日志输出
- 启用网络日志记录
- 使用断点调试关键代码

## 📈 性能优化

### 已实现的优化
- 使用ViewBinding减少findViewById调用
- 协程处理异步操作
- 网络请求缓存和重试机制
- 内存泄漏预防

### 建议的优化
- 添加图片缓存机制
- 实现数据本地存储
- 优化网络请求频率
- 添加性能监控

## 🔄 版本历史

### v1.0.0 (当前版本)
- 基础功能实现
- 兼容Android 5.0+
- 支持路径规划和系统监控
- Material Design界面

## 📞 技术支持

如果遇到问题，请提供以下信息：
1. Android版本和设备型号
2. 应用版本号
3. 错误日志和截图
4. 复现步骤

## 📄 许可证

本项目仅供学习和研究使用。

---

**注意**: 这是兼容版本，专为老版本Android设备优化。如果您的设备支持更高版本的Android，建议使用标准版本以获得更好的性能和功能。

