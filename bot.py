import os
import json
import threading
import asyncio
from datetime import timedelta
import discord
from discord.ext import commands, tasks
from flask import Flask, render_template_string, request, redirect, url_for, session
import requests

# --- 1. ENTERPRISE OAUTH2 WEB DASHBOARD ---
app = Flask('')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'adda_zone_secure_oauth_key_v13')
data_lock = threading.Lock()

# আপনার দেওয়া নির্দিষ্ট ভেরিয়েবল নামগুলো এখানে হুবহু ব্যবহার করা হয়েছে
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', '')
REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', '')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
OWNER_ID = int(os.environ.get('OWNER_ID', '0').strip() or 0)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adda_Zone Security • Professional Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #090d16;
            --card-bg: #111827;
            --border-color: #1f2937;
            --accent-glow: #5865F2;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }
        body { background-color: var(--bg-color); color: var(--text-main); font-family: 'Inter', sans-serif; margin: 0; padding: 30px; display: flex; justify-content: center; align-items: center; min-height: 100vh; box-sizing: border-box; }
        .container { width: 100%; max-width: 800px; background: var(--card-bg); padding: 40px; border-radius: 16px; border: 1px solid var(--border-color); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6); text-align: center; }
        .header { margin-bottom: 30px; position: relative; }
        h1 { color: #38bdf8; margin: 0 0 8px 0; font-size: 26px; font-weight: 700; }
        p.subtitle { color: var(--text-muted); margin: 0; font-size: 14px; }
        
        .lang-selector { position: absolute; top: 0; right: 0; }
        .lang-selector select { padding: 6px 10px; background: #0a0f1d; border: 1px solid var(--border-color); border-radius: 6px; color: #38bdf8; font-size: 12px; font-weight: 600; cursor: pointer; }

        .login-box { padding: 40px 20px; background: #0a0f1d; border-radius: 12px; border: 1px solid var(--border-color); margin-top: 20px; }
        .discord-btn { display: inline-flex; align-items: center; gap: 10px; background-color: #5865F2; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(88, 101, 242, 0.4); }
        .discord-btn:hover { background-color: #4752C4; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(88, 101, 242, 0.6); }
        
        .dashboard-content { text-align: left; margin-top: 20px; }
        .form-section { background: #0a0f1d; padding: 20px; border-radius: 10px; border: 1px solid var(--border-color); margin-bottom: 20px; }
        .section-title { font-size: 14px; font-weight: 600; color: #38bdf8; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }
        
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 6px; font-weight: 500; font-size: 13px; color: #d1d5db; }
        input[type="text"], select { width: 100%; padding: 12px 16px; background: #111827; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box; }
        
        button.submit-btn { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: white; border: none; padding: 14px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; width: 100%; margin-top: 10px; }
        button.submit-btn:hover { background: linear-gradient(135deg, #0369a1 0%, #075985 100%); }
        
        .user-badge { display: inline-block; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); padding: 8px 16px; border-radius: 20px; color: #38bdf8; font-size: 13px; font-weight: 600; margin-bottom: 20px; }
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
            <p class="subtitle" id="t_subtitle">Professional Discord Authenticated Panel</p>
        </div>
        
        {% if not logged_in %}
        <div class="login-box">
            <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 14px;" id="t_login_desc">Secure authentication required to access server management controls.</p>
            <a href="/login" class="discord-btn" id="t_login_btn">
                <svg width="22" height="17" fill="currentColor" viewBox="0 0 127.14 96.36"><path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1,105.25,105.25,0,0,0,32.19-16.15c2.65-27.28-4.52-51.19-19.49-72.1M42.45,65.69C36.18,65.69,31,60,31,53s5.18-12.72,11.45-12.72S53.9,46,53.88,53s-5.18,12.69-11.43,12.69m42.24,0C78.41,65.69,73.2,60,73.2,53s5.18-12.72,11.45-12.72S96.13,46,96.11,53s-5.18,12.69-11.42,12.69"/></svg>
                Login with Discord / ডিসকর্ড দিয়ে লগইন করুন
            </a>
        </div>
        {% else %}
        <div class="dashboard-content">
            <div style="text-align: center;">
                <div class="user-badge">👤 Logged in as: <strong>{{ username }}</strong> (ID: {{ user_id }})</div>
            </div>
            
            <form method="POST" action="/update">
                <div class="form-section">
                    <div class="section-title" id="t_sec1_title">🔒 Target Server & Permissions</div>
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
                        <input type="text" id="ping_channel_id" name="ping_channel_id" placeholder="Enter Channel ID">
                    </div>
                    <div class="form-group">
                        <label for="ping_role_id" id="t_lbl_ping_role">Keep-Alive Target Role ID to Ping</label>
                        <input type="text" id="ping_role_id" name="ping_role_id" placeholder="Enter Role ID">
                    </div>
                </div>

                <button type="submit" class="submit-btn" id="t_btn_submit">Commit Changes</button>
            </form>
            <div style="text-align: center; margin-top: 15px;">
                <a href="/logout" style="color: #ef4444; font-size: 13px; text-decoration: none;" id="t_logout">Logout / Switch Account</a>
            </div>
        </div>
        {% endif %}

        <div class="footer">
            Adda_Zone Enterprise Security Architecture • OAuth2 Secured
        </div>
    </div>

    <script>
        const translations = {
            en: {
                title: "🛡️ Adda_Zone Security Hub",
                subtitle: "Professional Discord Authenticated Panel",
                login_desc: "Secure authentication required to access server management controls.",
                login_btn: "Login with Discord",
                sec1_title: "🔒 Target Server & Permissions",
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
                btn_submit: "Commit Changes",
                logout: "Logout / Switch Account"
            },
            bn: {
                title: "🛡️ অ্যাডাজোন সিকিউরিটি হাব",
                subtitle: "প্রফেশনাল ডিসকর্ড অথেন্টিকেটেড প্যানেল",
                login_desc: "সার্ভার ম্যানেজমেন্ট কন্ট্রোল প্যানেল ব্যবহার করতে ডিসকর্ড দিয়ে লগইন করুন।",
                login_btn: "ডিসকর্ড দিয়ে লগইন করুন",
                sec1_title: "🔒 টার্গেট সার্ভার ও পারমিশন",
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
                btn_submit: "পরিবর্তন সেভ করুন",
                logout: "লগআউট / অ্যাকাউন্ট পরিবর্তন করুন"
            }
        };

        function switchLanguage() {
            const lang = document.getElementById('lang_switch').value;
            const t = translations[lang];

            document.getElementById('t_title').innerText = t.title;
            document.getElementById('t_subtitle').innerText = t.subtitle;
            if(document.getElementById('t_login_desc')) document.getElementById('t_login_desc').innerText = t.login_desc;
            if(document.getElementById('t_sec1_title')) {
                document.getElementById('t_sec1_title').innerText = t.sec1_title;
                document.getElementById('t_lbl_guild').innerText = t.lbl_guild;
                document.getElementById('t_lbl_action').innerText = t.lbl_action;
                document.getElementById('t_lbl_cmd').innerText = t.lbl_cmd;
                document.getElementById('t_lbl_target_user').innerText = t.lbl_target_user;
                document.getElementById('t_lbl_sys_status').innerText = t.lbl_sys_status;
                document.getElementById('t_sec2_title').innerText = t.sec2_title;
                document.getElementById('t_lbl_ping_toggle').innerText = t.lbl_ping_toggle;
                document.getElementById('t_btn_submit').innerText = t.btn_submit;
                document.getElementById('t_logout').innerText = t.logout;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    logged_in = 'user_id' in session
    username = session.get('username', '')
    user_id = session.get('user_id', '')
    return render_template_string(DASHBOARD_HTML, logged_in=logged_in, username=username, user_id=user_id)

@app.route('/login')
def login():
    if not DISCORD_CLIENT_ID or not REDIRECT_URI:
        return "OAuth2 Error: CLIENT_ID or REDIRECT_URI is missing in environment variables!", 500
    discord_login_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('dashboard'))
    
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers)
    token_json = r.json()
    access_token = token_json.get('access_token')
    
    if not access_token:
        return redirect(url_for('dashboard'))
    
    user_headers = {'Authorization': f'Bearer {access_token}'}
    user_r = requests.get('https://discord.com/api/users/@me', headers=user_headers)
    user_data = user_r.json()
    
    session['user_id'] = str(user_data.get('id'))
    session['username'] = f"{user_data.get('username')}#{user_data.get('discriminator', '0')}"
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard'))

@app.route('/update', methods=['POST'])
def update_config():
    if 'user_id' not in session:
        return redirect(url_for('dashboard'))
    
    admin_user_id = session['user_id']
    guild_id = request.form.get('guild_id', '').strip()
    action_type = request.form.get('action_type', 'grant').strip()
    command_name = request.form.get('command_name', '').strip()
    user_id = request.form.get('user_id', '').strip()
    system_active_val = request.form.get('system_active', 'true').lower() == 'true'
    
    ping_toggle_val = request.form.get('ping_toggle', 'false').lower() == 'true'
    ping_channel_id = request.form.get('ping_channel_id', '').strip()
    ping_role_id = request.form.get('ping_role_id', '').strip()

    if not guild_id.isdigit():
        return redirect(url_for('dashboard'))

    uid_admin = int(admin_user_id)
    g_id_int = int(guild_id)

    global_owner = OWNER_ID
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
            if target_uid == OWNER_ID:
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
        return "!"
    guild_id = str(message.guild.id)
    g_data = load_server_config(guild_id)
    return g_data.get("prefix", "!")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

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
        elif current_strikes == 2:
            await member.kick(reason=f"Unauthorized Command Attempt 2: {reason_text}")
        else:
            await member.ban(reason=f"Unauthorized Command Attempt 3+: {reason_text}")
    except Exception as e:
        print(f"[PUNISHMENT ERROR] {e}")

@bot.check
async def global_whitelist_check(ctx):
    if not ctx.guild:
        return True
    if ctx.author.id == OWNER_ID or ctx.author.id == ctx.guild.owner_id:
        return True
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    cmd_name = ctx.command.name if ctx.command else ""
    cmd_perms = g_data.get("command_permissions", {})
    allowed_users = cmd_perms.get(cmd_name, [])
    if ctx.author.id not in allowed_users:
        if cmd_name in ["ping", "status"]:
            return True
        await apply_progressive_punishment(ctx.author, f"Tried to execute '{cmd_name}' without whitelist.")
        raise commands.CheckFailure("Unauthorized.")
    return True

@bot.event
async def on_ready():
    print(f'[ONLINE] Authenticated as {bot.user} (ID: {bot.user.id})')
    if not uptime_keep_alive_ping.is_running():
        uptime_keep_alive_ping.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="!help"))

@bot.command(name="on", aliases=["start", "enable"])
async def system_on(ctx):
    if not ctx.guild or (ctx.author.id != OWNER_ID and ctx.author.id != ctx.guild.owner_id):
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["active"] = True
    save_server_config(guild_id, g_data)
    await ctx.send("🟢 **System Fully Activated**")

@bot.command(name="off", aliases=["stop", "disable"])
async def system_off(ctx):
    if not ctx.guild or (ctx.author.id != OWNER_ID and ctx.author.id != ctx.guild.owner_id):
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["active"] = False
    save_server_config(guild_id, g_data)
    await ctx.send("🔴 **System Deactivated**")

@bot.command(name="help", aliases=["commands", "panel"])
async def help_command(ctx):
    prefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(title="🛡️ Isolated Control Center", description=f"Prefix: `{prefix}`", color=353942)
    embed.add_field(name="Commands", value=f"`{prefix}on`/`{prefix}off`, `{prefix}kick`, `{prefix}ban`, `{prefix}timeout`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"⚡ Latency: {round(bot.latency * 1000)}ms")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
    else:
        print("CRITICAL ERROR: DISCORD_BOT_TOKEN is missing in environment variables!")
