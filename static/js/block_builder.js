

(function(){
var CFG = window.BB_CONFIG;
var USERNAME = CFG.username;
var PAGE = CFG.page;
var MASTER_SKETCH = CFG.master || null;
var SUPABASE_URL = CFG.supabase_url;
var SUPABASE_KEY = CFG.supabase_key;
var DEFAULT_VIEW = CFG.default_view;
var LOCK_VIEW = CFG.lock_view;
var READONLY_MODE = CFG.readonly_mode;
var LOCK_MODE = CFG.lock_mode;
var UNO_DIGITAL_PINS=['0','1','2','3','4','5','6','7','8','9','10','11','12','13'];
var UNO_ANALOG_PINS=['A0','A1','A2','A3','A4','A5'];
var UNO_DIGITAL_IO_PINS=UNO_DIGITAL_PINS.concat(UNO_ANALOG_PINS);
var UNO_PWM_PINS=['3','5','6','9','10','11'];
var BLOCKS={
intvar:{allowed:['global','loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'text',l:'Name'},{t:'expr',l:'Value',fallback:'0'}],
  defaults:[null,{type:'value',params:['0'],children:[]}],
  genStmt:function(p,ex){return 'int '+(p[0]||'myVar')+' = '+genExpr(ex&&ex[1],p[1],'0')+';';}},
longvar:{allowed:['global','loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'text',l:'Name'},{t:'expr',l:'Value',fallback:'0'}],
  defaults:[null,{type:'value',params:['0'],children:[]}],
  genStmt:function(p,ex){return 'long '+(p[0]||'myLong')+' = '+genExpr(ex&&ex[1],p[1],'0')+';';}},
boolvar:{allowed:['global','loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'text',l:'Name'},{t:'sel',l:'Value',o:['true','false']}],
  genStmt:function(p){return 'bool '+(p[0]||'myFlag')+' = '+(p[1]||'false')+';';}},
setvar:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'vartext',l:'Var'},{t:'expr',l:'Value',fallback:'0'}],
  defaults:[null,{type:'value',params:['0'],children:[]}],
  genStmt:function(p,ex){return (p[0]||'myVar')+' = '+genExpr(ex&&ex[1],p[1],'0')+';';}},
increment:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'vartext',l:'Var'},{t:'sel',l:'Op',o:['++','--','+=','-=']},
          {t:'number',l:'By'}],
  genStmt:function(p){
    var v=p[0]||'myVar',op=p[1]||'++',n=p[2]||'1';
    if(op==='++'||op==='--')return v+op+';';
    return v+' '+op+' '+n+';';}},
stringvar:{allowed:['global','loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'text',l:'Name'},{t:'expr',l:'Value',fallback:'""'}],
  defaults:[null,{type:'value',params:[''],children:[]}],
  genStmt:function(p,ex){return 'String '+(p[0]||'myText')+' = '+genExpr(ex&&ex[1],p[1],'""')+';';}},
pinmode:{allowed:['setup'],asStatement:true,asExpr:false,
  inputs:[{t:'vartext',l:'Pin',o:'DIGITAL_PIN_OPTIONS'},{t:'sel',l:'Mode',o:['OUTPUT','INPUT','INPUT_PULLUP']}],
  genStmt:function(p){return 'pinMode('+(p[0])+', '+(p[1])+');';}},
digitalwrite:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'sel',l:'Pin',o:'DIGITAL_PIN_OPTIONS'},{t:'sel',l:'Value',o:['HIGH','LOW']}],
  genStmt:function(p){return 'digitalWrite('+(p[0])+', '+(p[1])+');';}},
analogwrite:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'sel',l:'Pin',o:'PWM_PIN_OPTIONS'},{t:'expr',l:'Value',fallback:'128'}],
  genStmt:function(p,ex){return 'analogWrite('+(p[0]||9)+', '+genExpr(ex&&ex[1],p[1],'128')+');';}},
analogread:{allowed:['loop','if','for','while'],asStatement:false,asExpr:true,
  inputs:[{t:'sel',l:'Pin',o:'ANALOG_PIN_OPTIONS'}],
  genExpr:function(p){return 'analogRead('+(p[0]||'A0')+')';}},
digitalread:{allowed:['loop','if','for','while'],asStatement:false,asExpr:true,
  inputs:[{t:'sel',l:'Pin',o:'DIGITAL_PIN_OPTIONS'}],
  genExpr:function(p){return 'digitalRead('+(p[0]||'2')+')';}},
delay:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'expr',l:'ms',fallback:'1000'}],
  genStmt:function(p,ex){return 'delay('+genExpr(ex&&ex[0],p[0],'1000')+');';}},
delaymicroseconds:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'expr',l:'us',fallback:'100'}],
  defaults:[{type:'value',params:['100'],children:[]}],
  genStmt:function(p,ex){return 'delayMicroseconds('+genExpr(ex&&ex[0],p[0],'100')+');';}},
millis:{allowed:['loop','if','for','while'],asStatement:false,asExpr:true,
  inputs:[],
  genExpr:function(p){return 'millis()';}},
tone:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'sel',l:'Pin',o:'DIGITAL_PIN_OPTIONS'},{t:'expr',l:'Freq',fallback:'440'},{t:'number',l:'Duration'}],
  genStmt:function(p,ex){var pin=(p[0]||5),f=genExpr(ex&&ex[1],p[1],'440'),d=p[2];
    return (d!==''&&d!==null&&d!==undefined)?('tone('+pin+', '+f+', '+d+');'):('tone('+pin+', '+f+');');}},
notone:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'expr',l:'Pin',fallback:'0'}],
  genStmt:function(p,ex){return 'noTone('+genExpr(ex&&ex[0],p[0],'0')+');';}},
random:{allowed:['loop','if','for','while'],asStatement:false,asExpr:true,
  inputs:[{t:'number',l:'Min'},{t:'number',l:'Max'}],
  genExpr:function(p){return 'random('+(p[0]||0)+', '+(p[1]||100)+')';}},
math:{allowed:[],asStatement:false,asExpr:true,
  inputs:[{t:'expr',l:'A',fallback:'0'},{t:'sel',l:'Op',o:[{v:'+',lb:'plus'},{v:'-',lb:'minus'},{v:'*',lb:'multiply'},{v:'/',lb:'divide'},{v:'%',lb:'modulo'}]},{t:'expr',l:'B',fallback:'0'}],
  genExpr:function(p,ch){
    var a=genExpr(ch&&ch[0],p[0],'0'),op=p[1]||'+',b=genExpr(ch&&ch[2],p[2],'0');
    return '('+a+' '+op+' '+b+')';}},
map:{allowed:[],asStatement:false,asExpr:true,
  inputs:[{t:'expr',l:'Val',fallback:'0'},{t:'number',l:'inLo'},{t:'number',l:'inHi'},{t:'number',l:'outLo'},{t:'number',l:'outHi'}],
  genExpr:function(p,ch){
    var v=genExpr(ch&&ch[0],p[0],'0');
    return 'map('+v+', '+(p[1]||0)+', '+(p[2]||1023)+', '+(p[3]||0)+', '+(p[4]||255)+')';}},
constrain:{allowed:[],asStatement:false,asExpr:true,
  inputs:[{t:'expr',l:'Val',fallback:'0'},{t:'number',l:'Lo'},{t:'number',l:'Hi'}],
  genExpr:function(p,ch){
    var v=genExpr(ch&&ch[0],p[0],'0');
    return 'constrain('+v+', '+(p[1]||0)+', '+(p[2]||255)+')';}},
value:{allowed:[],asStatement:false,asExpr:true,
  inputs:[{t:'vartext',l:'Value'}],
  genExpr:function(p){return (p[0]||'0');}},
serialbegin:{allowed:['setup'],asStatement:true,asExpr:false,
  inputs:[{t:'sel',l:'Baud',o:['9600','19200','38400','57600','115200']}],
  genStmt:function(p){return 'Serial.begin('+(p[0]||'9600')+');';}},
serialprint:{allowed:['setup','loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'expr',l:'Value',fallback:'"Hello"'},{t:'sel',l:'',o:['println','print']}],
  defaults:[{type:'value',params:['"Hello"'],children:[]},null],
  genStmt:function(p,ex){var fn=p[1]==='print'?'Serial.print':'Serial.println';
    return fn+'('+genExpr(ex&&ex[0],null,'"Hello"')+');';}},
serialreadstring:{allowed:[],asStatement:false,asExpr:true,
  inputs:[],
  genExpr:function(p){return 'Serial.readString()';}},
serialavailable:{allowed:[],asStatement:false,asExpr:true,
  inputs:[],
  genExpr:function(p){return 'Serial.available()';}},
codeblock:{allowed:['global','setup','loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'text',l:'Code'}],
  genStmt:function(p){return (p[0]||'');}},
phantom_resolved:{allowed:['global','setup','loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[],genStmt:function(){return '';}},
ifblock:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[],genStmt:function(){return '';}},
forloop:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[],genStmt:function(){return '';}},
whileloop:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[],genStmt:function(){return '';}},
};
var B=BLOCKS;
var SECTIONS={global:[],setup:[],loop:[]};
var exprSel=null;
var EXPR_COLORS={'analogread':'#1a7f37','digitalread':'#1a7f37','millis':'#0969da',
  'random':'#e36209','math':'#9a6700','map':'#6f42c1','constrain':'#cf222e','value':'#57606a'};
function getExprColor(type){return EXPR_COLORS[type]||'#57606a';}
function genExpr(exNode,fallbackParam,fallbackDefault){
  if(exNode&&exNode.type){
    var def=BLOCKS[exNode.type];
    if(!def||!def.genExpr)return String(fallbackParam||fallbackDefault||'0');
    return def.genExpr(exNode.params||[],exNode.children||[]);}
  var v=fallbackParam;if(v===''||v===null||v===undefined)v=fallbackDefault||'0';
  return String(v);}
function makeExNode(type){
  var def=BLOCKS[type];if(!def||!def.asExpr)return null;
  var params=def.inputs.map(function(inp){
    if(inp.t==='sel'){var f=inp.o[0];return typeof f==='object'?f.v:f;}
    if(inp.t==='number')return '0'; if(inp.t==='expr')return '';
    if(inp.t==='vartext')return '0'; return '';});
  var children=def.inputs.map(function(inp){return inp.t==='expr'?null:undefined;});
  return {type:type,params:params,children:children};}
