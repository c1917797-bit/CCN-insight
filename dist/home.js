const motion=document.getElementById('motion');
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
if(reduced){motion.hidden=true;}
motion.addEventListener('click',()=>{const paused=document.body.classList.toggle('paused');motion.setAttribute('aria-pressed',String(paused));motion.textContent=paused?'播放动效':'暂停动效';});
