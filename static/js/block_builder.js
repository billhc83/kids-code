(function(){
console.log("[DEBUG] block_builder.js: Execution started.");
var CFG = window.BB_CONFIG;
if(!CFG) { console.error("[DEBUG] block_builder.js: BB_CONFIG is missing!"); return; }
console.log("[DEBUG] block_builder.js: Config loaded.", CFG.mode);
console.log("[DEBUG] block_builder.js: About to declare variables.");
var USERNAME = CFG.username;
var PAGE = CFG.page;
var MASTER_SKETCH = CFG.master || null;
var SUPABASE_URL = CFG.supabase_url;
var SUPABASE_KEY = CFG.supabase_key;
var DEFAULT_VIEW = CFG.default_view;
var LOCK_VIEW = CFG.lock_view;
var READONLY_MODE = CFG.readonly_mode;
var LOCK_MODE = CFG.lock_mode;

var nextBtnState = { ready: false, mode: '', text: 'Complete Step', visible: false, prevVisible: false };
var stepLabel = 'Step';
var stepProgress = '';

var UNO_DIGITAL_PINS=['0','1','2','3','4','5','6','7','8','9','10','11','12','13'];
var UNO_ANALOG_PINS=['A0','A1','A2','A3','A4','A5'];
var UNO_DIGITAL_IO_PINS=UNO_DIGITAL_PINS.concat(UNO_ANALOG_PINS);
var UNO_PWM_PINS=['3','5','6','9','10','11'];
var BLOCKS = {
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
  inputs:[{t:'expr',l:'Value',fallback:'"Hello"'},{t:'sel',l:'Mode',o:['println','print']}],
  defaults:[{type:'value',params:['"Hello"'],children:[]},null],
  genStmt:function(p,ex){var fn=p[1]==='print'?'Serial.print':'Serial.println';
    return fn+'('+genExpr(ex&&ex[0],null,'"Hello"')+');';}},
serialreadstring:{allowed:[],asStatement:false,asExpr:true,
  inputs:[],
  genExpr:function(p){return 'Serial.readString()';}},
serialavailable:{allowed:[],asStatement:false,asExpr:true, // Added this block type
  inputs:[],
  genExpr:function(p){return 'Serial.available()';}},
codeblock:{allowed:['global','setup','loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[{t:'text',l:'Code'}],
  genStmt:function(p){return (p[0]||'');}},
ifblock:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[],genStmt:function(){return '';}},
forloop:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[],genStmt:function(){return '';}},
whileloop:{allowed:['loop','if','for','while'],asStatement:true,asExpr:false,
  inputs:[],genStmt:function(){return '';}},
};
console.log("[DEBUG] checkpoint 2");
var B = BLOCKS;
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
    exprSel={block:block,slotIdx:slotIdx};
    document.getElementById('statusbar').innerHTML='<span style="color:#9a6700">click an expression block to snap it in</span>';
    updatePalette();
    render();});
  wrap.appendChild(slot);return wrap;}
  console.log("[DEBUG] checkpoint 3");
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
            exprSel=null;updatePalette();render();return;} // Clear selection if already active
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
      es.addEventListener('change',function(e){e.stopPropagation();exNode.params[ji]=e.target.value;window.genCode();});
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
                ei.value=v;capturedExNodeVt.params[capturedJiVt]=v;window.genCode();
                closeDrop();});
              drop.appendChild(item);});
          }
          wrap.appendChild(drop);
        }
        ei.addEventListener('click',function(e){e.stopPropagation();openDrop('');});
        ei.addEventListener('focus',function(e){openDrop('');});
        ei.addEventListener('input',function(e){
          e.stopPropagation();
          capturedExNodeVt.params[capturedJiVt]=e.target.value;window.genCode();
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
      ei.addEventListener('input',function(e){e.stopPropagation();exNode.params[ji]=e.target.value;window.genCode();});
      chip.appendChild(ei);
    }});
  if(onRemove){
    var rx=document.createElement('span');rx.className='expr-remove';rx.textContent='x';
    rx.title='Remove expression';
    rx.addEventListener('click',function(e){e.stopPropagation();onRemove();});chip.appendChild(rx);}
  return chip;}
  console.log("[DEBUG] checkpoint 4");
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
var activePhantoml=null; // Now points to a slot object {arr, idx, slot}
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
  var step=PROGRESSION_MODE&&STEPS?STEPS[CURRENT_STEP]:null;
  var config=step?step.config:{structure:'none',filter:false,validation:'none',fill:true}; // Default fill:true

  if(exprSel){
    activePhantoml=null;
    ctx.className='has-expr';
    ctx.textContent=exprSel.isSubSlot?'fill sub-slot:':(exprSel.exSlot ? 'fill value slot: ' + exprSel.exSlot.phantom_meta.hint : 'fill value slot:');
    blockSec.style.display='none';
    exprTitle.style.display='';
    var expectedType=null;
    // Only restrict types if we are in a guided (partial) structure mode.
    // In free mode (structure: "none"), the palette should show everything even if the phantom has a specific type expectation.
    if(config.structure === 'partial'){
      if(exprSel.condObj){
        var ec=exprSel.condObj._expectedCond;
        if(ec){
          var sideKey=exprSel.side==='leftExpr'?'left':exprSel.side==='rightExpr'?'right':exprSel.side==='leftExpr2'?'left2':'right2';
          expectedType=ec[sideKey]||null;
        }
      }else if(exprSel.exSlot && exprSel.exSlot.phantom_meta && exprSel.exSlot.phantom_meta.expectedExTypes){
        // If it's a persistent expression slot, use its phantom_meta
        expectedType = exprSel.exSlot.phantom_meta.expectedExTypes[exprSel.slotIdx] || null;
      }else if(!exprSel.isSubSlot&&exprSel.block&&exprSel.block._expectedExpr){
        expectedType=exprSel.block._expectedExpr[exprSel.slotIdx]||null;}
    }
    exprSec.querySelectorAll('.block-btn').forEach(function(btn){
      var bType = btn.getAttribute('data-type');
      var visible = true;
      if(expectedType && bType !== expectedType) visible = false;
      if(visible && config.filter && PALETTE_ALLOWED !== null && PALETTE_ALLOWED.indexOf(bType) === -1) visible = false;
      btn.classList[visible ? 'remove' : 'add']('hidden');
    });
    return;
  }
  if(activePhantoml){
    var ph=activePhantoml.slot.phantom_meta; // Get phantom_meta from the slot
    var isPartial=config.structure==='partial';
    ctx.className='has-sel';
    ctx.textContent='place: '+ph.hint;
    blockSec.style.display='flex';
    exprTitle.style.display='';
    blockSec.querySelectorAll('.block-btn').forEach(function(btn){
      var type=btn.getAttribute('data-type');
      if(ph.expects){
        btn.classList[type===ph.expects?'remove':'add']('hidden');
      }else if(!isPartial){
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
    if(ok && config.filter && PALETTE_ALLOWED!==null) ok=PALETTE_ALLOWED.indexOf(type)!==-1;
    if(ok){btn.classList.remove('hidden');}else{btn.classList.add('hidden');}});
  exprSec.querySelectorAll('.block-btn').forEach(function(btn){btn.classList.add('hidden');});}
  console.log("[DEBUG] checkpoint 5");
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
    var step=PROGRESSION_MODE&&STEPS?STEPS[CURRENT_STEP]:null;
    var config=step?step.config:{structure:'none'};

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
      var arr=activePhantoml.arr;
      var idx=activePhantoml.idx;
      var slot = activePhantoml.slot; // This is the slot object
      var ph = slot.phantom_meta; // Get phantom metadata from the slot
      var newBlock;
      var step = PROGRESSION_MODE && STEPS ? STEPS[CURRENT_STEP] : null;
      var config = step ? step.config : { structure: 'none', fill: true };
      var isPartial = config.structure === 'partial'; // This is still used for general guidance logic
      var isMatchingPhantom = ph && type === ph.expects;

      if(type==='ifblock'){
        var cond={leftExpr:null,op:'==',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null};
        if(ph.condition && (isPartial || (isMatchingPhantom && config.fill === false))){
          cond.op=ph.condition.op||'==';
          cond.joiner=ph.condition.joiner||'none';
          cond.op2=ph.condition.op2||'==';
          cond._expectedCond = ph.expectedCondTypes || {
            left:ph.condition.leftExpr?ph.condition.leftExpr.type:null,
            right:ph.condition.rightExpr?ph.condition.rightExpr.type:null,
            left2:ph.condition.leftExpr2?ph.condition.leftExpr2.type:null,
            right2:ph.condition.rightExpr2?ph.condition.rightExpr2.type:null
          };
        }
        var ib=isPartial&&ph.ifbody?JSON.parse(JSON.stringify(ph.ifbody)):[];
        var eifs=isPartial&&ph.elseifs?JSON.parse(JSON.stringify(ph.elseifs)):[];
        var eb=isPartial&&ph.elsebody?JSON.parse(JSON.stringify(ph.elsebody)):null;
        newBlock={id:(Date.now()+Math.random()).toString(),type:'ifblock',
          condition:cond,ifbody:ib,elseifs:eifs,elsebody:eb};
      }else if(type==='forloop'){
        var ib=isPartial&&ph.body?JSON.parse(JSON.stringify(ph.body)):[];
        var fi=isPartial?(ph.forinit||'int i = 0'):'int i = 0';
        var fc=isPartial?(ph.forcond||'i < 10'):'i < 10';
        var fr=isPartial?(ph.forincr||'i++'):'i++';
        newBlock={id:(Date.now()+Math.random()).toString(),type:'forloop',forinit:fi,forcond:fc,forincr:fr,body:ib};
      }else if(type==='whileloop'){
        var wcond={leftExpr:null,op:'!=',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null};
        if(ph.condition && (isPartial || (isMatchingPhantom && config.fill === false))){
          wcond.op=ph.condition.op||'!=';
          wcond._expectedCond = ph.expectedCondTypes || {
            left:ph.condition.leftExpr?ph.condition.leftExpr.type:null,
            right:ph.condition.rightExpr?ph.condition.rightExpr.type:null
          };
        }
        var wb=isPartial&&ph.body?JSON.parse(JSON.stringify(ph.body)):[];
        newBlock={id:(Date.now()+Math.random()).toString(),type:'whileloop',condition:wcond,body:wb};
      }else{
        // Use phantom data if it matches the type, otherwise fall back to defaults vs empty slots
        var params = (isMatchingPhantom && ph.params) 
          ? JSON.parse(JSON.stringify(ph.params))
          : def.inputs.map(function(inp){
              if(inp.t==='sel'){var f=inp.o[0];return typeof f==='object'?f.v:f;}return '';
            });

        var exch;
        if (isMatchingPhantom && ph.exChildren) {
          exch = JSON.parse(JSON.stringify(ph.exChildren));
        } else {
          exch = (isPartial || config.fill === false)
            ? def.inputs.map(function(inp){ return inp.t === 'expr' ? null : undefined; })
            : (def.defaults ? def.defaults.map(function(d){return d ? JSON.parse(JSON.stringify(d)) : null;}) : []) || [];
        }
        
        var expectedExpr = (isPartial || isMatchingPhantom) ? (ph.expectedExTypes || (ph.exChildren ? ph.exChildren.map(function(e){return e?e.type:null;}) : null)) : null;

        newBlock={id:(Date.now()+Math.random()).toString(),type:type,params:params,exChildren:exch};
        if(expectedExpr)newBlock._expectedExpr=expectedExpr;
      }
      slot.content = newBlock; // Assign newBlock to the slot's content
      activePhantoml = null;
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
    console.log("[DEBUG] checkpoint 6");
function render(){
  console.log('render called', new Error().stack);
  var anc=collectAncestorArrays();
  renderSection('gs','global',anc);renderSection('ss','setup',anc);renderSection('ls','loop',anc);
  // Apply global readonly mode to inputs and action buttons
  ['gs','ss','ls'].forEach(function(id){
    var el=document.getElementById(id);
    var sn=id==='gs'?'global':id==='ss'?'setup':'loop';
    var base='section s-'+(id==='gs'?'global':id==='ss'?'setup':'loop');
    var isExpanded=el.classList.contains('expanded');
    el.className=(sel&&sel.targetArr===SECTIONS[sn])?base+' active':base;
    // Toggle readonly class for sections if global READONLY_MODE is active
    if(isExpanded)el.classList.add('expanded');});
  if(typeof genCode === 'function') genCode();
  if(typeof applySketchHighlights === 'function') applySketchHighlights();
  if (typeof READONLY_MODE !== 'undefined' && READONLY_MODE) {
    document.querySelectorAll('.blk-input,.cond-input,.vartext-input,.cond-select,.cond-joiner').forEach(function(el) {
      el.setAttribute('disabled', true);
    });
    document.querySelectorAll('.act').forEach(function(el) {
      el.style.display = 'none'; // Hide action buttons
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
    var block = arr[i];
    if (block.type === 'slot' && block.content) { // If it's a filled slot, check its content
      block = block.content;
    } else if (block.type === 'slot' && block.content === null) { // Empty slots don't affect depth
      continue;
    }
    if(block.type!=='codeblock')continue; // Only codeblocks affect brace depth
    var c=(block.params[0]||'').trim();
    if(c.charAt(c.length-1)==='{')depth++;
    if(c==='}'||c.match(/^\}/))depth=Math.max(0,depth-1); // Ensure depth doesn't go negative
  }
  return depth;
}
console.log("[DEBUG] checkpoint 7");
function renderSection(elId,sName,anc){
  var body=document.getElementById(elId+'-body');
  body.querySelectorAll('.ws-block,.if-block').forEach(function(e){e.remove();});
  SECTIONS[sName].forEach(function(block,idx){body.appendChild(renderBlock(block,idx,SECTIONS[sName],sName,sName,anc));});}
function renderBlock(block,idx,parentArr,section,pathStr,anc){
  if(block.type==='ifblock')return renderIfBlock(block,idx,parentArr,section,pathStr,anc);
  if(block.type==='forloop')return renderForBlock(block,idx,parentArr,section,pathStr,anc);
  if(block.type==='whileloop')return renderWhileBlock(block,idx,parentArr,section,pathStr,anc);
  if(block.type==='slot')return renderSlot(block,idx,parentArr,section,pathStr,anc); // Handle new slot type
  return renderActionBlock(block,idx,parentArr);}

// New function to render a slot (which can be empty or filled)
function renderSlot(slot, idx, parentArr, section, pathStr, anc) {
  if (slot.content === null) {
    // Render the phantom placeholder if the slot is empty
    var d=document.createElement('div');
    d.className='ws-block phantom-block';
    var depth=braceDepth(parentArr,idx); // braceDepth needs to handle slots
    if(depth>0)d.style.marginLeft=(depth*18)+'px';

    var isActive=activePhantoml&&activePhantoml.slot===slot; // Check if this slot is active
    if(isActive)d.classList.add('active');

    var icon=document.createElement('span');icon.className='phantom-icon';icon.textContent='+';
    var hint=document.createElement('span');hint.className='phantom-hint';hint.textContent=slot.phantom_meta.hint||'Place a block here';
    var exp=document.createElement('span');exp.className='phantom-expects';exp.textContent=slot.phantom_meta.expects||'';
    d.appendChild(icon);d.appendChild(hint);d.appendChild(exp);

    d.addEventListener('click',function(e){
      e.stopPropagation();
      if(activePhantoml&&activePhantoml.slot===slot){
        activePhantoml=null;
      }else{
        activePhantoml={arr:parentArr, idx:idx, slot:slot}; // activePhantoml now points to the slot
        sel=null;exprSel=null;
      }
      updatePalette();render();
    });
    return d;
  } else {
    // Render the actual block inside the slot
    return renderBlock(slot.content, idx, parentArr, section, pathStr, anc);
  }
}

// renderPhantomBlock and renderPhantomResolved are removed.
// The logic for phantom rendering is now inside renderSlot when slot.content is null.

function renderActionBlock(block,idx,parentArr){
  var d=document.createElement('div');
  var def=B[block.type];
  d.className='ws-block';
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
      bt.addEventListener('click',function(e){e.stopPropagation();fn();});return bt;} // mkb2 for codeblocks
    d.appendChild(mkb2('\u2191',function(){if(idx>0){var t=parentArr[idx-1];parentArr[idx-1]=parentArr[idx];parentArr[idx]=t;render();}}));
    d.appendChild(mkb2('\u2193',function(){if(idx<parentArr.length-1){var t=parentArr[idx+1];parentArr[idx+1]=parentArr[idx];parentArr[idx]=t;render();}}));
    d.appendChild(mkb2('\u00D7',function(){parentArr.splice(idx,1);render();}));
    // For codeblocks, deletion is always removal from array
    return d;}
  var nm=document.createElement('span');nm.className='blk-name';nm.textContent=block.type;d.appendChild(nm);
  var bdepth=braceDepth(parentArr,idx);if(bdepth>0)d.style.marginLeft=(bdepth*18)+'px';

  // Find the actual parent array for deletion, considering slots
  var actualParentArr = parentArr;
  var actualIdx = idx;

  def.inputs.forEach(function(inp,j){ // Loop through inputs for regular blocks
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
                ei.value=v;block.params[capturedJ]=v;window.genCode();
                closeDrop();});
              drop.appendChild(item);});
          }
          wrap.appendChild(drop);}
        ei.addEventListener('click',function(e){e.stopPropagation();openDrop('');});
        ei.addEventListener('focus',function(){openDrop('');});
        ei.addEventListener('input',function(e){
          e.stopPropagation();
          block.params[capturedJ]=e.target.value;window.genCode();
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
    el.addEventListener('input',function(e){e.stopPropagation();block.params[j]=e.target.value;window.genCode();
      if(block.type==='increment'&&inp.l==='Op'){
        var byF=d.querySelector('.by-field');
        if(byF)byF.style.display=(e.target.value==='++'||e.target.value==='--')?'none':'';}});
    if(block.type==='increment'&&inp.l==='By')f.className+=' by-field';
    f.appendChild(el);d.appendChild(f);});
  function mkb(ic,fn){var bt=document.createElement('button');bt.className='act';bt.textContent=ic;
    bt.addEventListener('click',function(e){e.stopPropagation();fn(actualParentArr, actualIdx);});return bt;} // mkb for regular blocks

  // Only add move/delete buttons if not in READONLY_MODE and not a locked codeblock
  var isLockedCodeblock = block.type === 'codeblock' && block.locked;
  if (!(typeof READONLY_MODE !== 'undefined' && READONLY_MODE) && !isLockedCodeblock) {
    // Up/Down buttons
    d.appendChild(mkb('\u2191',function(arr, i){if(i>0){var t=arr[i-1];arr[i-1]=arr[i];arr[i]=t;render();}}, parentArr, idx));
    d.appendChild(mkb('\u2193',function(arr, i){if(i<arr.length-1){var t=arr[i+1];arr[i+1]=arr[i];arr[i]=t;render();}}, parentArr, idx));
    d.appendChild(mkb('\u00D7',function(arr, i){
      if (arr[i].type === 'slot') {
        arr[i].content = null; // Clear the slot's content
      } else {
        arr.splice(i,1); // Otherwise, remove the block from the array
      }
      render();
    }, parentArr, idx));
  }
  return d;}
  console.log("[DEBUG] checkpoint 8");
