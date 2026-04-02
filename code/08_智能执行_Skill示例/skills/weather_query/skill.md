# 天气查询 Skill

## 功能描述
查询指定城市的当前天气信息和未来24小时天气预报。

## 使用方式
调用 `scripts/weather_query.py` 脚本，传入城市名称参数。

## 输入参数
- city: 城市名称（中文）

## 输出格式
返回JSON格式的天气信息，包含：
- city: 城市名称
- temperature: 当前温度（摄氏度）
- humidity: 湿度（百分比）
- weather: 天气状况
- forecast: 未来24小时预报
