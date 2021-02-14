from snaketalk import Bot, ExamplePlugin, Settings

bot = Bot(
    settings=Settings(
        MATTERMOST_URL="http://127.0.0.1",
        BOT_TOKEN="e691u15hajdebcnqpfdceqihcc",
        MATTERMOST_PORT=8065,
        SSL_VERIFY=False,
    ),
    plugins=[ExamplePlugin()],
)
bot.run()
