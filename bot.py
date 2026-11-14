import os
import json
import threading
import asyncio
from datetime import timedelta
import discord
from discord.ext import commands
from flask import Flask, render_template_string, request, redirect, url_for

# --- 1. WEB DASHBOARD & RENDER KEEP-ALIVE SERVER ---
app = Flask('')
app.secret_key = "adda_zone_secure_dashboard_key"

CONFIG_FILE = "config.json"
WHITELIST_FILE = "whitelist.json"
PUNISHMENT_FILE = "punishments.json"
data_lock = threading.Lock()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adda_Zone Security • Progressive Punishment Hub</title>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 850px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        h1 { color: #38bdf8; text-align: center; margin-bottom: 5px; font-size: 24px; }
        p.subtitle { text-align: center; color: #94a3b8; margin-bottom: 30px; font-size: 14px; }
        .card { background: #0f172a; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #334155; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #cbd5e1; }
        input[type="text"], select { width: 100%; padding: 10px; background: #1e293b; border: 1px solid #475569; border-radius: 6px; color: #fff; margin-bottom: 15px; box-sizing: border-box; }
        button { background: #0284c7; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; transition: background 0.2s; }
        button:hover { background: #0369a1; }
        .status-badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; background: #065f46; color: #34d399; }
        .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Adda_Zone Security Dashboard</h1>
        <p class="subtitle">Progressive Punishment & Granular Access Hub</p>
        
        <div class="card">
            <h3>System Status</h3>
            <p>Operational State: <span class="status-badge">ONLINE & SECURE</span></p>
            <p>Host Environment: <strong>Render Cloud Engine</strong></p>
        </div>

        <div class="card">
            <h3>Command-Specific Permission Panel</h3>
            <form method="POST" action="/update">
                <label for="guild_id">Target Server ID (Guild ID):</label>
                <input type="text" id="guild_id" name="guild_id" placeholder="Enter Discord Server ID" required>

                <label for="command_name">Select Command to Restrict:</label>
                <select id="command_name" name="command_name">
                    <option value="kick">Kick Command</option>
                    <option value="ban">Ban Command</option>
                    <option value="timeout">Timeout Command</option>
                    <option value="antinuke">Anti-Nuke Toggle</option>
                    <option value="setprefix">Prefix Change</option>
                    <option value="everyone_ping">Everyone / Role Ping Access</option>
                </select>

                <label for="user_id">User ID to Grant Permission:</label>
                <input type="text" id="user_id" name="user_id" placeholder="Discord User ID">

                <label for="system_active">System Activation (true/false):</label>
                <input type="text" id="system_active" name="system_active" placeholder="true or false" value="true">

                <button type="submit">Update Core Permissions</button>
            </form>
        </div>
        <div class="footer">Adda_Zone Security Architecture • Progressive Suite v5.3</div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/update', methods=['POST'])
def update_config():
    guild_id = request.form.get('guild_id', '').strip()
    command_name = request.form.get('command_name', '').strip()
    user_id = request.form.get('user_id', '').strip()
    system_active_val = request.form.get('system_active', 'true').lower() == 'true'

    if guild_id:
        with data_lock:
            whitelist_data = load_whitelist()
            if guild_id not in whitelist_data:
                whitelist_data[guild_id] = {
                    "active": False,
                    "prefix": "!",
                    "antinuke": True,
                    "command_permissions": {
                        "kick": [],
                        "ban": [],
                        "timeout": [],
                        "antinuke": [],
                        "setprefix": [],
                        "everyone_ping": []
                    },
                    "custom_cmds": {}
                }
            
            whitelist_data[guild_id]["active"] = system_active_val
            
            if user_id.isdigit() and command_name:
                uid = int(user_id)
                if "command_permissions" not in whitelist_data[guild_id]:
                    whitelist_data[guild_id]["command_permissions"] = {
                        "kick": [], "ban": [], "timeout": [], "antinuke": [], "setprefix": [], "everyone_ping": []
                    }
                
                if command_name in whitelist_data[guild_id]["command_permissions"]:
                    if uid not in whitelist_data[guild_id]["command_permissions"][command_name]:
                        whitelist_data[guild_id]["command_permissions"][command_name].append(uid)
            
            save_whitelist(whitelist_data)
    return redirect(url_for('dashboard'))

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()


# --- 2. CONFIGURATION & STATE MANAGEMENT ---
CONFIG_FILE = "config.json"
WHITELIST_FILE = "whitelist.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            if "prefix" not in data:
                data["prefix"] = "!"
            return data
    
    print("==========================================")
    print("   ADDA_ZONE SECURITY BOT - FIRST SETUP")
    print("==========================================")
    token = input("Enter Bot Token: ").strip()
    owner_id_input = input("Enter Global Owner ID: ").strip()
    
    try:
        owner_id = int(owner_id_input)
    except ValueError:
        owner_id = 0

    config = {"token": token, "owner_id": owner_id, "prefix": "!"}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
        
    print("[SUCCESS] Configuration saved successfully.\n")
    return config

config = load_config()

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_whitelist(data):
    with data_lock:
        with open(WHITELIST_FILE, "w") as f:
            json.dump(data, f, indent=4)

whitelist_data = load_whitelist()

# --- PROGRESSIVE PUNISHMENT SYSTEM ---
def load_punishments():
    if os.path.exists(PUNISHMENT_FILE):
        try:
            with open(PUNISHMENT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_punishments(data):
    with data_lock:
        with open(PUNISHMENT_FILE, "w") as f:
            json.dump(data, f, indent=4)

async def apply_progressive_punishment(member, reason_text):
    """প্রথমবার টাইমআউট, দ্বিতীয়বার কিক, তৃতীয়বার সরাসরি ব্যান"""
    punishments = load_punishments()
    guild_id = str(member.guild.id)
    user_id = str(member.id)
    
    if guild_id not in punishments:
        punishments[guild_id] = {}
        
    current_strikes = punishments[guild_id].get(user_id, 0) + 1
    punishments[guild_id][user_id] = current_strikes
    save_punishments(punishments)
    
    try:
        if current_strikes == 1:
            # প্রথম অপরাধ: ১০ মিনিটের টাইমআউট
            await member.timeout(timedelta(minutes=10), reason=f"Violation Strike 1: {reason_text}")
            try:
                await member.send(f"⚠️ **Security Notice:** You have received a **10-minute timeout** for violating server security rules. ({reason_text})")
            except:
                pass
        elif current_strikes == 2:
            # দ্বিতীয় অপরাধ: কিক
            await member.kick(reason=f"Violation Strike 2: {reason_text}")
        else:
            # তৃতীয় বা তার বেশি অপরাধ: চিরতরে ব্যান
            await member.ban(reason=f"Violation Strike 3+: {reason_text}")
    except Exception as e:
        print(f"[PUNISHMENT ERROR] Could not punish user {member.name}: {e}")

def get_prefix(bot, message):
    if not message.guild:
        return config.get("prefix", "!")
    guild_id = str(message.guild.id)
    return whitelist_data.get(guild_id, {}).get("prefix", config.get("prefix", "!"))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# --- GRANULAR PERMISSION CHECKER ---
def is_system_active(guild_id):
    g_data = whitelist_data.get(str(guild_id), {})
    return g_data.get("active", False)

def has_command_permission(ctx, command_name):
    if ctx.author.id == config["owner_id"]:
        return True
    
    if ctx.guild:
        if ctx.author.id == ctx.guild.owner_id:
            return True
            
        guild_id = str(ctx.guild.id)
        g_data = whitelist_data.get(guild_id, {})
        cmd_perms = g_data.get("command_permissions", {})
        allowed_users = cmd_perms.get(command_name, [])
        
        if ctx.author.id in allowed_users:
            return True
            
    return False

@bot.event
async def on_ready():
    print(f'[ONLINE] Authenticated as {bot.user} (ID: {bot.user.id})')
    print('[SECURITY] Progressive Punishments & Granular Access Active.')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over the network | !help"))

@bot.before_invoke
async def log_server_activity(ctx):
    if ctx.guild:
        print(f"[AUDIT] Command '{ctx.command}' executed in '{ctx.guild.name}' by {ctx.author} ({ctx.author.id})")
    else:
        print(f"[AUDIT-DM] Command '{ctx.command}' executed by {ctx.author}")


# --- 3. BOT COMMANDS ---

@bot.command(name="on", aliases=["start", "enable"])
async def system_on(ctx):
    if not ctx.guild:
        return
    if ctx.author.id != config["owner_id"] and ctx.author.id != ctx.guild.owner_id:
        return
    
    guild_id = str(ctx.guild.id)
    if guild_id not in whitelist_data:
        whitelist_data[guild_id] = {
            "active": False, "prefix": "!", "antinuke": True,
            "command_permissions": {"kick": [], "ban": [], "timeout": [], "antinuke": [], "setprefix": [], "everyone_ping": []},
            "custom_cmds": {}
        }
    
    whitelist_data[guild_id]["active"] = True
    save_whitelist(whitelist_data)
    
    embed = discord.Embed(title="🟢 System Fully Activated", description="Adda_Zone Security protocols are now **ONLINE and Operational**.", color=discord.Color.from_rgb(46, 204, 113))
    await ctx.send(embed=embed)

@bot.command(name="off", aliases=["stop", "disable"])
async def system_off(ctx):
    if not ctx.guild:
        return
    if ctx.author.id != config["owner_id"] and ctx.author.id != ctx.guild.owner_id:
        return
    
    guild_id = str(ctx.guild.id)
    if guild_id not in whitelist_data:
        whitelist_data[guild_id] = {
            "active": False, "prefix": "!", "antinuke": True,
            "command_permissions": {"kick": [], "ban": [], "timeout": [], "antinuke": [], "setprefix": [], "everyone_ping": []},
            "custom_cmds": {}
        }
    
    whitelist_data[guild_id]["active"] = False
    save_whitelist(whitelist_data)
    
    embed = discord.Embed(title="🔴 System Deactivated", description="Adda_Zone Security protocols have been placed on **Standby**.", color=discord.Color.from_rgb(231, 76, 60))
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["commands", "panel"])
async def help_command(ctx):
    if ctx.guild and not is_system_active(ctx.guild.id):
        if ctx.author.id != config["owner_id"] and ctx.author.id != ctx.guild.owner_id:
            return
    
    prefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(
        title="🛡️ Granular Control Center",
        description=f"Advanced command authorization directory.\n**Active Prefix:** `{prefix}`",
        color=discord.Color.from_rgb(35, 39, 42)
    )
    embed.add_field(name="⚙️ Core & Permissions", value=f"`{prefix}on` / `{prefix}off` - System Master Switch\n`{prefix}setprefix` - Modify prefix\n`{prefix}antinuke` - Toggle defense", inline=False)
    embed.add_field(name="⚖️ Granular Moderation", value=f"`{prefix}kick <user>` - Evict member\n`{prefix}ban <user>` - Permanent ban\n`{prefix}timeout <user> <mins>` - Timeout member", inline=False)
    embed.set_footer(text="Adda_Zone Security Architecture • Version 5.3")
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="⚡ Network Latency", description=f"Response time: **{latency}ms**.", color=discord.Color.from_rgb(46, 204, 113))
    await ctx.send(embed=embed)

@bot.command(name="status", aliases=["botstatus", "health"])
async def status(ctx):
    if not ctx.guild:
        return
    guild_id = str(ctx.guild.id)
    g_data = whitelist_data.get(guild_id, {})
    sys_state = "🟢 Online (Active)" if g_data.get("active", False) else "🔴 Offline (Standby)"
    latency = round(bot.latency * 1000)
    server_prefix = g_data.get("prefix", config.get("prefix", "!"))
    
    embed = discord.Embed(title="📊 Granular Access Diagnostics", description=f"Environment context for **{ctx.guild.name}**", color=discord.Color.from_rgb(52, 152, 219))
    embed.add_field(name="System Status", value=sys_state, inline=False)
    embed.add_field(name="Prefix", value=f"`{server_prefix}`", inline=True)
    embed.add_field(name="Latency", value=f"`{latency}ms`", inline=True)
    embed.set_footer(text="Progressive Punishment Engine Active")
    await ctx.send(embed=embed)

@bot.command(name="setprefix")
async def setprefix(ctx, new_prefix: str):
    if not ctx.guild:
        return
    if not has_command_permission(ctx, "setprefix"):
        await apply_progressive_punishment(ctx.author, "Unauthorized attempt to change prefix")
        return
    
    guild_id = str(ctx.guild.id)
    if guild_id not in whitelist_data:
        whitelist_data[guild_id] = {"active": False, "prefix": "!", "antinuke": True, "command_permissions": {"kick": [], "ban": [], "timeout": [], "antinuke": [], "setprefix": [], "everyone_ping": []}, "custom_cmds": {}}
    
    whitelist_data[guild_id]["prefix"] = new_prefix
    save_whitelist(whitelist_data)
    
    embed = discord.Embed(title="⚙️ Prefix Updated", description=f"New prefix: **`{new_prefix}`**", color=discord.Color.from_rgb(46, 204, 113))
    await ctx.send(embed=embed)

@bot.command(name="antinuke")
async def antinuke(ctx, mode: str):
    if not ctx.guild:
        return
    if not has_command_permission(ctx, "antinuke"):
        await apply_progressive_punishment(ctx.author, "Unauthorized attempt to toggle antinuke")
        return
    
    guild_id = str(ctx.guild.id)
    if guild_id not in whitelist_data:
        whitelist_data[guild_id] = {"active": False, "prefix": "!", "antinuke": True, "command_permissions": {"kick": [], "ban": [], "timeout": [], "antinuke": [], "setprefix": [], "everyone_ping": []}, "custom_cmds": {}}
    
    if mode.lower() == "on":
        whitelist_data[guild_id]["antinuke"] = True
        save_whitelist(whitelist_data)
        embed = discord.Embed(title="🛡️ Defense Protocol", description="Anti-Nuke status: **Enabled**", color=discord.Color.from_rgb(46, 204, 113))
        await ctx.send(embed=embed)
    elif mode.lower() == "off":
        whitelist_data[guild_id]["antinuke"] = False
        save_whitelist(whitelist_data)
        embed = discord.Embed(title="⚠️ Defense Protocol", description="Anti-Nuke status: **Disabled**", color=discord.Color.from_rgb(231, 76, 60))
        await ctx.send(embed=embed)

@bot.command(name="kick")
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if not ctx.guild:
        return
    if not has_command_permission(ctx, "kick"):
        await apply_progressive_punishment(ctx.author, "Unauthorized execution of kick command")
        return
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(title="👢 Member Evicted", description=f"Evicted {member.mention}\nReason: `{reason}`", color=discord.Color.from_rgb(231, 76, 60))
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Execution Error: {e}")

@bot.command(name="ban")
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if not ctx.guild:
        return
    if not has_command_permission(ctx, "ban"):
        await apply_progressive_punishment(ctx.author, "Unauthorized execution of ban command")
        return
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(title="🔨 Member Banned", description=f"Banned {member.mention}\nReason: `{reason}`", color=discord.Color.from_rgb(192, 57, 43))
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Execution Error: {e}")

@bot.command(name="timeout")
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    if not ctx.guild:
        return
    if not has_command_permission(ctx, "timeout"):
        await apply_progressive_punishment(ctx.author, "Unauthorized execution of timeout command")
        return
    try:
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="⏰ Activity Restricted", description=f"Timed out {member.mention} for `{minutes} minutes`.", color=discord.Color.from_rgb(241, 196, 15))
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Execution Error: {e}")


# --- 4. EVENTS & INTERCEPTORS (PROGRESSIVE PUNISHMENT SYSTEM) ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    try:
        if message.guild:
            guild_id = str(message.guild.id)
            
            if not is_system_active(guild_id):
                prefix = get_prefix(bot, message)
                if not message.content.startswith(prefix + "on"):
                    return
            
            g_data = whitelist_data.get(guild_id, {})
            prefix = g_data.get("prefix", config.get("prefix", "!"))
            
            is_global_owner = (message.author.id == config["owner_id"])
            is_guild_owner = (message.author.id == message.guild.owner_id)
            
            cmd_perms = g_data.get("command_permissions", {})
            allowed_pings = cmd_perms.get("everyone_ping", [])
            is_ping_allowed = (message.author.id in allowed_pings) or message.author.guild_permissions.mention_everyone
            
            # --- @everyone বা মাস পিং ভায়োলেশন চেক ---
            if ("@everyone" in message.content or "@here" in message.content or message.role_mentions) and not (is_global_owner or is_guild_owner or is_ping_allowed):
                try:
                    await message.delete()
                    await apply_progressive_punishment(message.author, "Unauthorized mass ping distribution")
                    return
                except:
                    pass

            # --- লিংক স্প্যাম ভায়োলেশন চেক ---
            if not (is_global_owner or is_guild_owner or message.author.guild_permissions.administrator):
                if "http://" in message.content or "https://www.discord.gg" in message.content or "discord.com/invite" in message.content:
                    try:
                        await message.delete()
                        await apply_progressive_punishment(message.author, "Unauthorized link distribution")
                        return
                    except:
                        pass
    except Exception as e:
        print(f"[Error] Message interceptor exception: {e}")

    await bot.process_commands(message)

@bot.event
async def on_guild_channel_delete(channel):
    try:
        guild_id = str(channel.guild.id)
        if not is_system_active(guild_id):
            return
        g_data = whitelist_data.get(guild_id, {})
        if not g_data.get("antinuke", True):
            return
        
        await asyncio.sleep(1.2)
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user
            if not user or user.id == bot.user.id or user.id == config["owner_id"] or user.id == channel.guild.owner_id:
                return
            
            member = channel.guild.get_member(user.id)
            if member:
                try:
                    await member.ban(reason="Anti-Nuke Trigger: Unauthorized channel deletion.")
                    print(f"[SECURITY] Neutralized threat: Banned {user.name} in '{channel.guild.name}'")
                except Exception as ex:
                    print(f"[ERROR] Could not neutralize threat: {ex}")
    except Exception as e:
        print(f"[Error] Channel monitor exception: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ **Syntax Error:** Required parameters are missing.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ **Syntax Error:** Invalid parameter types provided.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ **Access Denied:** Insufficient clearance level.")
    else:
        print(f"[Error] Unhandled exception in command '{ctx.command}': {error}")


# --- 5. MAIN EXECUTION ---
if __name__ == "__main__":
    keep_alive()
    bot_token = config.get("token")
    if bot_token:
        try:
            bot.run(bot_token)
        except Exception as e:
            print(f"❌ Fatal Error: {e}")
    else:
        print("❌ Critical: Bot token not found.")
