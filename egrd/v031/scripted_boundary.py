"""SCRIPTED_ONLY standard OpenAI HTTP fixture for the real ADK model boundary."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import threading


class ScriptedBoundary:
    def __init__(self,actions):self.actions=iter(actions);self.calls=[];self.cleaned=False

    def start(self):
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                assert self.path=='/v1/chat/completions'
                request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.calls.append(request);action=next(owner.actions,'End scripted engineering fixture.')
                if isinstance(action,tuple):
                    name,args=action
                    message=dict(role='assistant',content=None,tool_calls=[dict(id='scripted_'+str(len(owner.calls)),
                        type='function',function=dict(name=name,arguments=json.dumps(args)))])
                    reason='tool_calls'
                else:message=dict(role='assistant',content=action);reason='stop'
                reply=dict(id='SCRIPTED_ONLY_'+str(len(owner.calls)),object='chat.completion',created=1,
                    model=request['model'],choices=[dict(index=0,message=message,finish_reason=reason)],
                    usage=dict(prompt_tokens=100,completion_tokens=8,total_tokens=108))
                raw=json.dumps(reply).encode();self.send_response(200)
                self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
                self.end_headers();self.wfile.write(raw)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base_url=f'http://127.0.0.1:{self.server.server_port}/v1'
        return self

    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=5)
        self.cleaned=not self.thread.is_alive()