function renderExprSlot(block,slotIdx,label){
  if(!block.exChildren)block.exChildren=[];
  var exNode=block.exChildren[slotIdx]||null;
  var wrap=document.createElement('div');wrap.className='blk-field';
  var lbl=document.createElement('label');lbl.textContent=label;wrap.appendChild(lbl);
  var slot=document.createElement('div');
  slot.className='expr-slot'+(exNode?' has-expr':'');
  var isActive=exprSel&&exprSel.block===block&&exprSel.slotIdx===slotIdx;
  if(isActive)slot.classList.add('active');
  if(exNode){
    slot.appendChild(renderExprBlock(exNode,function(){block.exChildren[slotIdx]=null;exprSel=null;updatePalette();render();}));
  }else{
    var ph=document.createElement('span');ph.textContent=isActive?'> drop expr':'+ expr';slot.appendChild(ph);
  }
  slot.addEventListener('click',function(e){
    e.stopPropagation();
    if(exprSel&&exprSel.block===block&&exprSel.slotIdx===slotIdx){exprSel=null;updatePalette();render();return;}
    exprSel={block:block,slotIdx:slotIdx};sel=null;
    document.getElementById('statusbar').innerHTML='<span style="color:#9a6700">click an expression block to snap it in</span>';
    updatePalette();
    render();});
  wrap.appendChild(slot);return wrap;}
function renderExprBlock(exNode,onRemove){
  var def=BLOCKS[exNode.type];if(!def||!def.asExpr)return document.createTextNode('?');
  var chip=document.createElement('span');
  chip.className='expr-block-inline';
  chip.style.background=getExprColor(exNode.type);
  chip.style.color='#fff';
  var lbl=document.createElement('span');lbl.textContent=exNode.type;chip.appendChild(lbl);
  def.inputs.forEach(function(inp,ji){
    if(inp.t==='expr'){
      (function(capturedJi,capturedExNode){
        var subSlot=document.createElement('span');
        var isSubActive=exprSel&&exprSel.isSubSlot&&exprSel.exNode===capturedExNode&&exprSel.slotIdx===capturedJi;
        subSlot.style.cssText='display:inline-flex;align-items:center;border-radius:5px;padding:2px 6px;cursor:pointer;font-size:11px;min-width:34px;border:2px '+(isSubActive?'solid #fff':'dashed rgba(255,255,255,0.6)')+';background:'+(isSubActive?'rgba(255,255,255,0.35)':'rgba(255,255,255,0.15)')+';';
        var subNode=(capturedExNode.children&&capturedExNode.children[capturedJi])||null;
        if(subNode){
          subSlot.appendChild(renderExprBlock(subNode,function(){if(!capturedExNode.children)capturedExNode.children=[];capturedExNode.children[capturedJi]=null;exprSel=null;render();}));
        }else{
          var sph=document.createElement('span');sph.textContent=inp.l||'?';
          sph.style.cssText='opacity:0.85;font-weight:700;color:#fff;pointer-events:none;';subSlot.appendChild(sph);
        }
        subSlot.addEventListener('click',function(e){
          e.stopPropagation();
          if(exprSel&&exprSel.isSubSlot&&exprSel.exNode===capturedExNode&&exprSel.slotIdx===capturedJi){
            exprSel=null;updatePalette();render();return;}
          exprSel={exNode:capturedExNode,slotIdx:capturedJi,isSubSlot:true};sel=null;
          document.getElementById('statusbar').innerHTML='<span style="color:#9a6700">slot '+inp.l+' selected - click an expression to fill it</span>';
          document.querySelectorAll('.sub-slot-active').forEach(function(el){el.classList.remove('sub-slot-active');});
          subSlot.style.border='2px solid #fff';subSlot.style.background='rgba(255,255,255,0.35)';
          updatePalette();
        });
        chip.appendChild(subSlot);
      })(ji,exNode);
    }else if(inp.t==='sel'){
      var es=document.createElement('select');es.className='expr-sel';
      var opts=inp.o;if(typeof opts==='string')opts=getOptions(opts);
      if(!exNode.params[ji]){var op=document.createElement('option');op.value='';op.textContent='\u2014';es.appendChild(op);}
      opts.forEach(function(opt){var o=document.createElement('option');
        if(typeof opt==='object'){o.value=opt.v;o.textContent=opt.lb;}else{o.value=opt;o.textContent=opt;}
        es.appendChild(o);});es.value=exNode.params[ji]||'';
      es.addEventListener('click',function(e){e.stopPropagation();});
      es.addEventListener('change',function(e){e.stopPropagation();exNode.params[ji]=e.target.value;genCode();});
      chip.appendChild(es);
    }else if(inp.t==='vartext'){
      (function(capturedJiVt,capturedExNodeVt){
        var wrap=document.createElement('span');wrap.className='vartext-wrap';
        var ei=document.createElement('input');ei.type='text';ei.className='vartext-input';
        ei.value=capturedExNodeVt.params[capturedJiVt]||'0';
        ei.placeholder='0';
        var drop=null;
        function closeDrop(){if(drop){drop.remove();drop=null;}}
        function openDrop(filter){
          closeDrop();
          var vars=getVarSuggestions();
          var filtered=filter?vars.filter(function(v){return v.toLowerCase().indexOf(filter.toLowerCase())===0;}):vars;
          if(filtered.length===0&&filter){return;}
          drop=document.createElement('div');drop.className='vartext-drop';
          if(filtered.length===0){
            var empty=document.createElement('div');empty.className='vartext-drop-empty';
            empty.textContent='no variables yet';drop.appendChild(empty);
          }else{
            filtered.forEach(function(v){
              var item=document.createElement('div');item.className='vartext-drop-item';
              item.textContent=v;
              item.addEventListener('mousedown',function(e){
                e.preventDefault();e.stopPropagation();
                ei.value=v;capturedExNodeVt.params[capturedJiVt]=v;genCode();
                closeDrop();});
              drop.appendChild(item);});
          }
          wrap.appendChild(drop);
        }
        ei.addEventListener('click',function(e){e.stopPropagation();openDrop('');});
        ei.addEventListener('focus',function(e){openDrop('');});
        ei.addEventListener('input',function(e){
          e.stopPropagation();
          capturedExNodeVt.params[capturedJiVt]=e.target.value;genCode();
          var v=e.target.value;
          if(v===''){openDrop('');}else{openDrop(v);}
        });
        ei.addEventListener('blur',function(){setTimeout(closeDrop,150);});
        ei.addEventListener('keydown',function(e){
          e.stopPropagation();
          if(e.key==='Escape'||e.key==='Enter'){closeDrop();}
          if(e.key==='Enter'){ei.blur();}
        });
        wrap.appendChild(ei);chip.appendChild(wrap);
      })(ji,exNode);
    }else{
      var ei=document.createElement('input');ei.type=inp.t==='number'?'number':'text';
      ei.className='expr-input';ei.value=exNode.params[ji]||'';
      ei.style.width=(inp.t==='number'?'48px':'60px');
      ei.addEventListener('click',function(e){e.stopPropagation();});
      ei.addEventListener('input',function(e){e.stopPropagation();exNode.params[ji]=e.target.value;genCode();});
      chip.appendChild(ei);
    }});
  if(onRemove){
    var rx=document.createElement('span');rx.className='expr-remove';rx.textContent='x';
    rx.title='Remove expression';
    rx.addEventListener('click',function(e){e.stopPropagation();onRemove();});chip.appendChild(rx);}
  return chip;}
function getOptions(key){
  var base;
  if(key==='DIGITAL_PIN_OPTIONS'){base=UNO_DIGITAL_IO_PINS;}
  else if(key==='PWM_PIN_OPTIONS'){base=UNO_PWM_PINS;}
  else if(key==='ANALOG_PIN_OPTIONS'){base=UNO_ANALOG_PINS;}
  else{return [];}
  var opts=base.slice();
  SECTIONS.global.forEach(function(b){
    if(b.type==='intvar'){
      var n=b.params[0];
      if(n&&opts.indexOf(n)===-1)opts.push(n);
    }
  });
  return opts;
}
var sel=null;
var activePhantoml=null;
var PROGRESSION_MODE=false;
var STEPS=null;
var CURRENT_STEP=0;
var STUDENT_SAVES=[];
var CHECK_FAIL_COUNT=0;
var SKETCH_ERROR_PATHS = [];
var PALETTE_ALLOWED = CFG.palette || null;
function updatePalette(){
  var ctx=document.getElementById('pal-context');
  var blockSec=document.getElementById('pal-blocks-section');
  var exprSec=document.getElementById('pal-expr-section');
  var exprTitle=document.getElementById('pal-expr-title');
  if(exprSel){
    activePhantoml=null;
    ctx.className='has-expr';
    ctx.textContent=exprSel.isSubSlot?'fill sub-slot:':'fill value slot:';
    blockSec.style.display='none';
    exprTitle.style.display='';
    var guided=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';
    var expectedType=null;
    if(exprSel.condObj){
      var ec=exprSel.condObj._expectedCond;
      if(ec){
        var sideKey=exprSel.side==='leftExpr'?'left':exprSel.side==='rightExpr'?'right':exprSel.side==='leftExpr2'?'left2':'right2';
        expectedType=ec[sideKey]||null;
      }
    }else if(!exprSel.isSubSlot&&exprSel.block&&exprSel.block._expectedExpr){
      expectedType=exprSel.block._expectedExpr[exprSel.slotIdx]||null;}
    exprSec.querySelectorAll('.block-btn').forEach(function(btn){
      if(expectedType){
        btn.classList[btn.getAttribute('data-type')===expectedType?'remove':'add']('hidden');
      }else{
        btn.classList.remove('hidden');
      }});
    return;
  }
  if(activePhantoml){
    var ph=activePhantoml.phantom;
    var step=PROGRESSION_MODE&&STEPS?STEPS[CURRENT_STEP]:null;
    var guided=step?step.guidance==='guided':false;
    ctx.className='has-sel';
    ctx.textContent='place: '+ph.hint;
    blockSec.style.display='flex';
    exprTitle.style.display='';
    blockSec.querySelectorAll('.block-btn').forEach(function(btn){
      var type=btn.getAttribute('data-type');
      if(ph.expects){
        btn.classList[type===ph.expects?'remove':'add']('hidden');
      }else if(!guided){
        btn.classList.remove('hidden');
      }else{
        btn.classList.add('hidden');
      }});
    exprSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});
    return;
  }
  blockSec.style.display='flex';
  exprTitle.style.display='';
  if(!sel){
    ctx.className='';ctx.textContent='select a section';
    blockSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});
    exprSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});
    return;
  }
  ctx.className='has-sel';
  var parts=sel.pathStr.split(' \u2192 ');
  ctx.textContent='adding to: '+parts[parts.length-1];
  var inNested=sel.pathStr.indexOf('\u2192')!==-1;
  blockSec.querySelectorAll('.block-btn').forEach(function(btn){
    var type=btn.getAttribute('data-type');
    var def=BLOCKS[type];if(!def){btn.classList.remove('hidden');return;}
    var ok=inNested?(def.allowed.indexOf('if')!==-1||def.allowed.indexOf('for')!==-1||def.allowed.indexOf('while')!==-1)
                   :(def.allowed.indexOf(sel.section)!==-1);
    if(ok&&PALETTE_ALLOWED!==null)ok=PALETTE_ALLOWED.indexOf(type)!==-1;
    if(ok){btn.classList.remove('hidden');}else{btn.classList.add('hidden');}});
  exprSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});}
