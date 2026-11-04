# 每周内容配音 Weekly audio
# 读取 content.json，给还没有录音的「每周一帖」和「练习视频」的词语、句子生成女声（晓晓）和男声（云希），
# 放进 audio 文件夹，并把对照表写回 content.json。
# 用法（在 Mac「终端」里）：
#   cd ~/网络语音/网站上传 && python3 gen_weekly.py
# 然后把 content.json 和 audio 文件夹一起上传到 GitHub。
import asyncio, json, os, re, hashlib, sys
try:
    import edge_tts
except ImportError:
    sys.exit("edge-tts 没装。先运行： python3 -m pip install --user edge-tts")
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "content.json")
c = json.load(open(P, encoding="utf-8"))
covered = set(json.load(open(os.path.join(HERE, "covered.json"), encoding="utf-8")))
want = []
for w in c.get("weekly", []):
    for x in w.get("words", []):
        want.append(x[0])
    t = re.sub(r"\[[^\]]*\]", "", w.get("text", "")).strip()
    if t:
        want.append(t)
for v in c.get("videos", []):
    for x in v.get("words", []):
        want.append(x[0])
        if len(x) > 3 and x[3]:
            want.append(x[3])
    for L in v.get("lines", []):
        want.append(L.get("zh", ""))
    for p in v.get("patterns", []):
        if p.get("ex"):
            want.append(p["ex"])
want = [t for i, t in enumerate(want) if t and t not in covered and t not in want[:i]]
aud = c.setdefault("audio", {"f": {}, "m": {}})
VOICES = {"f": "zh-CN-XiaoxiaoNeural", "m": "zh-CN-YunxiNeural"}
os.makedirs(os.path.join(HERE, "audio"), exist_ok=True)

async def one(v, text, sem):
    rel = "audio/%s_%s.mp3" % (v, hashlib.md5(text.encode("utf-8")).hexdigest()[:10])
    path = os.path.join(HERE, rel)
    if not (os.path.exists(path) and os.path.getsize(path) > 500):
        async with sem:
            for attempt in range(4):
                try:
                    await edge_tts.Communicate(text, VOICES[v], rate=("-15%" if len(text) <= 4 else "-5%")).save(path)
                    if os.path.getsize(path) > 500:
                        break
                except Exception:
                    await asyncio.sleep(2 + attempt * 3)
            else:
                print("没成功 FAILED:", v, text)
                return
    aud.setdefault(v, {})[text] = rel

async def main():
    sem = asyncio.Semaphore(4)
    await asyncio.gather(*[one(v, t, sem) for v in VOICES for t in want])

asyncio.run(main())
json.dump(c, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n好了！新配了 %d 条（女声 + 男声）。把 content.json 和 audio 文件夹一起上传到 GitHub。" % len(want))
for t in want:
    print("  ·", t)
