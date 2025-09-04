// ===== HAMBÚRGUER / NAV DRAWER =====
const burger = document.getElementById('burger');
const drawer = document.getElementById('navDrawer');
burger?.addEventListener('click', () => {
  drawer.classList.toggle('open');
  const expanded = burger.getAttribute('aria-expanded') === 'true';
  burger.setAttribute('aria-expanded', String(!expanded));
});

// ===== MODAL helpers (dialog nativo) =====
window.openModal = (id) => {
  const el = document.getElementById(id);
  if (el?.showModal) el.showModal();
  else el?.classList.add('open');
};
window.closeModal = (id) => {
  const el = document.getElementById(id);
  if (el?.close) el.close();
  else el?.classList.remove('open');
};

// ===== CARROSSEL DE BANNERS =====
(function(){
  const slider = document.getElementById('slider');
  const track  = document.getElementById('slides');
  const prev   = document.getElementById('prev');
  const next   = document.getElementById('next');
  const dotsEl = document.getElementById('dots');

  if(!slider || !track) return;
  const slides = Array.from(track.children);
  if(slides.length === 0) return;

  let index = 0;
  const total = slides.length;
  let timer = null;
  const AUTO = 5000;

  // dots
  for(let i=0;i<total;i++){
    const d = document.createElement('button');
    d.className = 'dot' + (i===0 ? ' active':'');
    d.addEventListener('click', ()=> go(i, true));
    dotsEl.appendChild(d);
  }
  const dots = Array.from(dotsEl.children);

  function go(i, user=false){
    index = (i + total) % total;
    track.style.transform = `translateX(-${index*100}%)`;
    dots.forEach((el,idx)=> el.classList.toggle('active', idx===index));
    if(user){ restart(); }
  }
  function nextSlide(){ go(index+1); }
  function prevSlide(){ go(index-1); }
  function start(){ if(!timer) timer = setInterval(nextSlide, AUTO); }
  function stop(){ clearInterval(timer); timer = null; }
  function restart(){ stop(); start(); }

  next?.addEventListener('click', nextSlide);
  prev?.addEventListener('click', prevSlide);

  slider.addEventListener('mouseenter', stop);
  slider.addEventListener('mouseleave', start);

  let sx=0, dx=0;
  slider.addEventListener('touchstart',(e)=>{sx=e.touches[0].clientX;dx=0;stop();},{passive:true});
  slider.addEventListener('touchmove',(e)=>{dx=e.touches[0].clientX-sx;},{passive:true});
  slider.addEventListener('touchend',()=>{if(Math.abs(dx)>40){dx<0?nextSlide():prevSlide();}start();});

  if(total>1) start();
})();
