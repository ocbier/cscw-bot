import discord
from exceptions import ChannelNotFoundException
from discord.utils import get


class Bot:

    def __init__(self, token):
        self.token = token
        self.client = discord.Client(intents=discord.Intents.default())


    async def start(self):
        await self.client.start(self.token)

    # Sends a message to a channel with the matching channel id.
    async def send_message(self, channel_id, message):
        print('Sending message to channel with id ' + str(channel_id))
        channel_obj = self.client.get_channel(channel_id)

        if channel_obj is None:
            raise ChannelNotFoundException('Error sending message to channel. Could not get the channel with id ' + str(channel_id))
        else:
            await channel_obj.send(message)


    # Sends a message to a channel with the matching channel name.
    async def send_message_by_name(self, channel_name, message):

       
        channel_obj = discord.utils.get(self.client.get_all_channels(), name=channel_name, type=discord.ChannelType.text)

        if channel_obj is None:
            raise ChannelNotFoundException('Error sending message to channel. Could not get the channel with name ' + channel_name)
        else:
            await channel_obj.send(message)

        

    @staticmethod
    def get_valid_name(channel_name, channel_number):
        str_channel_number = str(channel_number)
        if channel_number < 10:
            str_channel_number = '0' + str_channel_number

        f_name = channel_name.strip().lower().replace(' ', '-').replace('&', 'and').replace(',', '-')
        f_name = str_channel_number + '-' + f_name

        return f_name