function setSelection(section,targetArr,pathStr){
  sel={section:section,targetArr:targetArr,pathStr:pathStr};
  document.getElementById('statusbar').innerHTML='adding to: <span>'+pathStr+'</span>';
  updatePalette();
  render();}
function clearSelection(){
  sel=null;exprSel=null;
  document.getElementById('statusbar').textContent='click a section or if body to select it';
  updatePalette();
  render();}
document.addEventListener('click',function(e){
  if(!e.target.closest('.section')&&!e.target.closest('.if-body')&&
     !e.target.closest('.block-btn')&&!e.target.closest('#codepanel')&&!e.target.closest('button')&&
     !e.target.closest('.expr-slot')&&!e.target.closest('.expr-block-inline')){
    clearSelection();}});
function expandSection(elId){
  ['gs','ss','ls'].forEach(function(id){
    document.getElementById(id).classList.toggle('expanded', id===elId);});}
function setupSection(elId,sName,label){
  var el=document.getElementById(elId);
  var hdr=el.querySelector('.section-header');
  var body=document.getElementById(elId+'-body');
  hdr.addEventListener('click',function(e){
    e.stopPropagation();
    expandSection(elId);
    setSelection(sName,SECTIONS[sName],label);
  });
  body.addEventListener('click',function(e){
    if(e.target===body){e.stopPropagation();setSelection(sName,SECTIONS[sName],label);}});}
setupSection('gs','global','Global');
setupSection('ss','setup','setup()');
setupSection('ls','loop','loop()');
document.querySelectorAll('.block-btn').forEach(function(btn){
  btn.addEventListener('click',function(e){
    e.stopPropagation();
    var type=btn.getAttribute('data-type');if(!type)return;
    var def=BLOCKS[type];if(!def)return;
    if(exprSel&&def.asExpr){
      var newNode=makeExNode(type);
      if(exprSel.condObj){
        exprSel.condObj[exprSel.side]=newNode;
      }else if(exprSel.isSubSlot){
        if(!exprSel.exNode.children)exprSel.exNode.children=[];
        exprSel.exNode.children[exprSel.slotIdx]=newNode;
      }else{
        if(!exprSel.block.exChildren)exprSel.block.exChildren=[];
        exprSel.block.exChildren[exprSel.slotIdx]=newNode;
      }
      exprSel=null;updatePalette();render();return;
    }
    if(activePhantoml&&def.asStatement){
      var ph=activePhantoml.phantom;
      var arr=activePhantoml.arr;
      var idx=activePhantoml.idx;
      var newBlock;
      if(type==='ifblock'){
        var guided=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';
        var cond={leftExpr:null,op:'==',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null};
        if(ph.condition&&guided){
          cond.op=ph.condition.op||'==';
          cond.joiner=ph.condition.joiner||'none';
          cond.op2=ph.condition.op2||'==';
          cond._expectedCond={
            left:ph.condition.leftExpr?ph.condition.leftExpr.type:null,
            right:ph.condition.rightExpr?ph.condition.rightExpr.type:null,
            left2:ph.condition.leftExpr2?ph.condition.leftExpr2.type:null,
            right2:ph.condition.rightExpr2?ph.condition.rightExpr2.type:null
          };}
        var ib=guided&&ph.ifbody?JSON.parse(JSON.stringify(ph.ifbody)):[];
        var eifs=guided&&ph.elseifs?JSON.parse(JSON.stringify(ph.elseifs)):[];
        var eb=guided&&ph.elsebody?JSON.parse(JSON.stringify(ph.elsebody)):null;
        newBlock={id:(Date.now()+Math.random()).toString(),type:'ifblock',
          condition:cond,ifbody:ib,elseifs:eifs,elsebody:eb};
      }else if(type==='forloop'){
        var guidedF=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';
        var ib=guidedF&&ph.body?JSON.parse(JSON.stringify(ph.body)):[];
        var fi=guidedF?(ph.forinit||'int i = 0'):'int i = 0';
        var fc=guidedF?(ph.forcond||'i < 10'):'i < 10';
        var fr=guidedF?(ph.forincr||'i++'):'i++';
        newBlock={id:(Date.now()+Math.random()).toString(),type:'forloop',forinit:fi,forcond:fc,forincr:fr,body:ib};
      }else if(type==='whileloop'){
        var guidedW=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';
        var wcond={leftExpr:null,op:'!=',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null};
        if(ph.condition&&guidedW){
          wcond.op=ph.condition.op||'!=';
          wcond._expectedCond={
            left:ph.condition.leftExpr?ph.condition.leftExpr.type:null,
            right:ph.condition.rightExpr?ph.condition.rightExpr.type:null
          };}
        var wb=guidedW&&ph.body?JSON.parse(JSON.stringify(ph.body)):[];
        newBlock={id:(Date.now()+Math.random()).toString(),type:'whileloop',condition:wcond,body:wb};
      }else{
        var guided=PROGRESSION_MODE&&STEPS&&STEPS[CURRENT_STEP]&&STEPS[CURRENT_STEP].guidance==='guided';
        var params=def.inputs.map(function(inp){
          if(inp.t==='sel'){var f=inp.o[0];return typeof f==='object'?f.v:f;}return '';});
        var exch=guided
          ?def.inputs.map(function(){return null;})
          :(def.defaults?def.defaults.map(function(d){return d?JSON.parse(JSON.stringify(d)):null;}):null)||[];
        var expectedExpr=guided&&ph.exChildren
          ?ph.exChildren.map(function(e){return e?e.type:null;})
          :null;
        newBlock={id:(Date.now()+Math.random()).toString(),type:type,params:params,exChildren:exch};
        if(expectedExpr)newBlock._expectedExpr=expectedExpr;
      }
      arr.splice(idx,1,newBlock);
      activePhantoml=null;
      checkStepComplete();
      updatePalette();render();return;
    }
    if(!def.asStatement){flash(type+' can only go in expression slots');return;}
    if(!sel){flash('Select a section or if body first');return;}
    var inIf=sel.pathStr.indexOf('\u2192')!==-1;
    if(inIf){if(def.allowed.indexOf('if')===-1&&def.allowed.indexOf('for')===-1&&def.allowed.indexOf('while')===-1){flash('"'+type+'" not allowed here');return;}}
    else{if(def.allowed.indexOf(sel.section)===-1){flash('Goes in: '+def.allowed.filter(function(a){return a!=='if'&&a!=='for'&&a!=='while';}).join(' or '));return;}}
    var block;
    if(type==='ifblock'){
      block={id:(Date.now()+Math.random()).toString(),type:'ifblock',
        condition:{leftExpr:null,op:'==',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null},
        ifbody:[],elseifs:[],elsebody:null};
    }else if(type==='forloop'){
      block={id:(Date.now()+Math.random()).toString(),type:'forloop',forinit:'int i = 0',forcond:'i < 10',forincr:'i++',body:[]};
    }else if(type==='whileloop'){
      block={id:(Date.now()+Math.random()).toString(),type:'whileloop',
        condition:{leftExpr:null,op:'!=',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null},
        body:[]};
    }else{
      var params=def.inputs.map(function(inp){
        if(inp.t==='sel'){var f=inp.o[0];return typeof f==='object'?f.v:f;}return '';});
      var exChildren=def.defaults?def.defaults.map(function(d){return d?JSON.parse(JSON.stringify(d)):null;}):[];
      block={id:(Date.now()+Math.random()).toString(),type:type,params:params,exChildren:exChildren};
    }
    sel.targetArr.push(block);render();});});
function render(){
  console.log('render called', new Error().stack);
  var anc=collectAncestorArrays();
  renderSection('gs','global',anc);renderSection('ss','setup',anc);renderSection('ls','loop',anc);
  ['gs','ss','ls'].forEach(function(id){
    var el=document.getElementById(id);
    var sn=id==='gs'?'global':id==='ss'?'setup':'loop';
    var base='section s-'+(id==='gs'?'global':id==='ss'?'setup':'loop');
    var isExpanded=el.classList.contains('expanded');
    el.className=(sel&&sel.targetArr===SECTIONS[sn])?base+' active':base;
    if(isExpanded)el.classList.add('expanded');});
  console.log('[DEBUG] render() finishing. Re-applying highlights.'); genCode(); applySketchHighlights();
  if (typeof READONLY_MODE !== 'undefined' && READONLY_MODE) {
    document.querySelectorAll('.blk-input,.cond-input,.vartext-input,.cond-select,.cond-joiner').forEach(function(el) {
      el.setAttribute('disabled', true);
    });
    document.querySelectorAll('.act').forEach(function(el) {
      el.style.display = 'none';
    });
    document.querySelectorAll('.ws-block,.if-body,.for-body,.while-body,.if-block,.for-block,.while-block').forEach(function(el) {
      el.style.pointerEvents = 'none';
    });
    document.querySelectorAll('.palette-block,.palette-item').forEach(function(el) {
      el.style.display = 'none';
    });
  }
}
function collectAncestorArrays(){
  var anc=[];if(!sel)return anc;
  function walk(arr){for(var i=0;i<arr.length;i++){var b=arr[i];
    if(b.type==='ifblock'){if(containsTarget(b))anc.push(b.id);
      walk(b.ifbody);b.elseifs.forEach(function(ei){walk(ei.body);});if(b.elsebody)walk(b.elsebody);
    }else if(b.type==='forloop'||b.type==='whileloop'){if(b.body&&isDescendantOf(b.body,sel.targetArr))anc.push(b.id);if(b.body)walk(b.body);}}}
  walk(SECTIONS[sel.section]);return anc;}
function containsTarget(ifBlock){
  if(ifBlock.ifbody===sel.targetArr)return true;
  for(var i=0;i<ifBlock.elseifs.length;i++)if(ifBlock.elseifs[i].body===sel.targetArr)return true;
  if(ifBlock.elsebody===sel.targetArr)return true;
  function walkDeep(arr){for(var j=0;j<arr.length;j++){var b=arr[j];
    if(b.type==='ifblock'&&containsTarget(b))return true;
    if((b.type==='forloop'||b.type==='whileloop')&&b.body&&isDescendantOf(b.body,sel.targetArr))return true;
  }return false;}
  return walkDeep(ifBlock.ifbody)||ifBlock.elseifs.some(function(ei){return walkDeep(ei.body);})||
         (ifBlock.elsebody?walkDeep(ifBlock.elsebody):false);}
function braceDepth(arr,idx){
  var depth=0;
  for(var i=0;i<idx;i++){
    if(arr[i].type!=='codeblock')continue;
    var c=(arr[i].params[0]||'').trim();
    if(c.charAt(c.length-1)==='{')depth++;
    if(c==='}'||c.match(/^\}/))depth=Math.max(0,depth-1);
  }
  return depth;
}
function renderSection(elId,sName,anc){
  var body=document.getElementById(elId+'-body');
  body.querySelectorAll('.ws-block,.if-block').forEach(function(e){e.remove();});
  SECTIONS[sName].forEach(function(block,idx){body.appendChild(renderBlock(block,idx,SECTIONS[sName],sName,sName,anc));});}
