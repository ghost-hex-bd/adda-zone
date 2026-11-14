import os
import json
import threading
import asyncio
from datetime import timedelta
import discord
from discord.ext import commands, tasks
from flask import Flask, render_template_string, request, redirect, url_for

# --- 1. ENTERPRISE WEB DASHBOARD (HIDDEN GLOBAL OWNER & DUAL-LEVEL PERMISSIONS) ---
app = Flask('')
app.secret_key = "adda_zone_secure_dashboard_key_v12"
data_lock = threading.Lock()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adda_Zone Security • Server Management Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #090d16;
            --card-bg: #111827;
            --border-color: #1f2937;
            --accent-glow: #0ea5e9;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }
        body { background-color: var(--bg-color); color: var(--text-main); font-family: 'Inter', sans-serif; margin: 0; padding: 30px; display: flex; justify-content: center; align-items: center; min-height: 100vh; box-sizing: border-box; }
        .container { width: 100%; max-width: 850px; background: var(--card-bg); padding: 40px; border-radius: 16px; border: 1px solid var(--border-color); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6); }
        .header { text-align: center; margin-bottom: 30px; position: relative; }
        h1 { color: #38bdf8; margin: 0 0 8px 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }
        p.subtitle { color: var(--text-muted); margin: 0; font-size: 14px; font-weight: 400; }
        
        .lang-selector { position: absolute; top: 0; right: 0; }
        .lang-selector select { padding: 6px 10px; background: #0a0f1d; border: 1px solid var(--border-color); border-radius: 6px; color: #38bdf8; font-size: 12px; font-weight: 600; cursor: pointer; }

        .status-box { background: rgba(14, 165, 233, 0.05); border: 1px solid rgba(14, 165, 233, 0.2); padding: 16px 20px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .status-title { font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .status-badge { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #34d399; }
        .dot { width: 8px; height: 8px; background-color: #34d399; border-radius: 50%; box-shadow: 0 0 10px #34d399; }

        .form-section { background: #0a0f1d; padding: 20px; border-radius: 10px; border: 1px solid var(--border-color); margin-bottom: 20px; }
        .section-title { font-size: 14px; font-weight: 600; color: #38bdf8; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }
        
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 6px; font-weight: 500; font-size: 13px; color: #d1d5db; }
        input[type="text"], select { width: 100%; padding: 12px 16px; background: #111827; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box; transition: all 0.3s ease; }
        input[type="text"]:focus, select:focus { outline: none; border-color: var(--accent-glow); box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15); }
        
        button { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: white; border: none; padding: 14px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; width: 100%; transition: all 0.3s ease; margin-top: 10px; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3); }
        button:hover { background: linear-gradient(135deg, #0369a1 0%, #075985 100%); transform: translateY(-1px); box-shadow: 0 6px 16px rgba(2, 132, 199, 0.4); }
        
        .footer { text-align: center; color: #4b5563; font-size: 12px; margin-top: 30px; border-top: 1px solid var(--border-color); padding-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="lang-selector">
                <select id="lang_switch" onchange="switchLanguage()">
                    <option value="en" selected>English</option>
                    <option value="bn">বাংলা</option>
                </select>
            </div>
            <h1 id="t_title">🛡️ Adda_Zone Security Hub</h1>
            <p class="subtitle" id="t_subtitle">Server Owner Protected Dashboard • v12.0</p>
        </div>
        
        <div class="status-box">
            <div>
                <span class="status-title" id="t_runtime_title">System Runtime</span>
                <div style="font-size: 14px; font-weight: 600; margin-top: 2px;">Render Cloud Engine</div>
            </div>
            <div class="status-badge">
                <div class="dot"></div> <span id="t_runtime_status">ONLINE & SECURED</span>
            </div>
        </div>

        <form method="POST" action="/update">
            <div class="form-section">
                <div class="section-title" id="t_sec1_title">🔒 Owner Authentication & Server Core</div>
                <div class="form-group">
                    <label for="admin_user_id" id="t_lbl_admin">Your Discord User ID *</label>
                    <input type="text" id="admin_user_id" name="admin_user_id" placeholder="Enter your Discord User ID" required>
                </div>
                <div class="form-group">
                    <label for="guild_id" id="t_lbl_guild">Target Server ID (Guild ID) *</label>
                    <input type="text" id="guild_id" name="guild_id" placeholder="Enter Discord Server ID" required>
                </div>

                <div class="form-group">
                    <label for="action_type" id="t_lbl_action">Action Type</label>
                    <select id="action_type" name="action_type">
                        <option value="grant">Grant / Add Permission (whitelist)</option>
                        <option value="revoke">Revoke / Remove Permission</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="command_name" id="t_lbl_cmd">Select Command / Feature Privilege</label>
                    <select id="command_name" name="command_name">
                        <option value="kick">Kick Command Access</option>
                        <option value="ban">Ban Command Access</option>
                        <option value="timeout">Timeout Command Access</option>
                        <option value="antinuke">Anti-Nuke Toggle Access</option>
                        <option value="setprefix">Prefix Change Access</option>
                        <option value="everyone_ping">Mass Ping / Role Ping Access</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="user_id" id="t_lbl_target_user">Target User ID (To Grant or Revoke)</label>
                    <input type="text" id="user_id" name="user_id" placeholder="e.g. 987654321098765432">
                </div>

                <div class="form-group">
                    <label for="system_active" id="t_lbl_sys_status">System Core Status</label>
                    <select id="system_active" name="system_active">
                        <option value="true" id="t_opt_sys_on">🟢 Fully Activated (ON)</option>
                        <option value="false" id="t_opt_sys_off">🔴 Standby / Deactivated (OFF)</option>
                    </select>
                </div>
            </div>

            <div class="form-section">
                <div class="section-title" id="t_sec2_title">⏰ 24/7 Keep-Alive Auto-Ping Settings</div>
                <div class="form-group">
                    <label for="ping_toggle" id="t_lbl_ping_toggle">Auto-Ping Switch (Enable/Disable)</label>
                    <select id="ping_toggle" name="ping_toggle">
                        <option value="true" id="t_opt_ping_on">🟢 Enable Auto-Ping (Active)</option>
                        <option value="false" id="t_opt_ping_off">🔴 Disable Auto-Ping (Off)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="ping_channel_id" id="t_lbl_ping_chan">Keep-Alive Target Channel ID</label>
                    <input type="text" id="ping_channel_id" name="ping_channel_id" placeholder="Enter Channel ID for 10-min Ping">
                </div>
                <div class="form-group">
                    <label for="ping_role_id" id="t_lbl_ping_role">Keep-Alive Target Role ID to Ping</label>
                    <input type="text" id="ping_role_id" name="ping_role_id" placeholder="Enter Role ID to notify">
                </div>
            </div>

            <button type="submit" id="t_btn_submit">Verify & Commit Changes</button>
        </form>

        <div class="footer">
            Adda_Zone Enterprise Security Architecture • End-to-End Encrypted
        </div>
    </div>

    <script>
        const translations = {
            en: {
                title: "🛡️ Adda_Zone Security Hub",
                subtitle: "Server Owner Protected Dashboard • v12.0",
                runtime_title: "System Runtime",
                runtime_status: "ONLINE & SECURED",
                sec1_title: "🔒 Owner Authentication & Server Core",
                lbl_admin: "Your Discord User ID *",
                lbl_guild: "Target Server ID (Guild ID) *",
                lbl_action: "Action Type",
                lbl_cmd: "Select Command / Feature Privilege",
                lbl_target_user: "Target User ID (To Grant or Revoke)",
                lbl_sys_status: "System Core Status",
                opt_sys_on: "🟢 Fully Activated (ON)",
                opt_sys_off: "🔴 Standby / Deactivated (OFF)",
                sec2_title: "⏰ 24/7 Keep-Alive Auto-Ping Settings",
                lbl_ping_toggle: "Auto-Ping Switch (Enable/Disable)",
                opt_ping_on: "🟢 Enable Auto-Ping (Active)",
                opt_ping_off: "🔴 Disable Auto-Ping (Off)",
                lbl_ping_chan: "Keep-Alive Target Channel ID",
                lbl_ping_role: "Keep-Alive Target Role ID to Ping",
                btn_submit: "Verify & Commit Changes"
            },
            bn: {
                title: "🛡️ আড্ডা জোন সিকিউরিটি হাব",
                subtitle: "সার্ভার ওনার প্রটেক্টেড ড্যাশবোর্ড • v১২.০",
                runtime_title: "সিস্টেম রানিং অবস্থা",
                runtime_status: "অনলাইন ও সুরক্ষিত",
                sec1_title: "🔒 ওনার অথেন্টিকেশন ও সার্ভার কোর",
                lbl_admin: "আপনার ডিসকর্ড ইউজার আইডি *",
                lbl_guild: "টার্গেট সার্ভার আইডি (গিল্ড আইডি) *",
                lbl_action: "কাজের ধরণ (পারমিশন দেওয়া বা তুলে নেওয়া)",
                lbl_cmd: "কমান্ড বা ফিচারের পারমিশন সিলেক্ট করুন",
                lbl_target_user: "টার্গেট ইউজার আইডি (যার পারমিশন পরিবর্তন হবে)",
                lbl_sys_status: "সিস্টেম কোরের অবস্থা",
                opt_sys_on: "🟢 পুরোপুরি সচল (ON)",
                opt_sys_off: "🔴 স্ট্যান্ডবাই / বন্ধ (OFF)",
                sec2_title: "⏰ ২৪/৭ সচল রাখার অটো-পিং সেটিংস",
                lbl_ping_toggle: "অটো-পিং সুইচ (চালু/বন্ধ)",
                opt_ping_on: "🟢 অটো-পিং চালু করুন (Active)",
                opt_ping_off: "🔴 অটো-পিং বন্ধ রাখুন (Off)",
                lbl_ping_chan: "অটো-পিং পাঠানোর টার্গেট চ্যানেল আইডি",
                lbl_ping_role: "পিং করার জন্য টার্গেট রোল আইডি",
                btn_submit: "ভেরিফাই করুন এবং পরিবর্তন সেভ করুন"
            }
        };

        function switchLanguage() {
            const lang = document.getElementById('lang_switch').value;
            const t = translations[lang];

            document.getElementById('t_title').innerText = t.title;
            document.getElementById('t_subtitle').innerText = t.subtitle;
            document.getElementById('t_runtime_title').innerText = t.runtime_title;
            document.getElementById('t_runtime_status').innerText = t.runtime_status;
            document.getElementById('t_sec1_title').innerText = t.sec1_title;
            document.getElementById('t_lbl_admin').innerText = t.lbl_admin;
            document.getElementById('t_lbl_guild').innerText = t.lbl_guild;
            document.getElementById('t_lbl_action').innerText = t.lbl_action;
            document.getElementById('t_lbl_cmd').innerText = t.lbl_cmd;
            document.getElementById('t_lbl_target_user').innerText = t.lbl_target_user;
            document.getElementById('t_lbl_sys_status').innerText = t.lbl_sys_status;
            document.getElementById('t_opt_sys_on').innerText = t.opt_sys_on;
            document.getElementById('t_opt_sys_off').innerText = t.opt_sys_off;
            document.getElementById('t_sec2_title').innerText = t.sec2_title;
            document.getElementById('t_lbl_ping_toggle').innerText = t.lbl_ping_toggle;
            document.getElementById('t_opt_ping_on').innerText = t.opt_ping_on;
            document.getElementById('t_opt_ping_off').innerText = t.opt_ping_off;
            document.getElementById('t_lbl_ping_chan').innerText = t.lbl_ping_chan;
            document.getElementById('t_lbl_ping_role').innerText = t.lbl_ping_role;
            document.getElementById('t_btn_submit').innerText = t.btn_submit;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/update', methods=['POST'])
def update_config():
    admin_user_id = request.form.get('admin_user_id', '').strip()
    guild_id = request.form.get('guild_id', '').strip()
    action_type = request.form.get('action_type', 'grant').strip()
    command_name = request.form.get('command_name', '').strip()
    user_id = request.form.get('user_id', '').strip()
    system_active_val = request.form.get('system_active', 'true').lower() == 'true'
    
    ping_toggle_val = request.form.get('ping_toggle', 'false').lower() == 'true'
    ping_channel_id = request.form.get('ping_channel_id', '').strip()
    ping_role_id = request.form.get('ping_role_id', '').strip()

    if not admin_user_id.isdigit() or not guild_id.isdigit():
        return redirect(url_for('dashboard'))

    uid_admin = int(admin_user_id)
    g_id_int = int(guild_id)

    global_owner = global_config.get("owner_id", 0)
    is_global = (uid_admin == global_owner)
    
    guild_obj = bot.get_guild(g_id_int)
    is_server_owner = False
    if guild_obj and guild_obj.owner_id == uid_admin:
        is_server_owner = True

    g_data_temp = load_server_config(guild_id)
    permission_managers = g_data_temp.get("permission_managers", [])
    is_manager = uid_admin in permission_managers

    if not (is_global or is_server_owner or is_manager):
        return redirect(url_for('dashboard'))

    with data_lock:
        g_data = load_server_config(guild_id)
        
        if user_id.isdigit():
            target_uid = int(user_id)
            if guild_obj and target_uid == guild_obj.owner_id:
                return redirect(url_for('dashboard'))
            if target_uid == global_config.get("owner_id", 0):
                return redirect(url_for('dashboard'))

        g_data["active"] = system_active_val
        g_data["ping_enabled"] = ping_toggle_val
        
        if ping_channel_id.isdigit():
            g_data["ping_channel_id"] = int(ping_channel_id)
        if ping_role_id.isdigit():
            g_data["ping_role_id"] = int(ping_role_id)
        
        if user_id.isdigit() and command_name:
            uid = int(user_id)
            if command_name in g_data["command_permissions"]:
                if action_type == "grant":
                    if uid not in g_data["command_permissions"][command_name]:
                        g_data["command_permissions"][command_name].append(uid)
                elif action_type == "revoke":
                    if uid in g_data["command_permissions"][command_name]:
                        g_data["command_permissions"][command_name].remove(uid)
        
        save_server_config(guild_id, g_data)
        
    return redirect(url_for('dashboard'))

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()


# --- 2. GLOBAL & ISOLATED FILE MANAGEMENT ---
CONFIG_FILE = "config.json"

def load_global_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    
    token = os.environ.get('DISCORD_BOT_TOKEN')
    owner_id_input = os.environ.get('OWNER_ID', '0')
    
    if not token:
        token = input("Enter Bot Token: ").strip()
        owner_id_input = input("Enter Global Owner ID: ").strip()
    
    try:
        owner_id = int(owner_id_input)
    except ValueError:
        owner_id = 0

    config = {"token": token, "owner_id": owner_id, "prefix": "!"}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    return config

global_config = load_global_config()

def get_server_config_filename(guild_id):
    return f"server_{guild_id}_config.json"

def get_server_punishment_filename(guild_id):
    return f"server_{guild_id}_punishments.json"

def load_server_config(guild_id):
    filename = get_server_config_filename(guild_id)
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "active": False,
        "prefix": "!",
        "antinuke": True,
        "ping_enabled": False,
        "ping_channel_id": None,
        "ping_role_id": None,
        "permission_managers": [],
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

def save_server_config(guild_id, data):
    filename = get_server_config_filename(guild_id)
    with data_lock:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

def load_server_punishments(guild_id):
    filename = get_server_punishment_filename(guild_id)
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_server_punishments(guild_id, data):
    filename = get_server_punishment_filename(guild_id)
    with data_lock:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

def get_prefix(bot, message):
    if not message.guild:
        return global_config.get("prefix", "!")
    guild_id = str(message.guild.id)
    g_data = load_server_config(guild_id)
    return g_data.get("prefix", "!")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# --- 24/7 BACKGROUND KEEP-ALIVE PING TASK ---
@tasks.loop(minutes=10)
async def uptime_keep_alive_ping():
    for guild in bot.guilds:
        try:
            guild_id = str(guild.id)
            g_data = load_server_config(guild_id)
            
            if not g_data.get("active", False) or not g_data.get("ping_enabled", False):
                continue
                
            channel_id = g_data.get("ping_channel_id")
            role_id = g_data.get("ping_role_id")
            
            if channel_id and role_id:
                channel = guild.get_channel(channel_id)
                role = guild.get_role(role_id)
                
                if channel and role:
                    await channel.send(f"🛡️ **[24/7 Uptime Signal]** Keep-Alive active check. {role.mention}")
        except Exception as e:
            print(f"[UPTIME PING ERROR] Guild {guild.name}: {e}")

@uptime_keep_alive_ping.before_loop
async def before_uptime_ping():
    await bot.wait_until_ready()

# --- ISOLATED PROGRESSIVE PUNISHMENT SYSTEM ---
async def apply_progressive_punishment(member, reason_text):
    guild_id = str(member.guild.id)
    user_id = str(member.id)
    
    punishments = load_server_punishments(guild_id)
    current_strikes = punishments.get(user_id, 0) + 1
    punishments[user_id] = current_strikes
    save_server_punishments(guild_id, punishments)
    
    try:
        if current_strikes == 1:
            await member.timeout(timedelta(minutes=10), reason=f"Unauthorized Command Attempt 1: {reason_text}")
            try:
                await member.send(f"⚠️ **Security Warning (Strike 1):** You have received a **10-minute timeout** in **{member.guild.name}** for trying to use bot commands without whitelist authorization.")
            except:
                pass
        elif current_strikes == 2:
            await member.kick(reason=f"Unauthorized Command Attempt 2: {reason_text}")
        else:
            await member.ban(reason=f"Unauthorized Command Attempt 3+: {reason_text}")
    except Exception as e:
        print(f"[PUNISHMENT ERROR] Could not punish user {member.name}: {e}")

@bot.check
async def global_whitelist_check(ctx):
    if not ctx.guild:
        return True
        
    if ctx.author.id == global_config["owner_id"] or ctx.author.id == ctx.guild.owner_id:
        return True
        
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    cmd_name = ctx.command.name if ctx.command else ""
    
    cmd_perms = g_data.get("command_permissions", {})
    allowed_users = cmd_perms.get(cmd_name, [])
    
    if ctx.author.id not in allowed_users:
        if cmd_name in ["ping", "status"]:
            return True
            
        await apply_progressive_punishment(ctx.author, f"Tried to execute command '{cmd_name}' without whitelist.")
        raise commands.CheckFailure("Unauthorized command execution attempt.")
        
    return True

@bot.event
async def on_ready():
    print(f'[ONLINE] Authenticated as {bot.user} (ID: {bot.user.id})')
    print('[SECURITY] Multi-Server Isolated File Architecture & Strict Whitelist Enforcement Active (v12.0).')
    if not uptime_keep_alive_ping.is_running():
        uptime_keep_alive_ping.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over the network | !help"))

# --- 3. BOT COMMANDS ---

@bot.command(name="on", aliases=["start", "enable"])
async def system_on(ctx):
    if not ctx.guild:
        return
    if ctx.author.id != global_config["owner_id"] and ctx.author.id != ctx.guild.owner_id:
        return
    
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["active"] = True
    save_server_config(guild_id, g_data)
    
    embed = discord.Embed(title="🟢 System Fully Activated", description="Adda_Zone Security protocols are now **ONLINE and Operational** for this server.", color=discord.Color.from_rgb(46, 204, 113))
    await ctx.send(embed=embed)

@bot.command(name="off", aliases=["stop", "disable"])
async def system_off(ctx):
    if not ctx.guild:
        return
    if ctx.author.id != global_config["owner_id"] and ctx.author.id != ctx.guild.owner_id:
        return
    
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["active"] = False
    save_server_config(guild_id, g_data)
    
    embed = discord.Embed(title="🔴 System Deactivated", description="Adda_Zone Security protocols have been placed on **Standby** for this server.", color=discord.Color.from_rgb(231, 76, 60))
    await ctx.send(embed=embed)

@bot.command(name="autoping")
async def autoping(ctx, action: str = None):
    if not ctx.guild:
        return
    if ctx.author.id != global_config["owner_id"] and ctx.author.id != ctx.guild.owner_id:
        await ctx.send("⛔ **Access Denied:** Only the Server Owner can configure Auto-Ping.")
        return

    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)

    if not action:
        await ctx.send("⚠️ **Syntax Error:** Use `!autoping on` or `!autoping off`.")
        return

    act = action.lower()
    if act == "on":
        g_data["ping_enabled"] = True
        save_server_config(guild_id, g_data)
        await ctx.send("🟢 **Auto-Ping Enabled:** 24/7 keep-alive signal is now active.")
    elif act == "off":
        g_data["ping_enabled"] = False
        save_server_config(guild_id, g_data)
        await ctx.send("🔴 **Auto-Ping Disabled:** 24/7 keep-alive signal has been turned off.")

@bot.command(name="setchannel")
async def setchannel(ctx, channel: discord.TextChannel):
    if not ctx.guild or (ctx.author.id != global_config["owner_id"] and ctx.author.id != ctx.guild.owner_id):
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["ping_channel_id"] = channel.id
    save_server_config(guild_id, g_data)
    await ctx.send(f"✅ **Keep-Alive Channel Set:** {channel.mention}")

@bot.command(name="setrole")
async def setrole(ctx, role: discord.Role):
    if not ctx.guild or (ctx.author.id != global_config["owner_id"] and ctx.author.id != ctx.guild.owner_id):
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["ping_role_id"] = role.id
    save_server_config(guild_id, g_data)
    await ctx.send(f"✅ **Keep-Alive Role Set:** {role.mention}")

@bot.command(name="help", aliases=["commands", "panel"])
async def help_command(ctx):
    prefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(
        title="🛡️ Isolated Control Center",
        description=f"Server-specific command authorization directory.\n**Active Prefix:** `{prefix}`",
        color=discord.Color.from_rgb(35, 39, 42)
    )
    embed.add_field(name="⚙️ Core & Permissions", value=f"`{prefix}on` / `{prefix}off` - System Master Switch\n`{prefix}setprefix` - Modify prefix\n`{prefix}antinuke` - Toggle defense", inline=False)
    embed.add_field(name="⚖️ Granular Moderation", value=f"`{prefix}kick <user>` - Evict member\n`{prefix}ban <user>` - Permanent ban\n`{prefix}timeout <user> <mins>` - Timeout member", inline=False)
    embed.set_footer(text="Adda_Zone Security Architecture • Version 12.0")
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
    g_data = load_server_config(guild_id)
    sys_state = "🟢 Online (Active)" if g_data.get("active", False) else "🔴 Offline (Standby)"
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(title="📊 Isolated Server Diagnostics", description=f"Environment context for **{ctx.guild.name}**", color=discord.Color.from_rgb(52, 152, 219))
    embed.add_field(name="System Status", value=sys_state, inline=False)
    embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="setprefix")
async def setprefix(ctx, new_prefix: str):
    if not ctx.guild:
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["prefix"] = new_prefix
    save_server_config(guild_id, g_data)
    await ctx.send(f"⚙️ **Prefix Updated:** `{new_prefix}`")

@bot.command(name="antinuke")
async def antinuke(ctx, mode: str):
    if not ctx.guild:
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["antinuke"] = (mode.lower() == "on")
    save_server_config(guild_id, g_data)
    await ctx.send(f"🛡️ **Anti-Nuke Status:** {mode.upper()}")

@bot.command(name="kick")
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if not ctx.guild:
        return
    await member.kick(reason=reason)
    await ctx.send(f"👢 Evicted {member.mention}")

@bot.command(name="ban")
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if not ctx.guild:
        return
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member.mention}")

@bot.command(name="timeout")
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    if not ctx.guild:
        return
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await ctx.send(f"⏰ Timed out {member.mention}")

# --- 4. EVENTS ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# --- 5. MAIN ---
if __name__ == "__main__":
    keep_alive()
    bot_token = global_config.get("token")
    if bot_token:
        bot.run(bot_token)
