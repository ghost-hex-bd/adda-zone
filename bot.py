import os
import json
import threading
from datetime import timedelta
import discord
from discord.ext import commands, tasks
from flask import Flask, render_template_string, request, redirect, url_for, session
import requests

# --- 1. ENTERPRISE OAUTH2 WEB DASHBOARD ---
app = Flask('')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'adda_zone_secure_oauth_key_v13')
data_lock = threading.Lock()

# আপনার সুনির্দিষ্ট ৪টি এনভায়রনমেন্ট ভেরিয়েবল এবং ক্লায়েন্ট সিক্রেট
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '').strip()
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '').strip()
DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', '').strip()
OWNER_ID = int(os.environ.get('OWNER_ID', '0').strip() or 0)
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', '').strip()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XIERON • Security Command Bridge</title>
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
        .container { width: 100%; max-width: 900px; background: var(--card-bg); padding: 40px; border-radius: 16px; border: 1px solid var(--border-color); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6); text-align: center; }
        .header { margin-bottom: 30px; position: relative; }
        h1 { color: #38bdf8; margin: 0 0 8px 0; font-size: 28px; font-weight: 700; }
        p.subtitle { color: var(--text-muted); margin: 0; font-size: 14px; }
        
        .lang-selector { position: absolute; top: 0; right: 0; }
        .lang-selector select { padding: 6px 10px; background: #0a0f1d; border: 1px solid var(--border-color); border-radius: 6px; color: #38bdf8; font-size: 12px; font-weight: 600; cursor: pointer; }

        .login-box { padding: 50px 20px; background: #0a0f1d; border-radius: 12px; border: 1px solid var(--border-color); margin-top: 20px; }
        .discord-btn { display: inline-flex; align-items: center; gap: 10px; background-color: #5865F2; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(88, 101, 242, 0.4); }
        .discord-btn:hover { background-color: #4752C4; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(88, 101, 242, 0.6); }
        
        .dashboard-content { text-align: left; margin-top: 20px; }
        .form-section { background: #0a0f1d; padding: 25px; border-radius: 12px; border: 1px solid var(--border-color); margin-bottom: 20px; }
        .section-title { font-size: 15px; font-weight: 600; color: #38bdf8; margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }
        
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 6px; font-weight: 500; font-size: 13px; color: #d1d5db; }
        input[type="text"], select { width: 100%; padding: 12px 16px; background: #111827; border: 1px solid var(--border-color); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box; }
        
        button.submit-btn { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: white; border: none; padding: 14px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; width: 100%; margin-top: 10px; }
        button.submit-btn:hover { background: linear-gradient(135deg, #0369a1 0%, #075985 100%); }
        
        .server-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .server-card { background: #111827; border: 1px solid var(--border-color); border-radius: 10px; padding: 15px; text-align: center; }
        .server-card h3 { color: #f3f4f6; font-size: 16px; margin: 0 0 5px 0; }
        .server-card p { color: var(--text-muted); font-size: 12px; margin: 0 0 10px 0; }

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
            <h1 id="t_title">🛡️ XIERON · Autonomous Sentinel Bridge</h1>
            <p class="subtitle" id="t_subtitle">Real-time Telemetry, Threat Firewall & Operational Controls</p>
        </div>
        
        {% if not logged_in %}
        <div class="login-box">
            <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 14px;" id="t_login_desc">Secure authentication required to access server telemetry and security grids.</p>
            <a href="/login" class="discord-btn" id="t_login_btn">
                <svg width="22" height="17" fill="currentColor" viewBox="0 0 127.14 96.36"><path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1,105.25,105.25,0,0,0,32.19-16.15c2.65-27.28-4.52-51.19-19.49-72.1M42.45,65.69C36.18,65.69,31,60,31,53s5.18-12.72,11.45-12.72S53.9,46,53.88,53s-5.18,12.69-11.43,12.69m42.24,0C78.41,65.69,73.2,60,73.2,53s5.18-12.72,11.45-12.72S96.13,46,96.11,53s-5.18,12.69-11.42,12.69"/></svg>
                Login with Discord / ডিসকর্ড দিয়ে লগইন করুন
            </a>
        </div>
        {% else %}
        <div class="dashboard-content">
            <div style="text-align: center;">
                <div class="user-badge">👤 Operator: <strong>{{ username }}</strong> (ID: {{ user_id }})</div>
            </div>

            <div class="form-section">
                <div class="section-title" id="t_sec_servers">🌐 Protected Hubs & Available Guilds</div>
                <div class="server-grid">
                    {% if guilds %}
                        {% for g in guilds %}
                        <div class="server-card">
                            <h3>{{ g.name }}</h3>
                            <p>ID: {{ g.id }}</p>
                            <span style="color: #38bdf8; font-size: 11px; font-weight: 600;">⚡ Sentinel Armed</span>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p style="color: var(--text-muted); font-size: 13px;">No mutual managed servers found where bot is installed.</p>
                    {% endif %}
                </div>
            </div>
            
            <form method="POST" action="/update">
                <div class="form-section">
                    <div class="section-title" id="t_sec1_title">🔒 Server Security Telemetry & Defenses</div>
                    <div class="form-group">
                        <label for="guild_id" id="t_lbl_guild">Select Authorized Guild *</label>
                        <select id="guild_id" name="guild_id" required>
                            {% if guilds %}
                                {% for g in guilds %}
                                <option value="{{ g.id }}">{{ g.name }} (ID: {{ g.id }})</option>
                                {% endfor %}
                            {% else %}
                                <option value="">No authorized server available</option>
                            {% endif %}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="antinuke_toggle" id="t_lbl_antinuke">Anti-Nuke Protection Matrix</label>
                        <select id="antinuke_toggle" name="antinuke_toggle">
                            <option value="true" id="t_opt_ani_on">🛡️ Anti-Nuke Armed (Optimal)</option>
                            <option value="false" id="t_opt_ani_off">⚠️ Anti-Nuke Disarmed</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="system_active" id="t_lbl_sys_status">Autonomous Sentinel Core</label>
                        <select id="system_active" name="system_active">
                            <option value="true" id="t_opt_sys_on">🟢 Fully Activated (Online)</option>
                            <option value="false" id="t_opt_sys_off">🔴 Standby / Offline</option>
                        </select>
                    </div>
                </div>

                <div class="form-section">
                    <div class="section-title" id="t_sec2_title">⏰ 24/7 Keep-Alive Uptime Telemetry</div>
                    <div class="form-group">
                        <label for="ping_toggle" id="t_lbl_ping_toggle">Auto-Ping Switch</label>
                        <select id="ping_toggle" name="ping_toggle">
                            <option value="true" id="t_opt_ping_on">🟢 Enable Shard Ping (Active)</option>
                            <option value="false" id="t_opt_ping_off">🔴 Disable Shard Ping (Off)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="ping_channel_id" id="t_lbl_ping_chan">Target Channel ID</label>
                        <input type="text" id="ping_channel_id" name="ping_channel_id" placeholder="Enter Channel ID">
                    </div>
                    <div class="form-group">
                        <label for="ping_role_id" id="t_lbl_ping_role">Target Role ID to Ping</label>
                        <input type="text" id="ping_role_id" name="ping_role_id" placeholder="Enter Role ID">
                    </div>
                </div>

                <button type="submit" class="submit-btn" id="t_btn_submit">Commit Telemetry Changes</button>
            </form>
            <div style="text-align: center; margin-top: 15px;">
                <a href="/logout" style="color: #ef4444; font-size: 13px; text-decoration: none;" id="t_logout">Terminate Session / Logout</a>
            </div>
        </div>
        {% endif %}

        <div class="footer">
            XIERON Autonomous Security Architecture · Shard #0 Active
        </div>
    </div>

    <script>
        const translations = {
            en: {
                title: "🛡️ XIERON · Autonomous Sentinel Bridge",
                subtitle: "Real-time Telemetry, Threat Firewall & Operational Controls",
                login_desc: "Secure authentication required to access server telemetry and security grids.",
                login_btn: "Login with Discord",
                sec_servers: "🌐 Protected Hubs & Available Guilds",
                sec1_title: "🔒 Server Security Telemetry & Defenses",
                lbl_guild: "Select Authorized Guild",
                lbl_antinuke: "Anti-Nuke Protection Matrix",
                opt_ani_on: "🛡️ Anti-Nuke Armed (Optimal)",
                opt_ani_off: "⚠️ Anti-Nuke Disarmed",
                lbl_sys_status: "Autonomous Sentinel Core",
                opt_sys_on: "🟢 Fully Activated (Online)",
                opt_sys_off: "🔴 Standby / Offline",
                sec2_title: "⏰ 24/7 Keep-Alive Uptime Telemetry",
                lbl_ping_toggle: "Auto-Ping Switch",
                opt_ping_on: "🟢 Enable Shard Ping (Active)",
                opt_ping_off: "🔴 Disable Shard Ping (Off)",
                lbl_ping_chan: "Target Channel ID",
                lbl_ping_role: "Target Role ID to Ping",
                btn_submit: "Commit Telemetry Changes",
                logout: "Terminate Session / Logout"
            },
            bn: {
                title: "🛡️ জিয়েরন · অটোনোমাস সেন্টিনেল ব্রিজ",
                subtitle: "রিয়েল-টাইম টেলিমেট্রি, থ্রেট ফায়ারওয়াল এবং অপারেশনাল কন্ট্রোল",
                login_desc: "সার্ভার টেলিমেট্রি এবং সিকিউরিটি গ্রিড অ্যাক্সেস করতে ডিসকর্ড দিয়ে লগইন করুন।",
                login_btn: "ডিসকর্ড দিয়ে লগইন করুন",
                sec_servers: "🌐 প্রটেক্টেড হাব ও এভেইলেবল গিল্ডসমূহ",
                sec1_title: "🔒 সার্ভার সিকিউরিটি টেলিমেট্রি ও ডিফেন্স",
                lbl_guild: "অনুমোদিত সার্ভার সিলেক্ট করুন",
                lbl_antinuke: "অ্যান্টি-নিউক প্রটেকশন ম্যাট্রিক্স",
                opt_ani_on: "🛡️ অ্যান্টি-নিউক আর্মেড (Optimal)",
                opt_ani_off: "⚠️ অ্যান্টি-নিউক ডিসআর্মড",
                lbl_sys_status: "অটোনোমাস সেন্টিনেল কোর",
                opt_sys_on: "🟢 পুরোপুরি সচল (Online)",
                opt_sys_off: "🔴 স্ট্যান্ডবাই / অফলাইন",
                sec2_title: "⏰ ২৪/৭ সচল রাখার আপটাইম টেলিমেট্রি",
                lbl_ping_toggle: "অটো-পিং সুইচ",
                opt_ping_on: "🟢 অটো-পিং চালু (Active)",
                opt_ping_off: "🔴 অটো-পিং বন্ধ (Off)",
                lbl_ping_chan: "টার্গেট চ্যানেল আইডি",
                lbl_ping_role: "পিং করার জন্য টার্গেট রোল আইডি",
                btn_submit: "টেলিমেট্রি পরিবর্তন সেভ করুন",
                logout: "সেশন টার্মিনেট / লগআউট করুন"
            }
        };

        function switchLanguage() {
            const lang = document.getElementById('lang_switch').value;
            const t = translations[lang];

            document.getElementById('t_title').innerText = t.title;
            document.getElementById('t_subtitle').innerText = t.subtitle;
            if(document.getElementById('t_login_desc')) document.getElementById('t_login_desc').innerText = t.login_desc;
            if(document.getElementById('t_sec_servers')) {
                document.getElementById('t_sec_servers').innerText = t.sec_servers;
                document.getElementById('t_sec1_title').innerText = t.sec1_title;
                document.getElementById('t_lbl_guild').innerText = t.lbl_guild;
                document.getElementById('t_lbl_antinuke').innerText = t.lbl_antinuke;
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
    guilds = session.get('guilds', [])
    return render_template_string(DASHBOARD_HTML, logged_in=logged_in, username=username, user_id=user_id, guilds=guilds)

@app.route('/login')
def login():
    if not DISCORD_CLIENT_ID or not DISCORD_REDIRECT_URI:
        return "OAuth2 Error: CLIENT_ID or DISCORD_REDIRECT_URI is missing!", 500
    discord_login_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify%20guilds"
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('dashboard'))
    
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI
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
    
    guilds_r = requests.get('https://discord.com/api/users/@me/guilds', headers=user_headers)
    user_guilds = guilds_r.json()
    
    managed_guilds = []
    if isinstance(user_guilds, list):
        for g in user_guilds:
            permissions = int(g.get('permissions', 0))
            is_owner = g.get('owner', False)
            has_admin = (permissions & 0x8) == 0x8
            
            if is_owner or has_admin:
                g_id = int(g.get('id'))
                if bot.get_guild(g_id):
                    managed_guilds.append({
                        'id': str(g_id),
                        'name': g.get('name', 'Unknown Server')
                    })

    session['user_id'] = str(user_data.get('id'))
    session['username'] = f"{user_data.get('username')}#{user_data.get('discriminator', '0')}"
    session['guilds'] = managed_guilds
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
    antinuke_val = request.form.get('antinuke_toggle', 'true').lower() == 'true'
    system_active_val = request.form.get('system_active', 'true').lower() == 'true'
    
    ping_toggle_val = request.form.get('ping_toggle', 'false').lower() == 'true'
    ping_channel_id = request.form.get('ping_channel_id', '').strip()
    ping_role_id = request.form.get('ping_role_id', '').strip()

    if not guild_id.isdigit():
        return redirect(url_for('dashboard'))

    uid_admin = int(admin_user_id)
    g_id_int = int(guild_id)

    is_global = (uid_admin == OWNER_ID)
    
    guild_obj = bot.get_guild(g_id_int)
    is_server_owner = False
    if guild_obj and guild_obj.owner_id == uid_admin:
        is_server_owner = True

    if not (is_global or is_server_owner):
        return redirect(url_for('dashboard'))

    with data_lock:
        g_data = load_server_config(guild_id)
        
        g_data["antinuke"] = antinuke_val
        g_data["active"] = system_active_val
        g_data["ping_enabled"] = ping_toggle_val
        
        if ping_channel_id.isdigit():
            g_data["ping_channel_id"] = int(ping_channel_id)
        if ping_role_id.isdigit():
            g_data["ping_role_id"] = int(ping_role_id)
        
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
        "ping_role_id": None
    }

def save_server_config(guild_id, data):
    filename = get_server_config_filename(guild_id)
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
                    await channel.send(f"🛡️ **[24/7 Uptime Shard Signal]** Keep-Alive active. {role.mention}")
        except Exception as e:
            print(f"[UPTIME PING ERROR] Guild {guild.name}: {e}")

@uptime_keep_alive_ping.before_loop
async def before_uptime_ping():
    await bot.wait_until_ready()

# --- অ্যান্টি-নিউক প্রটেকশন ও ইভেন্ট হ্যান্ডলার ---
@bot.event
async def on_guild_channel_create(channel):
    guild_id = str(channel.guild.id)
    g_data = load_server_config(guild_id)
    if not g_data.get("active", True) or not g_data.get("antinuke", True):
        return
    print(f"[ANTINUKE] Channel created firewall alert in {channel.guild.name}: {channel.name}")

@bot.event
async def on_guild_channel_delete(channel):
    guild_id = str(channel.guild.id)
    g_data = load_server_config(guild_id)
    if not g_data.get("active", True) or not g_data.get("antinuke", True):
        return
    print(f"[ANTINUKE] Channel deletion firewall alert in {channel.guild.name}: {channel.name}")

# --- প্রয়োজনীয় মডারেশন কমান্ডসমূহ (Kick, Ban, Timeout, Ping) ---
@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_command(ctx, member: discord.Member, *, reason=None):
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    if not g_data.get("active", True):
        await ctx.send("⚠️ সিকিউরিটি সিস্টেমটি বর্তমানে বন্ধ (OFF) রয়েছে।")
        return
    try:
        await member.kick(reason=reason)
        await ctx.send(f"✅ সফলভাবে কিক করা হয়েছে: **{member}** | কারণ: {reason}")
    except Exception as e:
        await ctx.send(f"❌ কিক করতে সমস্যা হয়েছে: {e}")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_command(ctx, member: discord.Member, *, reason=None):
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    if not g_data.get("active", True):
        await ctx.send("⚠️ সিকিউরিটি সিস্টেমটি বর্তমানে বন্ধ (OFF) রয়েছে।")
        return
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 সফলভাবে ব্যান করা হয়েছে: **{member}** | কারণ: {reason}")
    except Exception as e:
        await ctx.send(f"❌ ব্যান করতে সমস্যা হয়েছে: {e}")

@bot.command(name="timeout", aliases=["mute"])
@commands.has_permissions(moderate_members=True)
async def timeout_command(ctx, member: discord.Member, minutes: int, *, reason=None):
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    if not g_data.get("active", True):
        await ctx.send("⚠️ সিকিউরিটি সিস্টেমটি বর্তমানে বন্ধ (OFF) রয়েছে।")
        return
    try:
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"🔇 সফলভাবে টাইমআউট দেওয়া হয়েছে: **{member}** ({minutes} মিনিট) | কারণ: {reason}")
    except Exception as e:
        await ctx.send(f"❌ টাইমআউট দিতে সমস্যা হয়েছে: {e}")

@bot.command(name="on", aliases=["start", "enable"])
async def system_on(ctx):
    if not ctx.guild or (ctx.author.id != OWNER_ID and ctx.author.id != ctx.guild.owner_id):
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["active"] = True
    save_server_config(guild_id, g_data)
    await ctx.send("🟢 **XIERON Sentinel Core Fully Activated**")

@bot.command(name="off", aliases=["stop", "disable"])
async def system_off(ctx):
    if not ctx.guild or (ctx.author.id != OWNER_ID and ctx.author.id != ctx.guild.owner_id):
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["active"] = False
    save_server_config(guild_id, g_data)
    await ctx.send("🔴 **XIERON Sentinel Core Deactivated**")

@bot.command(name="help", aliases=["commands", "panel"])
async def help_command(ctx):
    prefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(title="🛡️ XIERON Sentinel Command Bridge", description=f"Prefix: `{prefix}`", color=353942)
    embed.add_field(name="Moderation Telemetry", value=f"`{prefix}kick @user`, `{prefix}ban @user`, `{prefix}timeout @user [minutes]`", inline=False)
    embed.add_field(name="Core Operations", value=f"`{prefix}on` / `{prefix}off`, `{prefix}ping`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"⚡ Gateway Telemetry Latency: {round(bot.latency * 1000)}ms (Shard #0 Active)")

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
