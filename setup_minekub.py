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

WELCOME = """# ⛏️ ยินดีต้อนรับเข้าสู่ MINEKUB!

🌍 **MINEKUB | Minecraft Thailand Community**
ยินดีต้อนรับนักผจญภัยทุกคน 💚 ไม่ว่าคุณจะเป็นมือใหม่ นักสร้างบ้าน หรือสายสำรวจ ที่นี่คือชุมชน Minecraft สำหรับทุกคน

**📌 เริ่มต้นใช้งาน**
📜 อ่าน #กฎเซิร์ฟเวอร์ ให้เรียบร้อย
✅ ไปที่ #รับยศสมาชิก เพื่อดูวิธีรับยศพื้นฐาน
🎭 เลือกยศ Java, Bedrock และสายการเล่นที่ชอบ
💬 ทักทาย หาเพื่อนเล่น และสนุกไปด้วยกัน

**MINEKUB — ขุด สร้าง ผจญภัย ไปด้วยกัน!**"""

RULES = """# 📜 กฎระเบียบ MINEKUB

**01 | 🤝 เคารพสมาชิกทุกคน** — ห้ามคุกคาม ดูหมิ่น เหยียดหยาม หรือกลั่นแกล้ง
**02 | 🚫 ห้ามสแปม** — ห้ามส่งข้อความซ้ำ แท็กรัว หรือรบกวนห้องเสียง
**03 | 🔞 เนื้อหาปลอดภัย** — ห้ามเผยแพร่สื่อลามก เนื้อหารุนแรงร้ายแรง หรือเนื้อหาผิดกฎหมาย
**04 | 📢 งดโฆษณา** — ห้ามโปรโมตลิงก์ เซิร์ฟเวอร์ หรือสินค้าโดยไม่ได้รับอนุญาต
**05 | 🔐 เคารพความเป็นส่วนตัว** — ห้ามเปิดเผยข้อมูลส่วนตัวของคนอื่น
**06 | 🎮 เล่นอย่างยุติธรรม** — ห้ามโกงหรือใช้ช่องโหว่ในกิจกรรมของชุมชน
**07 | 💬 ใช้ห้องให้ถูกประเภท** — โพสต์ให้ตรงหัวข้อและเคารพผู้ใช้งานคนอื่น
**08 | 🛡️ เคารพการดูแล** — ทีมงานจะพิจารณาตามหลักฐานและความรุนแรง

**⚠️ การบังคับใช้กฎ:** ตักเตือน → จำกัดการส่งข้อความ → เตะ/แบน โดยอาจข้ามขั้นสำหรับกรณีร้ายแรง

💚 ขอบคุณที่ร่วมกันดูแล MINEKUB"""

MEMBER_PANEL = """# ✅ MINEKUB | รับยศสมาชิก

ยศพื้นฐานสำหรับทุกคนคือ **✅ สมาชิก**
ยศนี้ใช้สำหรับเข้าร่วมพูดคุย หาเพื่อนเล่น แชร์ผลงาน และเข้าร่วมกิจกรรมของชุมชน

**ขั้นตอนรับยศ**
1. อ่านกฎเซิร์ฟเวอร์ให้ครบ
2. ไปที่ระบบ **Channels & Roles / Onboarding** ของ Discord แล้วเลือกยศสมาชิก ตามที่ทีมงานเปิดให้ใช้งาน
3. จากนั้นเลือกยศสายเกมของคุณในห้อง 🎭・เลือกรับยศ

🛠️ **สำหรับทีมงาน:** ห้องนี้เป็นข้อความแนะนำเท่านั้น ยังไม่มีปุ่มแจกยศอัตโนมัติจนกว่าจะตั้งค่า Discord Onboarding หรือเปิดบอทรับยศแบบออนไลน์"""

GAME_PANEL = """# 🎭 MINEKUB | เลือกรับยศ

🎮 **เวอร์ชันที่เล่น**
⛏️ Java Edition — เล่น Minecraft Java
📱 Bedrock Edition — เล่น Minecraft Bedrock

🌍 **สไตล์การเล่น**
🏗️ Builder — ชอบสร้างบ้าน
⚙️ Redstone — ชอบเครื่องจักร
🧭 Explorer — ชอบสำรวจ
🌳 Survival — ชอบเอาชีวิตรอด

ยศเหล่านี้เป็นตัวเลือกเสริม การกดรับยศจะเปิดใช้งานเมื่อทีมงานตั้งค่า **Discord Onboarding** หรือบอทจัดการยศแล้ว 💚"""

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

def ensure_role(roles):
    existing = next((role for role in roles if role["name"] in ("✅ สมาชิก", "สมาชิก")), None)
    if existing:
        plan("ใช้ยศสมาชิกเดิม: " + existing["name"])
        return existing
    plan("สร้างยศ ✅ สมาชิก (ไม่มีสิทธิ์ Administrator)")
    if DRY_RUN:
        return {"id": "DRY_ROLE", "name": "✅ สมาชิก"}
    created = request("POST", f"/guilds/{GUILD_ID}/roles", {
        "name": "✅ สมาชิก", "permissions": "0", "color": 3066993,
        "hoist": False, "mentionable": False
    })
    return created

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

def ensure_message(channel, content):
    if DRY_RUN and channel["id"].startswith("DRY_"):
        plan("จะส่งข้อความ: " + content.splitlines()[0] + " → #" + channel["name"])
        return
    history = request("GET", f"/channels/{channel['id']}/messages?limit=50")
    title = content.splitlines()[0]
    already = any(item.get("content", "").startswith(title) for item in history)
    if already:
        plan("มีข้อความหัวข้อนี้แล้ว: " + title)
    else:
        plan("ส่งข้อความ: " + title + " → #" + channel["name"])
        if not DRY_RUN:
            request("POST", f"/channels/{channel['id']}/messages", {
                "content": content, "allowed_mentions": {"parse": []}
            })

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
    ensure_role(roles)
    category = ensure_information_category(channels)
    for channel, content in ensure_channels(channels, category, me["id"]):
        ensure_message(channel, content)
    print("สำเร็จ: ตรวจสอบ/ตั้งค่าข้อความ MINEKUB แล้ว" if not DRY_RUN else
          "จบ Dry Run: ยังไม่มีการเปลี่ยนแปลงใน Discord", flush=True)

if __name__ == "__main__":
    main()