function renderBlock(block,idx,parentArr,section,pathStr,anc){
  if(block.type==='ifblock')return renderIfBlock(block,idx,parentArr,section,pathStr,anc);
  if(block.type==='forloop')return renderForBlock(block,idx,parentArr,section,pathStr,anc);
  if(block.type==='whileloop')return renderWhileBlock(block,idx,parentArr,section,pathStr,anc);
  if(block.type==='phantom')return renderPhantomBlock(block,idx,parentArr);
  if(block.type==='phantom_resolved')return renderPhantomResolved(block);
  return renderActionBlock(block,idx,parentArr);}
function renderPhantomBlock(block,idx,parentArr){
  var d=document.createElement('div');
  d.className='ws-block phantom-block';
  var depth=braceDepth(parentArr,idx);
  if(depth>0)d.style.marginLeft=(depth*18)+'px';
  var isActive=activePhantoml&&activePhantoml.arr===parentArr&&activePhantoml.idx===idx;
  if(isActive)d.classList.add('active');
  var icon=document.createElement('span');icon.className='phantom-icon';icon.textContent='+';
  var hint=document.createElement('span');hint.className='phantom-hint';hint.textContent=block.hint||'Place a block here';
  var exp=document.createElement('span');exp.className='phantom-expects';exp.textContent=block.expects||'';
  d.appendChild(icon);d.appendChild(hint);d.appendChild(exp);
  d.addEventListener('click',function(e){
    e.stopPropagation();
    if(activePhantoml&&activePhantoml.arr===parentArr&&activePhantoml.idx===idx){
      activePhantoml=null;
    }else{
      activePhantoml={arr:parentArr,idx:idx,phantom:block};
      sel=null;exprSel=null;
    }
    updatePalette();render();});
  return d;}
function renderPhantomResolved(block){
  var d=document.createElement('div');
  d.className='ws-block phantom-block';d.style.opacity='0.45';d.style.cursor='default';
  d.style.background='#f6f8fa';d.style.borderColor='#d0d7de';
  var icon=document.createElement('span');icon.className='phantom-icon';icon.textContent='\u2713';
  var hint=document.createElement('span');hint.className='phantom-hint';
  hint.style.color='#57606a';hint.textContent=block.hint||'';
  d.appendChild(icon);d.appendChild(hint);
  return d;}
function renderActionBlock(block,idx,parentArr){
  var def=B[block.type],d=document.createElement('div');d.className='ws-block';
  d.setAttribute('data-id', block.id);
  if(block.type==='codeblock'){
    d.classList.add('codeblock-block');
    var depth=braceDepth(parentArr,idx);
    var c=(block.params[0]||'').trim();
    if(c==='}'||c.match(/^\}/))depth=Math.max(0,depth-1);
    if(depth>0)d.style.marginLeft=(depth*18)+'px';
    var icon=document.createElement('span');d.appendChild(icon);
    var code=document.createElement('span');code.className='codeblock-code';
    code.textContent=block.params[0]||'';d.appendChild(code);
    function mkb2(ic,fn){var bt=document.createElement('button');bt.className='act';bt.textContent=ic;
      bt.addEventListener('click',function(e){e.stopPropagation();fn();});return bt;}
    d.appendChild(mkb2('\u2191',function(){if(idx>0){var t=parentArr[idx-1];parentArr[idx-1]=parentArr[idx];parentArr[idx]=t;render();}}));
    d.appendChild(mkb2('\u2193',function(){if(idx<parentArr.length-1){var t=parentArr[idx+1];parentArr[idx+1]=parentArr[idx];parentArr[idx]=t;render();}}));
    d.appendChild(mkb2('\u00D7',function(){parentArr.splice(idx,1);render();}));
    return d;}
  var nm=document.createElement('span');nm.className='blk-name';nm.textContent=block.type;d.appendChild(nm);
  var bdepth=braceDepth(parentArr,idx);if(bdepth>0)d.style.marginLeft=(bdepth*18)+'px';
  def.inputs.forEach(function(inp,j){
    if(inp.t==='expr'){
      d.appendChild(renderExprSlot(block,j,inp.l));return;}
    if(inp.t==='vartext'){
      (function(capturedJ,capturedInpO){
        var f=document.createElement('div');f.className='blk-field';
        var lb=document.createElement('label');lb.textContent=inp.l;f.appendChild(lb);
        var wrap=document.createElement('span');wrap.className='vartext-wrap';
        var ei=document.createElement('input');ei.type='text';ei.className='vartext-input';
        ei.value=block.params[capturedJ]||'';ei.placeholder='name';
        var drop=null;
        function closeDrop(){if(drop){drop.remove();drop=null;}}
        function openDrop(filter){
          closeDrop();
          var vars=capturedInpO?getPinSuggestions(capturedInpO):getVarSuggestions();
          var filtered=filter?vars.filter(function(v){return v.toLowerCase().indexOf(filter.toLowerCase())===0;}):vars;
          if(filtered.length===0&&filter){return;}
          drop=document.createElement('div');drop.className='vartext-drop';
          if(filtered.length===0){
            var empty=document.createElement('div');empty.className='vartext-drop-empty';
            empty.textContent='no options yet';drop.appendChild(empty);
          }else{
            filtered.forEach(function(v){
              var item=document.createElement('div');item.className='vartext-drop-item';
              item.textContent=v;
              item.addEventListener('mousedown',function(e){
                e.preventDefault();e.stopPropagation();
                ei.value=v;block.params[capturedJ]=v;genCode();
                closeDrop();});
              drop.appendChild(item);});
          }
          wrap.appendChild(drop);}
        ei.addEventListener('click',function(e){e.stopPropagation();openDrop('');});
        ei.addEventListener('focus',function(){openDrop('');});
        ei.addEventListener('input',function(e){
          e.stopPropagation();
          block.params[capturedJ]=e.target.value;genCode();
          e.target.value===''?openDrop(''):openDrop(e.target.value);});
        ei.addEventListener('blur',function(){setTimeout(closeDrop,150);});
        ei.addEventListener('keydown',function(e){
          e.stopPropagation();
          if(e.key==='Escape'||e.key==='Enter'){closeDrop();}
          if(e.key==='Enter'){ei.blur();}});
        wrap.appendChild(ei);f.appendChild(wrap);d.appendChild(f);
      })(j,inp.o||null);return;}
    var f=document.createElement('div');f.className='blk-field';
    var lb=document.createElement('label');lb.textContent=inp.l;f.appendChild(lb);
    var el;
    if(inp.t==='sel'){el=document.createElement('select');
      var opts=inp.o; if(typeof opts==='string'){opts=getOptions(opts);}
      if(!block.params[j]){var op=document.createElement('option');op.value='';op.textContent='\u2014';el.appendChild(op);}
      opts.forEach(function(opt){var o=document.createElement('option');
        if(typeof opt==='object'){o.value=opt.v;o.textContent=opt.lb;}else{o.value=opt;o.textContent=opt;}
        el.appendChild(o);});el.value=block.params[j];
    }else{el=document.createElement('input');el.type=inp.t==='number'?'number':'text';el.value=block.params[j];}
    el.className='blk-input';
    if(block.type==='increment'&&inp.l==='By'){
      var op=block.params[1]||'++';f.style.display=(op==='++'||op==='--')?'none':'';}
    el.addEventListener('click',function(e){e.stopPropagation();});
    el.addEventListener('input',function(e){e.stopPropagation();block.params[j]=e.target.value;genCode();
      if(block.type==='increment'&&inp.l==='Op'){
        var byF=d.querySelector('.by-field');
        if(byF)byF.style.display=(e.target.value==='++'||e.target.value==='--')?'none':'';}});
    if(block.type==='increment'&&inp.l==='By')f.className+=' by-field';
    f.appendChild(el);d.appendChild(f);});
  function mkb(ic,fn){var bt=document.createElement('button');bt.className='act';bt.textContent=ic;
    bt.addEventListener('click',function(e){e.stopPropagation();fn();});return bt;}
  d.appendChild(mkb('\u2191',function(){if(idx>0){var t=parentArr[idx-1];parentArr[idx-1]=parentArr[idx];parentArr[idx]=t;render();}}));
  d.appendChild(mkb('\u2193',function(){if(idx<parentArr.length-1){var t=parentArr[idx+1];parentArr[idx+1]=parentArr[idx];parentArr[idx]=t;render();}}));
  d.appendChild(mkb('\u00D7',function(){parentArr.splice(idx,1);render();}));
  return d;}
function renderIfBlock(block,idx,parentArr,section,parentPathStr,anc){
  var wrap=document.createElement('div');
  wrap.className='if-block'+(anc.indexOf(block.id)!==-1?' ancestor':'');
  wrap.setAttribute('data-id', block.id);
  var hdr=document.createElement('div');hdr.className='if-header';
  hdr.appendChild(kw('if ('));appendCondFields(hdr,block.condition);hdr.appendChild(kw(')'));
  hdr.appendChild(mkact('+ else if',function(){
    block.elseifs.push({condition:{leftExpr:null,op:'==',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null},body:[]});render();}));
  if(block.elsebody===null)hdr.appendChild(mkact('+ else',function(){block.elsebody=[];render();}));
  hdr.appendChild(mkact('\u00D7',function(){
    parentArr.splice(idx,1);
    if(sel&&(sel.targetArr===block.ifbody||isDescendant(block,sel.targetArr)))clearSelection();else render();}));
  wrap.appendChild(hdr);
  var ifPathStr=parentPathStr+' \u2192 if';
  var isOnlyBody=block.elseifs.length===0&&block.elsebody===null;
  wrap.appendChild(makeBodyZone(block.ifbody,section,ifPathStr,isOnlyBody,anc));
  block.elseifs.forEach(function(ei,eiIdx){
    var eiHdr=document.createElement('div');eiHdr.className='elseif-header';
    eiHdr.appendChild(kw('else if ('));appendCondFields(eiHdr,ei.condition);eiHdr.appendChild(kw(')'));
    eiHdr.appendChild(mkact('\u00D7',function(){block.elseifs.splice(eiIdx,1);render();}));
    wrap.appendChild(eiHdr);
    var eiPathStr=parentPathStr+' \u2192 else if';
    var eiIsLast=eiIdx===block.elseifs.length-1&&block.elsebody===null;
    wrap.appendChild(makeBodyZone(ei.body,section,eiPathStr,eiIsLast,anc));});
  if(block.elsebody!==null){
    var elHdr=document.createElement('div');elHdr.className='else-header';
    elHdr.appendChild(kw('else'));
    elHdr.appendChild(mkact('\u00D7',function(){block.elsebody=null;render();}));
    wrap.appendChild(elHdr);
    wrap.appendChild(makeBodyZone(block.elsebody,section,parentPathStr+' \u2192 else',true,anc));}
  return wrap;}
