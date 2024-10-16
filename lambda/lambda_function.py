import json
import boto3


OUTPUT = {
    "TurnOnLEDIntent": "LED on!",
    "TurnOffLEDIntent": "LED off.",
    "PourDrinkOneIntent": "Pouring...",
    "PourDrinkTwoIntent": "Pouring...",
    "PourDrinkThreeIntent": "Pouring...",
    "PourDrinkFourIntent": "Pouring...",
    "pour": "Pouring...",
}

iot_client = boto3.client("iot-data", region_name="us-west-2")



def lambda_handler(event, context):
    request = event["request"]
    print("request:", request)

    intent = request["intent"]["name"]
    slots = {}
    if "slots" in request["intent"]:
        slots = {
            key: slot["value"]
            for key, slot in request["intent"]["slots"].items()
        }
    payload = dict(
        intent=intent,
        slots=slots,
    )

    iot_response = iot_client.publish(
        topic="pico",
        qos=1,
        payload=json.dumps(payload),
    )
    print("iot_response:", iot_response)

    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": OUTPUT[intent]
            }
        }
    }
