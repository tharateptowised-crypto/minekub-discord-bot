"""MINEKUB one-shot Discord bootstrap. Only creates missing resources; never deletes."""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://discord.com/api/v10"
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "").strip()
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() != "false"
VIEW = 1 << 10
SEND = 1 << 11
HISTORY = 1 << 16
MANAGE_CHANNELS = 1 << 4
MANAGE_ROLES = 1 << 28

WELCOME = """# ⛏️ ยินดีต้อนรับสู่ MINEKUB!

🌍 **MINEKUB | Minecraft Thailand Community**

ยินดีต้อนรับนักผจญภัยทุกคน! 💚 ไม่ว่าจะเป็นมือใหม่ สายสร้างบ้าน สายสำรวจ หรือผู้เล่น Minecraft ระดับโปร ทุกคนสามารถสนุกและหาเพื่อนเล่นด้วยกันได้

**📌 เริ่มต้นใช้งาน 3 ขั้นตอน**
1️⃣ อ่านกฎในห้อง 📜・กฎเซิร์ฟเวอร์
2️⃣ ดูวิธีรับยศพื้นฐานในห้อง ✅・รับยศสมาชิก
3️⃣ เลือกเวอร์ชันเกมและสายที่ชอบในห้อง 🎭・เลือกรับยศ

💬 พูดคุย แชร์ผลงาน หาเพื่อน และร่วมสนุกกับชุมชนได้เลย!

**MINEKUB — ขุด • สร้าง • ผจญภัย ไปด้วยกัน!**"""

RULES = """# 📜 กฎชุมชน MINEKUB

**01 | 🤝 เคารพสมาชิกทุกคน** — ห้ามด่า เหยียด คุกคาม กลั่นแกล้ง หรือยั่วยุให้ทะเลาะกัน
**02 | 🚫 ห้ามสแปม** — ห้ามส่งข้อความซ้ำ แท็กรัว หรือใช้เสียงรบกวนผู้อื่น
**03 | 🔞 เนื้อหาต้องเหมาะสม** — ห้ามสื่อลามก ภาพรุนแรงร้ายแรง และเนื้อหาผิดกฎหมาย
**04 | 📢 ไม่โฆษณาโดยพลการ** — งดโปรโมตเซิร์ฟเวอร์อื่น ลิงก์ขายของ หรือชักชวนโดยไม่ได้รับอนุญาต
**05 | 🔐 เคารพข้อมูลส่วนตัว** — ห้ามเผยแพร่ข้อมูลส่วนบุคคล รูปภาพหรือข้อความส่วนตัวของผู้อื่น
**06 | 🎮 เล่นอย่างยุติธรรม** — ห้ามโกงหรือใช้ช่องโหว่ในกิจกรรมที่ MINEKUB จัด
**07 | 💬 ใช้ห้องให้ตรงประเภท** — โพสต์ตามหัวข้อของห้อง ไม่ป่วนห้องพูดคุย
**08 | 🛡️ ทำตามกฎและคำแนะนำทีมงาน** — หากพบปัญหาให้แจ้งผู้ดูแลพร้อมหลักฐาน

⚠️ **บทลงโทษ:** ตักเตือน, Timeout, เตะ หรือแบน ตามความรุนแรงของเหตุการณ์ ความผิดร้ายแรงอาจถูกแบนทันที

💚 ขอบคุณที่ช่วยกันทำให้ MINEKUB เป็นพื้นที่ดี ๆ ของทุกคน"""

MEMBER_PANEL = """# ✅ จุดรับยศสมาชิก | MINEKUB

🌱 **ยศเริ่มต้น: ✅ สมาชิก**
ยศพื้นฐานสำหรับทุกคนในชุมชน เมื่อรับยศแล้วสามารถเข้าร่วมพูดคุย หาเพื่อนเล่น แชร์ผลงาน และร่วมกิจกรรมในพื้นที่ที่ทีมงานเปิดให้

**วิธีรับยศ**
1️⃣ อ่านกฎในห้อง 📜・กฎเซิร์ฟเวอร์
2️⃣ เปิด **ช่องและยศ (Channels & Roles)** ใน Discord แล้วเลือก **✅ สมาชิก** หากทีมงานเปิด Onboarding ไว้
3️⃣ เลือกยศ Minecraft เพิ่มเติมที่ห้อง 🎭・เลือกรับยศ

❔ ไม่พบตัวเลือกยศ? โปรดติดต่อทีมงาน

💚 ยินดีต้อนรับสู่ MINEKUB!

*หมายเหตุ: ห้องนี้เป็นจุดแนะนำการรับยศ ระบบกดรับยศอัตโนมัติต้องเปิด Onboarding หรือบอทที่ออนไลน์ก่อน*"""

