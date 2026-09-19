# 項目別データ（data/topics/）を作り直すスクリプト
# 使い方：リポジトリの一番上で  python3 tools/build_topics.py
# 項目の追加・キーワードの修正は tools/taxonomy.json を編集してから実行する
import re, json
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE=os.path.join(ROOT,'data')+'/'
man=json.load(open(BASE+'manifest.json',encoding='utf-8'))
RUBY=re.compile(r'《[^》]*》')
RUBY2=re.compile(r'<[^<>]{1,30}>')
def parse(txt,slug,label):
    out=[]
    parts=re.split(r'^■■(.+?)■■[ \t]*$',txt,flags=re.M)
    for i in range(1,len(parts),2):
        title=parts[i].strip()
        lines=parts[i+1].split('\n')
        j=0
        while j<len(lines) and re.match(r'^[─━\s]*$',lines[j]): j+=1
        meta=[]
        while j<len(lines) and not re.match(r'^─{5,}\s*$',lines[j]):
            meta.append(lines[j]); j+=1
        body='\n'.join(lines[j+1:])
        body=re.sub(r'^[─\s]+|[─\s]+$','',body)
        src=' '.join(meta).strip()
        m=re.search(r'(1[89]\d{2})(\d{2})?(\d{2})?',src)
        date=m.group(0) if m else ''
        out.append(dict(slug=slug,vol=label,no=len(out),title=title,src=src,date=date,body=body,
                        flat=RUBY2.sub('',RUBY.sub('',title+'\n'+body))))
    return out
recs=[]
for v in man['volumes']:
    t=open(BASE+v['slug']+'.txt',encoding='utf-8').read()
    recs+=parse(t,v['slug'],v['label'])
print('項数',len(recs))

import pickle,re,json,collections
T=json.load(open(os.path.join(ROOT,'tools','taxonomy.json'),encoding='utf-8'))
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
subs=[(g['id'],s) for g in T for s in g['subs']]
comp={s[0]:re.compile(s[2]) for _,s in subs}
out=collections.defaultdict(list); meta=[]
for i,r in enumerate(recs):
    mt,pre=main_title(r)
    body=RUBY2.sub('',RUBY.sub('',r['body']))
    L=len(body)
    core=re.sub(r'[｢「『][^」｣』]*[」｣』]|[\(（][^)）]*[\)）]|[\s　0-9A-Za-z\-]','',mt)
    desc=len(core)>=2 or (r['slug']=='shiika' and len(core)>=1)
    summ,q=('',False) if desc else summary(r['body'])
    meta.append(dict(mt=mt if desc else '',summ=summ,q=q,L=L))
    if L==0: continue
    k=thresh(L)
    for gid,s in subs:
        sid=s[0]; rx=comp[sid]
        if gid=='shiika-kei':
            continue
        th=bool(rx.search(mt)) if desc else False
        c=len(rx.findall(body))
        if r['slug']=='shiika' and not th and c<max(2,k): continue
        if th or c>=k:
            tier=1 if (th or (c>=2 and c*1000/max(L,500)>=3)) else 2
            score=(50 if th else 0)+c*1000/max(L,400)+c*0.3
            out[sid].append((i,tier,round(score,2)))
    if r['slug']=='shiika':
        hit=False
        for s in [s for g,s in subs if g=='shiika-kei']:
            if comp[s[0]].search(r['title']): out[s[0]].append((i,1,1)); hit=True; break
        if not hit: out['p-daiei'].append((i,1,1))
out=dict(out)

import pickle,json,re,os,collections
OUT=os.path.join(ROOT,'data','topics'); os.makedirs(OUT,exist_ok=True)
RUBY=re.compile(r'《[^》]*》|<[^<>]{1,30}>')
def topsplit(p):
    out=[];d=0;cur=''
    for ch in p:
        if ch=='(':d+=1
        if ch==')':d-=1
        if ch=='|' and d==0: out.append(cur);cur=''
        else: cur+=ch
    out.append(cur);return out
def words(p):
    res=[]
    for a in topsplit(p):
        a=re.sub(r'\(\?<?[!=][^)]*\)','',a)
        def rep(m): return m.group(1).split('|')[0]
        while re.search(r'\(([^()]*)\)\??',a): a=re.sub(r'\(([^()]*)\)\??',rep,a,count=1)
        a=a.replace('?','')
        if a and a not in res: res.append(a)
    return res
def snippet(body,rx):
    f=RUBY.sub('',body).replace('\n','　')
    f=re.sub(r'　{2,}','　',f)
    pos=[m.start() for m in rx.finditer(f)] if rx else []
    if not pos: return f[:100]+('…' if len(f)>100 else '')
    best=pos[0];bc=0
    for p in pos:
        c=sum(1 for q in pos if p<=q<p+90)
        if c>bc: bc=c;best=p
    a=max(0,best-24); b=min(len(f),a+88)
    return ('…' if a else '')+f[a:b].strip('　')+('…' if b<len(f) else '')
subs=[s for g in T for s in g['subs']]
sidx={s[0]:i for i,s in enumerate(subs)}
rev=collections.defaultdict(list); ridx={}
index={'groups':[]}
vgroup=lambda slug:'kowa' if slug.startswith('kowa') else 'chojutsu' if slug.startswith('cho') else 'shiika'
total=0
for g in T:
    G={'id':g['id'],'name':g['name'],'desc':g['desc'],'subs':[]}; GROWS={}
    for s in g['subs']:
        sid,name,pat,desc=s
        rx=re.compile(pat) if pat else None
        items=sorted(out.get(sid,[]),key=lambda x:(x[1],-x[2]))
        rows=[]
        cnt=collections.Counter()
        for i,tier,score in items:
            r=recs[i]
            if i not in ridx: ridx[i]=len(ridx)
            rows.append([ridx[i],tier,round(score,1),snippet(r['body'],rx)])
            cnt[vgroup(r['slug'])]+=1
            rev[i].append(sidx[sid]*2+tier-1)
        GROWS[sid]=rows
        total+=len(rows)
        G['subs'].append({'id':sid,'name':name,'desc':desc,'pat':pat,'words':words(pat) if pat else [],
                          'n':len(rows),'n1':sum(1 for x in items if x[1]==1),'by':dict(cnt)})
    index['groups'].append(G)
    json.dump(GROWS,open(f"{OUT}/g-{g['id']}.json",'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
index['subs']=[s[0] for s in subs]
json.dump(index,open(f'{OUT}/index.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
R=[None]*len(ridx)
for i,k in ridx.items():
    r=recs[i]; m=meta[i]
    title=m['mt'] or m['summ'] or r['title']
    kind='t' if m['mt'] else ('q' if m['q'] else 'x')
    R[k]=[r['slug'],r['no'],r['date'],title,kind,r['title'],r['src'],rev[i]]
json.dump(R,open(f'{OUT}/recs.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
print(total)