function renderForBlock(block,idx,parentArr,section,parentPathStr,anc){
  var wrap=document.createElement('div');wrap.className='for-block';
  wrap.setAttribute('data-id', block.id);
  var hdr=document.createElement('div');hdr.className='for-header';
  var fkw=document.createElement('span');fkw.className='for-keyword';fkw.textContent='for (';hdr.appendChild(fkw);
  var fields=[{key:'init',label:'init',ph:'int i=0'},{key:'cond',label:'cond',ph:'i<10'},{key:'incr',label:'incr',ph:'i++'}];
  if(!block.forinit&&block.forinit!=='')block.forinit='int i = 0';
  if(!block.forcond&&block.forcond!=='')block.forcond='i < 10';
  if(!block.forincr&&block.forincr!=='')block.forincr='i++';
  var keys=['forinit','forcond','forincr'],labels=['init','cond','incr'],phs=['int i=0','i<10','i++'];
  for(var fi=0;fi<3;fi++){(function(ki,la,ph){
    var fw=document.createElement('div');fw.style.cssText='display:flex;flex-direction:column;font-size:8px;';
    var fl=document.createElement('label');fl.textContent=la;fl.style.color='#57606a';fw.appendChild(fl);
    var fe=document.createElement('input');fe.type='text';fe.className='cond-input';fe.value=block[ki]||'';
    fe.placeholder=ph;
    fe.addEventListener('click',function(e){e.stopPropagation();});
    fe.addEventListener('input',function(e){e.stopPropagation();block[ki]=e.target.value;genCode();});
    fw.appendChild(fe);hdr.appendChild(fw);
    if(fi<2){var sep=document.createElement('span');sep.className='for-keyword';sep.textContent=';';hdr.appendChild(sep);}
  })(keys[fi],labels[fi],phs[fi]);}
  var ekw=document.createElement('span');ekw.className='for-keyword';ekw.textContent=') {';hdr.appendChild(ekw);
  hdr.appendChild(mkact('\u00D7',function(){parentArr.splice(idx,1);
    if(sel&&(sel.targetArr===block.body||isDescendantOf(block.body,sel.targetArr)))clearSelection();else render();}));
  wrap.appendChild(hdr);
  if(!block.body)block.body=[];
  var bodyPath=parentPathStr+' \u2192 for';
  var bz=document.createElement('div');bz.className='for-body';
  if(sel&&sel.targetArr===block.body)bz.classList.add('selected');
  block.body.forEach(function(b,bi){bz.appendChild(renderBlock(b,bi,block.body,section,bodyPath,anc));});
  if(block.body.length===0){var hint=document.createElement('div');hint.className='body-hint';
    hint.textContent='click to select, then add blocks';bz.appendChild(hint);}
  bz.addEventListener('click',function(e){
    if(e.target===bz||e.target.classList.contains('body-hint')){e.stopPropagation();setSelection(section,block.body,bodyPath);}});
  wrap.appendChild(bz);
  var cz=document.createElement('div');cz.style.cssText='border-left:1px dashed #2e7d32;border-right:1px dashed #2e7d32;border-bottom:1px dashed #2e7d32;border-radius:0 0 5px 5px;padding:2px 6px;font-size:10px;color:#2e7d32;';
  cz.textContent='} // end for';wrap.appendChild(cz);
  return wrap;}
function renderWhileBlock(block,idx,parentArr,section,parentPathStr,anc){
  var wrap=document.createElement('div');wrap.className='while-block';
  wrap.setAttribute('data-id', block.id);
  var hdr=document.createElement('div');hdr.className='while-header';
  var wkw=document.createElement('span');wkw.className='while-keyword';wkw.textContent='while (';hdr.appendChild(wkw);
  if(!block.condition)block.condition={leftExpr:null,op:'!=',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null};
  appendCondFields(hdr,block.condition);
  var ewkw=document.createElement('span');ewkw.className='while-keyword';ewkw.textContent=') {';hdr.appendChild(ewkw);
  hdr.appendChild(mkact('\u00D7',function(){parentArr.splice(idx,1);
    if(sel&&(sel.targetArr===block.body||isDescendantOf(block.body,sel.targetArr)))clearSelection();else render();}));
  wrap.appendChild(hdr);
  if(!block.body)block.body=[];
  var bodyPath=parentPathStr+' \u2192 while';
  var bz=document.createElement('div');bz.className='while-body';
  if(sel&&sel.targetArr===block.body)bz.classList.add('selected');
  block.body.forEach(function(b,bi){bz.appendChild(renderBlock(b,bi,block.body,section,bodyPath,anc));});
  if(block.body.length===0){var hint=document.createElement('div');hint.className='body-hint';
    hint.textContent='click to select, then add blocks';bz.appendChild(hint);}
  bz.addEventListener('click',function(e){
    if(e.target===bz||e.target.classList.contains('body-hint')){e.stopPropagation();setSelection(section,block.body,bodyPath);}});
  wrap.appendChild(bz);
  var cz=document.createElement('div');cz.style.cssText='border-left:1px dashed #6a1b9a;border-right:1px dashed #6a1b9a;border-bottom:1px dashed #6a1b9a;border-radius:0 0 5px 5px;padding:2px 6px;font-size:10px;color:#6a1b9a;';
  cz.textContent='} // end while';wrap.appendChild(cz);
  return wrap;}
function isDescendantOf(body,targetArr){
  if(body===targetArr)return true;
  for(var i=0;i<body.length;i++){var b=body[i];
    if(b.type==='ifblock'){if(isDescendantOf(b.ifbody,targetArr))return true;
      for(var j=0;j<b.elseifs.length;j++)if(isDescendantOf(b.elseifs[j].body,targetArr))return true;
      if(b.elsebody&&isDescendantOf(b.elsebody,targetArr))return true;
    }else if(b.type==='forloop'||b.type==='whileloop'){if(isDescendantOf(b.body,targetArr))return true;}}
  return false;}
function makeBodyZone(arr,section,pathStr,isLast,anc){
  var div=document.createElement('div');
  div.className='if-body'+(isLast?' last':'');
  if(sel&&sel.targetArr===arr)div.classList.add('selected');
  arr.forEach(function(block,idx){div.appendChild(renderBlock(block,idx,arr,section,pathStr,anc));});
  if(arr.length===0){var hint=document.createElement('div');hint.className='body-hint';
    hint.textContent='click to select, then add blocks';div.appendChild(hint);}
  div.addEventListener('click',function(e){
    if(e.target===div||e.target.classList.contains('body-hint')){
      e.stopPropagation();setSelection(section,arr,pathStr);}});
  return div;}
function isDescendant(ifBlock,targetArr){
  if(ifBlock.ifbody===targetArr)return true;
  for(var i=0;i<ifBlock.elseifs.length;i++)if(ifBlock.elseifs[i].body===targetArr)return true;
  if(ifBlock.elsebody===targetArr)return true;
  function walkDeep(arr){for(var j=0;j<arr.length;j++){var b=arr[j];
    if(b.type==='ifblock'&&isDescendant(b,targetArr))return true;
    if((b.type==='forloop'||b.type==='whileloop')&&b.body&&isDescendantOf(b.body,targetArr))return true;
  }return false;}
  return walkDeep(ifBlock.ifbody)||ifBlock.elseifs.some(function(ei){return walkDeep(ei.body);})||
         (ifBlock.elsebody?walkDeep(ifBlock.elsebody):false);}
function kw(text){var s=document.createElement('span');s.className='if-keyword';s.textContent=text;return s;}
function mkact(text,fn){var b=document.createElement('button');b.className='act';b.textContent=text;
  b.addEventListener('click',function(e){e.stopPropagation();fn();});return b;}
function getConditionSuggestions(){
  var seen={},out=[];
  function add(v){if(!v)return;if(seen[v])return;seen[v]=true;out.push(v);}
  ['global','setup','loop'].forEach(function(sec){
    SECTIONS[sec].forEach(function(b){
      if(b.type==='pinmode'){
        var pin=b.params[0],mode=b.params[1];
        if(mode==='INPUT'||mode==='INPUT_PULLUP')add('digitalRead('+pin+')');
      }else if(b.type==='analogread'){
        var ap=b.params[0],vn=b.params[1]||'val';
        add('analogRead('+ap+')');
        add(vn);
      }else if(b.type==='intvar'||b.type==='stringvar'){
        add(b.params[0]);
      }
    });
  });
  ['HIGH','LOW'].forEach(add);
  return out;
}
function getVarSuggestions(){
  var seen={},out=[];
  function add(v){if(!v)return;if(seen[v])return;seen[v]=true;out.push(v);}
  ['global','setup','loop'].forEach(function(sec){
    SECTIONS[sec].forEach(function(b){
      if(b.type==='intvar'||b.type==='longvar'||b.type==='stringvar'){add(b.params[0]);}
      if(b.type==='codeblock'){
        var c=b.params[0]||'';
        var m=c.match(/(?:int|long|String|bool|unsigned long)\s+([a-zA-Z_]\w*)/);
        if(m)add(m[1]);
        var m2=c.match(/([a-zA-Z_]\w*)\s*=/);
        if(m2)add(m2[1]);
      }
    });
    function walkBody(arr){arr.forEach(function(b){
      if(b.type==='intvar'||b.type==='longvar'){add(b.params[0]);}
      if(b.ifbody)walkBody(b.ifbody);
      if(b.elseifs)b.elseifs.forEach(function(ei){walkBody(ei.body);});
      if(b.elsebody)walkBody(b.elsebody);
      if(b.body)walkBody(b.body);
    });}
    walkBody(SECTIONS[sec]);
  });
  return out;
}
function getPinSuggestions(optKey){
  var seen={},out=[];
  SECTIONS.global.forEach(function(b){
    if(b.type==='intvar'&&b.params[0]&&!seen[b.params[0]]){seen[b.params[0]]=true;out.push(b.params[0]);}
  });
  getOptions(optKey||'DIGITAL_PIN_OPTIONS').forEach(function(p){
    if(!seen[p]){seen[p]=true;out.push(p);}
  });
  return out;
}
function renderCondExprSlot(cond,side,label){
  var exNode=cond[side]||null;
  var wrap=document.createElement('div');wrap.className='blk-field';
  var lb=document.createElement('label');lb.textContent=label;wrap.appendChild(lb);
  var slot=document.createElement('div');
  slot.className='expr-slot'+(exNode?' has-expr':'');
  var isActive=exprSel&&exprSel.condObj===cond&&exprSel.side===side;
  if(isActive)slot.classList.add('active');
  if(exNode){
    slot.appendChild(renderExprBlock(exNode,function(){cond[side]=null;exprSel=null;updatePalette();render();}));
  }else{
    var ph=document.createElement('span');ph.textContent=isActive?'> drop expr':'+ expr';slot.appendChild(ph);
  }
  slot.addEventListener('click',function(e){
    e.stopPropagation();
    if(exprSel&&exprSel.condObj===cond&&exprSel.side===side){exprSel=null;updatePalette();render();return;}
    exprSel={condObj:cond,side:side};sel=null;
    document.getElementById('statusbar').innerHTML='<span style="color:#9a6700">click an expression to fill the '+label+' slot</span>';
    updatePalette();
    render();});
  wrap.appendChild(slot);return wrap;}
