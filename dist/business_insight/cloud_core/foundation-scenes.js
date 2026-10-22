/* Deterministic SVG projection of reviewed TableGit lesson inputs. No embedded example data. */
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const number=v=>Number.isInteger(v)?String(v):String(Number(v.toFixed(4)));
const group=(rows,role)=>rows.filter(r=>r.role===role).sort((a,b)=>a.position-b.position);
const param=(rows,role)=>group(rows,role)[0]?.numeric_value;
const val=(r,lang)=>r['label_'+lang]||String(r.column_index+1);
export function lessonArithmetic(method,rows){
 if(method==='quantization'){
  const bits=param(rows,'output_bits'),scale=param(rows,'scale'),zero=param(rows,'zero_point'),inputBits=param(rows,'input_bits');
  if(!Number.isInteger(bits)||bits<1||bits>8||!(scale>0)||!Number.isInteger(zero)||inputBits!==16)throw new Error('Invalid affine quantization example');
  const max=2**bits-1,original=group(rows,'original');
  const encoded=original.map(r=>{const x=r.numeric_value,q=Math.max(0,Math.min(max,Math.floor(x/scale+zero+.5))),reconstructed=scale*(q-zero);return {...r,q,code:q.toString(2).padStart(bits,'0'),reconstructed,error:reconstructed-x};});
  if(!original.length||original.length>8||original.some(r=>!/^[01]{16}$/.test(r.bit_pattern)))throw new Error('Missing original bit patterns');
  const binary16=pattern=>{const n=parseInt(pattern,2),sign=(n&32768)?-1:1,exp=(n>>10)&31,f=n&1023;return sign*(exp===0?f*2**-24:exp===31?NaN:(1+f/1024)*2**(exp-15));};
  if(original.some(r=>binary16(r.bit_pattern)!==r.numeric_value))throw new Error('Original bit pattern does not encode the displayed value');
  const probe=param(rows,'clip_probe'),probeCode=Math.max(0,Math.min(max,Math.floor(probe/scale+.5)+zero));return {scale,zero,bits,inputBits,max,encoded,originalPayload:original.length*inputBits,encodedPayload:original.length*bits,scaleBits:param(rows,'scale_bits'),zeroBits:param(rows,'zero_point_bits'),probe,probeCode,probeReconstructed:scale*(probeCode-zero)};
 }
 if(method==='pruning_sparsity'){
  const original=group(rows,'original'),masks=group(rows,'mask');if(!original.length||original.length!==masks.length)throw new Error('Incomplete pruning example');
  const entries=original.map(r=>{const mask=masks.find(m=>m.row_index===r.row_index&&m.column_index===r.column_index);if(!mask||![0,1].includes(mask.numeric_value))throw new Error('Invalid pruning mask');return {...r,mask:mask.numeric_value,result:r.numeric_value*mask.numeric_value};});const input=group(rows,'input');const output=(field)=>Array.from({length:Math.max(...entries.map(r=>r.row_index))+1},(_,i)=>entries.filter(r=>r.row_index===i).reduce((sum,r)=>sum+r[field]*input[r.column_index].numeric_value,0));return {entries,input,originalOutput:output('numeric_value'),prunedOutput:output('result'),threshold:param(rows,'threshold')};
 }
 if(method==='low_rank'){
  const original=group(rows,'original'),a=group(rows,'factor_a'),b=group(rows,'factor_b');
  const shape=x=>[Math.max(...x.map(r=>r.row_index))+1,Math.max(...x.map(r=>r.column_index))+1],os=shape(original),as=shape(a),bs=shape(b);
  if(as[0]!==os[0]||bs[1]!==os[1]||as[1]!==bs[0]||[original,a,b].some((x,i)=>x.length!==[os,as,bs][i][0]*[os,as,bs][i][1]))throw new Error('Incompatible factor shapes');
  const reconstructed=original.map(r=>({...r,reconstructed:Array.from({length:as[1]},(_,k)=>a.find(v=>v.row_index===r.row_index&&v.column_index===k).numeric_value*b.find(v=>v.row_index===k&&v.column_index===r.column_index).numeric_value).reduce((x,y)=>x+y,0)}));
  const input=group(rows,'input'),perturbation=group(rows,'perturbation')[0],dot=entries=>Array.from({length:os[0]},(_,i)=>entries.filter(r=>r.row_index===i).reduce((sum,r)=>sum+r.numeric_value*input[r.column_index].numeric_value,0));const intermediate=Array.from({length:bs[0]},(_,i)=>b.filter(r=>r.row_index===i).reduce((sum,r)=>sum+r.numeric_value*input[r.column_index].numeric_value,0));const changed=original.map(r=>r.row_index===perturbation.row_index&&r.column_index===perturbation.column_index?{...r,numeric_value:perturbation.numeric_value}:r);const factorOutput=Array.from({length:as[0]},(_,i)=>a.filter(r=>r.row_index===i).reduce((sum,r)=>sum+r.numeric_value*intermediate[r.column_index],0));return {original,a,b,os,as,bs,reconstructed,input,intermediate,output:dot(original),factorOutput,changedOutput:dot(changed),perturbation};
 }
 if(method==='distillation'){
  const teacher=group(rows,'teacher'),logits=group(rows,'student_logits'),temperature=param(rows,'temperature'),rate=param(rows,'learning_rate');
  if(temperature!==1||teacher.length!==logits.length||teacher.length<2||teacher.length>5||Math.abs(teacher.reduce((sum,r)=>sum+r.numeric_value,0)-1)>.00001)throw new Error('Invalid distillation teaching example');
  const softmax=x=>{const exp=x.map(v=>Math.exp(v-Math.max(...x))),sum=exp.reduce((a,b)=>a+b,0);return exp.map(v=>v/sum);};
  const initial=softmax(logits.map(r=>r.numeric_value)),gradient=initial.map((p,i)=>p-teacher[i].numeric_value),updated=logits.map((r,i)=>r.numeric_value-rate*gradient[i]),final=softmax(updated),loss=p=>-teacher.reduce((sum,r,i)=>sum+r.numeric_value*Math.log(p[i]),0);
  return {teacher,logits,initial,gradient,updated,final,initialLoss:loss(initial),finalLoss:loss(final),rate};
 }
 throw new Error('Unsupported lesson method');
}
export function renderLessonSVG({method,step,values,locale='zh',ui,narrow=false}){
 const d=lessonArithmetic(method,values),W=narrow?300:720,H=narrow?460:390,parts=[],motion=[];
 const t=k=>ui[k]||k,source=step.scene_kind,seconds=step.duration_ms/1000;
 const colors=['#5ce0d1','#7bb9ff','#c2a0ff','#f3c878'];
 const text=(x,y,s,size=18,anchor='start',cls='')=>parts.push('<text x="'+x+'" y="'+y+'" font-size="'+Math.max(narrow?16:17,size)+'" text-anchor="'+anchor+'" class="'+cls+'">'+esc(s)+'</text>');
 const rect=(x,y,w,h,cls='panel',r=10,fill='')=>parts.push('<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+r+'" class="'+cls+'"'+(fill?' fill="'+fill+'"':'')+'/>');
 const path=(p,cls='wire',stroke='')=>parts.push('<path d="'+p+'" class="'+cls+'"'+(stroke?' stroke="'+stroke+'"':'')+'/>');
 const line=(x,y,xx,yy,cls='wire',stroke='')=>path('M'+x+' '+y+'L'+xx+' '+yy,cls,stroke);
 const circle=(x,y,r,cls='signal',fill='')=>parts.push('<circle cx="'+x+'" cy="'+y+'" r="'+r+'" class="'+cls+'"'+(fill?' fill="'+fill+'"':'')+'/>');
 const frame=(x,y,w,h,label,color='#5ce0d1')=>{rect(x,y,w,h);path('M'+(x+1)+' '+(y+14)+'V'+(y+h-14),'accent',color);if(label)text(x+14,y+25,label,17,'start','muted');};
 const bits=(pattern,x,y,bw=16,color='#5ce0d1')=>{[...pattern].forEach((bit,i)=>{const xx=x+i*bw+(pattern.length===16?Math.floor(i/4)*5:0);rect(xx,y,bw-2,25,'bit',3,bit==='1'?color:'#172a42');text(xx+(bw-2)/2,y+18,bit,16,'middle',bit==='1'?'bit-dark':'bit-light');});};
 const move=(name,x,y,xx,yy,delay=0,body='<circle r="5" fill="#a3fff0"/>')=>{
  motion.push('@keyframes '+name+'{0%,'+(10+delay)+'%{transform:translate('+x+'px,'+y+'px)}'+(72+delay)+'%,100%{transform:translate('+xx+'px,'+yy+'px)}}.'+name+'{animation:'+name+' '+seconds+'s cubic-bezier(.35,0,.2,1) both}');
  parts.push('<g class="'+name+'" aria-hidden="true">'+body+'</g>');
 };
 const flow=(name,x,y,xx,yy,delay=0,color='#5ce0d1')=>{line(x,y,xx,yy,'flow-track',color);move(name,x,y,xx,yy,delay,'<circle r="5" fill="'+color+'"/><circle r="10" fill="'+color+'" opacity=".15"/>');};
 const matrix=(items,x,y,field='numeric_value',cw=43,ch=38,byRow=true)=>{
  items.forEach(r=>{const color=colors[(byRow?r.row_index:r.column_index)%colors.length],xx=x+r.column_index*cw,yy=y+r.row_index*ch;
   rect(xx,yy,cw-5,ch-5,'matrix-cell',5,color);text(xx+(cw-5)/2,yy+(ch-5)*.7,number(r[field]),18,'middle','matrix-value');
  });
 };
 const vector=(a,x,y,w=62,dy=46,color='#5ce0d1')=>a.forEach((v,i)=>{rect(x,y+i*dy,w,dy-8,'value-box',7);text(x+w/2,y+i*dy+(dy-8)*.7,number(v),22,'middle');path('M'+x+' '+(y+i*dy+7)+'V'+(y+i*dy+dy-15),'accent',color);});
 const heroMetric=(x,y,a,b,unit)=>{text(x,y,a,36,'middle','muted');text(x+74,y,'→',25,'middle','muted');text(x+148,y,b,38,'middle','emphasis');text(x+74,y+28,unit,16,'middle','muted');};
 const drawNetwork=(masked=false,output=d.originalOutput)=>{
  const ix=narrow?36:116,ox=narrow?264:604,top=narrow?115:100,gap=narrow?152:132;
  d.entries.forEach((r,i)=>{
   const y1=top+r.column_index*gap,y2=top+r.row_index*gap,remove=masked&&!r.mask,len=Math.hypot(ox-ix,y2-y1),name='edge'+i;
   if(remove)motion.push('@keyframes '+name+'{0%,22%{stroke-dashoffset:0}78%,100%{stroke-dashoffset:'+len+'}}.'+name+'{stroke-dasharray:'+len+';animation:'+name+' '+seconds+'s ease-in-out both}');
   parts.push('<path d="M'+ix+' '+y1+'L'+ox+' '+y2+'" class="'+(remove?'removed-connection '+name:'retained-connection')+'" stroke-width="'+(2+Math.min(4,Math.abs(r.numeric_value)))+'"/>');
   const fraction=r.row_index===r.column_index?.5:(r.column_index===1?.27:.73),lx=ix+(ox-ix)*fraction,ly=y1+(y2-y1)*fraction;
   const sub=n=>String(n).replace(/[0-9]/g,c=>'₀₁₂₃₄₅₆₇₈₉'[Number(c)]);
   rect(lx-42,ly-16,84,32,'label-plate',7);text(lx,ly+6,'w'+sub(r.row_index+1)+sub(r.column_index+1)+'='+number(r.numeric_value),17,'middle',remove?'error':'');
   if(!remove)move('wire'+i,ix,y1,ox,y2,i*3);
  });
  d.input.forEach((r,i)=>{circle(ix,top+i*gap,24,'node');text(ix,top+i*gap+7,number(r.numeric_value),21,'middle');});
  output.forEach((v,i)=>{circle(ox,top+i*gap,28,'node-output');text(ox,top+i*gap+7,number(v),20,'middle');});
  text(ix,top-48,'x',20,'middle','muted');text(ox,top-48,masked?'W′x':'Wx',20,'middle','muted');
 };
 if(method==='quantization'){
  const E=d.encoded;
  if(source==='quant-original'){
   text(18,29,t('original_values'),18,'start','muted');text(W-18,29,E.length+' × '+d.inputBits+' = '+d.originalPayload+' bit',19,'end','emphasis');
   E.forEach((r,i)=>{
    const y=(narrow?48:51)+i*(narrow?90:72),x=narrow?16:24;
    rect(x,y,W-x*2,narrow?76:62,'storage-band',9);
    if(narrow){text(x+10,y+26,number(r.numeric_value),23);text(W-26,y+26,d.inputBits+' bit',16,'end','muted');bits(r.bit_pattern,x+10,y+39,13.7,colors[i]);}
    else{text(x+18,y+39,number(r.numeric_value),25);bits(r.bit_pattern,190,y+18,26,colors[i]);text(674,y+39,d.inputBits,18,'end','muted');}
    move('read'+i,narrow?26:190,y+(narrow?72:53),narrow?273:618,y+(narrow?72:53),i*4,'<path d="M-12 0H12" stroke="'+colors[i]+'" stroke-width="3" stroke-linecap="round"/>');
   });
   text(W/2,H-18,t('representation_changes'),17,'middle','muted');
  }else if(source==='quant-parameters'){
   text(18,31,'s = '+number(d.scale)+'    z = '+d.zero,24);text(W-18,31,d.bits+' bit',25,'end','emphasis');
   const top=narrow?80:70,dy=narrow?82:67;
   text(37,top-17,'q',17,'middle','muted');text(narrow?125:330,top-17,t('stored_bits'),17,'middle','muted');text(W-48,top-17,'x̂',20,'middle','muted');
   for(let q=0;q<=d.max;q++){
    const y=top+q*dy;frame(17,y,W-34,dy-12,'',colors[q%4]);text(37,y+(dy-12)*.65,q,26,'middle');bits(q.toString(2).padStart(d.bits,'0'),narrow?103:293,y+15,narrow?29:40,colors[q%4]);
    text(W-48,y+(dy-12)*.65,number(d.scale*(q-d.zero)),25,'middle');
    flow('level'+q,narrow?170:420,y+(dy-12)/2,W-85,y+(dy-12)/2,q*4,colors[q%4]);
   }
  }else if(source==='quant-encode'){
   text(18,30,t('original_short'),17,'start','muted');text(W/2,30,t('reconstructed_short'),17,'middle','muted');text(W-18,30,'q → bit',17,'end','muted');
   E.forEach((r,i)=>{
    const y=58+i*(narrow?92:75),center=y+28;
    rect(16,y,narrow?88:150,56,'value-box',8);text(narrow?60:91,center+8,number(r.numeric_value),narrow?22:26,'middle');
    rect(W/2-(narrow?33:55),y,narrow?66:110,56,'value-box',8);text(W/2,center+8,number(r.reconstructed),narrow?24:28,'middle');
    const cx=narrow?247:621;rect(cx-29,y,58,56,'code-box',8);text(cx,center-2,r.code,24,'middle','emphasis');text(cx,center+20,'q='+r.q,16,'middle','muted');
    flow('snap'+i,narrow?105:167,center,W/2-(narrow?34:56),center,i*3,colors[i]);flow('encode'+i,W/2+(narrow?35:57),center,cx-31,center,16+i*2,colors[i]);
   });
  }else if(source==='quant-pack'){
   text(18,28,d.originalPayload+' bit',25,'start','muted');text(W-18,28,d.encodedPayload+' bit',28,'end','emphasis');
   const top=46,dy=narrow?35:43;
   E.forEach((r,i)=>{const y=top+i*dy;if(!narrow)text(27,y+19,number(r.numeric_value),17);bits(r.bit_pattern,narrow?26:170,y,narrow?13.7:24,colors[i]);});
   const targetY=narrow?286:262,bw=narrow?31:47,tx=narrow?26:172;
   text(18,narrow?225:241,t('reencode_short'),18,'start','muted');
   const pattern=E.map(r=>r.code).join('');bits(pattern,tx,targetY,bw);
   E.forEach((r,i)=>{
    const startX=narrow?24+i*66:640,startY=narrow?241:top+i*dy,endX=tx+i*d.bits*bw;
    path('M'+(startX+21)+' '+(startY+25)+'L'+(endX+22)+' '+targetY,'flow-track',colors[i]);
    motion.push('@keyframes pack'+i+'{0%,15%{transform:translate('+startX+'px,'+startY+'px);opacity:1}70%{transform:translate('+endX+'px,'+targetY+'px);opacity:1}82%,100%{transform:translate('+endX+'px,'+targetY+'px);opacity:0}}.pack'+i+'{animation:pack'+i+' '+seconds+'s cubic-bezier(.4,0,.15,1) both}');
    parts.push('<g aria-hidden="true" class="pack'+i+'"><rect width="42" height="25" rx="5" fill="'+colors[i]+'"/><text x="21" y="18" text-anchor="middle" font-size="18" fill="#081626" class="packet-text">'+esc(r.code)+'</text></g>');
   });
   const y=narrow?354:330,total=d.encodedPayload+d.scaleBits+d.zeroBits;
   text(18,y,t('payload_only')+': '+d.originalPayload+' → '+d.encodedPayload+' bit',17);
   text(18,y+30,'s '+d.scaleBits+' + z '+d.zeroBits+' + q '+d.encodedPayload+' = '+total+' bit',17,'start','muted');
   rect(18,y+43,W-36,5,'track',2);rect(18,y+43,(W-36)*total/d.originalPayload,5,'accent-bar',2);
  }else if(source==='quant-reconstruct'){
   const xmin=Math.min(...E.map(r=>r.numeric_value),...E.map(r=>r.reconstructed)),xmax=Math.max(...E.map(r=>r.numeric_value),...E.map(r=>r.reconstructed)),left=narrow?75:170,right=W-30,px=v=>left+(v-xmin)/(xmax-xmin)*(right-left);
   text(18,28,t('reconstruction_error'),18,'start','muted');
   E.forEach((r,i)=>{
    const y=62+i*(narrow?96:77);bits(r.code,18,y+4,22,colors[i]);line(left,y+29,right,y+29,'ruler');
    circle(px(r.numeric_value),y+29,6,'original-dot');circle(px(r.reconstructed),y+29,7,'reconstructed-dot');
    path('M'+px(r.numeric_value)+' '+(y+29)+'H'+px(r.reconstructed),'error-line');
    move('restore'+i,45,y+17,px(r.reconstructed),y+29,i*3,'<circle r="4" fill="'+colors[i]+'"/>');
    text(left,y+4,number(r.numeric_value)+' → '+number(r.reconstructed),18);text(right,y+62,'e = '+(r.error>0?'+':'')+number(r.error),17,'end','error');
   });
  }else if(source==='quant-error'){
   const raw=Math.floor(d.probe/d.scale+.5)+d.zero;
   text(18,29,t('boundary_probe')+': '+number(d.probe),20);
   frame(18,57,W-36,73,'');text(W/2,88,'q: '+raw+' → clip → '+d.probeCode,28,'middle');text(W/2,116,'x̂ = '+number(d.probeReconstructed),20,'middle','emphasis');
   const min=d.scale*(0-d.zero),max=d.probe,pad=narrow?27:72,py=narrow?237:224,px=v=>pad+(v-min)/(max-min)*(W-2*pad),end=px(d.probeReconstructed);
   line(px(min),py,px(max),py,'ruler');
   for(let q=0;q<=d.max;q++){const x=px(d.scale*(q-d.zero));line(x,py-8,x,py+8,'tick');text(x,py+35,number(d.scale*(q-d.zero)),17,'middle','muted');}
   line(end,py-37,px(d.probe),py-37,'error-line');circle(px(d.probe),py,7,'original-dot');circle(end,py,8,'reconstructed-dot');
   motion.push('@keyframes clipBack{0%,15%{transform:translate('+px(d.probe)+'px,'+py+'px)}70%,100%{transform:translate('+end+'px,'+py+'px)}}.clip-probe{animation:clipBack '+seconds+'s ease-in-out both}');
   parts.push('<g class="clip-probe" aria-hidden="true"><circle r="10" fill="#ff9589" opacity=".7"/><path d="M0 -22V-10" stroke="#ff9589" stroke-width="2"/></g>');
   text(W/2,narrow?343:318,'e = '+number(d.probeReconstructed-d.probe),32,'middle','error');
   text(W/2,H-28,t('sample_max_error')+': '+number(Math.max(...E.map(r=>Math.abs(r.error)))),17,'middle','muted');
  }
 }else if(method==='pruning_sparsity'){
  const E=d.entries;
  if(source==='prune-original'||source==='prune-mask'){
   drawNetwork(source==='prune-mask',source==='prune-mask'?d.prunedOutput:d.originalOutput);
   if(source==='prune-mask'){
    const y=narrow?324:278,gy=narrow?345:301; text(18,y,'|w| < '+number(d.threshold)+' → 0',20);
    text(18,gy+23,'W′',20,'start','emphasis');matrix(E,64,gy,'result',36,32);
    const mx=narrow?198:442;text(mx-33,gy+23,'M',20,'start','muted');matrix(E.map(r=>({...r,numeric_value:r.mask})),mx,gy,'numeric_value',36,32);
   }else{text(W/2,H-48,t('dense_weights')+': '+E.length,19,'middle','muted');}
  }else if(source==='prune-storage'){
   text(18,30,t('dense_slots'),20);const w=(W-52)/4;
   E.forEach((r,i)=>{rect(18+i*(w+5),57,w,65,r.result===0?'empty-slot':'value-box',8);text(18+i*(w+5)+w/2,99,number(r.result),28,'middle',r.result===0?'muted':'');});
   text(18,narrow?186:177,t('sparse_records'),20);
   E.filter(r=>r.mask).forEach((r,i)=>{const y=(narrow?218:204)+i*72;frame(18,y,W-36,57,'',colors[i]);text(32,y+36,'('+r.row_index+', '+r.column_index+')',22,'start','muted');text(W-44,y+36,number(r.result),30,'end','emphasis');flow('record'+i,W/2,y+29,W-80,y+29,i*5);});
   text(W/2,H-23,t('indices_required'),17,'middle','muted');
  }else{
   const left=narrow?22:70,right=narrow?177:492,yy=93;
   text(left,44,'Wx',23);text(right,44,'W′x',23,'start','emphasis');vector(d.originalOutput,left,yy,narrow?90:130,78,'#7bb9ff');vector(d.prunedOutput,right,yy,narrow?98:130,78);
   d.originalOutput.forEach((v,i)=>flow('skip'+i,left+(narrow?94:135),yy+i*78+34,right-8,yy+i*78+34,i*6));
   text(W/2,narrow?320:297,'Δy = ['+d.prunedOutput.map((v,i)=>number(v-d.originalOutput[i])).join(', ')+']',24,'middle','error');
   text(W/2,H-27,t('nonzero_values')+': '+E.length+' → '+E.filter(r=>r.result!==0).length,19,'middle','muted');
  }
 }else if(method==='low_rank'){
  if(source==='rank-original'){
   const cw=narrow?47:72,ch=narrow?52:58,x=narrow?39:195,y=50;
   matrix(d.original,x,y,'numeric_value',cw,ch);
   d.a.forEach((r,i)=>{text(x+d.os[1]*cw+25,y+i*ch+25,'='+number(r.numeric_value)+'×B',20,'start','muted');});
   const bx=narrow?46:195,by=narrow?330:310;
   text(18,by-20,t('shared_direction'),18,'start','muted');matrix(d.b,bx,by,'numeric_value',cw,43,false);
   flow('extract',W/2,y+d.os[0]*ch+10,W/2,by-33);
   text(W/2,H-15,d.os.join(' × ')+' = '+d.original.length+' '+t('parameters'),18,'middle','muted');
  }else if(source==='rank-factors'){
   const ax=narrow?29:120,ay=62,cw=narrow?40:58,ch=narrow?42:52,bx=narrow?130:350,by=narrow?129:113;
   text(ax,ay-18,'A · '+d.as.join('×'),19,'start','muted');matrix(d.a,ax,ay,'numeric_value',cw,ch);
   text(bx,by-18,'B · '+d.bs.join('×'),19,'start','muted');matrix(d.b,bx,by,'numeric_value',cw,ch,false);
   text(narrow?97:262,by+26,'×',30,'middle');flow('factor',ax+cw/2,ay+d.as[0]*ch+8,bx+d.bs[1]*cw/2,by+ch+34);
   heroMetric(narrow?71:286,narrow?356:321,d.original.length,d.a.length+d.b.length,t('parameters'));
  }else if(source==='rank-compute'){
   text(18,29,'x = ['+d.input.map(r=>number(r.numeric_value)).join(', ')+']',21);
   frame(18,48,W-36,67,'');text(W/2,75,'B · x',18,'middle','muted');text(W/2,103,d.b.map((r,i)=>number(r.numeric_value)+'×'+number(d.input[i].numeric_value)).join(' + ')+' = '+d.intermediate.map(number).join(', '),narrow?18:25,'middle');
   const y=171,ax=narrow?32:150,ox=narrow?213:520,middle=W/2;
   text(ax+18,y-14,'A',20,'middle','muted');matrix(d.a,ax,y,'numeric_value',40,40);text(ox+23,y-14,'y',20,'middle','emphasis');vector(d.factorOutput,ox,y,48,40);
   text(middle,y+70,'× '+d.intermediate.map(number).join(', '),28,'middle');
   move('intermediate',W/2,127,middle,y+105,0,'<rect x="-20" y="-17" width="40" height="34" rx="9" fill="#5ce0d1"/><text x="0" y="7" font-size="21" text-anchor="middle" class="packet-text">'+esc(d.intermediate.map(number).join(','))+'</text>');
   d.factorOutput.forEach((v,i)=>flow('product'+i,ax+45,y+i*40+16,ox-8,y+i*40+16,i*4));
   text(W/2,H-17,'W · x '+(d.output.every((v,i)=>Math.abs(v-d.factorOutput[i])<1e-9)?'=':'≈')+' A · (B · x)',18,'middle','muted');
  }else{
   const p=d.perturbation,old=d.original.find(r=>r.row_index===p.row_index&&r.column_index===p.column_index);
   text(18,31,'W['+(p.row_index+1)+','+(p.column_index+1)+']: '+number(old.numeric_value)+' → '+number(p.numeric_value),23);
   const x1=narrow?28:170,x2=narrow?184:465,y=89; text(x1,y-19,'Wx',20,'start','muted');text(x2,y-19,'A(Bx)',20,'start','emphasis');vector(d.changedOutput,x1,y,85,56,'#7bb9ff');vector(d.factorOutput,x2,y,85,56);
   d.changedOutput.forEach((v,i)=>{if(v!==d.factorOutput[i]){path('M'+(x1+90)+' '+(y+i*56+23)+'H'+(x2-7),'error-line');text(W/2,y+i*56+10,(v-d.factorOutput[i]>0?'+':'')+number(v-d.factorOutput[i]),18,'middle','error');}});
   text(W/2,H-54,'Wx − A(Bx)',20,'middle','error');text(W/2,H-25,t('approximation_changes_output'),18,'middle','muted');
  }
 }else{
  const teacher=d.teacher,barMax=narrow?105:215,left=narrow?24:118,right=narrow?166:425,top=narrow?113:90,dy=narrow?101:72;
  if(source==='distill-teacher'||source==='distill-student'){
   text(left,37,t('teacher'),20,'start','muted');text(right,37,t('student'),20,'start','emphasis');
   teacher.forEach((r,i)=>{
    const y=top+i*dy;text(18,narrow?y-36:y+18,val(r,locale),17,'start','muted');rect(left,y,barMax,24,'track',5);rect(right,y,barMax,24,'track',5);
    rect(left,y,r.numeric_value*barMax,24,'teacher-bar',5);text(left,y-9,number(r.numeric_value),18,'start','muted');
    const initial=d.initial[i],final=source==='distill-student'?d.final[i]:initial,iw=initial*barMax,fw=final*barMax;
    if(source==='distill-student')motion.push('@keyframes student'+i+'{0%,12%{width:'+iw+'px}78%,100%{width:'+fw+'px}}.student'+i+'{animation:student'+i+' '+seconds+'s ease-in-out both}');
    parts.push('<rect x="'+right+'" y="'+y+'" width="'+iw+'" height="24" rx="5" class="student-bar student'+i+'"/>');
    text(right,y-9,(source==='distill-student'?'p′=':'')+number(final),18);if(source==='distill-student'){path('M'+(right+iw)+' '+(y-4)+'V'+(y+29),'initial-marker');text(right,y+52,'p='+number(initial),17,'start','muted');}
    else flow('target'+i,left+barMax+8,y+12,right-10,y+12,i*5);
   });
   text(W/2,H-25,source==='distill-student'?'L: '+number(d.initialLoss)+' → '+number(d.finalLoss):'L = '+number(d.initialLoss),23,'middle',source==='distill-student'?'emphasis':'muted');
  }else if(source==='distill-target'){
   const rows=teacher.map((r,i)=>({label:val(r,locale),target:r.numeric_value,student:d.initial[i],loss:-r.numeric_value*Math.log(d.initial[i])}));
   rows.forEach((r,i)=>{const y=41+i*(narrow?87:73);frame(17,y,W-34,narrow?72:60,'',colors[i]);text(30,y+26,r.label,17,'start','muted');text(narrow?30:160,y+(narrow?55:26),'−'+number(r.target)+' ln('+number(r.student)+')',narrow?17:22);text(W-36,y+(narrow?26:48),'= '+number(r.loss),21,'end');move('loss'+i,W-42,y+30,W/2,H-61,i*4);});
   text(W/2,H-25,'L = '+number(d.initialLoss),29,'middle','emphasis');
  }else{
   const y0=53,dy=narrow?99:80;
   text(18,26,'p − t',19,'start','muted');text(W/2,26,'z → z′',19,'middle');text(W-18,26,'p′',19,'end','emphasis');
   teacher.forEach((r,i)=>{const y=y0+i*dy;frame(17,y,W-34,dy-15,'',colors[i]);text(29,y+27,val(r,locale),17,'start','muted');text(29,y+57,number(d.gradient[i]),18);
    text(W/2,y+29,number(d.logits[i].numeric_value)+' →',19,'middle','muted');text(W/2,y+58,number(d.updated[i]),21,'middle');
    text(W-33,y+45,number(d.final[i]),21,'end','emphasis');flow('gradient'+i,narrow?100:210,y+44,W/2-35,y+44,i*3);});
   text(W/2,H-20,'z′ → softmax → p′',20,'middle','muted');
  }
 }
 const css='text{fill:#eef7ff;font-family:Arial,"Microsoft YaHei",sans-serif;paint-order:stroke;stroke-width:0}.muted{fill:#a6bbd3}.emphasis{fill:#71f2dc;font-weight:700}.error{fill:#ffad9f}.panel{fill:#102139;stroke:#29415e}.storage-band{fill:#11233a;stroke:#243e59}.value-box{fill:#122942;stroke:#35627c}.code-box{fill:#153e47;stroke:#4db8ae}.matrix-cell{stroke:#8fcbd0;stroke-width:.6;fill-opacity:.88}.matrix-value{fill:#0a1829;font-weight:700}.bit{stroke:#33526f;stroke-width:.7}.bit-dark,.packet-text{fill:#071d2b;font-family:ui-monospace,Consolas,"Liberation Mono",monospace;font-weight:700}.bit-light{fill:#d2e3f3;font-family:monospace}.accent{fill:none;stroke-width:3;stroke-linecap:round}.accent-bar{fill:#5ce0d1}.wire,.ruler{fill:none;stroke:#506b88;stroke-width:1.5}.tick{fill:none;stroke:#92b4cc;stroke-width:2}.flow-track{fill:none;stroke-width:1.5;stroke-opacity:.4}.signal{fill:#71f2dc}.original-dot{fill:#b3cae2;stroke:#dcefff;stroke-width:1}.reconstructed-dot{fill:#5ce0d1;stroke:#a3fff0;stroke-width:1}.error-line{fill:none;stroke:#ff9e91;stroke-width:3;stroke-linecap:round}.retained-connection{fill:none;stroke:#4dd8c1;stroke-opacity:.7}.removed-connection{fill:none;stroke:#ff9d92;stroke-opacity:.85}.node{fill:#182f49;stroke:#86b0d1;stroke-width:2}.node-output{fill:#144147;stroke:#5ce0d1;stroke-width:2}.label-plate{fill:#0a172b;stroke:#263c54}.empty-slot{fill:#0b1729;stroke:#3b4b62;stroke-dasharray:4 4}.track{fill:#1b304a}.teacher-bar{fill:#8da8eb}.student-bar{fill:#5ce0d1}.initial-marker{fill:none;stroke:#a6c0d5;stroke-width:1;stroke-dasharray:3 3}';
 const backdrop='<defs><linearGradient id="stageBackground" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0c1b32"/><stop offset=".65" stop-color="#0b1529"/><stop offset="1" stop-color="#102a3d"/></linearGradient></defs><rect width="'+W+'" height="'+H+'" rx="16" fill="url(#stageBackground)"/><path d="M0 '+(H-1)+'H'+W+'" stroke="#24435b"/>';
 return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+W+' '+H+'" data-cycle="'+seconds+'" role="img" aria-label="'+esc(step['title_'+locale])+'"><title>'+esc(step['title_'+locale])+'</title><desc>'+esc(step['narration_'+locale])+'</desc><style>'+css+motion.join('')+'</style><g id="'+esc(source)+'">'+backdrop+parts.join('')+'</g></svg>';
}

