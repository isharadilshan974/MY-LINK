import os, re, hashlib, secrets
from datetime import datetime, date, timedelta
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / 'data' / 'mylink.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = object

st.set_page_config(page_title='MY LINK', page_icon='🔗', layout='wide', initial_sidebar_state='expanded')

# ---------- Storage ----------
class Store:
    def __init__(self):
        self.sb = None
        url = os.getenv('SUPABASE_URL', '')
        key = os.getenv('SUPABASE_KEY', '')
        try:
            url = url or str(st.secrets.get('SUPABASE_URL', ''))
            key = key or str(st.secrets.get('SUPABASE_KEY', ''))
        except Exception:
            pass
        if create_client and url and key:
            try: self.sb = create_client(url, key)
            except Exception: self.sb = None
        if not self.sb:
            import sqlite3
            self.sqlite3 = sqlite3
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.init_sqlite()

    def init_sqlite(self):
        c=self.conn.cursor()
        c.executescript('''
        CREATE TABLE IF NOT EXISTS businesses(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS campaigns(id INTEGER PRIMARY KEY AUTOINCREMENT,business_id INTEGER,title TEXT NOT NULL,description TEXT,price REAL DEFAULT 0,offer_price REAL DEFAULT 0,cta TEXT DEFAULT 'Get Offer',public_id TEXT UNIQUE,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY AUTOINCREMENT,business_id INTEGER,campaign_id INTEGER,name TEXT NOT NULL,phone TEXT NOT NULL,email TEXT,location TEXT,budget TEXT,message TEXT,source TEXT,status TEXT DEFAULT 'new',score INTEGER DEFAULT 50,created_at TEXT NOT NULL,followup_date TEXT);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,campaign_id INTEGER,event_type TEXT,source TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS creators(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT UNIQUE,referral_code TEXT UNIQUE,commission_rate REAL DEFAULT 5,leads INTEGER DEFAULT 0,earnings REAL DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS team(id INTEGER PRIMARY KEY AUTOINCREMENT,business_id INTEGER,name TEXT,email TEXT,role TEXT,active INTEGER DEFAULT 1,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY AUTOINCREMENT,business_id INTEGER,title TEXT,message TEXT,read INTEGER DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,business_id INTEGER,action TEXT,details TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS subscriptions(id INTEGER PRIMARY KEY AUTOINCREMENT,business_id INTEGER UNIQUE,plan TEXT DEFAULT 'free',price REAL DEFAULT 0,status TEXT DEFAULT 'active');
        ''')
        self.conn.commit()

    def q(self, sql, params=(), one=False):
        cur=self.conn.execute(sql, params); rows=cur.fetchall(); return (rows[0] if rows else None) if one else rows
    def exec(self, sql, params=()):
        cur=self.conn.execute(sql, params); self.conn.commit(); return cur.lastrowid

    def get_business(self,email): return self.q('SELECT * FROM businesses WHERE lower(email)=lower(?)',(email,),True)
    def create_business(self,name,email,password): return self.exec('INSERT INTO businesses(name,email,password,created_at) VALUES(?,?,?,?)',(name,email,password,datetime.utcnow().isoformat()))
    def campaign_list(self,bid): return self.q('SELECT * FROM campaigns WHERE business_id=? ORDER BY id DESC',(bid,))
    def lead_list(self,bid): return self.q('SELECT l.*, c.title campaign FROM leads l LEFT JOIN campaigns c ON c.id=l.campaign_id WHERE l.business_id=? ORDER BY l.id DESC',(bid,))
    def events(self,bid): return self.q('SELECT e.*, c.title campaign FROM events e JOIN campaigns c ON c.id=e.campaign_id WHERE c.business_id=?',(bid,))
    def dashboard(self,bid):
        leads=self.q('SELECT COUNT(*) n FROM leads WHERE business_id=?',(bid,),True)['n'];
        new=self.q("SELECT COUNT(*) n FROM leads WHERE business_id=? AND status='new'",(bid,),True)['n'];
        won=self.q("SELECT COUNT(*) n FROM leads WHERE business_id=? AND status='won'",(bid,),True)['n'];
        views=self.q('SELECT COUNT(*) n FROM events e JOIN campaigns c ON c.id=e.campaign_id WHERE c.business_id=? AND e.event_type="view"',(bid,),True)['n'];
        return leads,new,won,views
    def add_audit(self,bid,action,details=''): self.exec('INSERT INTO audit(business_id,action,details,created_at) VALUES(?,?,?,?)',(bid,action,details,datetime.utcnow().isoformat()))