function renderIfBlock(block,idx,parentArr,section,parentPathStr,anc){
  var wrap=document.createElement('div');
  wrap.className='if-block'+(anc.indexOf(block.id)!==-1?' ancestor':'');
  wrap.setAttribute('data-id', block.id);
  var hdr=document.createElement('div');hdr.className='if-header';
  hdr.appendChild(kw('if ('));appendCondFields(hdr,block.condition);hdr.appendChild(kw(')'));
  // Only add 'else if' and 'else' buttons if not in READONLY_MODE
  if (!(typeof READONLY_MODE !== 'undefined' && READONLY_MODE)) {
    hdr.appendChild(mkact('+ else if',function(){
      block.elseifs.push({condition:{leftExpr:null,op:'==',rightExpr:null,joiner:'none',leftExpr2:null,op2:'==',rightExpr2:null},body:[]});render();}));
    if(block.elsebody===null)hdr.appendChild(mkact('+ else',function(){block.elsebody=[];render();}));
    hdr.appendChild(mkact('\u00D7',function(){
      if (parentArr[idx] && parentArr[idx].type === 'slot') {
        parentArr[idx].content = null;
    } else {
      parentArr.splice(idx,1);
    }
    if(sel&&(sel.targetArr===block.ifbody||isDescendant(block,sel.targetArr)))clearSelection();else render();}));
  wrap.appendChild(hdr);
  var ifPathStr=parentPathStr+' \u2192 if';
  var isOnlyBody=block.elseifs.length===0&&block.elsebody===null;
  wrap.appendChild(makeBodyZone(block.ifbody,section,ifPathStr,isOnlyBody,anc));
  block.elseifs.forEach(function(ei,eiIdx){
    var eiHdr=document.createElement('div');eiHdr.className='elseif-header';
    eiHdr.appendChild(kw('else if ('));appendCondFields(eiHdr,ei.condition);eiHdr.appendChild(kw(')')); // Cond fields for else if
    if (!(typeof READONLY_MODE !== 'undefined' && READONLY_MODE)) {
      eiHdr.appendChild(mkact('\u00D7',function(){block.elseifs.splice(eiIdx,1);render();}));
    }
    wrap.appendChild(eiHdr);
    var eiPathStr=parentPathStr+' \u2192 else if';
    var eiIsLast=eiIdx===block.elseifs.length-1&&block.elsebody===null;
    wrap.appendChild(makeBodyZone(ei.body,section,eiPathStr,eiIsLast,anc));});
  if(block.elsebody!==null){
    var elHdr=document.createElement('div');elHdr.className='else-header';
    elHdr.appendChild(kw('else'));
    if (!(typeof READONLY_MODE !== 'undefined' && READONLY_MODE)) {
      elHdr.appendChild(mkact('\u00D7',function(){block.elsebody=null;render();}));
    }
    wrap.appendChild(elHdr);
    wrap.appendChild(makeBodyZone(block.elsebody,section,parentPathStr+' \u2192 else',true,anc));}
  return wrap;}}
