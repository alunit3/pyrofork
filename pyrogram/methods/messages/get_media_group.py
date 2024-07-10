#  Pyrofork - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#  Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>
#
#  This file is part of Pyrofork.
#
#  Pyrofork is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrofork is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrofork.  If not, see <http://www.gnu.org/licenses/>.

import logging
from typing import Union, List

import pyrogram
from pyrogram import types

log = logging.getLogger(__name__)


class GetMediaGroup:
    async def get_media_group(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        message_id: int
    ) -> List["types.Message"]:
        """Get the media group a message belongs to.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
                You can also use chat public link in form of *t.me/<username>* (str).

            message_id (``int``):
                The id of one of the messages that belong to the media group.
                
        Returns:
            List of :obj:`~pyrogram.types.Message`: On success, a list of messages of the media group is returned.
            
        Raises:
            ValueError: 
                In case the passed message_id is negative or equal 0. 
                In case target message doesn't belong to a media group.
        """

        if message_id <= 0:
            raise ValueError("Passed message_id is negative or equal to zero.")

        # First, get the target message
        target_message = await self.get_messages(chat_id, message_ids=message_id)

        if not target_message:
            raise ValueError(f"Message with ID {message_id} not found")

        if not target_message.media_group_id:
            raise ValueError("The message doesn't belong to a media group")

        media_group_id = target_message.media_group_id

        # Function to get messages in chunks
        async def get_message_chunk(start_id, end_id):
            return await self.get_messages(
                chat_id=chat_id,
                message_ids=range(start_id, end_id + 1),
                replies=0
            )

        # Search backwards
        media_group = []
        current_id = message_id
        while True:
            chunk = await get_message_chunk(max(1, current_id - 9), current_id)
            group_messages = [msg for msg in chunk if msg.media_group_id == media_group_id]
            if not group_messages or group_messages[0].id != current_id - len(group_messages) + 1:
                break
            media_group = group_messages + media_group
            current_id = group_messages[0].id - 1
            if current_id <= 0:
                break

        # Search forwards
        current_id = message_id + 1
        while True:
            chunk = await get_message_chunk(current_id, current_id + 9)
            group_messages = [msg for msg in chunk if msg.media_group_id == media_group_id]
            if not group_messages:
                break
            media_group.extend(group_messages)
            current_id = group_messages[-1].id + 1

        if not media_group:
            raise ValueError("Failed to retrieve the media group")

        return types.List(sorted(media_group, key=lambda x: x.id))