GAME_PANEL = """# 🎭 เลือกยศของคุณ | MINEKUB

เลือกเวอร์ชัน Minecraft และสไตล์การเล่น เพื่อให้สมาชิกคนอื่นหาเพื่อนเล่นด้วยได้ง่ายขึ้น

**🎮 เวอร์ชันที่เล่น**
⛏️ **Java Edition** — ผู้เล่น Minecraft Java
📱 **Bedrock Edition** — ผู้เล่น Minecraft Bedrock

**🌍 สายการเล่น**
🏗️ **Builder** — ชอบสร้างบ้าน
⚙️ **Redstone** — ชอบวงจรและเครื่องจักร
🧭 **Explorer** — ชอบสำรวจโลก Minecraft
🌳 **Survival** — ชอบเอาชีวิตรอด

✅ เลือกได้หลายยศผ่าน **ช่องและยศ (Channels & Roles)** เมื่อทีมงานเปิดใช้งาน

💚 ทุกสไตล์การเล่นมีที่อยู่ใน MINEKUB!"""

ROLE_SPECS = [
    ("⛏️ Java Edition", ["Java Edition", "Java Player"], 0x1F8B4C, 0),
    ("📱 Bedrock Edition", ["Bedrock Edition", "Bedrock Player"], 0x3498DB, 0),
    ("🏗️ Builder", ["Builder", "นักสร้าง"], 0xF1C40F, 0),
    ("⚙️ Redstone", ["Redstone", "ผู้เชี่ยวชาญเรดสโตน"], 0xE74C3C, 0),
    ("🧭 Explorer", ["Explorer", "นักสำรวจ"], 0x85C1E9, 0),
    ("🌳 Survival", ["Survival", "เอาชีวิตรอด"], 0x229954, 0),
    ("✅ สมาชิก", ["สมาชิก"], 0x2ECC71, (1 << 10) | (1 << 11) | (1 << 16) | (1 << 20) | (1 << 21)),
]

LEGACY_TITLES = {
    "# ⛏️ ยินดีต้อนรับสู่ MINEKUB!": ["# ⛏️ ยินดีต้อนรับเข้าสู่ MINEKUB!"],
    "# 📜 กฎชุมชน MINEKUB": ["# 📜 กฎระเบียบ MINEKUB"],
    "# ✅ จุดรับยศสมาชิก | MINEKUB": ["# ✅ MINEKUB | รับยศสมาชิก"],
    "# 🎭 เลือกยศของคุณ | MINEKUB": ["# 🎭 MINEKUB | เลือกรับยศ"],
}

CHANNELS = [
    ("👋・ยินดีต้อนรับ", ["ยินดีต้อนรับ", "welcome"], WELCOME),
    ("📜・กฎเซิร์ฟเวอร์", ["กฎเซิร์ฟเวอร์", "rules"], RULES),
    ("✅・รับยศสมาชิก", ["รับยศสมาชิก", "รับยศ", "verify", "verification"], MEMBER_PANEL),
    ("🎭・เลือกรับยศ", ["เลือกรับยศ", "choose-roles", "roles"], GAME_PANEL),
]

def request(method, path, body=None):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Authorization": "Bot " + TOKEN, "User-Agent": "MINEKUB-Setup/1.0"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(5):
        req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else None
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", "replace")
            if err.code == 429 and attempt < 4:
                try:
                    delay = min(30, float(json.loads(detail).get("retry_after", 2)))
                except (ValueError, TypeError):
                    delay = 2
                time.sleep(max(delay, 0.5))
                continue
            raise RuntimeError(f"Discord API {method} {path}: HTTP {err.code}: {detail[:500]}") from None
    raise RuntimeError("Discord API retry limit reached")

def key(value):
    return re.sub(r"[^a-z0-9ก-๙]", "", value.casefold())

def find_channel(channels, candidates, channel_type=0):
    keys = {key(name) for name in candidates}
    return next((ch for ch in channels if ch["type"] == channel_type and key(ch["name"]) in keys), None)

def plan(line):
    print(("[DRY RUN] " if DRY_RUN else "[APPLY] ") + line, flush=True)

def ensure_roles(roles):
    current = {key(r["name"]): r for r in roles}
    for name, aliases, color, perms in ROLE_SPECS:
        existing = next((current[key(n)] for n in [name] + aliases if key(n) in current), None)
        if existing:
            if name == "✅ สมาชิก" and (int(existing.get("permissions", "0")) & 8):
                sys.exit("พบยศสมาชิกเดิมมีสิทธิ์ Administrator โปรดตรวจสอบก่อนดำเนินการ")
            plan("ใช้ยศเดิม (ไม่แก้สิทธิ์เดิม): " + existing["name"])
            continue
        plan("สร้างยศใหม่: " + name)
        if not DRY_RUN:
            created = request("POST", f"/guilds/{GUILD_ID}/roles", {
                "name": name, "permissions": str(perms), "color": color,
                "hoist": False, "mentionable": False
            })
            current[key(name)] = created

