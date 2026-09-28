/* ASO Vending Machine — comportamiento compartido.
   El sitio funciona sin JavaScript (todo el contenido está en el HTML);
   esto solo agrega el menú móvil y el armado de mensajes de WhatsApp. */
(() => {
  "use strict";
  const WA = document.body.dataset.wa;            // viene de build.py (CONFIG["whatsapp"])
  const waUrl = texto => "https://wa.me/" + WA + (texto ? "?text=" + encodeURIComponent(texto) : "");

  /* — Menú móvil: altura de la cabecera y cierre al navegar — */
  const top = document.querySelector(".top");
  const menu = document.querySelector(".menu-movil");
  const medir = () => top && document.documentElement.style.setProperty("--alto-top", top.offsetHeight + "px");
  medir(); addEventListener("resize", medir, { passive: true });
  if (menu) {
    menu.addEventListener("toggle", () => { medir(); document.body.style.overflow = menu.open ? "hidden" : ""; });
    menu.querySelectorAll("a").forEach(a => a.addEventListener("click", () => { menu.open = false; }));
    addEventListener("keydown", e => { if (e.key === "Escape" && menu.open) menu.open = false; });
  }

  /* — Formularios que terminan en WhatsApp — */
  document.querySelectorAll("form[data-wa]").forEach(form => {
    const err = form.querySelector(".err");
    form.addEventListener("submit", e => {
      e.preventDefault();
      if (form.querySelector('[name="web"]')?.value.trim()) return;       // trampa anti-bot
      const faltan = [...form.querySelectorAll("[required]")].filter(el => !el.value.trim());
      if (faltan.length) {
        if (err) err.textContent = "Completa los campos marcados para poder responderte.";
        faltan[0].focus();
        return;
      }
      if (err) err.textContent = "";
      const lineas = [form.dataset.wa];
      form.querySelectorAll("[data-etiqueta]").forEach(el => {
        const v = el.value.trim();
        if (v) lineas.push(el.dataset.etiqueta + ": " + v);
      });
      window.open(waUrl(lineas.join("\n")), "_blank", "noopener");
    });
  });

  /* — Cotizador: recomienda un tipo de equipo (orientativo) — */
  const cot = document.getElementById("cotizador");
  if (cot) {
    const salida = document.getElementById("recomendacion");
    const val = n => (cot.querySelector(`[name="${n}"]:checked`) || {}).value || "";
    const multi = n => [...cot.querySelectorAll(`[name="${n}"]:checked`)].map(i => i.value);
    let resumen = "";
    cot.addEventListener("submit", e => {
      e.preventDefault();
      const lugar = val("lugar"), personas = val("personas"), horario = val("horario"), espacio = val("espacio");
      const quiere = multi("quiere");
      const err = cot.querySelector(".err");
      if (!lugar || !personas || !horario || !espacio || !quiere.length) {
        err.textContent = "Responde las cinco preguntas para ver la recomendación.";
        return;
      }
      err.textContent = "";
      const snacks = quiere.includes("Snacks"), bebidas = quiere.includes("Bebidas frías"), cafe = quiere.includes("Café");
      const equipos = [];
      if (snacks && bebidas) {
        equipos.push(espacio === "Poco espacio o un solo enchufe" || personas === "Menos de 30"
          ? "Una máquina combinada de snacks y bebidas"
          : "Máquina de snacks y máquina de bebidas frías por separado, o una combinada si prefieres ocupar menos frente");
      } else if (snacks) equipos.push("Una máquina de snacks (espirales)");
      else if (bebidas) equipos.push("Una máquina de bebidas frías");
      if (cafe) equipos.push("Una máquina de café automática");
      const notas = [];
      if (horario !== "Horario de oficina") notas.push("Como el lugar funciona fuera del horario comercial, la máquina cubre justo la franja en que no hay dónde comprar.");
      if (personas === "Menos de 30") notas.push("Con poco flujo diario lo evaluamos en la visita y te decimos con franqueza si el punto da o no para una máquina.");
      if (lugar === "Colegio") notas.push("En colegios el surtido completo debe ir sin sellos de advertencia (Ley 20.606).");
      salida.querySelector("[data-equipos]").innerHTML = equipos.map(t => "<li>" + t + "</li>").join("");
      salida.querySelector("[data-notas]").innerHTML = notas.map(t => "<li>" + t + "</li>").join("");
      salida.hidden = false;
      resumen = [
        "Hola, quiero una propuesta de máquina expendedora.",
        "Lugar: " + lugar, "Personas al día: " + personas, "Horario: " + horario,
        "Espacio: " + espacio, "Busco: " + quiere.join(", "),
        "Recomendación del sitio: " + equipos.join(" + ")
      ].join("\n");
      salida.focus();
    });
    document.getElementById("enviarRecomendacion")?.addEventListener("click", () => {
      if (resumen) window.open(waUrl(resumen), "_blank", "noopener");
    });
  }
})();
