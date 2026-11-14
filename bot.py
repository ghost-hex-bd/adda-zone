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
    <title>Adda_Zone • Advanced Security & Permission Hub</title>
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
        .container { width: 100%; max-width: 950px; background: var(--card-bg); padding: 40px; border-radius: 16px; border: 1px solid var(--border-color); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6); text-align: center; }
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
        button.submit-btn:hover { background: linear-gradient(135deg, #0369a1 100%, #075985 100%); }
        
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
            <h1 id="t_title">🛡️ Adda_Zone Security Hub</h1>
            <p class="subtitle" id="t_subtitle">Dynamic Dropdown Channel, Role & Member Permission Panel</p>
        </div>
        
        {% if not logged_in %}
        <div class="login-box">
            <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 14px;" id="t_login_desc">Secure authentication required to access management controls.</p>
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
                <div class="section-title" id="t_sec_servers">🌐 Protected Servers & Managed Hubs</div>
                <div class="server-grid">
                    {% if guilds %}
                        {% for g in guilds %}
                        <div class="server-card">
                            <h3>{{ g.name }}</h3>
                            <p>ID: {{ g.id }}</p>
                            <span style="color: #38bdf8; font-size: 11px; font-weight: 600;">⚡ Adda_Zone Protected</span>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p style="color: var(--text-muted); font-size: 13px;">No mutual managed servers found where Adda_Zone is installed.</p>
                    {% endif %}
                </div>
            </div>
            
            <form method="POST" action="/update">
                <div class="form-section">
                    <div class="section-title" id="t_sec1_title">🔒 Core Defenses & Anti-Nuke Control</div>
                    <div class="form-group">
                        <label for="guild_id" id="t_lbl_guild">Select Target Server *</label>
                        <select id="guild_id" name="guild_id" onchange="location.href='/?guild_id='+this.value" required>
                            <option value="">-- Choose Server --</option>
                            {% if guilds %}
                                {% for g in guilds %}
                                <option value="{{ g.id }}" {% if selected_guild_id == g.id %}selected{% endif %}>{{ g.name }} (ID: {{ g.id }})</option>
                                {% endfor %}
                            {% endif %}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="antinuke_toggle" id="t_lbl_antinuke">Anti-Nuke Defense (ON / OFF)</label>
                        <select id="antinuke_toggle" name="antinuke_toggle">
                            <option value="true" {% if current_config.antinuke %}selected{% endif %}>🛡️ Anti-Nuke ON (Protected)</option>
                            <option value="false" {% if not current_config.antinuke %}selected{% endif %}>⚠️ Anti-Nuke OFF (Unprotected)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="system_active" id="t_lbl_sys_status">Bot Core Status (Active / Standby)</label>
                        <select id="system_active" name="system_active">
                            <option value="true" {% if current_config.active %}selected{% endif %}>🟢 Fully Activated (ON)</option>
                            <option value="false" {% if not current_config.active %}selected{% endif %}>🔴 Standby / Deactivated (OFF)</option>
                        </select>
                    </div>
                </div>

                <div class="form-section">
                    <div class="section-title" id="t_sec_whitelist">👑 Member Whitelist & Moderator Selector</div>
                    <div class="form-group">
                        <label for="whitelist_member" id="t_lbl_whitelist">Select Server Member to Whitelist (মডারেটর হিসেবে সিলেক্ট করুন)</label>
                        <select id="whitelist_member" name="whitelist_member">
                            <option value="">-- Select Member from Server --</option>
                            {% if server_members %}
                                {% for m in server_members %}
                                <option value="{{ m.id }}">{{ m.name }} (ID: {{ m.id }})</option>
                                {% endfor %}
                            {% else %}
                                <option value="">Select a server above first to load members</option>
                            {% endif %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="action_type" id="t_lbl_action">Whitelist Action (অ্যাকশন সিলেক্ট করুন)</label>
                        <select id="action_type" name="action_type">
                            <option value="add">➕ Add to Whitelist (অনুমতি দিন)</option>
                            <option value="remove">➖ Remove from Whitelist (অনুমতি উঠিয়ে নিন)</option>
                        </select>
                    </div>
                </div>

                <div class="form-section">
                    <div class="section-title" id="t_sec_perms">⚙️ Advanced Security & Mention Permissions</div>
                    <div class="form-group">
                        <label for="allow_everyone" id="t_lbl_everyone">Allow @everyone Mentions & Ping</label>
                        <select id="allow_everyone" name="allow_everyone">
                            <option value="true" {% if current_config.allow_everyone %}selected{% endif %}>✅ Allowed (@everyone Mention Enabled)</option>
                            <option value="false" {% if not current_config.allow_everyone %}selected{% endif %}>❌ Blocked (@everyone Mention Restricted)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="allow_roles" id="t_lbl_roles">Allow Role Mentions & Pings</label>
                        <select id="allow_roles" name="allow_roles">
                            <option value="true" {% if current_config.allow_roles %}selected{% endif %}>✅ Allowed (Role Pings Enabled)</option>
                            <option value="false" {% if not current_config.allow_roles %}selected{% endif %}>❌ Blocked (Role Pings Restricted)</option>
                        </select>
                    </div>
                </div>

                <div class="form-section">
                    <div class="section-title" id="t_sec2_title">⏰ 24/7 Keep-Alive Auto-Ping & Channel/Role Settings</div>
                    <div class="form-group">
                        <label for="ping_toggle" id="t_lbl_ping_toggle">Auto-Ping Switch</label>
                        <select id="ping_toggle" name="ping_toggle">
                            <option value="true" {% if current_config.ping_enabled %}selected{% endif %}>🟢 Enable Auto-Ping</option>
                            <option value="false" {% if not current_config.ping_enabled %}selected{% endif %}>🔴 Disable Auto-Ping</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="ping_channel_id" id="t_lbl_ping_chan">Select Target Channel (চ্যানেল ড্রপডাউন থেকে সিলেক্ট করুন)</label>
                        <select id="ping_channel_id" name="ping_channel_id">
                            <option value="">-- Choose Channel --</option>
                            {% if server_channels %}
                                {% for c in server_channels %}
                                <option value="{{ c.id }}" {% if current_config.ping_channel_id == c.id|int %}selected{% endif %}>#{{ c.name }} (ID: {{ c.id }})</option>
                                {% endfor %}
                            {% else %}
                                <option value="">Select a server above first</option>
                            {% endif %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="ping_role_id" id="t_lbl_ping_role">Select Target Role to Ping (রোল ড্রপডাউন থেকে সিলেক্ট করুন)</label>
                        <select id="ping_role_id" name="ping_role_id">
                            <option value="">-- Choose Role --</option>
                            {% if server_roles %}
                                {% for r in server_roles %}
                                <option value="{{ r.id }}" {% if current_config.ping_role_id == r.id|int %}selected{% endif %}>@{{ r.name }} (ID: {{ r.id }})</option>
                                {% endfor %}
                            {% else %}
                                <option value="">Select a server above first</option>
                            {% endif %}
                        </select>
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
            Adda_Zone Security Architecture • Dynamic Dropdown Suite Active
        </div>
    </div>

    <script>
        const translations = {
            en: {
                title: "🛡️ Adda_Zone Security Hub",
                subtitle: "Dynamic Dropdown Channel, Role & Member Permission Panel",
                login_desc: "Secure authentication required to access management controls.",
                login_btn: "Login with Discord",
                sec_servers: "🌐 Protected Servers & Managed Hubs",
                sec1_title: "🔒 Core Defenses & Anti-Nuke Control",
                lbl_guild: "Select Target Server",
                lbl_antinuke: "Anti-Nuke Defense (ON / OFF)",
                lbl_sys_status: "Bot Core Status (Active / Standby)",
                sec_whitelist: "👑 Member Whitelist & Moderator Selector",
                lbl_whitelist: "Select Server Member to Whitelist",
                lbl_action: "Whitelist Action",
                sec_perms: "⚙️ Advanced Security & Mention Permissions",
                lbl_everyone: "Allow @everyone Mentions & Ping",
                lbl_roles: "Allow Role Mentions & Pings",
                sec2_title: "⏰ 24/7 Keep-Alive Auto-Ping & Channel/Role Settings",
                lbl_ping_toggle: "Auto-Ping Switch",
                lbl_ping_chan: "Select Target Channel",
                lbl_ping_role: "Select Target Role to Ping",
                btn_submit: "Commit Changes",
                logout: "Logout / Switch Account"
            },
            bn: {
                title: "🛡️ অ্যাডাজোন সিকিউরিটি হাব",
                subtitle: "ডাইনামিক ড্রপডাউন চ্যানেল, রোল ও মেম্বার পারমিশন প্যানেল",
                login_desc: "ম্যানেজমেন্ট কন্ট্রোল প্যানেল ব্যবহার করতে ডিসকর্ড দিয়ে লগইন করুন।",
                login_btn: "ডিসকর্ড দিয়ে লগইন করুন",
                sec_servers: "🌐 প্রোটেক্টেড সার্ভার ও ম্যানেজড হাবসমূহ",
                sec1_title: "🔒 মূল প্রতিরক্ষা ও অ্যান্টি-নিউক ডিফেন্স",
                lbl_guild: "টার্গেট সার্ভার সিলেক্ট করুন",
                lbl_antinuke: "অ্যান্টি-নিউক ডিফেন্স (ON / OFF)",
                lbl_sys_status: "বট কোরের অবস্থা (সচল/স্ট্যান্ডবাই)",
                sec_whitelist: "👑 মেম্বার হোয়াইটলিস্ট ও মডারেটর সিলেক্টর",
                lbl_whitelist: "তালিকা থেকে মেম্বার সিলেক্ট করুন",
                lbl_action: "হোয়াইটলিস্ট অ্যাকশন (যুক্ত বা বাদ দিন)",
                sec_perms: "⚙️ এডভান্সড সিকিউরিটি ও মেনশন পারমিশন",
                lbl_everyone: "@everyone মেনশন ও পিং করার অনুমতি",
                lbl_roles: "রোল মেনশন ও পিং করার অনুমতি",
                sec2_title: "⏰ ২৪/৭ সচল রাখার অটো-পিং ও চ্যানেল/রোল সেটিংস",
                lbl_ping_toggle: "অটো-পিং সুইচ",
                lbl_ping_chan: "টার্গেট চ্যানেল সিলেক্ট করুন",
                lbl_ping_role: "পিং করার জন্য টার্গেট রোল সিলেক্ট করুন",
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
            if(document.getElementById('t_sec_servers')) {
                document.getElementById('t_sec_servers').innerText = t.sec_servers;
                document.getElementById('t_sec1_title').innerText = t.sec1_title;
                document.getElementById('t_lbl_guild').innerText = t.lbl_guild;
                document.getElementById('t_lbl_antinuke').innerText = t.lbl_antinuke;
                document.getElementById('t_lbl_sys_status').innerText = t.lbl_sys_status;
                document.getElementById('t_sec_whitelist').innerText = t.sec_whitelist;
                document.getElementById('t_lbl_whitelist').innerText = t.lbl_whitelist;
                document.getElementById('t_lbl_action').innerText = t.lbl_action;
                document.getElementById('t_sec_perms').innerText = t.sec_perms;
                document.getElementById('t_lbl_everyone').innerText = t.lbl_everyone;
                document.getElementById('t_lbl_roles').innerText = t.lbl_roles;
                document.getElementById('t_sec2_title').innerText = t.sec2_title;
                document.getElementById('t_lbl_ping_toggle').innerText = t.lbl_ping_toggle;
                document.getElementById('t_lbl_ping_chan').innerText = t.lbl_ping_chan;
                document.getElementById('t_lbl_ping_role').innerText = t.lbl_ping_role;
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
    
    selected_guild_id = request.args.get('guild_id', '').strip()
    server_members = []
    server_channels = []
    server_roles = []
    current_config = load_server_config(selected_guild_id) if selected_guild_id else {}
    
    if selected_guild_id and selected_guild_id.isdigit():
        guild_obj = bot.get_guild(int(selected_guild_id))
        if guild_obj:
            for member in guild_obj.members:
                if not member.bot:
                    server_members.append({
                        'id': str(member.id),
                        'name': f"{member.name} ({member.display_name})"
                    })
            for channel in guild_obj.text_channels:
                server_channels.append({
                    'id': str(channel.id),
                    'name': channel.name
                })
            for role in guild_obj.roles:
                if role.name != "@everyone":
                    server_roles.append({
                        'id': str(role.id),
                        'name': role.name
                    })

    return render_template_string(
        DASHBOARD_HTML, 
        logged_in=logged_in, 
        username=username, 
        user_id=user_id, 
        guilds=guilds, 
        selected_guild_id=selected_guild_id,
        server_members=server_members,
        server_channels=server_channels,
        server_roles=server_roles,
        current_config=current_config
    )

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
    user_discord_id = int(user_data.get('id', 0))
    is_global_owner = (user_discord_id == OWNER_ID)
    
    if isinstance(user_guilds, list):
        for g in user_guilds:
            permissions = int(g.get('permissions', 0))
            is_owner = g.get('owner', False)
            has_admin = (permissions & 0x8) == 0x8
            g_id = int(g.get('id'))
            
            bot_in_guild = bot.get_guild(g_id) is not None
            
            if is_global_owner and bot_in_guild:
                managed_guilds.append({
                    'id': str(g_id),
                    'name': g.get('name', 'Unknown Server')
                })
            elif not is_global_owner and (is_owner or has_admin) and bot_in_guild:
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
    
    selected_member_id = request.form.get('whitelist_member', '').strip()
    action_type = request.form.get('action_type', 'add').strip()
    
    allow_everyone_val = request.form.get('allow_everyone', 'true').lower() == 'true'
    allow_roles_val = request.form.get('allow_roles', 'true').lower() == 'true'
    
    ping_toggle_val = request.form.get('ping_toggle', 'false').lower() == 'true'
    ping_channel_id = request.form.get('ping_channel_id', '').strip()
    ping_role_id = request.form.get('ping_role_id', '').strip()

    if not guild_id.isdigit():
        return redirect(url_for('dashboard'))

    uid_admin = int(admin_user_id)
    g_id_int = int(guild_id)

    is_global = (uid_admin == OWNER_ID)
    guild_obj = bot.get_guild(g_id_int)
    is_server_owner = (guild_obj and guild_obj.owner_id == uid_admin)

    g_data_temp = load_server_config(guild_id)
    is_whitelisted = uid_admin in g_data_temp.get("whitelist", [])

    if not (is_global or is_server_owner or is_whitelisted):
        return redirect(url_for('dashboard'))

    with data_lock:
        g_data = load_server_config(guild_id)
        
        g_data["antinuke"] = antinuke_val
        g_data["active"] = system_active_val
        g_data["ping_enabled"] = ping_toggle_val
        g_data["allow_everyone"] = allow_everyone_val
        g_data["allow_roles"] = allow_roles_val
        
        # মেম্বার সিলেক্ট করে হোয়াইটলিস্টে যোগ বা বাদ দেওয়ার লজিক
        if selected_member_id.isdigit():
            m_id_int = int(selected_member_id)
            if action_type == 'add':
                if m_id_int not in g_data["whitelist"]:
                    g_data["whitelist"].append(m_id_int)
            elif action_type == 'remove':
                if m_id_int in g_data["whitelist"]:
                    g_data["whitelist"].remove(m_id_int)
            
        if ping_channel_id.isdigit():
            g_data["ping_channel_id"] = int(ping_channel_id)
        if ping_role_id.isdigit():
            g_data["ping_role_id"] = int(ping_role_id)
        
        save_server_config(guild_id, g_data)
        
    return redirect(url_for('dashboard', guild_id=guild_id))

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
        "whitelist": [],
        "allow_everyone": True,
        "allow_roles": True,
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

# পারমিশন চেকার ফাংশন
def is_authorized(ctx):
    if not ctx.guild:
        return False
    if ctx.author.id == OWNER_ID or ctx.author.id == ctx.guild.owner_id:
        return True
    g_data = load_server_config(str(ctx.guild.id))
    return ctx.author.id in g_data.get("whitelist", [])

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
                    await channel.send(f"🛡️ **[Adda_Zone Uptime Signal]** Keep-Alive active check. {role.mention}")
        except Exception as e:
            print(f"[UPTIME PING ERROR] Guild {guild.name}: {e}")

@uptime_keep_alive_ping.before_loop
async def before_uptime_ping():
    await bot.wait_until_ready()

# --- অ্যান্টি-নিউক ডিফেন্স ইভেন্ট ও মেনশন রেস্ট্রিকশন লগার ---
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    
    guild_id = str(message.guild.id)
    g_data = load_server_config(guild_id)
    
    if g_data.get("active", True):
        # @everyone মেনশন রেস্ট্রিকশন চেক
        if not g_data.get("allow_everyone", True) and ("@everyone" in message.content or "@here" in message.content):
            if not message.author.guild_permissions.administrator and message.author.id != OWNER_ID:
                try:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, এই সার্ভারে `@everyone` মেনশন করার অনুমতি নেই!", delete_after=5)
                    return
                except Exception:
                    pass

        # রোল মেনশন রেস্ট্রিকশন চেক
        if not g_data.get("allow_roles", True) and len(message.role_mentions) > 0:
            if not message.author.guild_permissions.administrator and message.author.id != OWNER_ID:
                try:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, এই সার্ভারে রোল মেনশন করার অনুমতি নেই!", delete_after=5)
                    return
                except Exception:
                    pass

    await bot.process_commands(message)

@bot.event
async def on_guild_channel_create(channel):
    guild_id = str(channel.guild.id)
    g_data = load_server_config(guild_id)
    if not g_data.get("active", True) or not g_data.get("antinuke", True):
        return
    print(f"[Adda_Zone AUDIT LOG] Channel created: {channel.name} in {channel.guild.name}")

@bot.event
async def on_guild_channel_delete(channel):
    guild_id = str(channel.guild.id)
    g_data = load_server_config(guild_id)
    if not g_data.get("active", True) or not g_data.get("antinuke", True):
        return
    print(f"[Adda_Zone AUDIT LOG] Channel deleted: {channel.name} in {channel.guild.name}")

# --- ১. কিক, ব্যান ও টাইমআউট কমান্ড ---
@bot.command(name="kick")
async def kick_command(ctx, member: discord.Member, *, reason=None):
    if not is_authorized(ctx):
        await ctx.send("❌ আপনার এই কমান্ডটি চালানোর অনুমতি নেই (হোয়াইটলিস্টে নেই)।")
        return
    try:
        await member.kick(reason=reason)
        await ctx.send(f"✅ সফলভাবে কিক করা হয়েছে: **{member}** | কারণ: {reason}")
    except Exception as e:
        await ctx.send(f"❌ কিক করতে সমস্যা হয়েছে: {e}")

@bot.command(name="ban")
async def ban_command(ctx, member: discord.Member, *, reason=None):
    if not is_authorized(ctx):
        await ctx.send("❌ আপনার এই ব্যান কমান্ডটি চালানোর অনুমতি নেই।")
        return
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 সফলভাবে ব্যান করা হয়েছে: **{member}** | কারণ: {reason}")
    except Exception as e:
        await ctx.send(f"❌ ব্যান করতে সমস্যা হয়েছে: {e}")

@bot.command(name="timeout", aliases=["mute"])
async def timeout_command(ctx, member: discord.Member, minutes: int, *, reason=None):
    if not is_authorized(ctx):
        await ctx.send("❌ আপনার এই টাইমআউট কমান্ডটি চালানোর অনুমতি নেই।")
        return
    try:
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"🔇 সফলভাবে টাইমআউট দেওয়া হয়েছে: **{member}** ({minutes} মিনিট) | কারণ: {reason}")
    except Exception as e:
        await ctx.send(f"❌ টাইমআউট দিতে সমস্যা হয়েছে: {e}")

# --- ২. ভয়েস কন্ট্রোল কমান্ড (Server Mute, Unmute, Deafen) ---
@bot.command(name="vcmute")
async def vcmute_command(ctx, member: discord.Member, *, reason=None):
    if not is_authorized(ctx):
        await ctx.send("❌ আপনার ভয়েস মিউট করার অনুমতি নেই।")
        return
    try:
        await member.edit(mute=True, reason=reason)
        await ctx.send(f"🎙️🔇 ভয়েস মিউট করা হয়েছে: **{member}**")
    except Exception as e:
        await ctx.send(f"❌ ভয়েস মিউট করতে সমস্যা হয়েছে: {e}")

@bot.command(name="vcunmute")
async def vcunmute_command(ctx, member: discord.Member, *, reason=None):
    if not is_authorized(ctx):
        await ctx.send("❌ আপনার ভয়েস আনমিউট করার অনুমতি নেই।")
        return
    try:
        await member.edit(mute=False, reason=reason)
        await ctx.send(f"🎙️🔊 ভয়েস আনমিউট করা হয়েছে: **{member}**")
    except Exception as e:
        await ctx.send(f"❌ ভয়েস আনমিউট করতে সমস্যা হয়েছে: {e}")

@bot.command(name="vcdeafen")
async def vcdeafen_command(ctx, member: discord.Member, *, reason=None):
    if not is_authorized(ctx):
        await ctx.send("❌ আপনার ডিফেন (Deafen) করার অনুমতি নেই।")
        return
    try:
        await member.edit(deafen=True, reason=reason)
        await ctx.send(f"🎧 সার্ভার ডিফেন্ড করা হয়েছে: **{member}**")
    except Exception as e:
        await ctx.send(f"❌ ডিফেন করতে সমস্যা হয়েছে: {e}")

# --- ৩. সিস্টেম অন/অফ কন্ট্রোল ---
@bot.command(name="on", aliases=["start", "enable"])
async def system_on(ctx):
    if not is_authorized(ctx):
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["active"] = True
    save_server_config(guild_id, g_data)
    await ctx.send("🟢 **Adda_Zone Security Core & Anti-Nuke Fully Activated**")

@bot.command(name="off", aliases=["stop", "disable"])
async def system_off(ctx):
    if not is_authorized(ctx):
        return
    guild_id = str(ctx.guild.id)
    g_data = load_server_config(guild_id)
    g_data["active"] = False
    save_server_config(guild_id, g_data)
    await ctx.send("🔴 **Adda_Zone Security Core & Anti-Nuke Deactivated**")

@bot.command(name="help", aliases=["commands", "panel"])
async def help_command(ctx):
    prefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(title="🛡️ Adda_Zone Security & Voice Command Hub", description=f"Prefix: `{prefix}`", color=353942)
    embed.add_field(name="Moderation Commands", value=f"`{prefix}kick @user`, `{prefix}ban @user`, `{prefix}timeout @user [minutes]`", inline=False)
    embed.add_field(name="Voice Controls", value=f"`{prefix}vcmute @user`, `{prefix}vcunmute @user`, `{prefix}vcdeafen @user`", inline=False)
    embed.add_field(name="System Controls", value=f"`{prefix}on` / `{prefix}off`, `{prefix}ping`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"⚡ Adda_Zone Latency: {round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    keep_alive()
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
    else:
        print("CRITICAL ERROR: DISCORD_BOT_TOKEN is missing in environment variables!")
