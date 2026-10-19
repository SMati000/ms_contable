(function () {
  const visor = document.getElementById("visor");
  const contenedor = document.getElementById("contenedor-recibo");
  const recibo = document.getElementById("recibo-svg");
  const lupa = document.getElementById("lupa");
  const lupaSvg = document.getElementById("lupa-contenido");
  const nivelZoom = document.getElementById("nivel-zoom");
  const botonLupa = document.getElementById("alternar-lupa");

  if (!visor || !contenedor || !recibo || !lupa || !lupaSvg) return;

  const factorLupa = 2.5;
  const minimoZoom = 0.5;
  const maximoZoom = 6;
  const viewBox = recibo.viewBox.baseVal;
  const copiaRecibo = recibo.cloneNode(true);
  copiaRecibo.removeAttribute("id");
  copiaRecibo.setAttribute("width", "100%");
  copiaRecibo.setAttribute("height", "100%");
  copiaRecibo.style.transform = "none";
  lupaSvg.appendChild(copiaRecibo);

  let zoom = 1;
  let x = 0;
  let y = 0;
  let arrastre = null;
  let lupaActiva = false;
  let ultimaPosicion = null;

  function dimensoes() {
    return {
      largura: visor.clientWidth,
      altura: visor.clientHeight,
    };
  }

  function limitarDesplazamiento() {
    const { largura, altura } = dimensoes();
    const larguraRecibo = recibo.clientWidth * zoom;
    const alturaRecibo = recibo.clientHeight * zoom;

    if (zoom <= 1) {
      x = (largura - larguraRecibo) / 2;
      y = (altura - alturaRecibo) / 2;
      return;
    }

    x = Math.max(largura - larguraRecibo, Math.min(0, x));
    y = Math.max(altura - alturaRecibo, Math.min(0, y));
  }

  function aplicarTransformacion() {
    limitarDesplazamiento();
    contenedor.style.transform = `translate(${x}px, ${y}px) scale(${zoom})`;
    nivelZoom.value = `${Math.round(zoom * 100)}%`;
    nivelZoom.textContent = nivelZoom.value;
  }

  function acercarEn(nuevoZoom, puntoX, puntoY) {
    const limitado = Math.max(minimoZoom, Math.min(maximoZoom, nuevoZoom));
    const escala = limitado / zoom;
    x = puntoX - (puntoX - x) * escala;
    y = puntoY - (puntoY - y) * escala;
    zoom = limitado;
    aplicarTransformacion();
    actualizarLupa();
  }

  function alternarLupa(estado) {
    lupaActiva = estado;
    lupa.classList.toggle("activa", lupaActiva);
    botonLupa.setAttribute("aria-pressed", String(lupaActiva));
    if (lupaActiva) actualizarLupa();
  }

  function actualizarLupa() {
    if (!lupaActiva || !ultimaPosicion) return;

    const { largura, altura } = dimensoes();
    const anchoLupa = lupa.offsetWidth;
    const altoLupa = lupa.offsetHeight;
    const centroX = ultimaPosicion.x;
    const centroY = ultimaPosicion.y;
    const xLupa = Math.max(0, Math.min(largura - anchoLupa, centroX - anchoLupa / 2));
    const yLupa = Math.max(0, Math.min(altura - altoLupa, centroY - altoLupa / 2));
    lupa.style.left = `${xLupa}px`;
    lupa.style.top = `${yLupa}px`;

    const escalaSvgX = viewBox.width / recibo.clientWidth;
    const escalaSvgY = viewBox.height / recibo.clientHeight;
    const centroSvgX = ((centroX - x) / zoom) * escalaSvgX;
    const centroSvgY = ((centroY - y) / zoom) * escalaSvgY;
    const anchoViewBox = (anchoLupa * escalaSvgX) / (zoom * factorLupa);
    const altoViewBox = (altoLupa * escalaSvgY) / (zoom * factorLupa);
    const inicioX = centroSvgX - anchoViewBox / 2;
    const inicioY = centroSvgY - altoViewBox / 2;

    copiaRecibo.setAttribute(
      "viewBox",
      `${inicioX} ${inicioY} ${anchoViewBox} ${altoViewBox}`,
    );
  }

  document.getElementById("imprimir").addEventListener("click", function () {
    window.print();
  });

  document.getElementById("acercar").addEventListener("click", function () {
    const { largura, altura } = dimensoes();
    acercarEn(zoom * 1.25, largura / 2, altura / 2);
  });

  document.getElementById("alejar").addEventListener("click", function () {
    const { largura, altura } = dimensoes();
    acercarEn(zoom / 1.25, largura / 2, altura / 2);
  });

  document.getElementById("restablecer").addEventListener("click", function () {
    zoom = 1;
    x = 0;
    y = 0;
    aplicarTransformacion();
    actualizarLupa();
  });

  botonLupa.addEventListener("click", function () {
    alternarLupa(!lupaActiva);
  });

  visor.addEventListener("wheel", function (evento) {
    evento.preventDefault();
    const rectangulo = visor.getBoundingClientRect();
    const puntoX = evento.clientX - rectangulo.left;
    const puntoY = evento.clientY - rectangulo.top;
    const nuevoZoom = zoom * Math.exp(-evento.deltaY * 0.0015);
    acercarEn(nuevoZoom, puntoX, puntoY);
  }, { passive: false });

  visor.addEventListener("pointerdown", function (evento) {
    if (evento.button !== 0) return;
    arrastre = { puntero: evento.pointerId, x: evento.clientX, y: evento.clientY };
    visor.setPointerCapture(evento.pointerId);
    visor.classList.add("arrastrando");
    evento.preventDefault();
  });

  visor.addEventListener("pointermove", function (evento) {
    const rectangulo = visor.getBoundingClientRect();
    ultimaPosicion = {
      x: evento.clientX - rectangulo.left,
      y: evento.clientY - rectangulo.top,
    };

    if (arrastre && arrastre.puntero === evento.pointerId) {
      x += evento.clientX - arrastre.x;
      y += evento.clientY - arrastre.y;
      arrastre.x = evento.clientX;
      arrastre.y = evento.clientY;
      aplicarTransformacion();
    }
    actualizarLupa();
  });

  function terminarArrastre(evento) {
    if (!arrastre || arrastre.puntero !== evento.pointerId) return;
    arrastre = null;
    visor.classList.remove("arrastrando");
  }

  visor.addEventListener("pointerup", terminarArrastre);
  visor.addEventListener("pointercancel", terminarArrastre);
  visor.addEventListener("lostpointercapture", terminarArrastre);

  window.addEventListener("resize", function () {
    aplicarTransformacion();
    actualizarLupa();
  });

  aplicarTransformacion();
})();
