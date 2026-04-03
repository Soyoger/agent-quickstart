import json
import sys

def query_tickets(from_city, to_city, date, ticket_type):
    train_data = {
        "北京-上海": [
            {"train_no": "G1", "departure": "07:00", "arrival": "11:36", "duration": "4小时36分", "price": 553, "seats": "有票"},
            {"train_no": "G3", "departure": "08:00", "arrival": "12:28", "duration": "4小时28分", "price": 553, "seats": "有票"}
        ],
        "上海-北京": [
            {"train_no": "G2", "departure": "07:00", "arrival": "11:36", "duration": "4小时36分", "price": 553, "seats": "有票"}
        ]
    }
    
    flight_data = {
        "北京-上海": [
            {"flight_no": "CA1234", "departure": "08:00", "arrival": "10:30", "duration": "2小时30分", "price": 1280, "seats": "有票"},
            {"flight_no": "MU5678", "departure": "14:00", "arrival": "16:30", "duration": "2小时30分", "price": 980, "seats": "有票"}
        ]
    }
    
    key = f"{from_city}-{to_city}"
    if ticket_type == "train":
        return {"type": "train", "data": train_data.get(key, [])}
    elif ticket_type == "flight":
        return {"type": "flight", "data": flight_data.get(key, [])}
    else:
        return {"error": "不支持的车票类型"}

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(json.dumps({"error": "参数不足"}, ensure_ascii=False))
        sys.exit(1)
    from_city = sys.argv[1]
    to_city = sys.argv[2]
    date = sys.argv[3]
    ticket_type = sys.argv[4]
    result = query_tickets(from_city, to_city, date, ticket_type)
    print(json.dumps(result, ensure_ascii=False))
