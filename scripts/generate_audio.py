from pathlib import Path
import re, subprocess, urllib.request

root=Path(__file__).resolve().parents[1]
source=(root/'briefings/testausgabe-03.md').read_text(encoding='utf-8')
voice_dir=root/'.voice-cache'
voice_dir.mkdir(exist_ok=True)
base='https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx'
model=voice_dir/'de_DE-thorsten-medium.onnx'
config=voice_dir/'de_DE-thorsten-medium.onnx.json'
for url,path in [(base,model),(base+'.json',config)]:
    if not path.exists():
        urllib.request.urlretrieve(url,path)
matches=list(re.finditer(r'^#{1,3}\s+(?:Kapitel\s*)?([1-6])[.\s:–-]+(.+)$',source,re.M|re.I))
if len(matches)<6:
    raise RuntimeError('Expected six chapter headings')
out=root/'audio'/'testausgabe-03'
out.mkdir(parents=True,exist_ok=True)
for idx,match in enumerate(matches):
    n=int(match.group(1))
    end=matches[idx+1].start() if idx+1<len(matches) else len(source)
    body=source[match.start():end]
    body=re.split(r'^##\s+(?:Kiswahili|Muhtasari)',body,flags=re.M|re.I)[0]
    body=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',body)
    body=re.sub(r'(?m)^#{1,6}\s*','',body)
    body=re.sub(r'(?m)^\s*[-*]\s+','',body)
    body=re.sub(r'[*_`|]','',body)
    body=re.sub(r'https?://\S+','',body)
    body=re.sub(r'\n{3,}','\n\n',body).strip()
    target=out/f'kapitel-{n}.wav'
    subprocess.run(['piper','--model',str(model),'--config',str(config),'--output_file',str(target)],input=body,text=True,check=True)
    mp3=out/f'kapitel-{n}.mp3'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(target),'-codec:a','libmp3lame','-b:a','64k',str(mp3)],check=True)
    target.unlink()
    print(mp3,mp3.stat().st_size)

# Combine all six chapters into one continuous weekly audio edition.
playlist=out/'chapters.txt'
playlist.write_text(''.join("file 'kapitel-{}.mp3'\n".format(n) for n in range(1,7)),encoding='utf-8')
full=out/'gesamtausgabe.mp3'
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(playlist),'-c','copy',str(full)],check=True)
playlist.unlink()
print(full,full.stat().st_size)
