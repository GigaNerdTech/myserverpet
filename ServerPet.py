import discord
import re
import mysql.connector
from mysql.connector import Error
import subprocess
import time
import requests
import random
from discord.utils import get
import discord.utils
from datetime import datetime
import asyncio

client = discord.Client(heartbeat_timeout=600)

async def log_message(log_entry):
    current_time_obj = datetime.now()
    current_time_string = current_time_obj.strftime("%b %d, %Y-%H:%M:%S.%f")
    print(current_time_string + " - " + log_entry, flush = True)
    
async def commit_sql(sql_query, params = None):
    await log_message("Commit SQL: " + sql_query + "\n" + "Parameters: " + str(params))
    try:
        connection = mysql.connector.connect(host='localhost', database='ServerPet', user='REDACTED', password='REDACTED')    
        cursor = connection.cursor()
        result = cursor.execute(sql_query, params)
        connection.commit()
        return True
    except mysql.connector.Error as error:
        await log_message("Database error! " + str(error))
        return False
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            
                
async def select_sql(sql_query, params = None):
    await log_message("Select SQL: " + sql_query + "\n" + "Parameters: " + str(params))
    try:
        connection = mysql.connector.connect(host='localhost', database='ServerPet', user='REDACTED', password='REDACTED')
        cursor = connection.cursor()
        result = cursor.execute(sql_query, params)
        records = cursor.fetchall()
        await log_message("Returned " + str(records))
        return records
    except mysql.connector.Error as error:
        await log_message("Database error! " + str(error))
        return None
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()

async def execute_sql(sql_query):
    try:
        connection = mysql.connector.connect(host='localhost', database='ServerPet', user='REDACTED', password='REDACTED')
        cursor = connection.cursor()
        result = cursor.execute(sql_query)
        return True
    except mysql.connector.Error as error:
        await log_message("Database error! " + str(error))
        return False
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            
            
async def send_message(message, response):
    await log_message("Message sent back to server " + message.guild.name + " channel " + message.channel.name + " in response to user " + message.author.name + "\n\n" + response)
    message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
    for chunk in message_chunks:
        await message.channel.send(">>> " + chunk)
        time.sleep(1)
		
@client.event
async def on_ready():
    await log_message("Logged into Discord!")

@client.event
async def on_guild_join(guild):
    await log_message("Joined guild " + guild.name)
    
@client.event
async def on_guild_remove(guild):
    await log_message("Left guild " + guild.name)
    