function renderForBlock(block,idx,parentArr,section,parentPathStr,anc){
  var wrap=document.createElement('div');wrap.className='for-block';
  wrap.setAttribute('data-id', block.id);
  var hdr=document.createElement('div');hdr.className='for-header'; // Header for for loop
  hdr.appendChild(kw('for ('));
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
    fe.addEventListener('input',function(e){e.stopPropagation();block[ki]=e.target.value;window.genCode();});
    fw.appendChild(fe);hdr.appendChild(fw);
    if(fi<2){var sep=document.createElement('span');sep.className='for-keyword';sep.textContent=';';hdr.appendChild(sep);}
  })(keys[fi],labels[fi],phs[fi]);}
  var ekw=document.createElement('span');ekw.className='for-keyword';ekw.textContent=') {';hdr.appendChild(ekw);
  if (!(typeof READONLY_MODE !== 'undefined' && READONLY_MODE)) {
    hdr.appendChild(mkact('\u00D7',function(){
      if (parentArr[idx] && parentArr[idx].type === 'slot') {
        parentArr[idx].content = null;
      } else {
        parentArr.splice(idx,1);
      }
      if(sel&&(sel.targetArr===block.body||isDescendantOf(block.body,sel.targetArr)))clearSelection();else render();}));
  }
  wrap.appendChild(hdr); // Forloop itself is deleted, not its content
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
  if (!(typeof READONLY_MODE !== 'undefined' && READONLY_MODE)) {
    hdr.appendChild(mkact('\u00D7',function(){
      if (parentArr[idx] && parentArr[idx].type === 'slot') {
        parentArr[idx].content = null;
      } else {
        parentArr.splice(idx,1);
      }
      if(sel&&(sel.targetArr===block.body||isDescendantOf(block.body,sel.targetArr)))clearSelection();else render();}));
  }
  wrap.appendChild(hdr); // Whileloop itself is deleted, not its content
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
  console.log("[DEBUG] checkpoint 9");
