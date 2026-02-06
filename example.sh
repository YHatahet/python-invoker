 curl -X POST http://localhost:5000/invoke -H "Content-Type: application/json" -d '{
    "event": {"num1": 10, "num2": 20},
    "code": "def handler(event, context):\n    print(\"Calculating sum...\")\n    return event[\"num1\"] + event[\"num2\"]"
