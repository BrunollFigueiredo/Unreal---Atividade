import unreal, pathlib, traceback, time
ROOT = pathlib.Path(r'C:\Users\Bruno\Unreal---Atividade 5.7\work\moedas')
def report(message):
    with (ROOT / 'status.log').open('a', encoding='utf-8') as f: f.write(str(message) + '\n')
    unreal.log(str(message))
def tick(delta):
    command = ROOT / 'command.py'
    if command.exists():
        source = command.read_text(encoding='utf-8-sig')
        command.rename(ROOT / ('executed_' + str(time.time_ns()) + '.py'))
        try: exec(compile(source, str(command), 'exec'), globals())
        except Exception: report(traceback.format_exc())
TICK_HANDLE = unreal.register_slate_post_tick_callback(tick)
report('WATCHER_READY')
