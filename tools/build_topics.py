# 項目別データ（data/topics/）を作り直すスクリプト
# 使い方：リポジトリの一番上で  python3 tools/build_topics.py
# 項目の追加・キーワードの修正は tools/taxonomy.json を編集してから実行する
#   pat : 本文・見出しで数えることば（正規表現、| 区切り）。「A&&B」と書くと、Aを数え、Bも本文に出てくる項だけに絞る
#   leaves : 通信カレッジ目次の細目名。全集の見出しと一致した項は「目次対応」として先頭に置かれる
import os,re,json,collections
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(ROOT,'data'); OUT=os.path.join(DATA,'topics')
man=json.load(open(os.path.join(DATA,'manifest.json'),encoding='utf-8'))
TAX=json.load(open(os.path.join(ROOT,'tools','taxonomy.json'),encoding='utf-8'))
RUBY=re.compile(r'《[^》]*》')

def parse(txt,slug):
    out=[]
    parts=re.split(r'^■■(.+?)■■[ \t]*$',txt,flags=re.M)
    for i in range(1,len(parts),2):
        lines=parts[i+1].split('\n'); j=0
        while j<len(lines) and re.match(r'^[─━\s]*$',lines[j]): j+=1
        meta=[]
        while j<len(lines) and not re.match(r'^─{5,}\s*$',lines[j]): meta.append(lines[j]); j+=1
        body=re.sub(r'^[─\s]+|[─\s]+$','','\n'.join(lines[j+1:]))
        src=' '.join(meta).strip()
        m=re.search(r'(1[89]\d{2})(\d{2})?(\d{2})?',src)
        out.append(dict(slug=slug,no=len(out),title=parts[i].strip(),src=src,date=m.group(0) if m else '',body=body))
    return out
recs=[]
for v in man['volumes']:
    recs+=parse(open(os.path.join(DATA,v['slug']+'.txt'),encoding='utf-8').read(),v['slug'])
print('項数',len(recs))
RUBY2=re.compile(r'<[^<>]{1,30}>'); RUBY=re.compile(r'《[^》]*》')
BOIL=['御講話','御教え','教えの光','妙智の光','妙智之光','妙智の鍵','信仰余話','無碍光','御光話','特別御面会','午後の部','午前の部','御垂示','御誕生祭','妙智の業','の御講話','御言葉','御光話録','御面会']
def main_title(r):
    t=r['title']
    if '【' in t:
        m=t[t.index('【')+1:]; return m.replace('】','').replace('■','').strip(), t[:t.index('【')]
    if r['slug']=='shiika':
        m=re.sub(r'^\S*\d{6,8}\S*[　\s\t]+','',t); m=re.sub(r'^(栄光|地天|讃歌集)\S*[　\s]+','',m)
        return m.strip(), ''
    m=re.sub(r'▽[^▽]*▽','',t).replace('■','')
    if '●' in m: m=m[m.rindex('●')+1:]
    LEAD=[r'(光録|垂録|教集|地天|光明会報|日光会報|直心会報|光録補|光明|光|LE|[^　\s]{0,4}会報)[^　\s]*[　\s]*',
          r'(S|T|M)\d+/\d+(/\d+)?(\([日月火水木金土]\))?',
          r'(昭和|大正|明治)[一二三四五六七八九十〇元]+年[一二三四五六七八九十]+月([一二三四五六七八九十]+日)?',
          r'\d{6,8}', r'[\(（][^)）]{0,12}[\)）]', r'[｢「『](妙智の光|妙智之光|妙智の鍵|教えの光|信仰余話|無碍光|妙智の業)[」｣』]',
          r'の?(御講話|御教え|御光話|御垂示|御面会|特別御面会|午後の部|午前の部|御誕生祭御教え|御言葉|教えの光)',
          r'[\s　、,．.。・:：]+']
    ch=True
    while ch:
        ch=False
        for p in LEAD:
            n=re.sub('^'+p,'',m)
            if n!=m: m=n; ch=True
    m=re.sub(r'】+$','',m).strip(' 　★☆')
    return m, ''
