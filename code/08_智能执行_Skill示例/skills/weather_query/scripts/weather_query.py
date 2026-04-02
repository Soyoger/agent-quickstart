import json
import sys

def get_weather(city):
    weather_data = {
        "北京": {
            "city": "北京",
            "temperature": 18,
            "humidity": 45,
            "weather": "晴朗",
            "forecast": "未来24小时晴朗，温度15-22°C"
        },
        "上海": {
            "city": "上海",
            "temperature": 22,
            "humidity": 65,
            "weather": "多云",
            "forecast": "未来24小时多云转小雨，温度19-25°C"
        },
        "广州": {
            "city": "广州",
            "temperature": 28,
            "humidity": 75,
            "weather": "小雨",
            "forecast": "未来24小时小雨，温度25-31°C"
        },
        "深圳": {
            "city": "深圳",
            "temperature": 27,
            "humidity": 70,
            "weather": "阴天",
            "forecast": "未来24小时阴天转多云，温度24-30°C"
        }
    }
    return weather_data.get(city, {
        "city": city,
        "temperature": "未知",
        "humidity": "未知",
        "weather": "暂无数据",
        "forecast": "暂无预报数据"
    })

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "请提供城市名称"}, ensure_ascii=False))
        sys.exit(1)
    city = sys.argv[1]
    result = get_weather(city)
    print(json.dumps(result, ensure_ascii=False))
