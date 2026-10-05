import base64,io,av,httpx
with httpx.Client(base_url='http://127.0.0.1:8765',trust_env=False,timeout=60) as client:
    r=client.post('/tts',json={'text':'Synthetic pump check for local audio validation.','language':'en'})
    r.raise_for_status()
    raw=base64.b64decode(r.json()['audio_base64'])
    for fmt,codec,mime in [('webm','libopus','audio/webm'),('ogg','libopus','audio/ogg'),('mp4','aac','audio/mp4'),('wav','pcm_s16le','audio/wav')]:
        output=io.BytesIO()
        with av.open(io.BytesIO(raw)) as source, av.open(output,'w',format=fmt) as sink:
            stream=sink.add_stream(codec,rate=48000)
            stream.layout='mono'
            for frame in source.decode(audio=0):
                for packet in stream.encode(frame): sink.mux(packet)
            for packet in stream.encode(None): sink.mux(packet)
        r=client.post('/stt',json={'audio_base64':base64.b64encode(output.getvalue()).decode(),'mime_type':mime,'language':'en'})
        r.raise_for_status()
        assert r.json()['text'].strip(), mime
        print(mime, 'PASS: local decode and real Whisper returned text',flush=True)