def summary(body):
    b=RUBY2.sub('',RUBY.sub('',body)).strip()
    lines=[l.strip(' 　') for l in b.split('\n') if l.strip(' 　') and '岡田茂吉全集' not in l and not re.match(r'^[▽△].*[▽△]$',l.strip(' 　'))]
    if not lines: return '',False
    while len(lines)>1 and (len(lines[0])<12 or re.match(r'^[（(【〔].*[）)】〕]$',lines[0])) and not re.match(r'^(〔\s*質問者|御伺い|－－)',lines[0]): lines=lines[1:]
    l=lines[0]; q=False
    m=re.match(r'^(〔\s*(質問者|御伺い|お伺い)\s*〕|【\s*質問者\s*】|御伺い|おうかがい|お伺い|－－|――|──|問[　 ]|（問）|\(問\))\s*',l)
    if m: l=l[m.end():]; q=True
    l=re.sub(r'^【\s*明主様\s*】','',l).strip(' 　')
    parts=[p for p in re.split(r'(?<=[。？\?！])',l) if p]
    s=''
    for p in parts:
        s+=p
        if len(s)>=22: break
    if len(s)>60: s=s[:58]+'…'
    return s,q
def thresh(L):
    return 1 if L<600 else 2 if L<2000 else 3 if L<5000 else 4 if L<10000 else 5

def nz(s): return re.sub(r'[\s　、，,。・「」『』（）()\[\]【】〔〕｢｣]','',s).replace('就て','ついて').replace('就いて','ついて')
def leafbase(t):
    b=re.sub(r'（.*?）','',t); b=re.sub(r'\s*\d+\s*$','',b.strip()); return nz(b)
def snippet(body,rx):
    f=RUBY2.sub('',RUBY.sub('',body)).replace('\n','　'); f=re.sub(r'　{2,}','　',f)
    pos=[m.start() for m in rx.finditer(f)] if rx else []
    if not pos: return f[:90]+('…' if len(f)>90 else '')
    best=pos[0];bc=0
    for p in pos:
        c=sum(1 for q in pos if p<=q<p+90)
        if c>bc: bc=c;best=p
    a=max(0,best-24); b=min(len(f),a+88)
    return ('…' if a else '')+f[a:b].strip('　')+('…' if b<len(f) else '')

meta=[];bodies=[]
for r in recs:
    mt,_=main_title(r)
    core=re.sub(r'[｢「『][^」｣』]*[」｣』]|[\(（][^)）]*[\)）]|[\s　0-9A-Za-z\-]','',mt)
    desc=len(core)>=2 or (r['slug']=='shiika' and len(core)>=1)
    summ,q=('',False) if desc else summary(r['body'])
    meta.append(dict(mt=mt if desc else '',summ=summ,q=q))
    bodies.append(RUBY2.sub('',RUBY.sub('',r['body'])))
titleidx=collections.defaultdict(list)
for i,m in enumerate(meta):
    if m['mt'] and bodies[i]: titleidx[nz(m['mt'])].append(i)
def anchors(leaves):
    got=set()
    for t in leaves:
        b=leafbase(t)
        if len(b)<2: continue
        for k,ids in titleidx.items():
            if k==b or (len(b)>=5 and b in k) or (len(k)>=5 and k in b and len(k)>=len(b)*0.6):
                got.update(ids)
    return got

SHIIKA={'p-sanka':r'讃歌|御歌|祭典|大祭|御詠','p-waka':r'和歌|短歌|詠草|歌会|即詠','p-kanku':r'冠句|沓句|笑冠|狂句|川柳','p-kyoka':r'狂歌|阿呆陀羅|陀羅経|都々逸|歌謡|詩|〔無題〕|○'}
def thresh(L): return 1 if L<600 else 2 if L<2000 else 3 if L<5000 else 4 if L<10000 else 5
subs=[]; 
for h in TAX:
    for c in h['chaps']:
        for s in c['subs']: subs.append((h,c,s))
sidx={s['id']:i for i,(_,_,s) in enumerate(subs)}
res={}
shiika_form={}
for i,r in enumerate(recs):
    if r['slug']!='shiika' or not bodies[i]: continue
    for k,p in SHIIKA.items():
        if re.search(p,r['title']): shiika_form[i]=k; break
    else: shiika_form[i]='p-daiei'
