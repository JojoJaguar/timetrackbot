import os
from slack_bolt import App
from pathlib import Path
from dotenv import load_dotenv
from clickupython import client


env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


# Clickup app configs
API_KEY = os.environ.get("CLICKUP_TOKEN")
clickup_client = client.ClickUpClient(API_KEY)

# Slack app configs
app = App(
    token=os.environ.get("SLACK_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

channel_members_email = []


@app.command("/tt")
def scrumHasStarted(ack, client):
    ack()

    members = app.client.conversations_members(channel="C03N6B94HL5")
    for member in members["members"]:
        profile = app.client.users_info(user=member)
        if (
            profile["user"]["name"] != "timetrackbot"
        ):  # In order to prevent the scraping bots user info since bolt gives error
            channel_member_email = profile["user"]["profile"]["email"]
            channel_members_email.append(channel_member_email)

    print(channel_members_email)

    # scraping user ID's and create a dictionary as key is email adress and value is ID
    users_clickup = clickup_client.get_teams()
    usersDictionary = {}
    for user in users_clickup.teams[0].members:
        for email in channel_members_email:
            if user.user.email == email:
                usersDictionary[f"{email}"] = user.user.id

    print(usersDictionary)

    # Using usersDictionary to get click up user IDs
    clickup_user_IDs = []
    for user_email in usersDictionary:
        clickup_user_IDs.append(usersDictionary.get(user_email))

    timeTrackingDataList = clickup_client.get_time_entries_in_range(
        team_id="2430514",
        assignees=clickup_user_IDs,
        start_date="june 1 2022",
        end_date="june 30 2022",
    )

    # creating a dictionary from the all tasks from the clickup which is taken with userIDs

    userTimeTrackDictionary = {}

    for user_email in usersDictionary:

        totaltimetrack_of_user = 0

        userTimeTrackDictionary[user_email] = totaltimetrack_of_user

        for data in timeTrackingDataList:
            if data.user.email == user_email:
                totaltimetrack_of_user += data.duration

        totaltimetrack_of_user = totaltimetrack_of_user / 3600000

        userTimeTrackDictionary[user_email] = totaltimetrack_of_user

    client.chat_postMessage(
        channel="timetrackbottest", text=f"{userTimeTrackDictionary} hours"
    )


# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
