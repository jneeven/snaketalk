from snaketalk import Bot, ExamplePlugin, Settings

bot = Bot(
    settings=Settings(
        MATTERMOST_URL="http://127.0.0.1",
        BOT_TOKEN="tdf5ozcwt7yf9kb6xzs748ot1h",
        MATTERMOST_PORT=8065,
        SSL_VERIFY=False,
    ),
    plugins=[ExamplePlugin()],
)
bot.run()
