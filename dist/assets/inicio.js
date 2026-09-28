/* ASO — video de la portada gobernado por el scroll */
/* ═══════════════════════════════════════════════════════════
   2 · Video gobernado por el scroll
   El video nunca se reproduce: su tiempo = progreso de scroll.
   Los MP4 vienen codificados con todos los cuadros clave (-g 1),
   así retroceder cuesta lo mismo que avanzar.
   ═══════════════════════════════════════════════════════════ */
(() => {
  "use strict";

  /* Medidas reales del gabinete dentro del cuadro 16:9 del video.
     Con esto se calcula el tamaño para que la máquina ocupe
     PROPORCION del área de la pantalla. Ajusta PROPORCION y listo. */
  const PROPORCION = 0.25;                  // ← la máquina ocupa este % del área de pantalla
  const MAQ = { w: 0.292, h: 0.843 };       // fracción del cuadro 16:9 que ocupa la máquina cerrada
  const AR  = 16 / 9;

  const FUENTES = {
    grande:  { src: "/assets/aso-scroll.mp4",    fps: 20 },   // 1440x810
    chica:   { src: "/assets/aso-scroll-sm.mp4", fps: 18 }    // 1280x720
  };

  const video  = document.getElementById("bg");
  const poster = document.getElementById("posterImg");
  const fill   = document.getElementById("railFill");
  const rail   = document.querySelector(".rail");
  const top    = document.querySelector(".top");
  const root   = document.documentElement;

  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const clamp  = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const suave  = t => t * t * (3 - 2 * t);

  /* — Elección de archivo: pantalla chica o conexión pobre → versión liviana — */
  const con = navigator.connection || {};
  const liviano = innerWidth < 900 || con.saveData === true ||
                  /^(slow-2g|2g|3g)$/.test(con.effectiveType || "");
  const FUENTE = liviano ? FUENTES.chica : FUENTES.grande;
  const FPS = FUENTE.fps;

  let duracion = 0, maxScroll = 1, objetivo = 0, actual = 0, ultimoCuadro = -1;
  let listo = false, vertical = false, tPrev = performance.now();

  /* — Encuadre — */
  function encajar(Wp, Hp) {
    return (Wp / Hp >= AR) ? { w: Hp * AR, h: Hp } : { w: Wp, h: Wp / AR };
  }
  function dimensionar() {
    const Wp = innerWidth, Hp = innerHeight;
    vertical = Wp / Hp < 1.15;
    const { w: Wv, h: Hv } = encajar(Wp, Hp);

    // escala para que (máquina ÷ pantalla) = PROPORCION
    let s = Math.sqrt((PROPORCION * Wp * Hp) / (MAQ.w * MAQ.h * Wv * Hv));
    // tope de alto: la máquina nunca se sale por arriba ni por abajo
    s = Math.min(s, (vertical ? 0.52 : 0.88) * Hp / (MAQ.h * Hv));
    s = vertical ? clamp(s, 1.0, 2.05) : clamp(s, 0.85, 1.12);

    [video, poster].forEach(el => {
      el.style.width  = Wv + "px";
      el.style.height = Hv + "px";
      el.style.marginLeft = (-Wv / 2) + "px";
      el.style.marginTop  = (-Hv / 2) + "px";
      el.style.transformOrigin = "50% 50%";
    });
    return s;
  }
  let escala = 1;

  /* En el inicio la máquina se corre a la derecha para dejar
     el texto sobre negro limpio; vuelve al centro al 12% del scroll. */
  function encuadrar(p) {
    const e = suave(clamp(p / 0.12));
    let dx = 0, dy = 0, k = escala;
    if (vertical) {
      // en vertical la máquina sube y cede un poco de tamaño después del inicio,
      // para que el texto de las secciones tenga su propia franja limpia
      const v = suave(clamp(p / 0.16));
      dy = (-0.155 - 0.115 * v) * innerHeight;
      k  = escala * (1 - 0.14 * v);
    } else {
      // arranca corrida a la derecha (texto sobre negro limpio) y queda
      // ligeramente descentrada para que el texto nunca la pise de lleno
      dx = (0.06 + (1 - e) * 0.085) * innerWidth;
      k  = escala * (1 + 0.04 * e);
    }
    const t = `translate3d(${dx.toFixed(1)}px,${dy.toFixed(1)}px,0) scale(${k.toFixed(4)})`;
    video.style.transform = t;
    poster.style.transform = t;
  }

  /* — Riel — */
  const secs = [...document.querySelectorAll("main .sec")];
  const ticks = secs.map(s => {
    const a = document.createElement("a");
    a.href = "#" + s.id;
    a.innerHTML = `<span>${s.dataset.label}</span>`;
    a.setAttribute("aria-label", s.dataset.label);
    rail.appendChild(a);
    return a;
  });
  function ubicarTicks() {
    secs.forEach((s, i) => {
      const y = s.getBoundingClientRect().top + scrollY;
      ticks[i].style.top = (clamp(y / maxScroll) * 100) + "%";
    });
  }

  function medir() {
    escala = dimensionar();
    maxScroll = Math.max(1, root.scrollHeight - innerHeight);
    ubicarTicks();
  }

  function alScrollear() {
    const p = clamp(scrollY / maxScroll);
    objetivo = p * duracion;
    // tope < 1: siempre queda algo de máquina visible, nunca se apaga del todo
    root.style.setProperty("--scrim", (clamp(p / 0.09) * 0.93).toFixed(3));
    fill.style.transform = "scaleY(" + p.toFixed(4) + ")";
    encuadrar(p);
    top.classList.toggle("stuck", scrollY > 40);
    let on = 0;
    secs.forEach((s, i) => { if (s.getBoundingClientRect().top <= innerHeight * 0.5) on = i; });
    ticks.forEach((t, i) => { t.classList.toggle("on", i === on); t.classList.toggle("past", i < on); });
  }

  function latir(ahora) {
    requestAnimationFrame(latir);
    if (!listo) return;
    const dt = Math.min(0.1, (ahora - tPrev) / 1000); tPrev = ahora;
    // seguimiento exponencial: el video alcanza al scroll sin saltos
    actual += (objetivo - actual) * (1 - Math.exp(-dt * 13));
    if (Math.abs(objetivo - actual) < 0.5 / FPS) actual = objetivo;
    const cuadro = Math.round(actual * FPS);
    if (cuadro !== ultimoCuadro && !video.seeking) {
      ultimoCuadro = cuadro;
      video.currentTime = Math.min(duracion - 0.001, (cuadro + 0.02) / FPS);
    }
  }

  function arrancar() {
    if (listo) return;
    duracion = video.duration || 20;
    listo = true;
    video.pause();
    poster.style.display = "none";
    medir(); alScrollear();
    actual = objetivo;
  }

  /* — Arranque — */
  if (reduce) {
    // Sin movimiento: queda el cuadro inicial fijo
    poster.style.display = "block";
    video.style.display = "none";
    medir();
    encuadrar(1);
    root.style.setProperty("--scrim", "1");
    addEventListener("resize", () => { medir(); encuadrar(1); }, { passive: true });
  } else {
    poster.style.display = "block";
    medir(); encuadrar(0);

    /* El video se descarga completo y se sirve desde memoria (blob).
       Motivo: si el servidor no acepta peticiones por rango (Cloudflare
       responde 200 sin Accept-Ranges), el navegador marca el video como
       no desplazable y currentTime vuelve siempre a 0. Un blob siempre
       es desplazable, en cualquier navegador, incluido Safari/iOS. */
    const barra = document.getElementById("carga");
    async function cargarBlob(src) {
      const r = await fetch(src);
      if (!r.ok) throw new Error("HTTP " + r.status);
      const total = +r.headers.get("content-length") || 0;
      if (!r.body || !total) return URL.createObjectURL(await r.blob());
      const lector = r.body.getReader(), partes = [];
      let recibido = 0;
      for (;;) {
        const { done, value } = await lector.read();
        if (done) break;
        partes.push(value); recibido += value.length;
        barra.style.transform = "scaleX(" + (recibido / total).toFixed(3) + ")";
      }
      return URL.createObjectURL(new Blob(partes, { type: "video/mp4" }));
    }
    barra.classList.add("on");
    cargarBlob(FUENTE.src)
      .then(url => { video.src = url; })
      .catch(() => { video.src = FUENTE.src; })   // respaldo: carga directa
      .finally(() => {
        video.load();
        barra.style.transform = "scaleX(1)";
        setTimeout(() => barra.classList.remove("on"), 350);
      });

    // iOS/Safari solo permite buscar cuadros si el video "arrancó" una vez
    const destrabar = () => { video.play().then(() => video.pause()).catch(() => {}); };
    video.addEventListener("loadedmetadata", arrancar, { once: true });
    video.addEventListener("loadeddata", destrabar, { once: true });
    video.addEventListener("canplay", arrancar, { once: true });
    // Si el video no carga, la página sigue viva con el cuadro fijo
    video.addEventListener("error", () => {
      listo = false;
      video.style.display = "none";
      poster.style.display = "block";
    }, { once: true });
    ["touchstart", "pointerdown", "keydown", "wheel"].forEach(ev =>
      addEventListener(ev, destrabar, { once: true, passive: true }));
    if (video.readyState >= 1) arrancar();

    addEventListener("scroll", alScrollear, { passive: true });
    addEventListener("resize", () => { medir(); alScrollear(); }, { passive: true });
    addEventListener("orientationchange", () => setTimeout(() => { medir(); alScrollear(); }, 220));
    addEventListener("load", () => { medir(); alScrollear(); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { medir(); alScrollear(); });
    requestAnimationFrame(latir);
    alScrollear();
  }

  /* — Aparición de bloques — */
  if ("IntersectionObserver" in window && !reduce) {
    const io = new IntersectionObserver((entradas) => {
      entradas.forEach(e => { if (e.isIntersecting) { e.target.classList.add("seen"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -12% 0px", threshold: .12 });
    document.querySelectorAll(".rise").forEach(el => io.observe(el));
  } else {
    document.querySelectorAll(".rise").forEach(el => el.classList.add("seen"));
  }
})();
