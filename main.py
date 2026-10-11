import os
from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from dotenv import load_dotenv

from bot import run_rag_pipeline  # Adjust to your actual pipeline file

load_dotenv()

app = Flask(__name__)

slack_app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
    process_before_response=False
)

handler = SlackRequestHandler(slack_app)


@slack_app.event("app_mention")
def handle_app_mention(event, say):
    user_query = event.get("text")
    channel_id = event.get("channel")
    print(f"Received tag mention in channel {channel_id}: {user_query}")

    try:
        ai_response = run_rag_pipeline(user_query)
    except Exception as e:
        print(f"Error running RAG pipeline: {e}")
        ai_response = "Sorry, I encountered an error processing your request."

    say(text=ai_response, channel=channel_id)


@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json(silent=True)
    print("--- RAW SLACK PAYLOAD RECEIVED ---")
    print(data)
    print("-----------------------------------")

    return handler.handle(request)


if __name__ == "__main__":
    app.run(port=8000, debug=True)
