import json
from datetime import datetime, timedelta
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP

mcp = FastMCP(name="智能出行助手")

class TravelTools:
    """智能出行助手工具集"""

    def search_flights(self, origin: str, destination: str, date: str):
        """查询从出发地到目的地在特定日期的机票航班信息。"""
        print(f"    -> 执行查询: {origin} 到 {destination}")
        flights = [
            {"flight_no": "CA1234", "price": 1200, "time": "08:00"},
            {"flight_no": "MU5678", "price": 980, "time": "14:30"},
        ]
        return json.dumps(flights, ensure_ascii=False)

    def book_ticket(self, flight_no: str, passenger_name: str):
        """根据航班号为指定的乘客预订机票。"""
        print(f"    -> 执行订票: {passenger_name} -> {flight_no}")
        return json.dumps(
            {"status": "success", "order_id": "ORD20260402XYZ"}, ensure_ascii=False
        )

    def send_notification(self, message: str, channel: str = "SMS"):
        """向用户发送行程确认通知。"""
        print(f"    -> 发送{channel}通知: {message}")
        return json.dumps({"status": "sent"}, ensure_ascii=False)

    def get_date(self, relative_date: str):
        """将相对日期（今天、明天）转换为 YYYY-MM-DD 格式。"""
        today = datetime.now()
        if relative_date == "今天":
            target_date = today
        elif relative_date == "明天":
            target_date = today + timedelta(days=1)
        elif relative_date == "后天":
            target_date = today + timedelta(days=2)
        else:
            return json.dumps({"error": "仅支持今天、明天、后天"}, ensure_ascii=False)
        
        result = target_date.strftime("%Y-%m-%d")
        print(f"    -> 日期转换: {relative_date} -> {result}")
        return json.dumps({"date": result}, ensure_ascii=False)


travel_tools = TravelTools()


@mcp.tool("get_date", description="将相对日期（如'今天'、'明天'、'后天'）转换为具体的 YYYY-MM-DD 格式。")
def get_date(
    relative_date: Annotated[str, Field(description="相对日期名称，可选：'今天'、'明天'、'后天'")],
) -> str:
    return travel_tools.get_date(relative_date)


@mcp.tool("search_flights", description="查询从出发地到目的地在特定日期的机票航班信息。")
def search_flights(
    origin: Annotated[str, Field(description="出发地，如'北京'")],
    destination: Annotated[str, Field(description="目的地，如'上海'")],
    date: Annotated[str, Field(description="日期，如'2026-04-03'")],
) -> str:
    return travel_tools.search_flights(origin, destination, date)


@mcp.tool("book_ticket", description="根据航班号为指定的乘客预订机票。")
def book_ticket(
    flight_no: Annotated[str, Field(description="航班号，如'CA1234'")],
    passenger_name: Annotated[str, Field(description="乘客姓名，如'张三'")],
) -> str:
    return travel_tools.book_ticket(flight_no, passenger_name)


@mcp.tool("send_notification", description="向用户发送行程确认通知。")
def send_notification(
    message: Annotated[str, Field(description="要发送的通知内容")],
    channel: Annotated[str, Field(description="通知渠道，如'SMS'或'Email'")] = "SMS",
) -> str:
    return travel_tools.send_notification(message, channel)


if __name__ == "__main__":
    mcp.run(transport="http", port=9005)