function isDescendantOf(body,targetArr){
  if(body===targetArr)return true;
  for(var i=0;i<body.length;i++){var b=body[i];
    var blockToCheck = b.type === 'slot' ? b.content : b;
    if (blockToCheck) {
      if(blockToCheck.type==='ifblock'){if(isDescendantOf(blockToCheck.ifbody,targetArr))return true;
        for(var j=0;j<blockToCheck.elseifs.length;j++)if(isDescendantOf(blockToCheck.elseifs[j].body,targetArr))return true;
        if(blockToCheck.elsebody&&isDescendantOf(blockToCheck.elsebody,targetArr))return true;
      }else if(blockToCheck.type==='forloop'||blockToCheck.type==='whileloop'){if(blockToCheck.body&&isDescendantOf(blockToCheck.body,targetArr))return true;}
    }
  }
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
  if(ifBlock.elsebody===targetArr)return true; // Check if elsebody is the target
  function walkDeep(arr){for(var j=0;j<arr.length;j++){var b=arr[j];
    var blockToCheck = b.type === 'slot' ? b.content : b;
    if (blockToCheck) {
      if(blockToCheck.type==='ifblock'&&isDescendant(blockToCheck,targetArr))return true;
      if((blockToCheck.type==='forloop'||blockToCheck.type==='whileloop')&&blockToCheck.body&&isDescendantOf(blockToCheck.body,targetArr))return true;
    }
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
  el.addEventListener('change',function(e){e.stopPropagation();obj[labelText]=e.target.value;window.genCode();});
  f.appendChild(el);return f;}
  console.log("[DEBUG] checkpoint 10");
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
    var blockToGen = b;
    if (b.type === 'slot') {
      if (b.content === null) return; // Don't generate code for empty slots
      blockToGen = b.content;
    }
    // Now blockToGen is guaranteed to be a real block or codeblock
    if(blockToGen.type==='codeblock'){
      var c=(blockToGen.params[0]||'').trim();
      if(c==='}'||c.match(/^\}/))extra=Math.max(0,extra-1);
      lines.push(genBlock(blockToGen,indent+extra));
      if(c.charAt(c.length-1)==='{')extra++;
    }else{lines.push(genBlock(blockToGen,indent+extra));}
  });
  return lines.join('\n');}