for h,c,s in subs:
    sid=s['id']; items={}
    if sid.startswith('p-'):
        for i,k in shiika_form.items():
            if k==sid: items[i]=(1,1.0)
        res[sid]=items; continue
    parts=s['pat'].split('&&'); A=re.compile(parts[0]); B=re.compile(parts[1]) if len(parts)>1 else None
    for i,r in enumerate(recs):
        body=bodies[i]; L=len(body)
        if not L: continue
        mt=meta[i]['mt']
        th=bool(mt and A.search(mt))
        c_=len(A.findall(body))
        if not th and not c_: continue
        if B and not (B.search(body) or (mt and B.search(mt))): continue
        k=thresh(L)
        if r['slug']=='shiika' and not th and c_<max(2,k): continue
        if th or c_>=k:
            tier=1 if (th or (c_>=2 and c_*1000/max(L,500)>=3)) else 2
            items[i]=(tier,round((50 if th else 0)+c_*1000/max(L,400)+c_*0.3,1))
    for i in anchors(s.get('leaves',[])):
        items[i]=(0,200.0)
    res[sid]=items

os.makedirs(OUT,exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith('.json'): os.remove(os.path.join(OUT,f))
ridx={}; rev=collections.defaultdict(list)
def topsplit(p):
    out=[];d=0;cur=''
    for ch in p:
        if ch=='(':d+=1
        if ch==')':d-=1
        if ch=='|' and d==0: out.append(cur);cur=''
        else: cur+=ch
    out.append(cur);return out
def words(p):
    res_=[]
    for a in topsplit(p.split('&&')[0]):
        a=re.sub(r'\(\?<?[!=][^)]*\)','',a)
        while re.search(r'\(([^()]*)\)\??',a): a=re.sub(r'\(([^()]*)\)\??',lambda m:m.group(1).split('|')[0],a,count=1)
        a=a.replace('?','').replace('^','').replace('$','')
        if a and a not in res_: res_.append(a)
    return res_
vg=lambda slug:'kowa' if slug.startswith('kowa') else 'chojutsu' if slug.startswith('cho') else 'shiika'
index={'hen':[],'subs':[s['id'] for _,_,s in subs]}
for h in TAX:
    Hn={'id':h['id'],'name':h['name'],'desc':h['desc'],'chaps':[]}
    for c in h['chaps']:
        Cn={'id':c['id'],'name':c['name'],'desc':c.get('desc',''),'subs':[]}; rowsfile={}
        for s in c['subs']:
            sid=s['id']; pat=s['pat'].split('&&')[0] if s['pat'] else ''
            rx=re.compile(pat) if pat else None
            its=sorted(res[sid].items(),key=lambda x:(x[1][0],-x[1][1]))
            rows=[];cnt=collections.Counter()
            for i,(tier,score) in its:
                if i not in ridx: ridx[i]=len(ridx)
                rows.append([ridx[i],tier,score,snippet(recs[i]['body'],rx)])
                cnt[vg(recs[i]['slug'])]+=1
                rev[i].append(sidx[sid]*3+tier)
            rowsfile[sid]=rows
            Cn['subs'].append({'id':sid,'name':s['name'],'pat':pat,'words':words(s['pat']) if s['pat'] else [],
                'leaves':s.get('leaves',[]),'ho':bool(s.get('ho')),'n':len(rows),
                'n0':sum(1 for x in its if x[1][0]==0),'n1':sum(1 for x in its if x[1][0]<=1),'by':dict(cnt)})
        json.dump(rowsfile,open(os.path.join(OUT,f"c-{c['id']}.json"),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
        Hn['chaps'].append(Cn)
    index['hen'].append(Hn)
R=[None]*len(ridx)
for i,k in ridx.items():
    r=recs[i]; m=meta[i]
    R[k]=[r['slug'],r['no'],r['date'],m['mt'] or m['summ'] or r['title'],'t' if m['mt'] else ('q' if m['q'] else 'x'),r['title'],r['src'],rev[i]]
json.dump(R,open(os.path.join(OUT,'recs.json'),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
json.dump(index,open(os.path.join(OUT,'index.json'),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
print('項目',len(subs),'振り分け',sum(len(v) for v in res.values()),'対象項',len(ridx))
