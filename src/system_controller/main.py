from system_controller.core.bot import Bot
from system_controller.core.config import token

bot = Bot()

if __name__ == "__main__":
    bot.run(token)