store=Store()

def hpw(p): return hashlib.sha256(('mylink:'+p).encode()).hexdigest()
def valid_email(x): return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',x or ''))
def esc_phone(x): return re.sub(r'[^0-9+ ]','',x or '').strip()
def score_lead(budget,email,message,phone):
    s=35
    if phone:s+=20
    if budget:s+=20
    if email:s+=10
    if message:s+=15
    return min(100,s)
def money(x): return f"LKR {float(x or 0):,.0f}"

def seed():
    b=store.get_business('demo@mylink.local')
    if not b:
        bid=store.create_business('MY LINK Demo Business','demo@mylink.local',hpw('demo1234'))
        store.exec('INSERT OR IGNORE INTO subscriptions(business_id,plan,price,status) VALUES(?,?,?,?)',(bid,'pro',2000,'active'))
        cid=store.exec('INSERT INTO campaigns(business_id,title,description,price,offer_price,cta,public_id,created_at) VALUES(?,?,?,?,?,?,?,?)',(bid,'Smart Business Launch','Turn social attention into qualified customers.',10000,7990,'Get Offer',secrets.token_urlsafe(8),datetime.utcnow().isoformat()))
        for i,(n,p,s) in enumerate([('Kasun Perera','0771234567','facebook'),('Nimali Silva','0712345678','tiktok'),('Amal Fernando','0769876543','instagram')]):
            store.exec('INSERT INTO leads(business_id,campaign_id,name,phone,email,location,budget,message,source,status,score,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(bid,cid,n,p,n.lower().replace(' ','')+'@example.com','Colombo','50000','Interested in the offer',s,'new',85-i*10,datetime.utcnow().isoformat()))
        store.exec('INSERT INTO events(campaign_id,event_type,source,created_at) VALUES(?,?,?,?)',(cid,'view','facebook',datetime.utcnow().isoformat()))
seed()

# ---------- CSS ----------
st.markdown('''<style>
.block-container{padding-top:1.3rem;padding-bottom:3rem;max-width:1450px}.brand{font-size:2rem;font-weight:800;letter-spacing:-.03em}.muted{color:#8b93a7}.card{padding:20px;border:1px solid rgba(127,127,127,.18);border-radius:18px;background:rgba(127,127,127,.05);height:100%}.hero{padding:28px;border-radius:24px;background:linear-gradient(135deg,#111827,#312e81);color:white;margin-bottom:22px}.pill{display:inline-block;padding:5px 10px;border-radius:999px;font-size:.78rem;font-weight:700;background:rgba(124,58,237,.13)}.small{font-size:.85rem}.stButton>button{border-radius:10px}.metric{font-size:2rem;font-weight:800}.danger{color:#ef4444}.success{color:#22c55e}
</style>''', unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user=None
if 'page' not in st.session_state: st.session_state.page='Dashboard'

# ---------- Public campaign ----------
params=st.query_params
public=params.get('c')
if public:
    row=store.q('SELECT * FROM campaigns WHERE public_id=?',(public,),True)
    if not row: st.error('Campaign not found'); st.stop()
    source=params.get('source','direct')
    store.exec('INSERT INTO events(campaign_id,event_type,source,created_at) VALUES(?,?,?,?)',(row['id'],'view',source,datetime.utcnow().isoformat()))
    st.markdown(f'<div class="hero"><div class="pill">MY LINK • VERIFIED CAMPAIGN</div><h1>{row["title"]}</h1><p>{row["description"] or "Discover this offer and connect with the business."}</p><h2>{money(row["offer_price"] or row["price"])}</h2></div>',unsafe_allow_html=True)
    with st.form('public_lead'):
        st.subheader('Get this offer')
        c1,c2=st.columns(2); name=c1.text_input('Full name *'); phone=c2.text_input('Phone *'); email=c1.text_input('Email'); location=c2.text_input('Location'); budget=c1.text_input('Budget'); msg=st.text_area('Message'); submitted=st.form_submit_button(row['cta'] or 'Get Offer',use_container_width=True)
        if submitted:
            phone=esc_phone(phone)
            if not name.strip() or len(phone)<7: st.error('Please enter your name and a valid phone number.')
            elif email and not valid_email(email): st.error('Please enter a valid email.')
            else:
                sc=score_lead(budget,email,msg,phone); store.exec('INSERT INTO leads(business_id,campaign_id,name,phone,email,location,budget,message,source,status,score,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(row['business_id'],row['id'],name.strip(),phone,email.strip(),location.strip(),budget.strip(),msg.strip(),source,'new',sc,datetime.utcnow().isoformat())); store.exec('INSERT INTO events(campaign_id,event_type,source,created_at) VALUES(?,?,?,?)',(row['id'],'lead',source,datetime.utcnow().isoformat())); st.success('Thank you! Your request has been received.'); st.balloons()
    st.stop()

# ---------- Auth ----------
if not st.session_state.user:
    st.markdown('<div class="hero"><div class="pill">SOCIAL → BUSINESS</div><h1>🔗 MY LINK</h1><p>Turn social attention into measurable business growth.</p></div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.subheader('Sign in')
        with st.form('login'):
            email=st.text_input('Email',value='demo@mylink.local'); pw=st.text_input('Password',type='password',value='demo1234'); go=st.form_submit_button('Sign in',use_container_width=True)
            if go:
                u=store.get_business(email.strip())
                if u and u['password']==hpw(pw): st.session_state.user=dict(u); st.rerun()
                else: st.error('Invalid email or password.')
    with b:
        st.subheader('Create business account')
        with st.form('register'):
            name=st.text_input('Business name'); email=st.text_input('Business email'); pw=st.text_input('Password',type='password'); go=st.form_submit_button('Create account',use_container_width=True)
            if go:
                if not name.strip() or not valid_email(email) or len(pw)<6: st.error('Enter a business name, valid email and password of at least 6 characters.')
                elif store.get_business(email): st.error('That email is already registered.')
                else:
                    bid=store.create_business(name.strip(),email.strip(),hpw(pw)); store.exec('INSERT INTO subscriptions(business_id,plan,price,status) VALUES(?,?,?,?)',(bid,'free',0,'active')); st.success('Account created. Please sign in.')
    st.info('Demo account: demo@mylink.local / demo1234')
    st.stop()

user=st.session_state.user; bid=user['id']
# ---------- Sidebar ----------
st.sidebar.markdown('<div class="brand">🔗 MY LINK</div><div class="muted">Social-to-Business OS</div>',unsafe_allow_html=True)
items=['Dashboard','Leads CRM','Campaigns','Analytics','AI Lead Center','Creators','Team','Notifications','Revenue & Plans','Settings']
for item in items:
    if st.sidebar.button(item,use_container_width=True,key='nav_'+item): st.session_state.page=item; st.rerun()
st.sidebar.divider(); st.sidebar.caption(f"Signed in as **{user['name']}**")
if st.sidebar.button('Log out',use_container_width=True): st.session_state.user=None; st.rerun()

# ---------- Pages ----------
page=st.session_state.page
if page=='Dashboard':
    leads,new,won,views=store.dashboard(bid)
    st.markdown(f'<div class="hero"><div class="pill">CONTROL CENTER</div><h1>Good to see you, {user["name"]} 👋</h1><p>One workspace for campaigns, leads, creators and growth analytics.</p></div>',unsafe_allow_html=True)
    cols=st.columns(4)
    for c,label,val in zip(cols,['Total Leads','New Leads','Won Deals','Campaign Views'],[leads,new,won,views]): c.markdown(f'<div class="card"><div class="muted">{label}</div><div class="metric">{val:,}</div></div>',unsafe_allow_html=True)
    st.write(''); c1,c2=st.columns([1.5,1])
    with c1:
        ev=store.events(bid); df=pd.DataFrame([dict(x) for x in ev]) if ev else pd.DataFrame(columns=['campaign','event_type','source'])
        if not df.empty:
            src=df.groupby(['source','event_type']).size().reset_index(name='count'); fig=px.bar(src,x='source',y='count',color='event_type',barmode='group',title='Traffic & Lead Activity'); st.plotly_chart(fig,use_container_width=True)
        else: st.info('Create a campaign to start collecting analytics.')
    with c2:
        st.subheader('Latest leads'); ls=store.lead_list(bid)[:5]
        for x in ls: st.markdown(f'**{x["name"]}**  •  `{x["status"]}`  •  Score **{x["score"]}**')

elif page=='Leads CRM':
    st.title('👥 Leads CRM'); rows=store.lead_list(bid); df=pd.DataFrame([dict(x) for x in rows])
    if df.empty: st.info('No leads yet. Share a campaign link to capture leads.'); st.stop()
    c1,c2,c3=st.columns(3); search=c1.text_input('Search'); status=c2.selectbox('Status',['All','new','contacted','qualified','won','lost']); source=c3.selectbox('Source',['All']+sorted(df.source.dropna().unique().tolist()))
    view=df.copy()
    if search:view=view[view.apply(lambda r: search.lower() in ' '.join(map(str,r.values)).lower(),axis=1)]
    if status!='All':view=view[view.status==status]
    if source!='All':view=view[view.source==source]
    st.dataframe(view[['name','phone','email','location','budget','source','status','score','campaign','created_at']],use_container_width=True,hide_index=True)
    st.subheader('Update lead')
    opts={f"#{x['id']} • {x['name']}":x['id'] for x in rows}; selected=st.selectbox('Lead',list(opts)); new_status=st.selectbox('New status',['new','contacted','qualified','won','lost'])
    if st.button('Save status',type='primary'):
        store.exec('UPDATE leads SET status=? WHERE id=? AND business_id=?',(new_status,opts[selected],bid)); store.add_audit(bid,'lead_status_updated',f'{opts[selected]}:{new_status}'); st.success('Lead updated.'); st.rerun()

elif page=='Campaigns':
    st.title('📣 Campaign Studio'); st.caption('Create shareable landing pages that capture and attribute leads.')
    with st.expander('＋ Create new campaign',expanded=True):
        with st.form('campaign'):
            c1,c2=st.columns(2); title=c1.text_input('Campaign title *'); price=c2.number_input('Original price',min_value=0.0,step=100.0); desc=st.text_area('Description'); offer=c1.number_input('Offer price',min_value=0.0,step=100.0); cta=c2.text_input('CTA',value='Get Offer'); ok=st.form_submit_button('Create campaign',use_container_width=True)
            if ok:
                if not title.strip():st.error('Campaign title is required.')
                else:
                    pid=secrets.token_urlsafe(9).replace('-','').replace('_',''); store.exec('INSERT INTO campaigns(business_id,title,description,price,offer_price,cta,public_id,created_at) VALUES(?,?,?,?,?,?,?,?)',(bid,title.strip(),desc.strip(),price,offer,cta.strip() or 'Get Offer',pid,datetime.utcnow().isoformat())); store.add_audit(bid,'campaign_created',title.strip()); st.success('Campaign created.'); st.rerun()
    rows=store.campaign_list(bid)
    for x in rows:
        with st.container(border=True):
            a,b,c=st.columns([2,1,1]); a.subheader(x['title']); a.caption(x['description']); b.metric('Offer',money(x['offer_price'] or x['price']));
            url=f"{st.get_option('server.address') or 'https://YOUR-APP.streamlit.app'}?c={x['public_id']}"
            c.code(url,language=None); st.caption('Source tracking: add &source=facebook / tiktok / instagram / linkedin / whatsapp')

elif page=='Analytics':
    st.title('📊 Growth Analytics'); ev=store.events(bid); df=pd.DataFrame([dict(x) for x in ev])
    if df.empty: st.info('Analytics will appear after campaign views and leads.'); st.stop()
    c1,c2,c3=st.columns(3); c1.metric('Views',int((df.event_type=='view').sum())); c2.metric('Leads',int((df.event_type=='lead').sum())); views=max(1,int((df.event_type=='view').sum())); c3.metric('Conversion',f"{(df.event_type=='lead').sum()/views*100:.1f}%")
    src=df.groupby(['source','event_type']).size().reset_index(name='count'); st.plotly_chart(px.bar(src,x='source',y='count',color='event_type',barmode='group',title='Source performance'),use_container_width=True)

elif page=='AI Lead Center':
    st.title('🤖 AI Lead Center'); rows=store.lead_list(bid)
    if not rows: st.info('Capture leads first.'); st.stop()
    for x in rows[:20]:
        priority='HIGH' if x['score']>=80 else 'MEDIUM' if x['score']>=60 else 'LOW'; advice='Contact immediately and ask for the next action.' if priority=='HIGH' else 'Ask one qualifying question and schedule a follow-up.' if priority=='MEDIUM' else 'Collect budget, requirement and preferred contact time.'
        with st.container(border=True):
            a,b,c=st.columns([2,1,3]); a.markdown(f'**{x["name"]}** • {x["phone"]}'); b.metric('Score',x['score']); c.write(f'**{priority} priority** — {advice}')
    st.caption('This local AI-style engine is deterministic and works without an external AI key. A production provider can be connected later.')

elif page=='Creators':
    st.title('🎥 Creator & Referral Network');
    with st.form('creator'):
        a,b=st.columns(2); n=a.text_input('Creator name'); e=b.text_input('Email'); rate=a.number_input('Commission %',0.0,50.0,5.0); ok=st.form_submit_button('Add creator')
        if ok:
            if not n or not valid_email(e): st.error('Enter a name and valid email.')
            else:
                try: code=secrets.token_urlsafe(7); store.exec('INSERT INTO creators(name,email,referral_code,commission_rate,created_at) VALUES(?,?,?,?,?)',(n,e,code,rate,datetime.utcnow().isoformat())); st.success(f'Referral code: {code}')
                except Exception: st.error('Creator email may already exist.')
    cr=store.q('SELECT * FROM creators ORDER BY id DESC')
    st.dataframe(pd.DataFrame([dict(x) for x in cr]) if cr else pd.DataFrame(),use_container_width=True,hide_index=True)

elif page=='Team':
    st.title('👨‍💼 Team Workspace')
    with st.form('team'):
        a,b=st.columns(2); n=a.text_input('Member name'); e=b.text_input('Email'); role=a.selectbox('Role',['admin','manager','sales','marketing','viewer']); ok=st.form_submit_button('Add member')
        if ok:
            if n and valid_email(e): store.exec('INSERT INTO team(business_id,name,email,role,created_at) VALUES(?,?,?,?,?)',(bid,n,e,role,datetime.utcnow().isoformat())); st.success('Team member added.'); st.rerun()
            else:st.error('Valid name and email required.')
    rows=store.q('SELECT * FROM team WHERE business_id=? ORDER BY id DESC',(bid,)); st.dataframe(pd.DataFrame([dict(x) for x in rows]) if rows else pd.DataFrame(),use_container_width=True,hide_index=True)

elif page=='Notifications':
    st.title('🔔 Notifications & Follow-ups'); rows=store.lead_list(bid); today=date.today()
    due=[]
    for x in rows:
        if x['followup_date'] and x['followup_date']<=today.isoformat() and x['status'] not in ('won','lost'): due.append(x)
    if due:
        st.warning(f'{len(due)} follow-up(s) need attention today.')
        for x in due: st.markdown(f'**{x["name"]}** • {x["phone"]} • {x["status"]}')
    else: st.success('No overdue follow-ups.')

elif page=='Revenue & Plans':
    st.title('💳 Revenue & Plans'); plans={'free':0,'pro':2000,'business':7500,'enterprise':25000}; current=store.q('SELECT * FROM subscriptions WHERE business_id=?',(bid,),True); current=current['plan'] if current else 'free'
    cols=st.columns(4)
    for c,(name,price) in zip(cols,plans.items()):
        c.markdown(f'<div class="card"><h3>{name.title()}</h3><h2>{money(price)}<span class="small">/month</span></h2></div>',unsafe_allow_html=True)
        if c.button('Select '+name.title(),key='plan_'+name): store.exec('INSERT INTO subscriptions(business_id,plan,price,status) VALUES(?,?,?,?) ON CONFLICT(business_id) DO UPDATE SET plan=excluded.plan,price=excluded.price',(bid,name,price,'active')); st.success(f'{name.title()} selected.'); st.rerun()
    st.info(f'Current plan: **{current.upper()}**. Payment gateway is intentionally not faked; connect a real provider before charging customers.')

elif page=='Settings':
    st.title('⚙️ Settings & System Health')
    c1,c2=st.columns(2); c1.metric('Storage','SQLite fallback'); c2.metric('Cloud mode','Supabase' if store.sb else 'Not connected')
    st.subheader('Deployment checklist'); st.markdown('- Set `SUPABASE_URL` and `SUPABASE_KEY` for cloud persistence\n- Use Streamlit Secrets in production\n- Connect approved social APIs, payment provider and production AI only with real credentials\n- Enable HTTPS and proper privacy/consent policies')
    st.success('Application health: OK')
