import json
import sys

def get_traffic_info(start, end):
    routes = [
        {"name": "推荐路线", "distance": "15.5公里", "duration": "35分钟", "congestion": "轻度拥堵"},
        {"name": "最短距离", "distance": "12.8公里", "duration": "45分钟", "congestion": "中度拥堵"},
        {"name": "高速优先", "distance": "18.2公里", "duration": "30分钟", "congestion": "畅通"}
    ]
    
    return {
        "start": start,
        "end": end,
        "routes": routes,
        "congestion_index": 0.6,
        "updated_at": "2026-04-02 10:30:00"
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "请提供起点和终点"}, ensure_ascii=False))
        sys.exit(1)
    start = sys.argv[1]
    end = sys.argv[2]
    result = get_traffic_info(start, end)
    print(json.dumps(result, ensure_ascii=False))
