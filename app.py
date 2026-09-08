
import streamlit as st
import sqlite3
import hashlib
import secrets
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px

APP_DIR = Path(__file__).parent
DB = APP_DIR / "mylink.db"

st.set_page_config(
    page_title="MY LINK",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: Inter, sans-serif; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0b1020 0%,#111a33 100%);
}
[data-testid="stSidebar"] * { color: #eef2ff !important; }
.hero {
    padding: 28px 32px; border-radius: 24px;
    background: linear-gradient(135deg,#111827 0%,#312e81 55%,#7c3aed 100%);
    color: white; margin-bottom: 22px;
    box-shadow: 0 18px 45px rgba(49,46,129,.25);
}
.hero h1 { font-size: 42px; margin: 0 0 8px; font-weight: 800; }
.hero p { margin: 0; opacity: .88; font-size: 16px; }
.badge { display:inline-block; padding:6px 11px; border-radius:999px;
    background:rgba(255,255,255,.14); font-size:12px; font-weight:700; }
.card {
    padding: 18px; border:1px solid rgba(148,163,184,.20);
    border-radius:18px; background:rgba(255,255,255,.02);
    min-height:110px;
}
.metric { font-size:30px; font-weight:800; margin-top:4px; }
.muted { color:#94a3b8; font-size:13px; }
.linkbox { padding:12px 14px; border-radius:12px; background:#f1f5f9;
    color:#0f172a; word-break:break-all; font-size:13px; }
.small-title { font-weight:700; font-size:15px; margin-bottom:8px; }
div[data-testid="stMetric"] {
    border:1px solid rgba(148,163,184,.18);
    padding:14px; border-radius:16px; background:rgba(255,255,255,.02);
}
.stButton>button { border-radius:12px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ---------- i18n ----------
T = {
"English": {
"dashboard":"Dashboard","leads":"Leads CRM","campaigns":"Campaign Studio","analytics":"Analytics",
"ai":"AI Lead Center","creators":"Creators","team":"Team","notifications":"Notifications",
"settings":"Settings","logout":"Log out","welcome":"Turn social attention into business.",
"total_leads":"Total Leads","new_leads":"New Leads","won":"Won Deals","views":"Campaign Views",
"conversion":"Conversion","create":"Create Campaign","save":"Save","search":"Search leads...",
"name":"Name","phone":"Phone","email":"Email","location":"Location","budget":"Budget",
"message":"Message","status":"Status","source":"Source","score":"Score","title":"Campaign title",
"description":"Description","price":"Price","offer":"Offer price","cta":"Call to action",
"no_data":"No data yet.","language":"Language","business":"Business","add_lead":"Add Lead",
"followup":"Follow-up","date":"Date","notes":"Notes","add":"Add","success":"Saved successfully.",
"share":"Share link","quick":"Quick Actions","recent":"Recent Leads","performance":"Performance",
"all":"All","new":"New","contacted":"Contacted","qualified":"Qualified","won_s":"Won","lost":"Lost",
"referrals":"Referrals","members":"Team Members","plan":"Plan","pro":"Pro","free":"Free",
"smart":"Smart Link","source_hint":"Use ?source=facebook, tiktok, instagram, linkedin or whatsapp",
"logout_confirm":"You have been logged out."
},
"සිංහල": {
"dashboard":"ඩෑෂ්බෝඩ්","leads":"ලීඩ් CRM","campaigns":"කැම්පේන්","analytics":"විශ්ලේෂණ",
"ai":"AI ලීඩ් මධ්‍යස්ථානය","creators":"ක්‍රියේටර්ස්","team":"කණ්ඩායම","notifications":"දැනුම්දීම්",
"settings":"සැකසුම්","logout":"ඉවත් වන්න","welcome":"Social Media අවධානය Business එකක් බවට පත් කරමු.",
"total_leads":"මුළු ලීඩ්","new_leads":"අලුත් ලීඩ්","won":"ජයගත් Deals","views":"Campaign Views",
"conversion":"Conversion","create":"Campaign එකක් සාදන්න","save":"සුරකින්න","search":"ලීඩ් සොයන්න...",
"name":"නම","phone":"දුරකථන","email":"ඊමේල්","location":"ස්ථානය","budget":"අයවැය",
"message":"පණිවිඩය","status":"තත්ත්වය","source":"මූලාශ්‍රය","score":"Score","title":"Campaign නම",
"description":"විස්තර","price":"මිල","offer":"Offer මිල","cta":"Action Button",
"no_data":"දත්ත නොමැත.","language":"භාෂාව","business":"ව්‍යාපාරය","add_lead":"ලීඩ් එකක් එක් කරන්න",
"followup":"Follow-up","date":"දිනය","notes":"සටහන්","add":"එක් කරන්න","success":"සාර්ථකව සුරකින ලදී.",
"share":"Share Link","quick":"ඉක්මන් ක්‍රියා","recent":"අලුත්ම ලීඩ්","performance":"කාර්යසාධනය",
"all":"සියල්ල","new":"අලුත්","contacted":"Contacted","qualified":"Qualified","won_s":"Won","lost":"Lost",
"referrals":"Referral","members":"කණ්ඩායම් සාමාජිකයින්","plan":"Plan","pro":"Pro","free":"Free",
"smart":"Smart Link","source_hint":"?source=facebook, tiktok, instagram, linkedin හෝ whatsapp භාවිතා කරන්න",
"logout_confirm":"ඔබ ඉවත් වී ඇත."
},
"தமிழ்": {
"dashboard":"டாஷ்போர்டு","leads":"லீட்ஸ் CRM","campaigns":"கேம்பெயின்கள்","analytics":"பகுப்பாய்வு",
"ai":"AI Lead Center","creators":"Creators","team":"Team","notifications":"Notifications",
"settings":"Settings","logout":"வெளியேறு","welcome":"Social attention-ஐ business-ஆக மாற்றுங்கள்.",
"total_leads":"மொத்த Leads","new_leads":"புதிய Leads","won":"வெற்றி Deals","views":"Campaign Views",
"conversion":"Conversion","create":"Campaign உருவாக்கு","save":"சேமி","search":"Leads தேடு...",
"name":"பெயர்","phone":"தொலைபேசி","email":"Email","location":"இடம்","budget":"Budget",
"message":"செய்தி","status":"நிலை","source":"Source","score":"Score","title":"Campaign title",
"description":"விளக்கம்","price":"விலை","offer":"Offer விலை","cta":"Action",
"no_data":"தரவு இல்லை.","language":"மொழி","business":"Business","add_lead":"Lead சேர்க்கவும்",
"followup":"Follow-up","date":"தேதி","notes":"குறிப்புகள்","add":"சேர்","success":"வெற்றிகரமாக சேமிக்கப்பட்டது.",
"share":"Share link","quick":"Quick Actions","recent":"Recent Leads","performance":"Performance",
"all":"All","new":"New","contacted":"Contacted","qualified":"Qualified","won_s":"Won","lost":"Lost",
"referrals":"Referrals","members":"Team Members","plan":"Plan","pro":"Pro","free":"Free",
"smart":"Smart Link","source_hint":"?source=facebook, tiktok, instagram, linkedin அல்லது whatsapp",
"logout_confirm":"நீங்கள் வெளியேறிவிட்டீர்கள்."
}}

def tr(k): return T[st.session_state.get("lang","English")].get(k,k)

# ---------- DB ----------
def connect():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS businesses(
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, plan TEXT DEFAULT 'Pro', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS campaigns(
        id INTEGER PRIMARY KEY, business_id INTEGER NOT NULL, public_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL, description TEXT DEFAULT '', price REAL DEFAULT 0,
        offer_price REAL DEFAULT 0, cta TEXT DEFAULT 'Get Offer',
        created_at TEXT NOT NULL, views INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY, business_id INTEGER NOT NULL, campaign_id INTEGER,
        name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT DEFAULT '',
        location TEXT DEFAULT '', budget TEXT DEFAULT '', message TEXT DEFAULT '',
        source TEXT DEFAULT 'direct', status TEXT DEFAULT 'new', score INTEGER DEFAULT 50,
        followup_date TEXT, notes TEXT DEFAULT '', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS creators(
        id INTEGER PRIMARY KEY, business_id INTEGER NOT NULL, name TEXT NOT NULL,
        email TEXT DEFAULT '', code TEXT UNIQUE NOT NULL, rate REAL DEFAULT 5,
        leads INTEGER DEFAULT 0, revenue REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS team(
        id INTEGER PRIMARY KEY, business_id INTEGER NOT NULL, name TEXT NOT NULL,
        email TEXT DEFAULT '', role TEXT DEFAULT 'Sales', active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY, business_id INTEGER NOT NULL, title TEXT NOT NULL,
        body TEXT NOT NULL, read INTEGER DEFAULT 0, created_at TEXT NOT NULL
    );
    """)
    # Demo business is only created when DB is empty.
    if c.execute("SELECT COUNT(*) FROM businesses").fetchone()[0] == 0:
        pw = hash_pw("demo1234")
        c.execute("INSERT INTO businesses(name,email,password_hash,plan,created_at) VALUES(?,?,?,?,?)",
                  ("MY LINK Demo Business","demo@mylink.local",pw,"Pro",now()))
        bid = c.execute("SELECT id FROM businesses WHERE email=?",("demo@mylink.local",)).fetchone()[0]
        cid = secrets.token_hex(5)
        c.execute("""INSERT INTO campaigns(business_id,public_id,title,description,price,offer_price,cta,created_at,views)
                     VALUES(?,?,?,?,?,?,?,?,?)""",(bid,cid,"Smart Business Launch",
                     "Turn social attention into qualified customers.",9990,7990,"Get Offer",now(),128))
        camp = c.execute("SELECT id FROM campaigns WHERE public_id=?",(cid,)).fetchone()[0]
        sample = [
            ("Amal Fernando","0771234567","amal@example.com","Colombo","LKR 100,000","Need more details","facebook","new",82),
            ("Nimali Silva","0715552211","nimali@example.com","Panadura","LKR 50,000","Interested","instagram","qualified",91),
            ("Kasun Perera","0768889000","","Moratuwa","","Please call me","tiktok","contacted",68),
            ("Sahan Jay","0752223333","","Kalutara","LKR 150,000","Looking for an offer","whatsapp","won",96),
        ]
        for x in sample:
            c.execute("""INSERT INTO leads(business_id,campaign_id,name,phone,email,location,budget,message,source,status,score,created_at)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(bid,camp,*x,now()))
        c.execute("INSERT INTO creators(business_id,name,email,code,rate,leads,revenue) VALUES(?,?,?,?,?,?,?)",
                  (bid,"Nethmi Creator","creator@example.com","MYLINK-NETHMI",5,24,18500))
        c.execute("INSERT INTO team(business_id,name,email,role) VALUES(?,?,?,?)",
                  (bid,"Sales Manager","manager@example.com","Manager"))
        c.execute("INSERT INTO notifications(business_id,title,body,created_at) VALUES(?,?,?,?)",
                  (bid,"Welcome to MY LINK","Your workspace is ready. Create your first campaign.",now()))
        c.commit(); c.close()

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def verify_pw(p,h): return hash_pw(p)==h

init_db()

# ---------- State / auth ----------
if "lang" not in st.session_state: st.session_state.lang = "English"
if "user_id" not in st.session_state: st.session_state.user_id = None
if "page" not in st.session_state: st.session_state.page = "Dashboard"

def q(sql, params=(), one=False):
    c=connect()
    rows=c.execute(sql,params).fetchall()
    c.close()
    return rows[0] if one and rows else (None if one else rows)

def execute(sql, params=()):
    c=connect(); cur=c.execute(sql,params); c.commit(); rid=cur.lastrowid; c.close(); return rid

def current_business():
    return q("SELECT * FROM businesses WHERE id=?", (st.session_state.user_id,), True)

def set_page(p):
    st.session_state.page=p

# ---------- Login ----------
if not st.session_state.user_id:
    st.markdown("""
    <div class="hero" style="max-width:900px;margin:55px auto 20px;">
      <span class="badge">SOCIAL → BUSINESS OS</span>
      <h1>🔗 MY LINK</h1>
      <p>One beautiful workspace for campaigns, leads, analytics, creators and growth.</p>
    </div>
    """, unsafe_allow_html=True)
    left,right=st.columns([1.2,1])
    with left:
        st.subheader("Welcome back")
        with st.form("login"):
            email=st.text_input("Email", value="demo@mylink.local")
            password=st.text_input("Password", type="password", value="demo1234")
            if st.form_submit_button("Sign in", use_container_width=True):
                b=q("SELECT * FROM businesses WHERE email=?",(email.strip().lower(),),True)
                if b and verify_pw(password,b["password_hash"]):
                    st.session_state.user_id=b["id"]; st.rerun()
                else: st.error("Invalid email or password.")
    with right:
        st.info("Demo account\n\nEmail: `demo@mylink.local`\n\nPassword: `demo1234`")
        st.caption("For production, connect Supabase/PostgreSQL and replace demo authentication with managed identity.")
    st.stop()

b=current_business()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🔗 MY LINK")
    st.caption("Social-to-Business OS")
    st.divider()
    pages=["Dashboard","Leads CRM","Campaign Studio","Analytics","AI Lead Center","Creators","Team","Notifications","Settings"]
    for p in pages:
        if st.button(tr({"Dashboard":"dashboard","Leads CRM":"leads","Campaign Studio":"campaigns","Analytics":"analytics","AI Lead Center":"ai","Creators":"creators","Team":"team","Notifications":"notifications","Settings":"settings"}[p]), key="nav_"+p, use_container_width=True):
            set_page(p); st.rerun()
    st.divider()
    st.markdown(f"**{b['name']}**")
    st.caption(f"{b['email']} • {b['plan']}")
    if st.button(tr("logout"), use_container_width=True):
        st.session_state.user_id=None; st.rerun()

# ---------- Dashboard ----------
if st.session_state.page=="Dashboard":
    leads=q("SELECT * FROM leads WHERE business_id=?",(b["id"],))
    campaigns=q("SELECT * FROM campaigns WHERE business_id=?",(b["id"],))
    total=len(leads); newc=sum(x["status"]=="new" for x in leads); won=sum(x["status"]=="won" for x in leads)
    views=sum(x["views"] for x in campaigns); conv=(won/total*100) if total else 0
    st.markdown(f'<div class="hero"><span class="badge">CONTROL CENTER</span><h1>{tr("welcome")}</h1><p>{b["name"]} • {b["plan"]} workspace</p></div>', unsafe_allow_html=True)
    a,c,d,e=st.columns(4)
    a.metric(tr("total_leads"),total); c.metric(tr("new_leads"),newc); d.metric(tr("won"),won); e.metric(tr("views"),views)
    st.divider()
    l,r=st.columns([1.45,1])
    with l:
        st.subheader(tr("performance"))
        if leads:
            df=pd.DataFrame([dict(x) for x in leads])
            by=df.groupby("source").size().reset_index(name="leads").sort_values("leads",ascending=False)
            fig=px.bar(by,x="source",y="leads",title="Leads by source")
            fig.update_layout(height=320,margin=dict(l=10,r=10,t=50,b=10))
            st.plotly_chart(fig,use_container_width=True)
        else: st.info(tr("no_data"))
    with r:
        st.subheader(tr("quick"))
        if st.button("➕ "+tr("create"),use_container_width=True): set_page("Campaign Studio"); st.rerun()
        if st.button("👤 "+tr("add_lead"),use_container_width=True): set_page("Leads CRM"); st.rerun()
        if st.button("🤖 "+tr("ai"),use_container_width=True): set_page("AI Lead Center"); st.rerun()
        st.metric(tr("conversion"),f"{conv:.1f}%")
    st.subheader(tr("recent"))
    if leads:
        df=pd.DataFrame([dict(x) for x in leads]).sort_values("created_at",ascending=False).head(6)
        st.dataframe(df[["name","phone","source","status","score","created_at"]],use_container_width=True,hide_index=True)

# ---------- Leads ----------
elif st.session_state.page=="Leads CRM":
    st.title("👥 "+tr("leads"))
    search=st.text_input("🔎 "+tr("search"))
    status=st.selectbox(tr("status"),[tr("all"),"new","contacted","qualified","won","lost"])
    rows=q("SELECT * FROM leads WHERE business_id=? ORDER BY created_at DESC",(b["id"],))
    data=[dict(x) for x in rows]
    if search:
        s=search.lower(); data=[x for x in data if s in (x["name"]+x["phone"]+x["email"]+x["location"]).lower()]
    if status!=tr("all"): data=[x for x in data if x["status"]==status]
    if data:
        df=pd.DataFrame(data)
        st.dataframe(df[["id","name","phone","email","location","budget","source","status","score","followup_date","created_at"]],
                     use_container_width=True,hide_index=True)
    st.divider()
    with st.expander("➕ "+tr("add_lead"),expanded=False):
        with st.form("addlead"):
            c1,c2=st.columns(2)
            name=c1.text_input(tr("name")); phone=c2.text_input(tr("phone"))
            email=c1.text_input(tr("email")); location=c2.text_input(tr("location"))
            budget=c1.text_input(tr("budget")); source=c2.selectbox(tr("source"),["direct","facebook","instagram","tiktok","linkedin","whatsapp"])
            msg=st.text_area(tr("message"))
            if st.form_submit_button(tr("add"),use_container_width=True):
                if not name.strip() or not phone.strip(): st.error("Name and phone are required.")
                else:
                    score=min(100,50+(20 if budget else 0)+(10 if email else 0)+(10 if msg else 0))
                    execute("""INSERT INTO leads(business_id,name,phone,email,location,budget,message,source,status,score,created_at)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(b["id"],name,phone,email,location,budget,msg,source,"new",score,now()))
                    st.success(tr("success")); st.rerun()
    if data:
        st.subheader("Update lead")
        lid=st.selectbox("Lead ID",[x["id"] for x in data])
        selected=next(x for x in data if x["id"]==lid)
        ns=st.selectbox(tr("status"),["new","contacted","qualified","won","lost"],index=["new","contacted","qualified","won","lost"].index(selected["status"]))
        fd=st.date_input(tr("followup"),value=date.fromisoformat(selected["followup_date"]) if selected["followup_date"] else date.today())
        notes=st.text_area(tr("notes"),value=selected["notes"] or "")
        if st.button(tr("save"),use_container_width=True):
            execute("UPDATE leads SET status=?,followup_date=?,notes=? WHERE id=? AND business_id=?",(ns,fd.isoformat(),notes,lid,b["id"]))
            st.success(tr("success")); st.rerun()

# ---------- Campaigns ----------
elif st.session_state.page=="Campaign Studio":
    st.title("🚀 "+tr("campaigns"))
    with st.form("campaign"):
        c1,c2=st.columns(2)
        title=c1.text_input(tr("title"))
        cta=c2.text_input(tr("cta"),"Get Offer")
        price=c1.number_input(tr("price"),min_value=0.0,value=0.0,step=100.0)
        offer=c2.number_input(tr("offer"),min_value=0.0,value=0.0,step=100.0)
        desc=st.text_area(tr("description"))
        if st.form_submit_button(tr("create"),use_container_width=True):
            if not title.strip(): st.error("Campaign title is required.")
            else:
                pid=secrets.token_urlsafe(8).replace("-","").replace("_","")
                execute("""INSERT INTO campaigns(business_id,public_id,title,description,price,offer_price,cta,created_at,views)
                           VALUES(?,?,?,?,?,?,?,?,0)""",(b["id"],pid,title,desc,price,offer,cta,now()))
                st.success("Campaign created."); st.rerun()
    st.divider()
    rows=q("SELECT * FROM campaigns WHERE business_id=? ORDER BY created_at DESC",(b["id"],))
    for x in rows:
        with st.container(border=True):
            st.subheader(x["title"])
            st.write(x["description"])
            m1,m2,m3=st.columns(3); m1.metric("Price",f"LKR {x['price']:,.0f}"); m2.metric("Offer",f"LKR {x['offer_price']:,.0f}"); m3.metric("Views",x["views"])
            base=st.context.url if hasattr(st.context,"url") else "https://your-app.streamlit.app"
            link=f"{base}?campaign={x['public_id']}"
            st.markdown(f'<div class="linkbox">🔗 {link}</div>',unsafe_allow_html=True)
            st.caption(tr("source_hint"))
            st.code(f"{link}&source=facebook",language="text")

# ---------- Analytics ----------
elif st.session_state.page=="Analytics":
    st.title("📊 "+tr("analytics"))
    rows=q("SELECT * FROM leads WHERE business_id=?",(b["id"],))
    camps=q("SELECT * FROM campaigns WHERE business_id=?",(b["id"],))
    if rows:
        df=pd.DataFrame([dict(x) for x in rows])
        c1,c2=st.columns(2)
        with c1:
            fig=px.pie(df,names="source",title="Lead source mix",hole=.45)
            st.plotly_chart(fig,use_container_width=True)
        with c2:
            fig=px.bar(df.groupby("status").size().reset_index(name="count"),x="status",y="count",title="Pipeline")
            st.plotly_chart(fig,use_container_width=True)
        st.subheader("Campaign performance")
        campdf=pd.DataFrame([dict(x) for x in camps]) if camps else pd.DataFrame()
        if not campdf.empty:
            campdf["leads"]=[q("SELECT COUNT(*) c FROM leads WHERE campaign_id=?",(x["id"],),True)["c"] for x in camps]
            campdf["conversion"]=(campdf["leads"]/campdf["views"].replace(0,1)*100).round(1)
            st.dataframe(campdf[["title","views","leads","conversion"]],use_container_width=True,hide_index=True)
    else: st.info(tr("no_data"))

# ---------- AI ----------
elif st.session_state.page=="AI Lead Center":
    st.title("🤖 "+tr("ai"))
    st.caption("Local explainable scoring engine — no fake external AI calls.")
    rows=q("SELECT * FROM leads WHERE business_id=? ORDER BY score DESC",(b["id"],))
    if rows:
        for x in rows:
            priority="🔥 HIGH" if x["score"]>=80 else ("🟡 MEDIUM" if x["score"]>=60 else "⚪ LOW")
            with st.container(border=True):
                c1,c2,c3=st.columns([2,1,3])
                c1.markdown(f"**{x['name']}**  \n{x['phone']} • {x['source']}")
                c2.metric("Score",x["score"])
                c3.write(priority)
                if x["score"]>=80: st.success("Contact quickly. Lead has strong qualification signals.")
                elif x["score"]>=60: st.warning("Ask one qualifying question and schedule a follow-up.")
                else: st.info("Collect budget, requirement and contact details.")
    else: st.info(tr("no_data"))

# ---------- Creators ----------
elif st.session_state.page=="Creators":
    st.title("🤝 "+tr("creators"))
    with st.form("creator"):
        n,e=st.columns(2); name=n.text_input(tr("name")); email=e.text_input(tr("email"))
        rate=st.number_input("Commission %",0.0,50.0,5.0)
        if st.form_submit_button(tr("add"),use_container_width=True):
            code="MYLINK-"+secrets.token_hex(4).upper()
            execute("INSERT INTO creators(business_id,name,email,code,rate) VALUES(?,?,?,?,?)",(b["id"],name,email,code,rate))
            st.success(tr("success")); st.rerun()
    rows=q("SELECT * FROM creators WHERE business_id=?",(b["id"],))
    if rows: st.dataframe(pd.DataFrame([dict(x) for x in rows]),use_container_width=True,hide_index=True)

# ---------- Team ----------
elif st.session_state.page=="Team":
    st.title("👥 "+tr("team"))
    with st.form("team"):
        n,e=st.columns(2); name=n.text_input(tr("name")); email=e.text_input(tr("email"))
        role=st.selectbox("Role",["Sales","Manager","Admin","Viewer"])
        if st.form_submit_button(tr("add"),use_container_width=True):
            execute("INSERT INTO team(business_id,name,email,role) VALUES(?,?,?,?)",(b["id"],name,email,role))
            st.success(tr("success")); st.rerun()
    rows=q("SELECT * FROM team WHERE business_id=?",(b["id"],))
    if rows: st.dataframe(pd.DataFrame([dict(x) for x in rows]),use_container_width=True,hide_index=True)

# ---------- Notifications ----------
elif st.session_state.page=="Notifications":
    st.title("🔔 "+tr("notifications"))
    rows=q("SELECT * FROM notifications WHERE business_id=? ORDER BY created_at DESC",(b["id"],))
    for x in rows:
        st.info(f"**{x['title']}**\n\n{x['body']}\n\n{x['created_at']}")

# ---------- Settings ----------
elif st.session_state.page=="Settings":
    st.title("⚙️ "+tr("settings"))
    lang=st.selectbox(tr("language"),list(T.keys()),index=list(T.keys()).index(st.session_state.lang))
    if lang!=st.session_state.lang:
        st.session_state.lang=lang; st.rerun()
    st.subheader(tr("business"))
    st.write(f"**{b['name']}**")
    st.write(b["email"])
    st.write(f"Plan: **{b['plan']}**")
    st.divider()
    st.subheader("Deployment health")
    st.success("MY LINK is running")
    st.write("Database: SQLite local mode")
    st.write("Cloud sync: ready for Supabase/PostgreSQL integration")
    st.warning("For public production, enable managed authentication, PostgreSQL, secrets, backups, rate limiting and HTTPS.")