function appendCondFields(parent,cond){
  parent.appendChild(renderCondExprSlot(cond,'leftExpr','left'));
  parent.appendChild(condField('op',cond,'opsel'));
  parent.appendChild(renderCondExprSlot(cond,'rightExpr','right'));
  parent.appendChild(condField('joiner',cond,'joinsel'));
  var g2=document.createElement('span');
  g2.style.display=cond.joiner!=='none'?'contents':'none';
  g2.appendChild(renderCondExprSlot(cond,'leftExpr2','left2'));
  g2.appendChild(condField('op2',cond,'opsel'));
  g2.appendChild(renderCondExprSlot(cond,'rightExpr2','right2'));
  parent.appendChild(g2);
  var joinEl=parent.querySelector('.cond-joiner');
  joinEl.addEventListener('change',function(){g2.style.display=joinEl.value!=='none'?'contents':'none';});}
function condField(labelText,obj,type){
  var f=document.createElement('div');f.className='cond-field';
  var lb=document.createElement('label');lb.textContent=labelText;f.appendChild(lb);
  var el;
  if(type==='opsel'){el=document.createElement('select');el.className='cond-select';
    [['==','equals'],['!=','not equals'],['>','greater than'],['<','less than'],['>=','greater or equal'],['<=','less than or equal']].forEach(function(o){
      var opt=document.createElement('option');opt.value=o[0];opt.textContent=o[1];el.appendChild(opt);});
    el.value=obj[labelText];
  }else if(type==='joinsel'){el=document.createElement('select');el.className='cond-joiner';
    [['none','\u2014'],['and','and'],['or','or']].forEach(function(o){
      var opt=document.createElement('option');opt.value=o[0];opt.textContent=o[1];el.appendChild(opt);});
    el.value=obj[labelText];
  }
  el.addEventListener('click',function(e){e.stopPropagation();});
  el.addEventListener('change',function(e){e.stopPropagation();obj[labelText]=e.target.value;genCode();});
  f.appendChild(el);return f;}
function genCond(c){
  var left=c.leftExpr?genExpr(c.leftExpr,null,'x'):(c.left||'x');
  var right=c.rightExpr?genExpr(c.rightExpr,null,'0'):(c.right||'0');
  var base=left+' '+(c.op||'==')+' '+right;
  if(c.joiner&&c.joiner!=='none'){
    var left2=c.leftExpr2?genExpr(c.leftExpr2,null,'x'):(c.left2||'x');
    var right2=c.rightExpr2?genExpr(c.rightExpr2,null,'0'):(c.right2||'0');
    if(left2!=='x')base+=' '+(c.joiner==='and'?'&&':'||')+' '+left2+' '+(c.op2||'==')+' '+right2;
  }
  return base;}
function genBlocks(arr,indent){
  var lines=[],extra=0;
  arr.forEach(function(b){
    if(b.type==='phantom'||b.type==='phantom_resolved')return;
    if(b.type==='codeblock'){
      var c=(b.params[0]||'').trim();
      if(c==='}'||c.match(/^\}/))extra=Math.max(0,extra-1);
      lines.push(genBlock(b,indent+extra));
      if(c.charAt(c.length-1)==='{')extra++;
    }else{lines.push(genBlock(b,indent+extra));}
  });
  return lines.join('\n');}
function genBlock(block,indent){
  var pad='';for(var i=0;i<indent;i++)pad+='   ';
  if(block.type==='ifblock'){
    var lines=[pad+'if ('+genCond(block.condition)+') {'];
    lines.push(genBlocks(block.ifbody,indent+1));
    lines.push(pad+'}');
    block.elseifs.forEach(function(ei){
      lines.push(pad+'else if ('+genCond(ei.condition)+') {');
      lines.push(genBlocks(ei.body,indent+1));
      lines.push(pad+'}');});
    if(block.elsebody!==null){
      lines.push(pad+'else {');
      lines.push(genBlocks(block.elsebody,indent+1));
      lines.push(pad+'}');}
    return lines.join('\n');}
  if(block.type==='forloop'){
    var init=block.forinit||'int i = 0';
    var cond=block.forcond||'i < 10';
    var incr=block.forincr||'i++';
    var lines=[pad+'for ('+init+'; '+cond+'; '+incr+') {'];
    lines.push(genBlocks(block.body||[],indent+1));
    lines.push(pad+'}');
    return lines.join('\n');}
  if(block.type==='whileloop'){
    var cond=block.condition?genCond(block.condition):(block.whilecond||'true');
    var lines=[pad+'while ('+cond+') {'];
    lines.push(genBlocks(block.body||[],indent+1));
    lines.push(pad+'}');
    return lines.join('\n');}
  return pad+BLOCKS[block.type].genStmt(block.params,block.exChildren||[]);}
function genCode(){
  var co=document.getElementById('codeout');
  var gv=genBlocks(SECTIONS.global,0);
  var sc=genBlocks(SECTIONS.setup,1);
  var lc=genBlocks(SECTIONS.loop,1);
  co.textContent='// Arduino Sketch\n// Block Builder\n// ------------\n\n'
    +(gv?gv+'\n\n':'')
    +'void setup() {\n'+(sc?sc+'\n':'')+'}'+
    '\n\nvoid loop() {\n'+(lc?lc+'\n':'')+'}';checkStepComplete();}
function findBlockById(id){
  var found=null;
  function walk(arr){
    if(!arr)return;
    for(var i=0;i<arr.length;i++){
      if(arr[i].id==id){found=arr[i];return;}
      if(arr[i].ifbody)walk(arr[i].ifbody);
      if(arr[i].elseifs)arr[i].elseifs.forEach(function(ei){walk(ei.body);});
      if(arr[i].elsebody)walk(arr[i].elsebody);
      if(arr[i].body)walk(arr[i].body);}}
  ['global','setup','loop'].forEach(function(s){walk(SECTIONS[s]);});
  return found;}
window.getBlockCode=function(id){
  var b=findBlockById(id);if(!b)return null;
  var code=genBlock(b,0);return code.split('\n')[0].trim();};
window.getGeneratedCode = function() { return document.getElementById('codeout').textContent; };
window.isProgressionMode = function() { return PROGRESSION_MODE; };
window.setBlockData = function(data) {
  if (!data) return;
  SECTIONS.global = data.global || [];
  SECTIONS.setup = data.setup || [];
  SECTIONS.loop = data.loop || [];
  clearSelection();
  if (typeof MASTER_SKETCH !== 'undefined' && MASTER_SKETCH) validateSketch();
};
function flash(txt){
  var mb=document.getElementById('msg');mb.textContent=txt;mb.classList.add('show');
  setTimeout(function(){mb.classList.remove('show');},2500);}
window.copyCode = function(){
  var txt=document.getElementById('codeout').textContent;
  if(navigator.clipboard&&navigator.clipboard.writeText)
    navigator.clipboard.writeText(txt).then(function(){flash('Copied!');}).catch(function(){fbCopy(txt);});
  else fbCopy(txt);};
function fbCopy(txt){
  var ta=document.createElement('textarea');ta.value=txt;
  ta.style.cssText='position:fixed;opacity:0;';document.body.appendChild(ta);ta.select();
  try{document.execCommand('copy');flash('Copied!');}catch(e){flash('Select manually');}
  document.body.removeChild(ta);}
window.resetBlocks = function(){
  SECTIONS.global=[];SECTIONS.setup=[];SECTIONS.loop=[];clearSelection();render();genCode();
};
function saveBlocks(){
  if(!USERNAME||!PAGE)return;
  var state;
  if(PROGRESSION_MODE){
    state = {current_step: CURRENT_STEP, student_saves: STUDENT_SAVES};
  } else {
    state = {global: SECTIONS.global, setup: SECTIONS.setup, loop: SECTIONS.loop};
  }
  fetch(SUPABASE_URL+'/rest/v1/block_saves?on_conflict=username,page',
    {method:'POST',
     headers:{'apikey':SUPABASE_KEY,'Authorization':'Bearer '+SUPABASE_KEY,
       'Content-Type':'application/json','Prefer':'resolution=merge-duplicates,return=minimal'},
     body:JSON.stringify({username:USERNAME,page:PAGE,blocks_json:JSON.stringify(state),updated_at:new Date().toISOString()})
    }).then(function(r){if(r.ok)flash('Saved!');else flash('Save failed');});}
window.saveBlocks = saveBlocks;
function loadBlocks(){
  if(!USERNAME||!PAGE||PAGE==='null'||PAGE==='undefined')return;
  fetch(SUPABASE_URL+'/rest/v1/block_saves?username=eq.'+USERNAME+'&page=eq.'+PAGE,
    {headers:{'apikey':SUPABASE_KEY,'Authorization':'Bearer '+SUPABASE_KEY}})
  .then(function(r){return r.json();})
  .then(function(data){
    if(data&&data.length>0){
      var saved=JSON.parse(data[0].blocks_json);
      if(PROGRESSION_MODE&&saved.current_step!==undefined){
        CURRENT_STEP=saved.current_step;
        STUDENT_SAVES=saved.student_saves||[];
        var allSaves={global:[],setup:[],loop:[]};
        STUDENT_SAVES.forEach(function(sv){
          allSaves.global=allSaves.global.concat(sv.global||[]);
          allSaves.setup=allSaves.setup.concat(sv.setup||[]);
          allSaves.loop=allSaves.loop.concat(sv.loop||[]);});
        buildWorkspace(CURRENT_STEP,allSaves);
        clearSelection();render();genCode();if(typeof checkStepComplete==='function')checkStepComplete();
      }else{
        SECTIONS.global=saved.global;
        SECTIONS.setup=saved.setup;
        SECTIONS.loop=saved.loop;}
      clearSelection();render();genCode();
      flash('Loaded!');}})
  .catch(function(){flash('Load failed');});}
window.saveBlocks = saveBlocks;

window.resetBlocks = function(){
  if(!confirm('Reset to original? Your saved progress will be lost.'))return;
  STUDENT_SAVES=[];CURRENT_STEP=0;
  if(CFG.mode === 'progression'){
    PROGRESSION_MODE = true;
    STEPS = CFG.steps;
    buildWorkspace(0, null);
  } else {
    SECTIONS.global = CFG.blocks ? CFG.blocks.global : [];
    SECTIONS.setup = CFG.blocks ? CFG.blocks.setup : [];
    SECTIONS.loop = CFG.blocks ? CFG.blocks.loop : [];
    genCode();
    render();
  }
  clearSelection();render();genCode();
  flash('Reset!');
};
function countPhantoms(arr){
  var n=0;
  arr.forEach(function(b){
    if(b.type==='phantom')n++;
    if(b.type==='ifblock'){n+=countPhantoms(b.ifbody);b.elseifs.forEach(function(ei){n+=countPhantoms(ei.body);});if(b.elsebody)n+=countPhantoms(b.elsebody);}
    if((b.type==='forloop'||b.type==='whileloop')&&b.body)n+=countPhantoms(b.body);
  });
  return n;}
