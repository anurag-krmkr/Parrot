from pymongo import MongoClient
from utilities.config import my_secret
import motor.motor_asyncio

cluster = motor.motor_asyncio.AsyncIOMotorClient(
    f"mongodb+srv://user:{str(my_secret)}@cluster0.xjask.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
)

parrot_db = cluster['parrot_db']
economy_db = cluster['economy']
msg_db = cluster['msg_db']
tags = cluster['tags']


async def cmd_increment(cmd: str):
    collection = parrot_db['cmd_count']
    data = await collection.find_one({'_id': cmd})
    if not data:
        return await collection.insert_one({'_id': cmd, 'count': 1})
    collection.update_one({'_id': cmd}, {'$inc': {'count': 1}})


async def ge_update(user_id: int, bank: int, wallet: int):
    collection = economy_db['global_economy']
    data = await collection.find_one({'_id': user_id})
    if not data:
        await collection.insert_one({'_id': user_id, 'bank': 0, 'wallet': 400})

    await collection.update_one({"_id": user_id},
                          {"$set": {
                              'bank': bank,
                              'wallet': wallet
                          }})


async def gchat_update(guild_id: int, post: dict):
    collection = parrot_db['global_chat']
    data = await collection.find_one({'_id': guild_id})
    if not data:
        await collection.insert_one({'_id': guild_id})

    await collection.update_one({'_id': guild_id}, {'$set': post})


async def msg_increment(guild_id: int, user_id: int):
    collection = msg_db[f'{guild_id}']
    data = await collection.find_one({'_id': user_id})
    if not data: 
        await collection.insert_one({'_id': user_id, 'count': 1})
        
    await collection.update_one({'_id': user_id}, {'$inc': {'count': 1}})


async def telephone_update(guild_id: int, event: str, value):
    collection = parrot_db["telephone"]
    data = await collection.find_one({'_id': guild_id})
    if not data:
        await collection.insert_one({'_id': guild_id, "channel": None, "pingrole": None, "is_line_busy": False, "memberping": None, "blocked": []})

    await collection.update_one({'_id': guild_id}, {"$set": {event: value}})


async def ticket_update(guild_id: int, post):
    collection = parrot_db["ticket"]
    data = await collection.find_one({'_id': guild_id})
    if not data:
        await collection.insert_one({
            '_id': guild_id,
            "ticket-counter": 0,
            "valid-roles": [],
            "pinged-roles": [],
            "ticket-channel-ids": [],
            "verified-roles": [],
            "message_id": None,
            "log": None,
            "category": None,
            "channel_id": None
        })

    await collection.update_one({'_id': guild_id}, {"$set": post})


async def guild_update(guild_id: int, post: dict):
    collection = parrot_db['server_config']
    data = await collection.find_one({'_id': guild_id})
    if not data:
        await collection.insert_one({
            '_id': guild_id,
            'prefix': '$',
            'mod_role': None,
            'action_log': None,
            'mute_role': None,
        })

    await collection.update_one({'_id': guild_id}, {"$set": post})


async def guild_join(guild_id: int):
    collection = parrot_db['server_config']
    post = {
        '_id': guild_id,
        'prefix': '$',
        'mod_role': None,
        'action_log': None,
        'mute_role': None,
    }
    await collection.insert_one(post)
    collection = parrot_db['global_chat']
    post = {
        '_id': guild_id,
        'channel_id': None,
        'webhook': None,
        'ignore-role': None,
    }
    await collection.insert_one(post)
    collection = parrot_db["telephone"]

    post = {
        "_id": guild_id,
        "channel": None,
        "pingrole": None,
        "is_line_busy": False,
        "memberping": None,
        "blocked": []
    }

    await collection.insert_one(post)
    collection = parrot_db["ticket"]
    post = {
        "_id": guild_id,
        "ticket-counter": 0,
        "valid-roles": [],
        "pinged-roles": [],
        "ticket-channel-ids": [],
        "verified-roles": [],
        "message_id": None,
        "log": None,
        "category": None,
        "channel_id": None
    }

    await collection.insert_one(post)


async def guild_remove(guild_id: int):
    collection = parrot_db['server_config']
    await collection.delete_one({'_id': guild_id})
    collection = parrot_db[f'{guild_id}']
    await collection.drop()
    collection = parrot_db['global_chat']
    await collection.delete_one({'_id': guild_id})
    collection = parrot_db["telephone"]
    await collection.delete_one({'_id': guild_id})
    collection = parrot_db["ticket"]
    await collection.delete_one({'_id': guild_id})