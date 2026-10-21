function markNavigation(){
 const current=location.pathname.replace(/\.html$/,'').replace(/\/index$/,'/')||'/';
 document.querySelectorAll('nav a').forEach(a=>{const u=new URL(a.href),path=u.pathname.replace(/\.html$/,'').replace(/\/index$/,'/');const active=u.hash?location.hash===u.hash:current===path&&!location.hash;if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
}
markNavigation();addEventListener('hashchange',markNavigation);