function countIncomplete(arr){
  var n=0;
  arr.forEach(function(b){
    if(b.type==='phantom'||b.type==='phantom_resolved'||b.type==='codeblock')return;
    if(b.type==='ifblock'){
      var c=b.condition;
      if(c){if(!c.leftExpr)n++;if(!c.rightExpr)n++;
        if(c.joiner!=='none'){if(!c.leftExpr2)n++;if(!c.rightExpr2)n++;}}
      n+=countIncomplete(b.ifbody);
      b.elseifs.forEach(function(ei){
        var ec=ei.condition;
        if(ec){if(!ec.leftExpr)n++;if(!ec.rightExpr)n++;}
        n+=countIncomplete(ei.body);});
      if(b.elsebody)n+=countIncomplete(b.elsebody);
      return;}
    if(b.type==='whileloop'){
      var c=b.condition;
      if(c){if(!c.leftExpr)n++;if(!c.rightExpr)n++;}
      if(b.body)n+=countIncomplete(b.body);return;}
    if(b.type==='forloop'){
      if(b.body)n+=countIncomplete(b.body);return;}
    var def=BLOCKS[b.type];if(!def)return;
    def.inputs.forEach(function(inp,j){
      if(inp.t==='expr'){
        if(!b.exChildren||!b.exChildren[j])n++;
      }else if(inp.t==='text'||inp.t==='number'||inp.t==='vartext'){
        if(!b.params||!b.params[j]||b.params[j]==='')n++;
      }
    });
  });
  return n;}
function compareExpr(u,t){
  if(!u&&!t)return true;if(!u||!t)return false;
  if(u.type!==t.type)return false;
  if(u.type==='value'){return (u.params[0]||'').trim()===(t.params[0]||'').trim();}
  for(var i=0;i<(u.params||[]).length;i++)if((u.params[i]||'').trim()!==(t.params[i]||'').trim())return false;
  var uc=u.children||[],tc=t.children||[];
  if(uc.length!==tc.length)return false;
  for(var i=0;i<uc.length;i++)if(!compareExpr(uc[i],tc[i]))return false;
  return true;}
function compareCondition(u,t){
  if(!u&&!t)return true;if(!u||!t)return false;
  if(u.op!==t.op)return false;
  if(!compareExpr(u.leftExpr,t.leftExpr))return false;
  if(!compareExpr(u.rightExpr,t.rightExpr))return false;
  if(u.joiner!==t.joiner)return false;
  if(u.joiner!=='none'){
    if(u.op2!==t.op2)return false;
    if(!compareExpr(u.leftExpr2,t.leftExpr2))return false;
    if(!compareExpr(u.rightExpr2,t.rightExpr2))return false;
  }
  return true;}
function generateExprHint(u,t,tier){
  if(!u&&!t)return null;if(!u)return 'Missing value';
  if(u.type!==t.type)return 'Wrong type: use '+t.type;
  var def=BLOCKS[u.type];
  if(u.type==='value'){
    var uv=(u.params[0]||'').trim(),tv=(t.params[0]||'').trim();
    if(uv!==tv)return tier===3?'Value should be '+tv:'Check value';
  }
  for(var i=0;i<(u.params||[]).length;i++){
    if((u.params[i]||'').trim()!==(t.params[i]||'').trim()){
       var lbl=(def&&def.inputs[i])?def.inputs[i].l:'setting';
       return tier===3?lbl+' should be '+t.params[i]:'Check '+lbl;
    }
  }
  var uc=u.children||[],tc=t.children||[];
  if(uc.length!==tc.length)return 'Structure mismatch';
  for(var i=0;i<uc.length;i++){
    var h=generateExprHint(uc[i],tc[i],tier);
    if(h){
       var lbl=(def&&def.inputs[i])?def.inputs[i].l:'slot';
       return lbl+': '+h;
    }
  }
  return null;}
function generateCondHint(u,t,tier){
  if(!u&&!t)return null;if(!u||!t)return 'Condition missing';
  var h=generateExprHint(u.leftExpr,t.leftExpr,tier);if(h)return 'Left side: '+h;
  if(u.op!==t.op)return tier===3?'Operator should be '+t.op:'Check operator';
  h=generateExprHint(u.rightExpr,t.rightExpr,tier);if(h)return 'Right side: '+h;
  if(t.joiner!=='none'){
    if(u.joiner!==t.joiner)return 'Check joiner (and/or)';
    h=generateExprHint(u.leftExpr2,t.leftExpr2,tier);if(h)return '2nd Left: '+h;
    if(u.op2!==t.op2)return tier===3?'2nd Op should be '+t.op2:'Check 2nd operator';
    h=generateExprHint(u.rightExpr2,t.rightExpr2,tier);if(h)return '2nd Right: '+h;
  }
  return null;}
function generateHint(u,t,tier){
  if(tier<2)return '';
  if(u.type!==t.expects)return 'Wrong block. Should be '+t.expects;
  var def=BLOCKS[u.type];
  if(!def)return '';
  for(var i=0;i<(t.params||[]).length;i++){
    if(!def.inputs[i])continue;
    var up=u.params[i]||'',tp=t.params[i]||'';
    if(up.trim()!==tp.trim()){
      var lbl=(def&&def.inputs[i])?def.inputs[i].l:'field';
      return tier===3?'Check '+lbl+': expected "'+tp+'"':'Check '+lbl;
    }
  }
  if(t.expects==='ifblock'||t.expects==='whileloop'){
    var h=generateCondHint(u.condition,t.condition,tier);if(h)return h;
  }
  if(t.expects==='forloop'){
    if((u.forinit||'')!==(t.forinit||''))return tier===3?'Init: '+t.forinit:'Check init';
    if((u.forcond||'')!==(t.forcond||''))return tier===3?'Cond: '+t.forcond:'Check condition';
    if((u.forincr||'')!==(t.forincr||''))return tier===3?'Incr: '+t.forincr:'Check increment';
  }
  var uex=u.exChildren||[],tex=t.exChildren||[];
  for(var i=0;i<tex.length;i++){
    var h=generateExprHint(uex[i],tex[i],tier);
    if(h){
       var lbl=(def&&def.inputs[i])?def.inputs[i].l:'slot';
       return lbl+': '+h;
    }
  }
  return '';}
function collectBadIds(uList,tList,tier,badIds){
  if(!uList||!tList)return;
  uList.forEach(function(ub,i){
    var tb=tList[i];if(!tb)return;
    if(tb.type==='phantom'){
      if(!compareBlock(ub,tb))badIds.push({id:ub.id,hint:generateHint(ub,tb,tier)});
      var tc=null;
      if(tb.expects==='ifblock')tc={ifbody:tb.ifbody,elseifs:tb.elseifs,elsebody:tb.elsebody};
      else if(tb.expects==='forloop'||tb.expects==='whileloop')tc={body:tb.body};
      if(tc){
        if(ub.type==='ifblock'){collectBadIds(ub.ifbody,tc.ifbody,tier,badIds);
          if(ub.elseifs&&tc.elseifs)ub.elseifs.forEach(function(ei,k){if(tc.elseifs[k])collectBadIds(ei.body,tc.elseifs[k].body,tier,badIds);});
          if(ub.elsebody&&tc.elsebody)collectBadIds(ub.elsebody,tc.elsebody,tier,badIds);}
        else if(ub.type==='forloop'||ub.type==='whileloop'){collectBadIds(ub.body,tc.body,tier,badIds);}
      }
    }
  });}
function compareBlock(u,t){
  if(!u)return false;
  if(t.type==='phantom'){
    if(u.type!==t.expects)return false;
    if(t.expects==='ifblock'||t.expects==='whileloop'){
       if(!compareCondition(u.condition,t.condition))return false;
    }
    if(t.expects==='forloop'){
       if((u.forinit||'')!==(t.forinit||''))return false;
       if((u.forcond||'')!==(t.forcond||''))return false;
       if((u.forincr||'')!==(t.forincr||''))return false;
    }
    for(var i=0;i<(t.params||[]).length;i++){
       var up=u.params[i]||'',tp=t.params[i]||'';
       if(up.trim()!==tp.trim())return false;
    }
    var uex=u.exChildren||[],tex=t.exChildren||[];
    for(var i=0;i<tex.length;i++){
       if(!compareExpr(uex[i],tex[i]))return false;
    }
    return true;
  }
  return true;}
function validateStep(){
  if(!STEPS||!STEPS[CURRENT_STEP])return true;
  var tmpl=STEPS[CURRENT_STEP];
  var valid=true;var tier=1;if(CHECK_FAIL_COUNT>=2)tier=2;if(CHECK_FAIL_COUNT>=4)tier=3;
  var badIds=[];
  ['global','setup','loop'].forEach(function(sec){
    var uArr=SECTIONS[sec],tArr=tmpl[sec];
    collectBadIds(uArr,tArr,tier,badIds);
  });
  if(badIds.length>0)valid=false;
  document.querySelectorAll('.ws-block,.if-block,.for-block,.while-block').forEach(function(el){el.classList.remove('error-block');});
  document.querySelectorAll('.block-hint').forEach(function(el){el.remove();});
  if(!valid){
    CHECK_FAIL_COUNT++;
    badIds.forEach(function(bid){
      var el=document.querySelector('[data-id="'+bid.id+'"]');
      if(el){
        el.classList.add('error-block');
        if(bid.hint){var hd=document.createElement('div');hd.className='block-hint';hd.textContent=bid.hint;el.appendChild(hd);}
      }
    });
  }
  return valid;}
function checkSketchFields(uList, mList, badIds, path = [], section = ''){
  if(!uList||!mList)return;
  for(var i=0;i<uList.length&&i<mList.length;i++){
    var ub=uList[i],mb=mList[i];
    if(!ub||!mb)continue;
    if(ub.type!==mb.type)continue;
    var bad=false;
    if(mb.params){
      for(var j=0;j<mb.params.length;j++){
        var mv=mb.params[j],uv=(ub.params&&ub.params[j]!==undefined)?ub.params[j]:'';
        if(typeof mv==='string'&&mv.trim()!==''&&(!uv||(typeof uv==='string'&&uv.trim()===''))){
          badIds.push({id: ub.id, section: section, path: path.concat([i]), hint: 'Fill in all the fields for this block'});
          bad=true;break;}}}
    if(!bad&&mb.exChildren){
      for(var j=0;j<mb.exChildren.length;j++){
        var me=mb.exChildren[j],ue=ub.exChildren?ub.exChildren[j]:null;
        if(me&&me.params&&me.params[0]&&me.params[0].trim()!==''&&(!ue||!ue.params||!ue.params[0]||ue.params[0].trim()==='')){
          badIds.push({id: ub.id, section: section, path: path.concat([i]), hint: 'Fill in all the fields for this block'});
          bad=true;break;}}}
    if(ub.type==='ifblock'){
      checkSketchFields(ub.ifbody, mb.ifbody, badIds, path.concat([i, 'ifbody']), section);
      if(ub.elseifs && mb.elseifs) {
        ub.elseifs.forEach(function(ei, k) {
          if(mb.elseifs[k]) checkSketchFields(ei.body, mb.elseifs[k].body, badIds, path.concat([i, 'elseifs', k, 'body']), section);
        });
      }
      if(mb.elsebody)checkSketchFields(ub.elsebody||[], mb.elsebody, badIds, path.concat([i, 'elsebody']), section);
    }else if(ub.type==='forloop'||ub.type==='whileloop'){
      checkSketchFields(ub.body, mb.body, badIds, path.concat([i, 'body']), section);}}}
