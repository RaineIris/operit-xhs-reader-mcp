<!-- operit-mcp-json: {"version":"v1"} -->
<!-- operit-parser-version: v1 -->

## 📋 插件信息

**描述:** Xhs Reader 是一个专为 AI 提供小红书内容解析的工具包。通过输入图文帖子链接，它能自动提取帖子的标题、文案，并利用腾讯混元 Vision 模型智能识别每张图片内容，帮助用户一键全面获取和理解小红书的完整图文信息。

## 🔑 如何获取混元 API Key

1. 打开腾讯云控制台：[console.cloud.tencent.com/hunyuan](https://console.cloud.tencent.com/hunyuan)
2. 注意别走错路：
   - 混元生图 ❌（那是画图的）
   - 图像分析与处理 TIIA ❌（只认车认商品）
   - **混元大模型 API ✅ 进这里**
3. 选择「使用 OpenAI SDK 方式接入」，点击「创建 API Key」
4. 复制以 `sk-` 开头的 key，**只显示一次，请妥善保存**
5. 进入左侧「设置」，打开「开通后付费」（不开这个 vision 调不了）
6. 进入「资源包管理」领取新用户免费 100 万 token

## 📦 安装方式

1. 打开 Operit MCP 配置页面
2. 点击右下角 ➕ 号，选择从「仓库」导入
3. 直接粘贴本 GitHub 仓库的网址链接
4. 导入后，点击该插件 → 编辑环境变量 → 将 `HUNYUAN_API_KEY` 改为您自己的 API Key
5. 启用插件即可。首次启动时会自动配置并拉取所需依赖，无需手动操作！

## ⚙️ 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `HUNYUAN_API_KEY` | ✅ | 腾讯混元大模型 API Key |