function genBlock(block,indent){
  var pad='';for(var i=0;i<indent;i++)pad+='   ';
  var blockToGen = block;
  if (block.type === 'slot') {
    if (block.content === null) return ''; // Should be handled by genBlocks, but safety check
    blockToGen = block.content;
  }
  if(blockToGen.type==='ifblock'){
    var lines=[pad+'if ('+genCond(blockToGen.condition)+') {'];
    lines.push(genBlocks(block.ifbody,indent+1));
    lines.push(pad+'}');
    blockToGen.elseifs.forEach(function(ei){
      lines.push(pad+'else if ('+genCond(ei.condition)+') {');
      lines.push(genBlocks(ei.body,indent+1));
      lines.push(pad+'}');});
    if(blockToGen.elsebody!==null){
      lines.push(pad+'else {');
      lines.push(genBlocks(blockToGen.elsebody,indent+1));
      lines.push(pad+'}');}
    return lines.join('\n');} // Use blockToGen here
  if(blockToGen.type==='forloop'){
    var init=blockToGen.forinit||'int i = 0';
    var cond=blockToGen.forcond||'i < 10';
    var incr=blockToGen.forincr||'i++';
    var lines=[pad+'for ('+init+'; '+cond+'; '+incr+') {'];
    lines.push(genBlocks(blockToGen.body||[],indent+1));
    lines.push(pad+'}');
    return lines.join('\n');} // Use blockToGen here
  if(blockToGen.type==='whileloop'){
    var cond=blockToGen.condition?genCond(blockToGen.condition):(blockToGen.whilecond||'true');
    var lines=[pad+'while ('+cond+') {'];
    lines.push(genBlocks(blockToGen.body||[],indent+1));
    lines.push(pad+'}');
    return lines.join('\n');} // Use blockToGen here
  return pad+BLOCKS[blockToGen.type].genStmt(blockToGen.params,blockToGen.exChildren||[]);}
function genCode(){
  var co=document.getElementById('codeout');
  var gv=genBlocks(SECTIONS.global,0);
  var sc=genBlocks(SECTIONS.setup,1);
  var lc=genBlocks(SECTIONS.loop,1);
  co.textContent='// Arduino Sketch\n// Block Builder\n// ------------\n\n'
    +(gv?gv+'\n\n':'')
    +'void setup() {\n'+(sc?sc+'\n':'')+'}'+
    '\n\nvoid loop() {\n'+(lc?lc+'\n':'')+'}';checkStepComplete();}