def ensure_information_category(channels):
    cat = find_channel(channels, ["📌 เริ่มต้นที่นี่", "เริ่มต้นที่นี่", "information", "start-here"], 4)
    if cat:
        plan("ใช้หมวดหมู่เดิม: " + cat["name"])
        return cat
    plan("สร้างหมวดหมู่ 📌 เริ่มต้นที่นี่")
    if DRY_RUN:
        return {"id": "DRY_CATEGORY", "name": "📌 เริ่มต้นที่นี่", "type": 4}
    cat = request("POST", f"/guilds/{GUILD_ID}/channels", {"name": "📌 เริ่มต้นที่นี่", "type": 4})
    channels.append(cat)
    return cat

def ensure_channels(channels, category, bot_id):
    results = []
    for name, aliases, content in CHANNELS:
        existing = find_channel(channels, [name] + aliases, 0)
        if existing:
            plan("ใช้ห้องเดิม: " + existing["name"])
            results.append((existing, content))
            continue
        plan("สร้างห้อง " + name + " (สมาชิกอ่านข้อความได้ แต่ส่งข้อความไม่ได้)")
        if DRY_RUN:
            results.append(({"id": "DRY_" + str(len(results)), "name": name, "type": 0}, content))
            continue
        overwrites = [
            {"id": GUILD_ID, "type": 0, "allow": str(VIEW | HISTORY), "deny": str(SEND)},
            {"id": bot_id, "type": 1, "allow": str(VIEW | SEND | HISTORY), "deny": "0"},
        ]
        payload = {"name": name, "type": 0, "parent_id": category["id"],
                   "permission_overwrites": overwrites}
        created = request("POST", f"/guilds/{GUILD_ID}/channels", payload)
        channels.append(created)
        results.append((created, content))
    return results

def ensure_message(channel, content, bot_id):
    title = content.splitlines()[0]
    known_titles = {title, *LEGACY_TITLES.get(title, [])}
    if len(content) > 2000:
        raise ValueError("Discord message exceeds 2000 characters: " + title)
    if DRY_RUN and str(channel["id"]).startswith("DRY_"):
        plan("จะส่งข้อความ: " + title + " → #" + channel["name"])
        return
    history = request("GET", f"/channels/{channel['id']}/messages?limit=100")
    def first_line(m):
        return (m.get("content") or "").splitlines()[0:1]
    own = next((m for m in history if str(m.get("author", {}).get("id")) == str(bot_id)
                and any(line in known_titles for line in first_line(m))), None)
    other = next((m for m in history if str(m.get("author", {}).get("id")) != str(bot_id)
                  and any(line in known_titles for line in first_line(m))), None)
    payload = {"content": content, "allowed_mentions": {"parse": []}}
    if own:
        if own.get("content") == content:
            plan("ข้อความล่าสุดอยู่แล้ว: " + title)
        else:
            plan("ปรับปรุงข้อความเดิมของบอท: " + title)
            if not DRY_RUN:
                request("PATCH", f"/channels/{channel['id']}/messages/{own['id']}", payload)
    elif other:
        plan("พบข้อความหัวข้อเดียวกันของสมาชิก/ทีมงาน จึงไม่เขียนทับ: " + title)
    else:
        plan("ส่งข้อความ: " + title + " → #" + channel["name"])
        if not DRY_RUN:
            request("POST", f"/channels/{channel['id']}/messages", payload)

def main():
    if not TOKEN or not GUILD_ID or not GUILD_ID.isdigit():
        sys.exit("กรุณาตั้ง GitHub Secrets DISCORD_BOT_TOKEN และ DISCORD_GUILD_ID ให้ถูกต้อง")
    guild = request("GET", f"/guilds/{GUILD_ID}")
    guild_name = guild.get("name", "")
    if guild_name.strip().casefold() != "minekub":
        sys.exit(f"หยุดเพื่อความปลอดภัย: Server ID นี้ชื่อ {guild_name!r} ไม่ใช่ MINEKUB")
    me = request("GET", "/users/@me")
    roles = request("GET", f"/guilds/{GUILD_ID}/roles")
    channels = request("GET", f"/guilds/{GUILD_ID}/channels")
    plan(f"ตรวจสอบเซิร์ฟเวอร์ {guild_name} สำเร็จ | บอท {me['username']}")
    ensure_roles(roles)
    category = ensure_information_category(channels)
    for channel, content in ensure_channels(channels, category, me["id"]):
        ensure_message(channel, content, me["id"])
    print("สำเร็จ: ตรวจสอบ/ตั้งค่าข้อความ MINEKUB แล้ว" if not DRY_RUN else
          "จบ Dry Run: ยังไม่มีการเปลี่ยนแปลงใน Discord", flush=True)

if __name__ == "__main__":
    main()
