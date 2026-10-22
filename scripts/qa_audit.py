"""QA-аудит кадров через Playwright (headless) с ожиданием завершения анимации.

Запуск: python scripts/qa_audit.py <pres_id> <start_idx> <end_idx> [desktop|mobile]
        python scripts/qa_audit.py <pres_id> <idx,idx,...> [desktop|mobile]   # явный список
Скриншоты: /app/uploads/qa_full/<idx>-<slug>.png  (хост: uploads/qa_full/)
           mobile → /app/uploads/qa_mobile/<idx>-<slug>.png

Режим mobile (портрет): канвас слайда — лист 450×800, контент обязан
умещаться БЕЗ скролла и клиппинга. Флаг = внутренний overflow:auto/scroll
с переполнением или hidden-клиппинг.
"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "http://frontend:5173"
OUT = "/app/uploads/qa_full"
SETTLE_JS = """
() => {
  const all=[...document.querySelectorAll('.slide')].find(s=>s.offsetParent!==null);
  if(!all) return -1;
  const root=all.children[1] && all.children[1].firstElementChild;
  if(!root) return -1;
  let moving=0;
  const walk=(el)=>{
    const cs=getComputedStyle(el);
    if(cs.display!=='none'){
      const op=parseFloat(cs.opacity||'1');
      if(op>0.02 && op<0.98) moving++;
    }
    for(const c of el.children) walk(c);
  };
  walk(root);
  return moving;
}
"""
AUDIT_JS = """
() => {
  const vw=innerWidth, vh=innerHeight;
  const slide=[...document.querySelectorAll('.slide')].find(s=>s.offsetParent!==null);
  if(!slide) return {err:'no slide'};
  const kids=[...slide.children];
  const headerBottom = kids.length>1 && kids[0] ? kids[0].getBoundingClientRect().bottom : 0;
  // Контент — всегда ПОСЛЕДНИЙ ребёнок .slide: в col-layout это kids[1],
  // в row-layout kids[2] (между ними VerticalDivider). kids[1] в row = 4px-полоска.
  const contentEl = kids.length>1 ? kids[kids.length-1] : kids[0];
  const root=contentEl?contentEl.firstElementChild:null;
  if(!root) return {err:'no root'};
  const rr=root.getBoundingClientRect();
  let maxX=-1e9, minX=1e9, minY=1e9, maxY=-1e9, textLen=0, clip=0, invisible=0;
  const walk=(el)=>{
    const cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden') return;
    const pe=cs.pointerEvents;
    const r=el.getBoundingClientRect();
    if(pe!=='none' && r.width>0&&r.height>0){
      maxX=Math.max(maxX,r.right); minX=Math.min(minX,r.left);
      minY=Math.min(minY,r.top); maxY=Math.max(maxY,r.bottom);
    }
    const txt=(el.childElementCount===0 && el.textContent)?el.textContent.trim():'';
    if(txt){
      textLen+=txt.length;
      const op=parseFloat(cs.opacity||'1');
      if(op<0.15) invisible+=txt.length;
      if(cs.textOverflow!=='ellipsis'){
        if(el.scrollHeight>el.clientHeight+2 && /hidden/.test(cs.overflowY)) clip++;
        if(el.scrollWidth>el.clientWidth+2 && /hidden/.test(cs.overflowX)) clip++;
      }
    }
    for(const c of el.children) walk(c);
  };
  walk(root);
  const cw=Math.max(0,maxX-minX), ch=Math.max(0,maxY-minY);
  const fill=(rr.width*rr.height)>0 ? Math.round((cw*ch)/(rr.width*rr.height)*100) : 0;
  return {
    root:[Math.round(rr.left),Math.round(rr.top),Math.round(rr.right),Math.round(rr.bottom)],
    rootOff: rr.left<-2||rr.top<-2||rr.right>vw+2||rr.bottom>vh+2,
    overlapHeader: minY < headerBottom-2,
    hOver: maxX>vw+2, vOver: maxY>vh+2,
    fill, textLen, clip, invisible
  };
}
"""


MOBILE_AUDIT_JS = """
() => {
  const slide=[...document.querySelectorAll('.slide')].find(s=>s.offsetParent!==null);
  if(!slide) return {err:'no slide'};
  const kids=[...slide.children];
  // Контент — всегда ПОСЛЕДНИЙ ребёнок .slide (см. AUDIT_JS).
  const contentEl = kids.length>1 ? kids[kids.length-1] : kids[0];
  const root=contentEl?contentEl.firstElementChild:null;
  if(!root) return {err:'no root'};
  let textLen=0, clip=0, invisible=0, scrollReq=0;
  const scrollEls=[];
  const rr=root.getBoundingClientRect();
  let maxBottom=-1e9, maxRight=-1e9;
  const walk=(el)=>{
    const cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden') return;
    if(cs.pointerEvents!=='none'){
      const r=el.getBoundingClientRect();
      if(r.width>0&&r.height>0){ maxBottom=Math.max(maxBottom,r.bottom); maxRight=Math.max(maxRight,r.right); }
    }
    const oy=cs.overflowY, ox=cs.overflowX;
    const scrollY=(oy==='auto'||oy==='scroll') && el.scrollHeight>el.clientHeight+2;
    const scrollX=(ox==='auto'||ox==='scroll') && el.scrollWidth>el.clientWidth+2;
    if(scrollY||scrollX){
      scrollReq++;
      if(scrollEls.length<4) scrollEls.push({
        cls:((el.className&&String(el.className).slice(0,55))||el.tagName),
        dy: scrollY? el.scrollHeight-el.clientHeight:0,
        dx: scrollX? el.scrollWidth-el.clientWidth:0,
      });
    }
    const txt=(el.childElementCount===0 && el.textContent)?el.textContent.trim():'';
    if(txt){
      textLen+=txt.length;
      const op=parseFloat(cs.opacity||'1');
      if(op<0.15) invisible+=txt.length;
      if(cs.textOverflow!=='ellipsis' && !(cs.webkitLineClamp && cs.webkitLineClamp!=='none')){
        if(el.scrollHeight>el.clientHeight+2 && /hidden/.test(oy)) clip++;
        if(el.scrollWidth>el.clientWidth+2 && /hidden/.test(ox)) clip++;
      }
    }
    for(const c of el.children) walk(c);
  };
  walk(root);
  const rootScroll = root.scrollHeight>root.clientHeight+2 || root.scrollWidth>root.clientWidth+2;
  const rootDy = Math.max(0, root.scrollHeight-root.clientHeight);
  const rootDx = Math.max(0, root.scrollWidth-root.clientWidth);
  const contentDy = Math.round(maxBottom - rr.bottom);
  const contentDx = Math.round(maxRight - rr.right);
  const contentOver = contentDy > 2 || contentDx > 2;
  const pageScroll = (document.scrollingElement.scrollHeight||0) > innerHeight+2;
  return { rootScroll, rootDy, rootDx, contentOver, contentDy, contentDx, scrollReq, clip, invisible, textLen, pageScroll, scrollEls };
}
"""


def api_slides(pres_id):
    import requests
    r = requests.get(f"http://localhost:8000/presentations/{pres_id}", timeout=30)
    r.raise_for_status()
    d = r.json()
    slides = d.get("slides") or []
    return sorted(slides, key=lambda s: s.get("order_index", 0))


def main():
    pres = int(sys.argv[1])
    if "," in sys.argv[2]:
        indices = [int(x) for x in sys.argv[2].split(",") if x.strip()]
        mode = sys.argv[3] if len(sys.argv) > 3 else "desktop"
    else:
        start = int(sys.argv[2]); end = int(sys.argv[3])
        indices = list(range(start, end))
        mode = sys.argv[4] if len(sys.argv) > 4 else "desktop"
    mobile = mode == "mobile"
    out = "/app/uploads/qa_mobile" if mobile else OUT
    audit_js = MOBILE_AUDIT_JS if mobile else AUDIT_JS
    vp = {"width": 390, "height": 844} if mobile else {"width": 1920, "height": 1080}
    slides = api_slides(pres)
    rows = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu"])
        pg = b.new_page(viewport=vp)
        for i in indices:
            if i < 0 or i >= len(slides):
                continue
            s = slides[i]
            slug = s.get("component")
            base = float(s.get("start_time") or 0)
            try:
                # domcontentloaded вместо load: SPA гидрируется до готовности медиа,
                # иначе каждый кадр ждёт загрузку всех картинок/видео kitchen-sink.
                pg.goto(f"{BASE}/p/{pres}?slide={i}", wait_until="domcontentloaded", timeout=90000)
                pg.wait_for_function("() => !!window.useDirectorInstance", timeout=90000)
                target = base + 6000
                pg.evaluate("(t) => { const d=window.useDirectorInstance; d.pause(); d.seek(t); }", target)
                # settle
                still = 0
                for _ in range(12):
                    pg.wait_for_timeout(200)
                    moving = pg.evaluate(SETTLE_JS)
                    if moving == 0:
                        still += 1
                        if still >= 2:
                            break
                    else:
                        still = 0
                # re-assert exact time right before capture (clock may keep running)
                pg.evaluate("(t) => { const d=window.useDirectorInstance; d.pause(); d.seek(t); }", target)
                pg.wait_for_timeout(200)
                pg.screenshot(path=f"{out}/{i:03d}-{slug}.png")
                a = pg.evaluate(audit_js)
            except Exception as e:
                a = {"err": str(e)[:120]}
            a["i"] = i; a["slug"] = slug
            rows.append(a)
            print(json.dumps(a, ensure_ascii=False), flush=True)
        b.close()
    if mobile:
        bad = [r for r in rows if r.get("err") or r.get("contentOver") or r.get("scrollReq") or r.get("clip") or (r.get("textLen", 0) < 12)]
    else:
        bad = [r for r in rows if r.get("err") or r.get("rootOff") or r.get("overlapHeader") or r.get("hOver") or r.get("vOver") or (r.get("textLen", 0) < 12)]
    print("\n=== SUMMARY ===")
    print(f"checked={len(rows)} flagged={len(bad)}")
    for r in bad:
        print(json.dumps(r, ensure_ascii=False))
    # Заполнение кадра <40% (грубая эвристика «пустоты», contract §1). Не влияет
    # на flagged — контент может быть осознанно центрирован, но полезно для ревью.
    if not mobile:
        sparse = [r for r in rows if not r.get("err") and r.get("fill", 100) < 40]
        sparse.sort(key=lambda r: r.get("fill", 100))
        print(f"\n=== SPARSE (fill<40%) — {len(sparse)} ===")
        for r in sparse:
            print(f"  {r.get('i')} {r.get('slug')} fill={r.get('fill')}%")


if __name__ == "__main__":
    main()