window.genCode = genCode;
function findBlockById(id){
  var found=null;
  function walk(arr){
    if(!arr)return;
    for(var i=0;i<arr.length;i++){ // Iterate through the array
      var b = arr[i];
      var blockToCheck = b.type === 'slot' ? b.content : b; // Get the actual block if it's a slot
      if(blockToCheck && blockToCheck.id==id){found=blockToCheck;return;} // Check ID of actual block
      if(b.type==='slot' && b.content){ // If it's a filled slot, recurse into its content
        if(b.content.type==='ifblock'){if(b.content.ifbody)walk(b.content.ifbody);
          if(b.content.elseifs)b.content.elseifs.forEach(function(ei){walk(ei.body);});if(b.content.elsebody)walk(b.content.elsebody);}
        else if(b.content.type==='forloop'||b.content.type==='whileloop'){if(b.content.body)walk(b.content.body);}
      } else if (b.type !== 'slot') { // Regular blocks
        if(b.type==='ifblock'){if(b.ifbody)walk(b.ifbody);
          if(b.elseifs)b.elseifs.forEach(function(ei){walk(ei.body);});if(b.elsebody)walk(b.elsebody);}
        else if(b.type==='forloop'||b.body)walk(b.body); // Fixed: b.type==='forloop' || b.type==='whileloop'
      }
    }}
  ['global','setup','loop'].forEach(function(s){walk(SECTIONS[s]);});
  return found;}
window.getBlockCode=function(id){
  var b=findBlockById(id);if(!b)return null;
  var code=genBlock(b,0);return code.split('\n')[0].trim();};
window.getGeneratedCode = function() { return document.getElementById('codeout').textContent; };
window.isProgressionMode = function() { return PROGRESSION_MODE; };
window.setBlockData = function(data) {
  if (!data) return;
  SECTIONS.global = data.global || []; // This is for non-progression mode
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
console.log("[DEBUG] checkpoint 11");
function saveBlocks(){
  if(!USERNAME||!PAGE)return;
  var state;
  if(PROGRESSION_MODE){ // In progression mode, save the full SECTIONS state
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
        CURRENT_STEP = saved.current_step;
        STUDENT_SAVES = saved.student_saves || []; // STUDENT_SAVES now stores full SECTIONS states
        buildWorkspace(CURRENT_STEP); // buildWorkspace will load from STUDENT_SAVES
        clearSelection();render();window.genCode();if(typeof checkStepComplete==='function')checkStepComplete();
      } else {
      SECTIONS.global = saved.global || [];
      SECTIONS.setup = saved.setup || [];
      SECTIONS.loop = saved.loop || [];
    }
      clearSelection();render();window.genCode();
      flash('Loaded!');}})
  .catch(function(){flash('Load failed');});}

window.resetBlocks = function(){
  if(!confirm('Reset this step? Your progress on this step will be cleared.'))return;
  if(PROGRESSION_MODE){
    delete STUDENT_SAVES[CURRENT_STEP];
    buildWorkspace(CURRENT_STEP);
  } else {
    SECTIONS.global = CFG.blocks ? JSON.parse(JSON.stringify(CFG.blocks.global)) : [];
    SECTIONS.setup  = CFG.blocks ? JSON.parse(JSON.stringify(CFG.blocks.setup))  : [];
    SECTIONS.loop   = CFG.blocks ? JSON.parse(JSON.stringify(CFG.blocks.loop))   : [];
  }
  saveBlocks();
  clearSelection();render();window.genCode();
  flash('Reset!');
};
console.log("[DEBUG] checkpoint 12");
function countPhantoms(arr){
  var n = 0;
  arr.forEach(function(b){
    if(b.type === 'slot'){
      if(b.content === null) n++; // Count empty slots as phantoms
      else { // Recurse into content if it's a structural block
        if(b.content.type==='ifblock'){n+=countPhantoms(b.content.ifbody);b.content.elseifs.forEach(function(ei){n+=countPhantoms(ei.body);});if(b.content.elsebody)n+=countPhantoms(b.content.elsebody);}
        if((b.content.type==='forloop'||b.content.type==='whileloop')&&b.content.body)n+=countPhantoms(b.content.body);
      }
    } else if(b.type==='ifblock'){n+=countPhantoms(b.ifbody);b.elseifs.forEach(function(ei){n+=countPhantoms(ei.body);});if(b.elsebody)n+=countPhantoms(b.elsebody);}
    else if((b.type==='forloop'||b.type==='whileloop')&&b.body)n+=countPhantoms(b.body);
  });
  return n;}
function countIncomplete(arr){
  var n=0;
  arr.forEach(function(b){
    var currentBlock = b;
    if (b.type === 'slot') {if (b.content === null) return; currentBlock = b.content;} // If slot is empty, it's a phantom, not incomplete field
    if(currentBlock.type==='codeblock')return; // Codeblocks are always complete
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
    def.inputs.forEach(function(inp,j){ // Use currentBlock here
      if(inp.t==='expr'){
        if(!currentBlock.exChildren||!currentBlock.exChildren[j])n++;
      }else if(inp.t==='text'||inp.t==='number'||inp.t==='vartext'){
        if(!currentBlock.params||!currentBlock.params[j]||currentBlock.params[j]==='')n++;
      }
    });
  });
  return n;}
  console.log("[DEBUG] checkpoint 13");
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
  console.log("[DEBUG] checkpoint 14");
