/* Source directory controls: progressive enhancement of the complete HTML registry. */
(() => {
  const root=document.querySelector('[data-source-directory]');
  if(!root)return;
  const one=s=>root.querySelector(s), all=s=>[...root.querySelectorAll(s)];
  const cards=all('.source-table-row'),tabs=all('[data-source-tab]');
  const category=one('#channel-category'),priority=one('#channel-priority'),query=one('#channel-query'),ecosystem=one('#channel-ecosystem');
  const offsets={news:0,industry:0,academic:0};
  let domain='news';
  function reset(){for(const k of Object.keys(offsets))offsets[k]=0;}
  function inDomain(){return cards.filter(c=>c.dataset.sourceDomain===domain);}
  function matches(c){return (priority.value!=='important'||c.dataset.sourcePriority==='core')&&(!category.value||category.value===c.dataset.sourceCategory)&&(domain!=='industry'||!ecosystem.value||ecosystem.value===c.dataset.sourceEcosystem)&&c.dataset.sourceSearch.toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase());}
  function categories(){
    const previous=category.value;
    category.replaceChildren();
    const option=(value,label)=>{const o=document.createElement('option');o.value=value;o.textContent=label;category.append(o);};
    option('','全部子类');
    const names=[...new Set(inDomain().map(c=>c.dataset.sourceCategory))];
    for(const name of names)option(name,name+' · '+inDomain().filter(c=>c.dataset.sourceCategory===name).length);
    category.value=names.includes(previous)?previous:'';
  }
  function render(){
    const rows=inDomain().filter(matches),size=20;
    offsets[domain]=Math.min(offsets[domain],Math.max(0,Math.floor((rows.length-1)/size)*size));
    tabs.forEach(t=>{const selected=t.dataset.sourceTab===domain;t.setAttribute('aria-selected',String(selected));t.tabIndex=selected?0:-1;});
    one('#channel-cards').setAttribute('aria-labelledby','source-tab-'+domain);
    one('#channel-ecosystem-field').hidden=domain!=='industry';
    all('[data-source-panel]').forEach(p=>p.hidden=p.dataset.sourcePanel!==domain);
    cards.forEach(c=>c.hidden=true);
    rows.slice(offsets[domain],offsets[domain]+size).forEach(c=>c.hidden=false);
    all('[data-source-subcategory]').forEach(g=>g.hidden=![...g.querySelectorAll('.source-table-row')].some(c=>!c.hidden));
    one('#channel-empty').hidden=rows.length>0;
    one('#channel-pagination').hidden=rows.length<=size;
    one('#channel-range').textContent=`${rows.length?offsets[domain]+1:0}–${Math.min(offsets[domain]+size,rows.length)} / ${rows.length}`;
    one('#channel-prev').disabled=offsets[domain]===0;
    one('#channel-next').disabled=offsets[domain]+size>=rows.length;
    const label=tabs.find(t=>t.dataset.sourceTab===domain).textContent;
    one('#channel-status').textContent=`${label} · ${rows.length} 个信源 · 人工整理，具体进展见本期动态`;
  }
  function choose(key){domain=key;category.value='';ecosystem.value='';query.value='';reset();categories();render();}
  tabs.forEach((tab,index)=>{
    tab.addEventListener('click',()=>choose(tab.dataset.sourceTab));
    tab.addEventListener('keydown',event=>{
      let i;if(event.key==='ArrowRight')i=(index+1)%tabs.length;else if(event.key==='ArrowLeft')i=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')i=0;else if(event.key==='End')i=tabs.length-1;else return;
      event.preventDefault();choose(tabs[i].dataset.sourceTab);tabs[i].focus();
    });
  });
  for(const control of [category,priority,query,ecosystem])control.addEventListener(control===query?'input':'change',()=>{reset();render();});
  for(const direction of ['prev','next'])one('#channel-'+direction).addEventListener('click',()=>{offsets[domain]+=direction==='prev'?-20:20;render();one('#channel-status').scrollIntoView({block:'nearest'});});
  function deepLink(){
    const hash=location.hash,target=cards.find(c=>'#'+c.id===hash);
    if(target){
      if(target.dataset.sourcePriority!=='core')priority.value='all';
      choose(target.dataset.sourceDomain);
      offsets[domain]=Math.floor(inDomain().filter(matches).indexOf(target)/20)*20;
      render();target.scrollIntoView({block:'start'});return;
    }
    const layer=all('[data-source-subcategory]').find(g=>'#'+g.id===hash&&g.id);
    if(layer){choose('industry');category.value=layer.dataset.sourceSubcategory;render();layer.scrollIntoView({block:'start'});return;}
    const legacy=hash==='#industry-sources-ascend'?'ascend':hash==='#industry-sources-general'?'general':null;
    if(legacy){choose('industry');ecosystem.value=legacy;render();one('#sources-industry').scrollIntoView({block:'start'});return;}
    const tab=tabs.find(t=>hash==='#sources-'+t.dataset.sourceTab);
    if(tab){choose(tab.dataset.sourceTab);one('#sources-'+domain).scrollIntoView({block:'start'});}
  }
  categories();render();deepLink();window.addEventListener('hashchange',deepLink);
})();
