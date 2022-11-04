import discord
from exceptions import ChannelNotFoundException
from discord.utils import get
import asyncio
import os
from dotenv import load_dotenv

class Bot:

    def __init__(self, token, guild_id, test_mode = False):
        self.token = token
        self.client = discord.Client(intents=discord.Intents.default())
        self.guild_id = guild_id
        self.test_mode = test_mode


    async def start(self):
        await self.client.start(self.token)

    # Sends a message to a channel with the matching channel id.
    async def send_message(self, channel_id, message):
        print('Sending message to channel with id ' + str(channel_id))
        channel_obj = self.client.get_channel(channel_id)

        if channel_obj is None:
            raise ChannelNotFoundException('Error sending message to channel. Could not get the channel with id ' + str(channel_id))
        else:
            await channel_obj.send("[This is a test message]\n" + message)


    # Sends a message to a channel with the matching channel name. Append '-test' if in test mode.
    async def send_message_by_name(self, channel_name, message):
        target = channel_name if not self.test_mode else channel_name + '-test'
        channel_obj = discord.utils.get(self.client.get_all_channels(), guild__id = int(self.guild_id), name=target, type=discord.ChannelType.text)
        if channel_obj is None:
            raise ChannelNotFoundException('Error sending message to channel. Could not get the channel with name ' + channel_name)
        else:
            await channel_obj.send(message)

    async def get_channel_id_by_name(self, channel_name):
        print('get_channel_id_by_name:', channel_name)
        channel_obj = discord.utils.get(self.client.get_all_channels(), guild__id = int(self.guild_id), name=channel_name, type=discord.ChannelType.text)
        return channel_obj.id

    @staticmethod
    def get_valid_name(channel_name, channel_number):
        str_channel_number = str(channel_number)
        if channel_number < 10:
            str_channel_number = '0' + str_channel_number

        f_name = channel_name.strip().lower().replace(' ', '-').replace('&', 'and').replace(',', '').replace("'", '')
        f_name = str_channel_number + '-' + f_name

        return f_name




async def initiate(bot):
    await bot.start()
    await asyncio.sleep(10)
    

async def test(bot):
    await asyncio.sleep(2)
    await bot.send_message_by_name('📺-tv-test', 'bot test - Hello Discord!')
    id = await bot.get_channel_id_by_name('📺-tv-test')
    print(id)

async def main():
    load_dotenv()
    bot_token = os.getenv('TOKEN')
    live_tv_channel = int(os.getenv('TV_CHANNEL_ID'))
    guild_id = os.getenv('GUILD_ID')

    print (bot_token, live_tv_channel, guild_id)
    bot = Bot(bot_token, guild_id, test_mode = False) # Create the bot
    await asyncio.gather(initiate(bot), test(bot))


if __name__ == '__main__':
    asyncio.run(main())