function generateHint(u,t,tier){
  if(tier<2)return '';
  var pm=t.type==='slot'?t.phantom_meta:t;
  var tm=t.type==='slot'?t.master:t;
  if(u.type!==pm.expects)return 'Wrong block. Should be '+pm.expects;
  var def=BLOCKS[u.type];
  if(!def)return '';
  for(var i=0;i<(pm.params||[]).length;i++){
    if(!def.inputs[i])continue;
    var up=u.params[i]||'',tp=pm.params[i]||'';
    if(up.trim()!==tp.trim()){
      var lbl=def.inputs[i].l||'field';
      return tier===3?'Check '+lbl+': expected "'+tp+'"':'Check '+lbl;
    }
  }
  if(pm.expects==='ifblock'||pm.expects==='whileloop'){
    var h=generateCondHint(u.condition,pm.condition,tier);if(h)return h;
  }
  if(pm.expects==='forloop'){
    if((u.forinit||'')!==(pm.forinit||''))return tier===3?'Init: '+pm.forinit:'Check init';
    if((u.forcond||'')!==(pm.forcond||''))return tier===3?'Cond: '+pm.forcond:'Check condition';
    if((u.forincr||'')!==(pm.forincr||''))return tier===3?'Incr: '+pm.forincr:'Check increment';
  }
  var uex=u.exChildren||[];
  var tex=(tm&&tm.exChildren)||pm.exChildren||[];
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
  // Iterate through template list, as it defines the expected structure
  tList.forEach(function(tb,i){
    var ub = uList[i]; // Corresponding user block

    var tb=tList[i];if(!tb)return;
    if(tb.type==='slot'){ // Template is a slot
      if(ub===undefined || ub.type !== 'slot' || ub.content === null){ // User block is missing or slot is empty
        badIds.push({id:tb.id,hint:'Missing block'});
      } else { // User block is present and slot is filled, compare its content
        if(!compareBlock(ub.content,tb))badIds.push({id:ub.content.id,hint:generateHint(ub.content,tb,tier)});
        // Recurse into structural blocks within the slot's content
        var pm = tb.phantom_meta;
        var uc = ub.content;
        if(pm.expects==='ifblock'){collectBadIds(uc.ifbody,pm.ifbody,tier,badIds);
          if(uc.elseifs&&pm.elseifs)uc.elseifs.forEach(function(ei,k){if(pm.elseifs[k])collectBadIds(ei.body,pm.elseifs[k].body,tier,badIds);});
          if(uc.elsebody&&pm.elsebody)collectBadIds(uc.elsebody,pm.elsebody,tier,badIds);}
        else if(pm.expects==='forloop'||pm.expects==='whileloop'){collectBadIds(uc.body,pm.body,tier,badIds);}
      }
    } else if (tb.type === 'codeblock') { // Codeblocks are fixed, just check if they are present
      // No comparison needed for codeblocks, they are just there.
    }
  });
}
function compareBlock(u,t){
  if(!u)return false;
  if(t.type==='slot'){
    var pm = t.phantom_meta;
    if(u.type!==pm.expects)return false;
    var mc=t.master||pm;
    if(pm.expects==='ifblock'||pm.expects==='whileloop'){if(!compareCondition(u.condition,mc.condition))return false;}
    if(pm.expects==='forloop'){if((u.forinit||'')!==(mc.forinit||''))return false;
       if((u.forcond||'')!==(mc.forcond||''))return false;if((u.forincr||'')!==(mc.forincr||''))return false;}
    var masterParams=(t.master&&t.master.params)||pm.params||[];
    for(var i=0;i<masterParams.length;i++){
       var up=u.params[i]||'',tp=masterParams[i]||'';
       if(up.trim()!==tp.trim())return false;
    }
    var uex=u.exChildren||[];
    var tex=(t.master&&t.master.exChildren)||pm.exChildren||[];
    for(var i=0;i<tex.length;i++){
       if(!compareExpr(uex[i],tex[i]))return false;
    }
    return true;
  }
  return true;}
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
console.log("[DEBUG] checkpoint 15");
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
  console.log('SECTIONS (Current State):', SECTIONS);
  console.log('SKETCH_ERROR_PATHS:', SKETCH_ERROR_PATHS);
  console.log('--------------------------------');
};
console.log("[DEBUG] checkpoint 151");
function checkStepComplete(){
    console.log("[DEBUG] checkStepComplete called, PROGRESSION_MODE:", PROGRESSION_MODE);
  if(!PROGRESSION_MODE)return;
    console.log("[DEBUG] checkStepComplete past guard");
  var phantoms=countPhantoms(SECTIONS.global)+countPhantoms(SECTIONS.setup)+countPhantoms(SECTIONS.loop);
    console.log("[DEBUG] phantoms:", phantoms);
  var incomplete=countIncomplete(SECTIONS.global)+countIncomplete(SECTIONS.setup)+countIncomplete(SECTIONS.loop);
  var total=phantoms+incomplete;
  var step = STEPS&&STEPS[CURRENT_STEP]?STEPS[CURRENT_STEP]:null;
  var curGuidance = step && step.config ? (step.config.structure === 'none' ? 'free' : 'guided') : 'guided';

  if(curGuidance==='free'){
    nextBtnState.ready = true;
    nextBtnState.mode = 'next-mode';
    nextBtnState.text = 'Next Step \u2192';
    nextBtnState.visible = true;
    window.dispatchEvent(new CustomEvent('bb_next_state', {detail: {state: {
      ready: true, 'check-mode': false, 'next-mode': true, hidden: false, text: nextBtnState.text, prevVisible: nextBtnState.prevVisible
    }}}));
    return;
  }
console.log("[DEBUG] checkpoint 152");
  if(nextBtnState.mode === 'next-mode') return;
  if(nextBtnState.mode === 'check-mode'){
     if(total>0){
        nextBtnState.ready = false;
        nextBtnState.text = 'Complete Step';
        nextBtnState.mode = '';
        window.dispatchEvent(new CustomEvent('bb_next_state', {detail: {state: {
          ready: false, 'check-mode': false, 'next-mode': false, hidden: !nextBtnState.visible, text: nextBtnState.text, prevVisible: nextBtnState.prevVisible
        }}}));
     }
     return;
  }

  if(phantoms>0) stepProgress = phantoms+' block'+(phantoms===1?'':'s')+' to place';
  else if(incomplete>0) stepProgress = incomplete+' field'+(incomplete===1?'':'s')+' to fill';
  else stepProgress = 'complete';

  if(total===0){
    nextBtnState.ready = true;
    nextBtnState.text = 'Check Code';
    nextBtnState.mode = 'check-mode';
  } else {
    nextBtnState.ready = false;
    nextBtnState.text = 'Complete Step';
    nextBtnState.mode = '';
  }

  window.dispatchEvent(new CustomEvent('bb_step_update', {detail: {label: stepLabel, progress: stepProgress}}));
  window.dispatchEvent(new CustomEvent('bb_next_state', {detail: {state: {
    ready: nextBtnState.ready,
    'check-mode': nextBtnState.mode === 'check-mode',
    'next-mode': nextBtnState.mode === 'next-mode',
    hidden: !nextBtnState.visible,
    text: nextBtnState.text,
    prevVisible: nextBtnState.prevVisible
  }}}));

  return true;}
