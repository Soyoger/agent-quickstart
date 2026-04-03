# 交通信息查询 Skill

## 功能描述
查询实时交通状况、拥堵指数和路线规划建议。

## 使用方式
调用 `scripts/traffic_query.py` 脚本，传入起点和终点参数。

## 输入参数
- start: 起点
- end: 终点

## 输出格式
返回JSON格式的交通信息，包含：
- routes: 推荐路线列表
- congestion: 拥堵指数
- estimated_time: 预计时间