function applySketchHighlights(){
  document.querySelectorAll('.ws-block,.if-block,.for-block,.while-block').forEach(function(el){el.classList.remove('error-block');});
  document.querySelectorAll('.block-hint').forEach(function(el){el.remove();});
  if (SKETCH_ERROR_PATHS.length > 0) {
    var sb = document.getElementById('statusbar');
    if(sb) { sb.style.transition='background 0.2s'; sb.style.background='#ffebe9'; setTimeout(function(){sb.style.background='';}, 400); }
  }
  SKETCH_ERROR_PATHS.forEach(function(entry){
    var res = SECTIONS[entry.section];
    if(!res) return;
    for(var i=0; i<entry.path.length; i++){
      res = res[entry.path[i]];
      if(!res) break;
    }
    if(res && res.id){
      var el = document.querySelector('[data-id="'+res.id+'"]');
      if(el){
        el.classList.add('error-block');
        if(entry.hint){
          var hd=document.createElement('div');hd.className='block-hint';hd.textContent=entry.hint;
          var target = el.querySelector('.if-header, .for-header, .while-header') || el;
          target.appendChild(hd);
        }
      }
    }
  });
}
function validateSketch(){
  console.log('[DEBUG] validateSketch() invoked.');
  if(!MASTER_SKETCH)return {valid:true};
  var badIds=[];
  ['global','setup','loop'].forEach(function(sec){
    checkSketchFields(SECTIONS[sec], MASTER_SKETCH[sec], badIds, [], sec);
  });
  SKETCH_ERROR_PATHS=badIds;
  applySketchHighlights();
  return {valid: badIds.length===0, errorCount: badIds.length, errors: badIds};}
window.validateSketch = validateSketch;
window.dumpDebug = function() {
  console.log('--- BLOCK BUILDER DEBUG DUMP ---');
  console.log('MASTER_SKETCH:', MASTER_SKETCH);
  console.log('SECTIONS:', SECTIONS);
  console.log('SKETCH_ERROR_PATHS:', SKETCH_ERROR_PATHS);
  console.log('--------------------------------');
};
function checkStepComplete(){
  if(!PROGRESSION_MODE)return;
  var phantoms=countPhantoms(SECTIONS.global)+countPhantoms(SECTIONS.setup)+countPhantoms(SECTIONS.loop);
  var incomplete=countIncomplete(SECTIONS.global)+countIncomplete(SECTIONS.setup)+countIncomplete(SECTIONS.loop);
  var total=phantoms+incomplete;
  var btn=document.getElementById('nextbtn');
  var curGuidance = STEPS&&STEPS[CURRENT_STEP]?STEPS[CURRENT_STEP].guidance:'guided';
  if(curGuidance==='free'){
    btn.classList.add('ready');
    btn.classList.remove('check-mode');
    btn.textContent='Next Step \u2192';
    btn.classList.add('next-mode');
    btn.style.display='';
    return;
  }
  if(btn.classList.contains('next-mode'))return;
  if(btn.classList.contains('check-mode')){
     if(total>0){btn.classList.remove('ready');btn.textContent='Complete Step';btn.classList.remove('check-mode');}
     return;
  }
  var prog=document.getElementById('step-progress');
  if(prog){
    if(phantoms>0)prog.textContent=phantoms+' block'+(phantoms===1?'':'s')+' to place';
    else if(incomplete>0)prog.textContent=incomplete+' field'+(incomplete===1?'':'s')+' to fill';
    else prog.textContent='complete';}
  if(total===0){btn.classList.add('ready');btn.textContent='Check Code';btn.classList.add('check-mode');}
  else{btn.classList.remove('ready');btn.textContent='Complete Step';btn.classList.remove('check-mode');}}
function buildWorkspace(stepIdx,saves){
  if(!PROGRESSION_MODE||!STEPS||stepIdx>=STEPS.length)return;
  var step=STEPS[stepIdx];
  function mergeSaved(templateArr,savedArr){
    if(!savedArr||!savedArr.length)return templateArr.slice();
    var STRUCTURAL=['ifblock','forloop','whileloop'];
    var out=[];
    var si=0;
    templateArr.forEach(function(b){
      if(b.type==='phantom_resolved'){
        if(si<savedArr.length){
          var sb=savedArr[si];
          var code=genBlock(sb,0).trim();
          out.push({id:sb.id,type:'codeblock',params:[code]});
          si++;}
      }else{out.push(b);}
    });
    return out;
  }
  var savedG=saves?saves.global:null;
  var savedS=saves?saves.setup:null;
  var savedL=saves?saves.loop:null;
  SECTIONS.global=mergeSaved(step.global,savedG);
  SECTIONS.setup=mergeSaved(step.setup,savedS);
  SECTIONS.loop=mergeSaved(step.loop,savedL);
  PALETTE_ALLOWED = (step.palette !== undefined && step.palette !== null) ? step.palette : null;
  var lbl=document.getElementById('step-label');
  var bar=document.getElementById('step-bar');
  if(lbl)lbl.textContent=step.label;
  if(bar)bar.style.display='flex';
  window.CURRENT_STEP_META = {guidance: step.guidance, view: step.view};
  window.dispatchEvent(new CustomEvent('stepchange', {detail: window.CURRENT_STEP_META}));
  var activeId='ls';
  if(step.active==='global')activeId='gs';
  else if(step.active==='setup')activeId='ss';
  expandSection(activeId);
  var nbtn=document.getElementById('nextbtn');
  if(nbtn){nbtn.classList.remove('next-mode');nbtn.classList.remove('check-mode');nbtn.classList.remove('ready');}
  if(nbtn){nbtn.classList.remove('next-mode');nbtn.classList.remove('check-mode');nbtn.classList.remove('ready');}
  if(nbtn)nbtn.style.display=(step.guidance==='open'||stepIdx>=STEPS.length-1)?'none':'';
  var pbtn=document.getElementById('prevbtn');
  if(pbtn)pbtn.style.display=stepIdx>0?'':'none';
  if(window.updateDrawer) window.updateDrawer(stepIdx);
  checkStepComplete();}
document.getElementById('nextbtn').addEventListener('click',function(){
  if(!document.getElementById('nextbtn').classList.contains('ready'))return;
  var btn=document.getElementById('nextbtn');
  var meta=window.CURRENT_STEP_META || {};
  if(btn.classList.contains('check-mode')){
    if(meta.view==='editor'){
      btn.textContent='Compiling...'; btn.disabled=true;
      var code=window.getEditorCode?window.getEditorCode():'';
      fetch('http://127.0.0.1:3210/compile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:code})})
      .then(function(r){return r.json();})
      .then(function(data){
        btn.disabled=false;
        if(data.success){
          btn.textContent='Next Step \u2192'; btn.classList.remove('check-mode'); btn.classList.add('next-mode'); flash('Correct!');
        }else{
          btn.textContent='Check Code'; flash('Compile failed: '+(data.message||'check your code syntax'));
        }
      }).catch(function(){ btn.disabled=false; btn.textContent='Check Code'; flash('Compiler Agent offline'); });
      return;
    }
    if(validateStep()){
      btn.textContent='Next Step \u2192';
      btn.classList.remove('check-mode');
      btn.classList.add('next-mode');
      flash('Correct!');
      CHECK_FAIL_COUNT=0;
    }else{
      flash('Incorrect - check highlighted blocks');
    }
    return;
  }
  try{
    var STRUCTURAL=['ifblock','forloop','whileloop'];
    var saves={global:SECTIONS.global.filter(function(b){return b.type!=='phantom'&&b.type!=='phantom_resolved';}),
               setup:SECTIONS.setup.filter(function(b){return b.type!=='phantom'&&b.type!=='phantom_resolved';}),
               loop:SECTIONS.loop.filter(function(b){return b.type!=='phantom'&&b.type!=='phantom_resolved';}) };
    STUDENT_SAVES.push(JSON.parse(JSON.stringify(saves)));
    CURRENT_STEP++;
    flash('advancing to step '+CURRENT_STEP);
    var allSaves={global:[],setup:[],loop:[]};
    STUDENT_SAVES.forEach(function(sv){
      allSaves.global=allSaves.global.concat(sv.global||[]);
      allSaves.setup=allSaves.setup.concat(sv.setup||[]);
      allSaves.loop=allSaves.loop.concat(sv.loop||[]);
    });
    buildWorkspace(CURRENT_STEP,allSaves);
    flash('built step '+CURRENT_STEP);
    clearSelection();render();genCode();
    flash('Step '+(CURRENT_STEP+1)+'!');
    saveBlocks();
    if(window.openDrawer) window.openDrawer();
  }catch(e){flash('ERR: '+e.message);console.error(e);}});
document.getElementById('nextbtn').addEventListener('click', function(){
  // ... your existing nextbtn code - that part is fine
});

document.getElementById('prevbtn').addEventListener('click', function(){
  if(!PROGRESSION_MODE || CURRENT_STEP <= 0) return;
  if(!confirm('Go back to previous step? Your progress on the current step will be discarded.')) return;
  CURRENT_STEP--;
  STUDENT_SAVES.pop();
  var allSaves = {global:[], setup:[], loop:[]};
  STUDENT_SAVES.forEach(function(sv){
    allSaves.global = allSaves.global.concat(sv.global);
    allSaves.setup = allSaves.setup.concat(sv.setup);
    allSaves.loop = allSaves.loop.concat(sv.loop);
  });
  buildWorkspace(CURRENT_STEP, allSaves);
  flash('Returned to step ' + CURRENT_STEP);
  clearSelection(); render(); genCode();
});

if(CFG.is_overlay){
  window.addEventListener('message', function(e){
    if(e.data && e.data.type === 'bb_save_request'){
      saveBlocks();
      setTimeout(function(){ window.parent.postMessage({type:'bb_close'}, '*'); }, 600);
    }
  });
}



if(CFG.mode === 'progression'){
  PROGRESSION_MODE = true;
  STEPS = CFG.steps;
  CURRENT_STEP = 0;
  CHECK_FAIL_COUNT = 0;
  STUDENT_SAVES = [];
  buildWorkspace(0, null);
} else {
  SECTIONS.global = CFG.blocks ? CFG.blocks.global : [];
  SECTIONS.setup = CFG.blocks ? CFG.blocks.setup : [];
  SECTIONS.loop = CFG.blocks ? CFG.blocks.loop : [];
  genCode();
  render();
}
if(USERNAME){ loadBlocks(); }
updatePalette();
render();
if(PROGRESSION_MODE) checkStepComplete();

})();