console.log("[DEBUG] checkpoint 16");
function validateStep(){
  if(!STEPS||!STEPS[CURRENT_STEP])return true;
  var tmpl=STEPS[CURRENT_STEP];
  var valid=true; var tier=1; if(CHECK_FAIL_COUNT>=2)tier=2; if(CHECK_FAIL_COUNT>=4)tier=3;
  var badIds=[];
  ['global','setup','loop'].forEach(function(sec){ collectBadIds(SECTIONS[sec], tmpl[sec], tier, badIds); });
  if(badIds.length>0)valid=false;
  document.querySelectorAll('.ws-block,.if-block,.for-block,.while-block').forEach(function(el){el.classList.remove('error-block');});
  document.querySelectorAll('.block-hint').forEach(function(el){el.remove();});
  if(!valid){ CHECK_FAIL_COUNT++; badIds.forEach(function(bid){ var el=document.querySelector('[data-id="'+bid.id+'"]');
      if(el){ el.classList.add('error-block'); if(bid.hint){var hd=document.createElement('div');hd.className='block-hint';hd.textContent=bid.hint;el.appendChild(hd);}}}); }
  return valid;}
console.log("[DEBUG] checkpoint 17");
function buildWorkspace(stepIdx, saves) {
  if (!PROGRESSION_MODE || !STEPS || stepIdx >= STEPS.length) return;
  var step = STEPS[stepIdx];
  if (STUDENT_SAVES[stepIdx]) {
    var savedState = STUDENT_SAVES[stepIdx]; SECTIONS.global = JSON.parse(JSON.stringify(savedState.global)); SECTIONS.setup = JSON.parse(JSON.stringify(savedState.setup)); SECTIONS.loop = JSON.parse(JSON.stringify(savedState.loop));
  } else { SECTIONS.global = JSON.parse(JSON.stringify(step.global)); SECTIONS.setup = JSON.parse(JSON.stringify(step.setup)); SECTIONS.loop = JSON.parse(JSON.stringify(step.loop)); }
  PALETTE_ALLOWED = (step.palette !== undefined && step.palette !== null) ? step.palette : null;
  stepLabel = step.label;
  window.dispatchEvent(new CustomEvent('bb_step_update', { detail: { label: stepLabel, progress: '' } }));
  window.CURRENT_STEP_META = { guidance: step.config.structure === 'none' ? 'free' : 'guided', view: step.config.interface };
  window.dispatchEvent(new CustomEvent('stepchange', { detail: window.CURRENT_STEP_META }));
  var activeId = (step.active === 'global') ? 'gs' : (step.active === 'setup' ? 'ss' : 'ls'); expandSection(activeId);
  nextBtnState.visible = !(step.config.structure === 'none' || stepIdx >= STEPS.length - 1);
  nextBtnState.ready = false; nextBtnState.mode = ''; nextBtnState.text = 'Complete Step'; nextBtnState.prevVisible = stepIdx > 0;
  window.dispatchEvent(new CustomEvent('bb_next_state', { detail: { state: { ready: false, 'check-mode': false, 'next-mode': false, hidden: !nextBtnState.visible, text: nextBtnState.text, prevVisible: nextBtnState.prevVisible }}}));
  if (window.updateDrawer) window.updateDrawer(stepIdx);
  checkStepComplete(); render(); genCode(); }

window.bbNext = function() {
  if (!nextBtnState.ready) return;
  if (nextBtnState.mode === 'check-mode') {
    if (validateStep()) { nextBtnState.text = 'Next Step \u2192'; nextBtnState.mode = 'next-mode';
      window.dispatchEvent(new CustomEvent('bb_next_state', { detail: { state: { ready: true, 'check-mode': false, 'next-mode': true, hidden: false, text: nextBtnState.text, prevVisible: nextBtnState.prevVisible } } }));
      flash('Correct!'); CHECK_FAIL_COUNT = 0; } else { flash('Incorrect - check highlighted blocks'); }
    return; }
  try { STUDENT_SAVES[CURRENT_STEP] = JSON.parse(JSON.stringify(SECTIONS));
    CURRENT_STEP++; buildWorkspace(CURRENT_STEP); saveBlocks();
    if (window.openDrawer) window.openDrawer();
  } catch (e) { flash('ERR: ' + e.message); console.error(e); } };

window.bbPrev = function() {
  if (!PROGRESSION_MODE || CURRENT_STEP <= 0) return;
  CURRENT_STEP--; STUDENT_SAVES.pop(); buildWorkspace(CURRENT_STEP); };

window.getCurrentStepMeta = function() { return window.CURRENT_STEP_META || {}; };

if (CFG.is_overlay) { window.addEventListener('message', function(e){ if(e.data && e.data.type === 'bb_save_request'){ saveBlocks(); setTimeout(function(){ window.parent.postMessage({type:'bb_close'}, '*'); }, 600); } }); }

console.log("[DEBUG] block_builder.js: Initializing workspace.");
if (CFG.mode === 'progression') { PROGRESSION_MODE = true; STEPS = CFG.steps; CURRENT_STEP = 0; STUDENT_SAVES = []; buildWorkspace(0, null); } 
else { SECTIONS.global = CFG.blocks ? CFG.blocks.global : []; SECTIONS.setup = CFG.blocks ? CFG.blocks.setup : []; SECTIONS.loop = CFG.blocks ? CFG.blocks.loop : []; render(); window.genCode(); }
if (USERNAME && (PROGRESSION_MODE || !CFG.force_preset)) loadBlocks();
updatePalette();
render();
if (PROGRESSION_MODE) checkStepComplete();
})();