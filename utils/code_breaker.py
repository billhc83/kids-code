from typing import Union

def serial_monitor(answer: str, cipher_lines: list, message: Union[str, list] = 'C O D E  B R E A K E R', height: int = 480):
    """
    Render an interactive Arduino serial monitor simulation.

    Parameters
    ----------
    answer : str
        The secret word (uppercase, exactly 5 letters).
        e.g. 'SPARK'

    cipher_lines : list of str
        The cipher rows to display on startup.
        e.g. ['X K Q S P A R K M Z', 'B R T F L A M E Q X', ...]

    message : str or list of str
        Header message printed between the divider lines.
        A string prints as a single line.
        A list prints each item as its own line.
        e.g. 'C O D E  B R E A K E R'
        e.g. ['Good job agent', 'Your mission today...', 'Find the word.']

    height : int
        Height of the component in pixels. Default 480.
    """

    message_lines = [message] if isinstance(message, str) else message
    message_js = ''.join(
    "print('  " + str(line).replace("'", "\\'") + "  ','system');"
    for line in message_lines
    )

    win_js = ''.join(
        "print('  " + str(line).replace("'", "\\'") + "  ','win');"
        for line in message_lines
    )


    answer = answer.strip().upper()

    # Build JS array of cipher lines
    cipher_js = '[' + ','.join(
        '"' + line.replace('\\', '\\\\').replace('"', '\\"') + '"'
        for line in cipher_lines
    ) + ']'

    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "body{background:#ffffff;display:flex;justify-content:center;padding:12px;font-family:monospace;}"
        ".monitor{background:#1a1a1a;border-radius:10px;overflow:hidden;width:100%;max-width:560px;"
        "  border:0.5px solid #444;}"
        ".bar{background:#2d2d2d;padding:8px 14px;display:flex;align-items:center;gap:8px;"
        "  border-bottom:0.5px solid #444;}"
        ".dot{width:10px;height:10px;border-radius:50%;}"
        ".bar-label{font-size:12px;color:#888;flex:1;text-align:center;}"
        ".output{padding:12px 14px;min-height:200px;max-height:300px;overflow-y:auto;"
        "  font-size:13px;line-height:1.7;}"
        ".line{color:#d4d4d4;white-space:pre;}"
        ".line.sent{color:#7ec8e3;}"
        ".line.result{color:#b5cea8;font-weight:500;}"
        ".line.win{color:#4ec994;font-weight:500;}"
        ".line.fail{color:#f48771;}"
        ".line.system{color:#888;}"
        ".viz{padding:0 14px 8px;display:none;}"
        ".viz-label{font-size:11px;color:#666;margin-bottom:4px;}"
        ".viz-row{display:flex;gap:6px;}"
        ".box{width:32px;height:32px;border-radius:4px;display:flex;align-items:center;"
        "  justify-content:center;font-size:14px;font-weight:500;color:#fff;}"
        ".hit{background:#3a7050;}.miss{background:#555;}.empty{background:#333;color:#666;}"
        ".input-row{display:flex;border-top:0.5px solid #444;}"
        ".guess{flex:1;background:#111;border:none;outline:none;color:#d4d4d4;"
        "  font-family:monospace;font-size:13px;padding:10px 14px;"
        "  text-transform:uppercase;letter-spacing:2px;}"
        ".guess::placeholder{color:#555;letter-spacing:0;text-transform:none;}"
        ".sendbtn{background:#2d5a3d;border:none;color:#4ec994;font-family:monospace;"
        "  font-size:12px;padding:10px 16px;cursor:pointer;}"
        ".sendbtn:hover{background:#3a7050;}"
        ".sendbtn:disabled{opacity:0.4;cursor:default;}"
        ".baud{font-size:11px;color:#555;padding:5px 14px;border-top:0.5px solid #2d2d2d;}"
        "</style></head><body>"
        "<div class='monitor'>"
        "  <div class='bar'>"
        "    <div class='dot' style='background:#e05252'></div>"
        "    <div class='dot' style='background:#e0a952'></div>"
        "    <div class='dot' style='background:#52b052'></div>"
        "    <div class='bar-label'>Serial Monitor &mdash; 9600 baud</div>"
        "  </div>"
        "  <div class='output' id='out'></div>"
        "  <div class='viz' id='viz'>"
        "    <div class='viz-label'>letter check:</div>"
        "    <div class='viz-row' id='boxes'></div>"
        "  </div>"
        "  <div class='input-row'>"
        "    <input class='guess' id='inp' maxlength='5' placeholder='type your 5-letter guess...' autocomplete='off' spellcheck='false'/>"
        "    <button class='sendbtn' id='btn'>SEND</button>"
        "  </div>"
        "  <div class='baud'>9600 baud &nbsp;|&nbsp; NL &amp; CR &nbsp;|&nbsp; autoscroll on</div>"
        "</div>"
        "<script>"
        "var ANSWER='" + answer + "';"
        "var CIPHER=" + cipher_js + ";"
        "var solved=false;"
        "var out=document.getElementById('out');"
        "var inp=document.getElementById('inp');"
        "var btn=document.getElementById('btn');"
        "var viz=document.getElementById('viz');"
        "var boxes=document.getElementById('boxes');"
        "function print(text,cls){"
        "  var d=document.createElement('div');"
        "  d.className='line'+(cls?' '+cls:'');"
        "  d.textContent=text;"
        "  out.appendChild(d);"
        "  out.scrollTop=out.scrollHeight;}"
        "function showViz(guess){"
        "  boxes.innerHTML='';"
        "  for(var i=0;i<5;i++){"
        "    var b=document.createElement('div');"
        "    b.className='box';"
        "    if(i<guess.length){"
        "      b.textContent=guess[i];"
        "      b.classList.add(guess[i]===ANSWER[i]?'hit':'miss');"
        "    }else{b.textContent='?';b.classList.add('empty');}"
        "    boxes.appendChild(b);}"
        "  viz.style.display='block';}"
        "function check(raw){"
        "  var guess=raw.trim().toUpperCase();"
        "  print('> '+guess,'sent');"
        "  if(guess.length!==5){print('Please enter exactly 5 letters.','fail');return;}"
        "  var likeness=0;"
        "  for(var i=0;i<5;i++){if(guess[i]===ANSWER[i])likeness++;}"
        "  showViz(guess);"
        "  print('Likeness = '+likeness,'result');"
        "  if(likeness===5){"
        "    print('=============================','win');"
        + win_js +
        "    print('=============================','win');"
        "    solved=true;inp.disabled=true;btn.disabled=true;"
        "  }else{print('Try again:','fail');}}"
        "btn.addEventListener('click',function(){"
        "  if(!solved&&inp.value.trim()){check(inp.value);inp.value='';inp.focus();}});"
        "inp.addEventListener('keydown',function(e){"
        "  if(e.key==='Enter'&&!solved&&inp.value.trim()){check(inp.value);inp.value='';}});"
        "inp.addEventListener('input',function(){"
        "  inp.value=inp.value.replace(/[^a-zA-Z]/g,'');});"
        "print('================================','system');"
        "print('     C O D E  B R E A K E R    ','system');"
        "print('================================','system');"
        "print('Find the hidden 5-letter word.','system');"
        "print('','system');"
        "CIPHER.forEach(function(line){print(line);});"
        "print('','system');"
        "print('Enter your guess:','system');"
        "</script></body></html>"
    )

    return html