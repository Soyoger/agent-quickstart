# 车票查询 Skill

## 功能描述
查询火车票和机票信息，支持单程和往返查询。

## 使用方式
调用 `scripts/ticket_query.py` 脚本，传入出发地、目的地、日期等参数。

## 输入参数
- from_city: 出发城市
- to_city: 到达城市
- date: 出发日期（YYYY-MM-DD）
- type: 车票类型（train/flight）

## 输出格式
返回JSON格式的车票信息列表。