@client.event
async def on_message(message):
    invite_url = "https://discord.com/api/oauth2/authorize?client_id=765017910452027403&guild_permissions=68608&scope=bot"
    if message.author == client.user:
        return
    if message.author.bot:
        return
        
    if message.content.startswith(':3'):


        command_string = message.content.split(' ')
        command = command_string[1].replace(':3 ','')
        parsed_string = message.content.replace(":3 " + command + " ","")
        username = message.author.name
        server_name = message.guild.name

        await log_message("Command " + message.content + " called by " + username + " from " + server_name)
        if (command == 'sayhi'):
            await message.channel.send("Hello there!")
        elif command == 'mynameis':
            if not message.author.guild_permissions.manage_guild:
                await send_message(message, "You need manage server permissions to change my name!")
                return
            records = await select_sql("""SELECT Id FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            if not records:
                result = await commit_sql("""INSERT INTO ServerPets (ServerId, UserId, PetName,PetSleep,PetHunger,PetAttention, PetCreated, PetMood) VALUES (%s, %s, %s,'100','100','100', %s, 'Happy');""",(str(message.guild.id),str(message.author.id),str(parsed_string),str(datetime.now())))
            else:
                result = await commit_sql("""UPDATE ServerPets SET PetName=%s WHERE ServerId=%s;""",(str(parsed_string),str(message.guild.id)))
            await send_message(message, "My name is now " + parsed_string + "!")
        elif command == 'mygenderis':
            if not message.author.guild_permissions.manage_guild:
                await send_message(message, "You need manage server permissions to change my gender!")
                return        
            records = await select_sql("""SELECT Id FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            if not records:
                await send_message(message, "You need to name me first!")
                return
            else:
                result = await commit_sql("""UPDATE ServerPets SET PetGender=%s WHERE ServerId=%s;""",(str(parsed_string),str(message.guild.id)))
            await send_message(message, "My gender is now " + parsed_string + "!")
        elif command == 'myspeciesis':
            if not message.author.guild_permissions.manage_guild:
                await send_message(message, "You need manage server permissions to change my species!")
                return        
            records = await select_sql("""SELECT Id FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            if not records:
                await send_message(message, "You need to name me first!")
                return
            else:
                result = await commit_sql("""UPDATE ServerPets SET PetSpecies=%s WHERE ServerId=%s;""",(str(parsed_string),str(message.guild.id)))
            await send_message(message, "My species is now " + parsed_string + "!") 
        elif command == 'mypictureis':
            if not message.author.guild_permissions.manage_guild:
                await send_message(message, "You need manage server permissions to change my picture!")
                return        
            records = await select_sql("""SELECT Id FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            if not records:
                await send_message(message, "You need to name me first!")
                return
            else:
                if message.attachments:
                    picture_link = message.attachments[0].url
                else:
                    picture_link = parsed_string
                result = await commit_sql("""UPDATE ServerPets SET PetPicture=%s WHERE ServerId=%s;""",(str(picture_link),str(message.guild.id)))
            await send_message(message, "You've set my picture!")
        elif command == 'myprofile':
            records = await select_sql("""SELECT PetName,IFNULL(PetGender,'Unknown'),IFNULL(PetSpecies,'Unknown'),PetCreated,PetPicture FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            if not records:
                await send_message(message, "You don't have a pet yet!")
                return
            embed = discord.Embed(title=message.guild.name + "'s Pet Profile")
            for row in records:
                embed.add_field(name="Name:",value =row[0])
                embed.add_field(name="Gender:",value=row[1])
                embed.add_field(name="Species:",value=row[2])
                embed.add_field(name="Adopted on:",value=str(row[3]))
                if row[4] is not None:
                    embed.set_thumbnail(url=row[4])
                    
            await message.channel.send(embed=embed)
        elif command == 'deletepet':
            if not message.author.guild_permissions.manage_guild:
                await send_message(message, "You need manage server permissions to give me up!")
                return        
            result = await commit_sql("""DELETE FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            await send_message(message, "Sorry to see you go! I'll miss you!")
        elif command == 'checkonme':
            records = await select_sql("""SELECT PetSleep, PetHunger, PetAttention, PetMood, PetName FROM ServerPets WHERE Serverid=%s;""",(str(message.guild.id),))
            if not records:
                await send_message(message, "You don't have a pet yet!")
                return
            for row in records:
                pet_sleep = int(row[0])
                pet_hunger = int(row[1])
                pet_attention = int(row[2])
                pet_mood = row[3]
                pet_name = row[4]
                
            response = pet_name
            if pet_sleep < 40:
                response = response + " needs to sleep,"
            if pet_hunger < 50:
                response = response + " is hungry, "
            if pet_attention < 40:
                response = response + ", needs some loving, "
            if pet_attention < 40:
                pet_mood = random.choice(["Needy","Lonely","Sad","Depressed","Scared"])
            elif pet_sleep < 40:
                pet_mood = random.choice(["Tired","Cranky","Angry","Annoyed","Exhausted","Weary"])
            elif pet_hunger < 50:
                pet_moood = random.choice(["Hungry","Famished","Starving"])
            else:
                mood = random.choice(["Happy","Joyous","Excited","Loving","Affectionate","Coy"])
            response = response + " feels " + pet_mood
            await send_message(message, response)
        elif command == 'feedme':
            food = random.randint(1,30)
            records = await select_sql("""SELECT PetName,PetHunger FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            if not records:
                await send_message(message, "You don't have a pet yet!")
                return
            for row in records:
                pet_name = row[0]
                pet_hunger = int(row[1])
            if pet_hunger > 95:
                await send_message(message, pet_name + " is already full and won't eat anymore!")
                return
            response = ""
            if food < 10:
                response = response + pet_name + " only ate a little bit. "
            elif food >= 10 and food < 20:
                response = response + pet_name + " ate a decent meal. "
            else:
                response = response + pet_name + " ate a lot of food! "
            pet_hunger = pet_hunger + food
            if pet_hunger < 40:
                response = response + "I'm still starving!"
            elif pet_hunger >= 41 and pet_hunger <= 70:
                response = response + "I could eat some more!"
            else:
                response = response + "Thanks, I'm full!"
              
            result = await commit_sql("""UPDATE ServerPets SET PetHunger=%s WHERE ServerId=%s;""",(str(pet_hunger),str(message.guild.id)))
            
            await send_message(message, response)
        elif command == 'loveme':
            love = random.randint(1,15)
            records = await select_sql("""SELECT PetName,PetAttention FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            if not records:
                await send_message(message, "You don't have a pet yet!")
                return
            for row in records:
                pet_name = row[0]
                pet_attention = int(row[1])
            if pet_attention > 95:
                await send_message(message, pet_name + " has enough love and beams at you!")
                return
            response = ""
            if love < 5:
                response = response + pet_name + " appreciates the love. "
            elif love >= 5 and love < 10:
                response = response + pet_name + " enjoys the lovings. "
            else:
                response = response + pet_name + " pounces and snuggles you! "
            pet_attention = pet_attention + love
            if pet_attention < 40:
                response = response + "I need more love!"
            elif pet_attention >= 41 and pet_attention <= 70:
                response = response + "I am happy but wouldn't mind more love!"
            else:
                response = response + "I am full of love and affection!"
            result = await commit_sql("""UPDATE ServerPets SET PetAttention=%s WHERE ServerId=%s;""",(str(pet_attention),str(message.guild.id)))
            
            await send_message(message, response) 
        elif command == 'putmetobed':
            new_sleep = random.randint(1,70)
            records = await select_sql("""SELECT PetName,PetSleep FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
            if not records:
                await send_message(message, "You don't have a pet yet!")
                return
            for row in records:
                pet_name = row[0]
                pet_sleep = int(row[1])
            if pet_sleep > 95:
                await send_message(message, pet_name + " is wide awake and raring to go!")
                return
            response = ""
            if new_sleep < 20:
                response = response + pet_name + " took a short nap. "
            elif new_sleep >= 20 and new_sleep < 50:
                response = response + pet_name + " slept a while. "
            else:
                response = response + pet_name + " slept the whole day away! "
            pet_sleep = pet_sleep + new_sleep
            if pet_sleep < 40:
                response = response + "I'm still sleepy!"
            elif pet_sleep >= 41 and pet_sleep <= 70:
                response = response + "I am mostly rested!"
            else:
                response = response + "I am so wired!"
            result = await commit_sql("""UPDATE ServerPets SET PetSleep=%s WHERE ServerId=%s;""",(str(pet_sleep),str(message.guild.id)))
            
            await send_message(message, response)
        elif (command == 'info' or command == 'help'):
            await send_message(message, "My Server Pet Commands:\n\n`:3 mynameis NAME`: Set my name. When you set my name, that's my adoption date! You have to do this first!\n`:3 mygenderis GENDER`: Set my gender. It's up to you!\n`:3 myspeciesis SPECIES`: Set my species! It's up to you!\n`:3 mypictureis LINK`: Set my profile picture to either a link or a direct Discord upload!\n`:3 myprofile`: See my name, adoption date, gender and species!\n`:3 checkonme`: Check my mood and if I'm hungry, sleepy or need love!\n`:3 feedme:` Give me some food!\n`:3 putmetobed`: Make me go to bed and rest!\n`:3 loveme`: Give me lots of snuggles!\n`:3 deletepet`: If you want another pet, run this. I'll miss you!\n`:3 inviteme`: Invite me to your server!")
        elif command == 'inviteme':
            await send_message(message, "Click here to invite me! I'm excited! https://discord.com/api/oauth2/authorize?client_id=801954015663226940&guild_permissions=116800&scope=bot")
    else:
        records = await select_sql("""SELECT PetSleep, PetHunger, PetAttention FROM ServerPets WHERE ServerId=%s;""",(str(message.guild.id),))
        if not records:
            return
        for row in records:
            pet_sleep = int(row[0])
            pet_hunger = int(row[1])
            pet_attention = int(row[2])
        mood = ""    
        count_drop = random.randint(1,3)
        if count_drop == 1:
            pet_sleep = pet_sleep - random.randint(1,5)
        elif count_drop == 2:
            pet_hunger = pet_hunger - random.randint(1,10)
        elif count_drop == 3:
            pet_attention = pet_attention - random.randint(1,10)
        if pet_attention < 50:
            mood = random.choice(["Needy","Lonely","Sad","Depressed","Scared"])
        elif pet_sleep < 30:
            mood = random.choice(["Tired","Cranky","Angry","Annoyed","Exhausted","Weary"])
        elif pet_hunger < 50:
            moood = random.choice(["Hungry","Famished","Starving"])
        else:
            mood = random.choice(["Happy","Joyous","Excited","Loving","Affectionate","Coy"])
        if pet_sleep < 0:
            pet_sleep = 0
        if pet_hunger < 0:
            pet_hunger = 0
        if pet_attention < 0:
            pet_attention = 0
        await commit_sql("""UPDATE ServerPets SET PetSleep=%s,PetHunger=%s,PetAttention=%s,PetMood=%s WHERE ServerId=%s;""",(str(pet_sleep),str(pet_hunger),str(pet_attention),str(mood),str(message.guild.id)))
        


client.run('REDACTED')