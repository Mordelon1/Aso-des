#!/usr/bin/env python3
"""
ASO Vending Machine — generador del sitio estático asoexpendedoras.cl

Uso:
    pip install markdown
    python build.py

Lee las entradas del blog desde contenido/blog/*.md, copia static/ y
escribe el sitio completo en dist/. Lo que se sube a Cloudflare es dist/.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path

import markdown

# ═══════════════════════════════════════════════════════════
# 1 · Datos del negocio — se cambian solo aquí
# ═══════════════════════════════════════════════════════════
CONFIG = {
    "dominio": "https://asoexpendedoras.cl",
    "marca": "ASO Vending Machine",
    "razon_social": "Asesorías y Servicios Organizacionales SpA",
    "rut": "77.711.542-1",
    "whatsapp": "56937368898",            # internacional, sin + ni espacios
    "telefono_visible": "+56 9 3736 8898",
    "telefono_schema": "+56937368898",
    "correo": "johanbustospardo@gmail.com",
    "ciudad": "Concepción",
    "region": "Región del Biobío",
    "comunas": ["Concepción", "Talcahuano", "San Pedro de la Paz", "Chiguayante", "Hualpén", "Penco"],
    "fundacion": "2023",
}

RAIZ = Path(__file__).parent
DIST = RAIZ / "dist"
HOY = dt.date.today().isoformat()
E = html.escape


# ═══════════════════════════════════════════════════════════
# 2 · Sectores (una página por tipo de cliente — sin nombres de clientes)
# ═══════════════════════════════════════════════════════════
SECTORES = [
    {
        "slug": "oficinas",
        "nombre": "Oficinas y edificios corporativos",
        "corto": "Oficinas",
        "title": "Máquinas expendedoras para oficinas en Concepción",
        "desc": "Vending de snacks, bebidas y café para oficinas y edificios corporativos del Gran Concepción. Instalación, reposición y mantención a cargo nuestro.",
        "h1": "Vending para <em>oficinas y edificios corporativos</em>",
        "lead": "Reemplaza la sala de café desabastecida y las salidas de veinte minutos al almacén de la esquina.",
        "resuelve": "En una oficina el problema rara vez es que no haya dónde comprar: es el tiempo que se pierde bajando a buscar algo y la administración del café compartido, que siempre termina siendo tarea de alguien que no la pidió.",
        "puntos": [
            "Café preparado en la máquina, sin que nadie tenga que comprar insumos ni lavar la jarra.",
            "Snacks y bebidas disponibles toda la jornada, incluida la tarde cuando ya cerró el casino.",
            "Sin caja chica ni cobros entre compañeros: cada persona paga con tarjeta en la máquina.",
        ],
        "secciones": [
            ("Cómo lo dimensionamos", [
                "Para una oficina de un solo piso solemos partir con un equipo combinado de snacks y bebidas, que ocupa poco frente. Si hay varios pisos, conviene un punto en el piso de mayor circulación antes que uno por piso.",
                "El café va en un equipo aparte cuando el consumo lo justifica; lo definimos contigo en la visita.",
            ]),
            ("Lo que necesitamos del edificio", [
                "Autorización de la administración para ingresar el equipo, un punto eléctrico de 220 V cercano y un horario acordado para las visitas de reposición.",
            ]),
        ],
    },
    {
        "slug": "clinicas-y-centros-medicos",
        "nombre": "Clínicas y centros de salud",
        "corto": "Salud",
        "title": "Máquinas expendedoras para clínicas y centros médicos",
        "desc": "Vending para clínicas, centros médicos y veterinarios en el Biobío: servicio 24/7 para turnos y salas de espera, con surtido adaptable a la política del recinto.",
        "h1": "Vending para <em>clínicas y centros de salud</em>",
        "lead": "Salas de espera con horarios largos y turnos que no calzan con ningún horario comercial.",
        "resuelve": "Un centro de salud tiene dos públicos usando el mismo pasillo: el personal en turno, que necesita algo a las tres de la mañana, y el acompañante que lleva horas esperando. Ninguno de los dos tiene dónde comprar a esa hora.",
        "puntos": [
            "Disponibilidad continua, incluidos turnos de noche, fines de semana y festivos.",
            "Surtido con alternativas bajas en azúcar y sin sellos, coherente con el lugar.",
            "Aplica también a clínicas veterinarias y centros de atención con público en espera.",
        ],
        "secciones": [
            ("Ubicación y coordinación", [
                "Definimos la ubicación considerando circulación de camillas, vías de evacuación y los criterios internos del establecimiento. La reposición se coordina en horarios de baja afluencia y nuestro personal cumple el protocolo de acceso que corresponda.",
            ]),
            ("Surtido según la política del recinto", [
                "Si el establecimiento tiene una política de alimentación definida, la aplicamos completa al armar el mix. Nos indican el criterio y ajustamos; no proponemos productos que la contradigan.",
            ]),
        ],
    },
    {
        "slug": "universidades-e-institutos",
        "nombre": "Universidades e institutos",
        "corto": "Educación superior",
        "title": "Máquinas expendedoras para universidades e institutos",
        "desc": "Vending para campus universitarios, institutos y centros de formación técnica en Concepción: reposición según calendario académico y pago con tarjeta.",
        "h1": "Vending para <em>universidades e institutos</em>",
        "lead": "Consumo concentrado en los minutos entre bloques, y casi nulo en receso académico.",
        "resuelve": "El campus tiene un patrón de demanda muy marcado: peaks cortos y altos entre clases, y períodos completos de baja actividad en vacaciones. Una máquina operada con frecuencia fija se agota en el peak y acumula producto en el receso.",
        "puntos": [
            "Reposición ajustada al calendario académico, no a un itinerario fijo.",
            "Pago con tarjeta de débito o crédito, que es como efectivamente paga el público estudiantil.",
            "Surtido orientado a precio accesible y formatos individuales.",
        ],
        "secciones": [
            ("Dónde conviene instalar", [
                "Los puntos que rinden son los de paso obligado: hall de acceso, bibliotecas con horario extendido y pabellones con bloques continuos. Las salas de estudio nocturnas suelen ser el mejor punto del campus, porque son las únicas abiertas cuando ya no hay casino.",
            ]),
            ("Concesiones y licitaciones", [
                "Podemos participar de concesiones y licitaciones internas. Entregamos la documentación tributaria y societaria que el proceso exija, con factura electrónica.",
            ]),
        ],
    },
    {
        "slug": "industria-y-faenas",
        "nombre": "Plantas, industria y faenas",
        "corto": "Industria",
        "title": "Máquinas expendedoras para industria y faenas",
        "desc": "Vending para plantas industriales, maestranzas y faenas del Biobío: servicio en los tres turnos, hidratación y opción de subsidio como beneficio.",
        "h1": "Vending para <em>plantas, industria y faenas</em>",
        "lead": "Turnos rotativos, distancia al casino y puntos donde nadie va a abrir un local.",
        "resuelve": "En planta el casino tiene horario y el turno de noche no lo alcanza. Portería, garita y áreas alejadas quedan fuera del radio de cualquier comercio. El vending cubre exactamente esa franja.",
        "puntos": [
            "Servicio disponible en los tres turnos, sin personal adicional en el lugar.",
            "Agua e isotónicas en puntos de trabajo con carga física o exposición a calor.",
            "Posibilidad de subsidiar el precio como beneficio de bienestar.",
        ],
        "secciones": [
            ("Condiciones del punto", [
                "Instalamos en áreas techadas, limpias y con acceso razonable para la reposición. En ambientes con polvo, humedad o vibración evaluamos el punto antes de comprometer el equipo: hay ubicaciones donde una máquina estándar no corresponde y preferimos decirlo antes.",
            ]),
            ("Acceso a faena", [
                "Nuestro personal cumple con la inducción, los elementos de protección y la documentación de acceso que exija la empresa mandante. Coordinamos las visitas con prevención de riesgos y con el horario de menor movimiento.",
            ]),
        ],
    },
    {
        "slug": "sucursales-y-atencion-de-publico",
        "nombre": "Sucursales y atención de público",
        "corto": "Atención de público",
        "title": "Máquinas expendedoras para sucursales y salas de espera",
        "desc": "Máquinas de café y snacks para sucursales, oficinas de atención de público y salas de espera en Concepción. Mejora la espera sin sumar tareas al personal.",
        "h1": "Vending para <em>sucursales y atención de público</em>",
        "lead": "Una espera con café es una espera distinta, y no le suma trabajo a quien atiende.",
        "resuelve": "En una sucursal el tiempo de espera es parte de la experiencia del cliente. Ofrecer café o algo para comer mejora esa espera, pero montar una cafetería no es el negocio de la sucursal. Una máquina bien ubicada lo resuelve sin personal adicional.",
        "puntos": [
            "Máquinas de café de presentación cuidada, pensadas para quedar a la vista del público.",
            "Pago con tarjeta en el mismo equipo: el personal de la sucursal no cobra ni maneja dinero.",
            "Número de contacto en la máquina para que el cliente resuelva cualquier problema directo con nosotros.",
        ],
        "secciones": [
            ("Imagen del espacio", [
                "En un espacio de atención la máquina queda a la vista. Cuidamos la ubicación, la limpieza y el estado del equipo para que sume a la imagen del lugar y no al revés.",
            ]),
            ("Propuesta formal", [
                "Para instituciones que requieren una evaluación interna preparamos una propuesta escrita con el modelo, las dimensiones, el consumo eléctrico y el plan de servicio, lista para presentar a quien aprueba.",
            ]),
        ],
    },
    {
        "slug": "gimnasios-y-recintos-deportivos",
        "nombre": "Gimnasios y recintos deportivos",
        "corto": "Deporte",
        "title": "Vending para gimnasios y recintos deportivos",
        "desc": "Vending de agua, isotónicas y snacks para gimnasios, clubes y recintos deportivos del Gran Concepción, con surtido pensado para antes y después de entrenar.",
        "h1": "Vending para <em>gimnasios y recintos deportivos</em>",
        "lead": "Hidratación y algo para recuperar, justo donde se entrena.",
        "resuelve": "Quien entrena necesita agua o una isotónica en el momento, no a dos cuadras. Un gimnasio o recinto deportivo con horario extendido tiene la demanda, pero no siempre el personal para atender un kiosco.",
        "puntos": [
            "Agua, isotónicas y bebidas frías como base del surtido.",
            "Barras, frutos secos y snacks para antes o después del entrenamiento.",
            "Disponible en todo el horario del recinto, incluidas las primeras horas y la noche.",
        ],
        "secciones": [
            ("Surtido según el público", [
                "No es lo mismo un gimnasio de musculación que un club con escuelas infantiles. Armamos el mix según quién usa el recinto y lo corregimos con lo que realmente se vende.",
            ]),
        ],
    },
]

# ═══════════════════════════════════════════════════════════
# 3 · Preguntas frecuentes (también alimentan el JSON-LD FAQPage)
# ═══════════════════════════════════════════════════════════
FAQ = [
    ("¿Tiene algún costo instalar la máquina?",
     "No. En la modalidad estándar (comodato) instalamos el equipo sin costo para la empresa y recuperamos la inversión con la venta al usuario final. La empresa aporta el espacio y la energía eléctrica."),
    ("¿Cuánta gente se necesita para que convenga instalar?",
     "Depende del tipo de lugar y del horario, no solo de la dotación. Un punto con menos personas pero turnos continuos puede vender más que una oficina grande de horario diurno. Lo evaluamos en la visita y te decimos con franqueza si no da."),
    ("¿Quién repone los productos?",
     "Nosotros. La empresa no maneja inventario, no compra producto ni asume merma por vencimiento."),
    ("¿Qué pasa si la máquina no entrega el producto o falla?",
     f"Cada máquina lleva un adhesivo con nuestro número. Quien tuvo el problema escribe por WhatsApp al {CONFIG['telefono_visible']} y lo resolvemos directamente, sin pasar por la administración del lugar."),
    ("¿Se puede pagar con tarjeta?",
     "Sí. Las máquinas cuentan con terminal de pago para tarjetas de débito y crédito."),
    ("¿Quién fija los precios de venta?",
     "Los proponemos nosotros y los acordamos con la empresa antes de instalar. Si la empresa quiere un precio más bajo para su gente, se puede evaluar una modalidad subsidiada."),
    ("¿Se puede pedir un surtido sin sellos de advertencia?",
     "Sí. En establecimientos de educación parvularia, básica y media es obligatorio por la Ley 20.606 y armamos el surtido completo sin sellos. En otros lugares lo aplicamos si es política interna."),
    ("¿En qué comunas operan?",
     "Concepción, Talcahuano, San Pedro de la Paz, Chiguayante, Hualpén, Penco y alrededores. Fuera de esa zona lo evaluamos caso a caso según el volumen del punto."),
    ("¿Hay contrato?",
     "Sí, se firma un contrato de comodato que regula el uso del equipo, los precios acordados y el plazo de aviso para retirarlo."),
    ("¿Emiten factura?",
     "Sí, factura electrónica. En la modalidad estándar la venta es al usuario final; si se acuerda un subsidio, facturamos a la empresa."),
    ("¿Qué necesito tener en el lugar?",
     "Un enchufe de 220 V cercano, piso firme y nivelado, un espacio bajo techo con tránsito de personas y autorización para que nuestro equipo ingrese a reponer en un horario acordado."),
]


# ═══════════════════════════════════════════════════════════
# 4 · Piezas comunes
# ═══════════════════════════════════════════════════════════
def url(ruta: str) -> str:
    return CONFIG["dominio"] + ruta


def wa(texto: str = "") -> str:
    from urllib.parse import quote
    return f"https://wa.me/{CONFIG['whatsapp']}" + (f"?text={quote(texto)}" if texto else "")


WA_ICONO = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-12.4 7.4L3 20.5l1.6-5.4'
            'A8.4 8.4 0 1 1 21 11.5z"/></svg>')

NAV = [
    ("/servicio/", "Servicio"),
    ("/maquinas/", "Máquinas"),
    ("/productos/", "Productos"),
    ("/sectores/", "Sectores"),
    ("/cotizador/", "Cotizador"),
    ("/blog/", "Blog"),
    ("/nosotros/", "Nosotros"),
    ("/preguntas-frecuentes/", "FAQ"),
]


def cabecera(ruta_actual: str) -> str:
    def item(href, txt):
        cur = ' aria-current="page"' if ruta_actual == href or (href != "/" and ruta_actual.startswith(href)) else ""
        if href == "/sectores/":
            subs = "".join(f'<li><a href="/sectores/{s["slug"]}/">{E(s["nombre"])}</a></li>' for s in SECTORES)
            return f'<li class="sub-wrap"><a href="{href}"{cur}>{txt}</a><ul class="sub">{subs}</ul></li>'
        return f'<li><a href="{href}"{cur}>{txt}</a></li>'

    escritorio = "".join(item(h, t) for h, t in NAV)
    movil = "".join(
        f'<li><a href="{h}">{t if t != "FAQ" else "Preguntas frecuentes"}</a>'
        + ('<ul class="sub">' + "".join(f'<li><a href="/sectores/{s["slug"]}/">{E(s["nombre"])}</a></li>' for s in SECTORES) + "</ul>" if h == "/sectores/" else "")
        + "</li>"
        for h, t in [("/", "Inicio")] + NAV + [("/soporte/", "¿Problema con una máquina?")]
    )
    return f"""<header class="top">
  <a class="logo" href="/" aria-label="{CONFIG['marca']} — inicio"><img src="/assets/logo-aso.webp" alt="{CONFIG['marca']}" width="573" height="225"></a>
  <nav class="nav" aria-label="Principal"><ul>{escritorio}</ul></nav>
  <a class="btn head" href="/contacto/">Cotizar instalación</a>
  <details class="menu-movil"><summary aria-label="Menú"><span></span></summary>
    <nav class="panel" aria-label="Menú móvil"><ul>{movil}</ul><a class="btn solid" href="/contacto/">Cotizar instalación</a></nav>
  </details>
</header>"""


def pie() -> str:
    sect = "".join(f'<li><a href="/sectores/{s["slug"]}/">{E(s["corto"])}</a></li>' for s in SECTORES)
    return f"""<footer class="pie">
  <div class="wrap">
    <div>
      <img src="/assets/logo-aso.webp" alt="{CONFIG['marca']}" width="573" height="225" loading="lazy">
      <address>{CONFIG['razon_social']} · RUT {CONFIG['rut']}<br>{CONFIG['ciudad']}, {CONFIG['region']}, Chile<br>
      WhatsApp <a href="{wa()}" rel="noopener">{CONFIG['telefono_visible']}</a><br>
      <a href="mailto:{CONFIG['correo']}">{CONFIG['correo']}</a></address>
    </div>
    <div><h2>Servicio</h2><ul>
      <li><a href="/servicio/">Cómo funciona</a></li><li><a href="/maquinas/">Máquinas</a></li>
      <li><a href="/productos/">Productos</a></li><li><a href="/cobertura/">Cobertura</a></li>
      <li><a href="/cotizador/">Cotizador</a></li><li><a href="/contacto/">Contacto</a></li></ul></div>
    <div><h2>Sectores</h2><ul>{sect}</ul></div>
    <div><h2>Recursos</h2><ul>
      <li><a href="/blog/">Blog</a></li><li><a href="/preguntas-frecuentes/">Preguntas frecuentes</a></li>
      <li><a href="/soporte/">¿Problema con una máquina?</a></li><li><a href="/nosotros/">Nosotros</a></li>
      <li><a href="/blog/feed.xml">RSS del blog</a></li></ul></div>
    <p class="legal">© {dt.date.today().year} {CONFIG['razon_social']}. Máquinas expendedoras de snacks, bebidas y café en {CONFIG['ciudad']} y la {CONFIG['region']}.</p>
  </div>
</footer>
<a class="wa-flota" href="{wa('Hola, quiero información sobre sus máquinas expendedoras.')}" rel="noopener" target="_blank" aria-label="Escríbenos por WhatsApp">{WA_ICONO}<span>WhatsApp</span></a>"""


def migas(items: list[tuple[str, str]]) -> str:
    """items: [(nombre, ruta)], el último es la página actual."""
    lis = "".join(
        f'<li><a href="{r}">{E(n)}</a></li>' if i < len(items) - 1 else f'<li aria-current="page">{E(n)}</li>'
        for i, (n, r) in enumerate(items)
    )
    return f'<nav class="migas wrap" aria-label="Ruta de navegación"><ol>{lis}</ol></nav>'


def cta_banda() -> str:
    return f"""<section class="cta-banda" aria-labelledby="cta-t">
  <div class="wrap">
    <div><h2 id="cta-t">Pide una propuesta <em>para tu espacio.</em></h2>
    <p>Cuéntanos cuánta gente circula y qué horario cubre. Respondemos con una propuesta concreta de máquina, surtido y frecuencia de reposición.</p></div>
    <div class="cta-row" style="margin:0"><a class="btn solid" href="/contacto/">Solicitar propuesta</a>
    <a class="textlink" href="{wa('Hola, quiero cotizar una máquina expendedora.')}" rel="noopener" target="_blank">Escribir por WhatsApp</a></div>
  </div>
</section>"""


# — Datos estructurados —
def org_schema() -> dict:
    return {
        "@type": ["LocalBusiness", "Organization"],
        "@id": url("/#negocio"),
        "name": CONFIG["marca"],
        "legalName": CONFIG["razon_social"],
        "taxID": CONFIG["rut"],
        "description": "Instalación, reposición y mantención de máquinas expendedoras de snacks, bebidas y café para empresas e instituciones de la Región del Biobío.",
        "url": url("/"),
        "logo": url("/assets/logo-aso.png"),
        "image": url("/assets/og.jpg"),
        "telephone": CONFIG["telefono_schema"],
        "email": CONFIG["correo"],
        "foundingDate": CONFIG["fundacion"],
        "priceRange": "$",
        "paymentAccepted": "Tarjeta de débito, tarjeta de crédito",
        "address": {"@type": "PostalAddress", "addressLocality": CONFIG["ciudad"],
                    "addressRegion": "Biobío", "addressCountry": "CL"},
        "areaServed": [{"@type": "City", "name": c} for c in CONFIG["comunas"]]
                      + [{"@type": "AdministrativeArea", "name": "Región del Biobío"}],
        "contactPoint": {"@type": "ContactPoint", "telephone": CONFIG["telefono_schema"],
                         "contactType": "customer service", "areaServed": "CL", "availableLanguage": "es"},
        "knowsAbout": ["máquinas expendedoras", "vending", "máquinas de café", "comodato de máquinas expendedoras"],
    }


def schema_pagina(ruta, titulo, desc, crumbs, extra=None, tipo="WebPage") -> str:
    grafo = [
        org_schema(),
        {"@type": "WebSite", "@id": url("/#sitio"), "url": url("/"), "name": CONFIG["marca"],
         "inLanguage": "es-CL", "publisher": {"@id": url("/#negocio")}},
        {"@type": tipo, "@id": url(ruta) + "#pagina", "url": url(ruta), "name": titulo, "description": desc,
         "isPartOf": {"@id": url("/#sitio")}, "about": {"@id": url("/#negocio")}, "inLanguage": "es-CL"},
    ]
    if len(crumbs) > 1:
        grafo.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": url(r)} for i, (n, r) in enumerate(crumbs)]})
    grafo += extra or []
    return json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False, indent=1)


def documento(*, ruta, title, desc, cuerpo, crumbs=None, extra_schema=None, tipo="WebPage",
              og_tipo="website", imagen="/assets/og.jpg", home=False, head_extra="", cta=True,
              indexar=True) -> str:
    crumbs = crumbs or [("Inicio", "/")]
    titulo_full = title if home else f"{title} | ASO Vending"
    return f"""<!DOCTYPE html>
<html lang="es-CL">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(titulo_full)}</title>
<meta name="description" content="{E(desc)}">
<meta name="robots" content="{'index, follow, max-image-preview:large' if indexar else 'noindex, follow'}">
<link rel="canonical" href="{url(ruta)}">
<meta name="theme-color" content="#000000">
<meta property="og:type" content="{og_tipo}">
<meta property="og:locale" content="es_CL">
<meta property="og:site_name" content="{CONFIG['marca']}">
<meta property="og:url" content="{url(ruta)}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:image" content="{url(imagen)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon-32.png" type="image/png" sizes="32x32">
<link rel="icon" href="/assets/icon.png" type="image/png" sizes="512x512">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="Blog ASO Vending" href="/blog/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..600;1,9..144,300..600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/estilos.css">
{head_extra}
<script type="application/ld+json">
{schema_pagina(ruta, title, desc, crumbs, extra_schema, tipo)}
</script>
</head>
<body{' class="home"' if home else ''} data-wa="{CONFIG['whatsapp']}">
<a class="skip" href="#contenido">Saltar al contenido</a>
{cabecera(ruta)}
{'' if home else migas(crumbs)}
<main id="contenido">
{cuerpo}
</main>
{cta_banda() if cta else ''}
{pie()}
<script src="/assets/sitio.js" defer></script>
</body>
</html>
"""


def hero(eyebrow, h1, lead, botones=True, imagen=None) -> str:
    fig = ""
    if imagen:
        src, alt, w, h = imagen
        fig = f'<figure class="figura"><img src="{src}" alt="{E(alt)}" width="{w}" height="{h}" fetchpriority="high"></figure>'
    ctas = ('<div class="cta-row"><a class="btn solid" href="/contacto/">Cotizar instalación</a>'
            '<a class="textlink" href="/cotizador/">Ver qué máquina te conviene</a></div>') if botones else ""
    return f"""<section class="hero{' con-imagen' if imagen else ''}"><div class="wrap">
  <div><p class="eyebrow">{eyebrow}</p><h1>{h1}</h1><p class="lead">{lead}</p>{ctas}</div>{fig}
</div></section>"""


def bloque(h2, contenido, id_=None) -> str:
    return f'<section class="bloque"{f" id={chr(34)}{id_}{chr(34)}" if id_ else ""}><div class="wrap dos-col"><div><h2>{h2}</h2></div><div>{contenido}</div></div></section>'


def lista(items) -> str:
    return '<ul class="lista">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def ps(textos) -> str:
    return "".join(f"<p>{t}</p>" for t in textos)


# ═══════════════════════════════════════════════════════════
# 5 · Blog
# ═══════════════════════════════════════════════════════════
def leer_posts() -> list[dict]:
    posts = []
    for f in sorted((RAIZ / "contenido" / "blog").glob("*.md")):
        texto = f.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", texto, re.S)
        if not m:
            raise SystemExit(f"{f.name}: falta el encabezado entre líneas ---")
        meta = {}
        for linea in m.group(1).splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        for req in ("titulo", "descripcion", "fecha"):
            if req not in meta:
                raise SystemExit(f"{f.name}: falta '{req}' en el encabezado")
        if meta.get("borrador", "no").lower() in ("si", "sí", "true"):
            continue
        cuerpo_md = m.group(2)
        palabras = len(re.findall(r"\w+", cuerpo_md))
        posts.append({
            "slug": meta.get("slug") or f.stem,
            "titulo": meta["titulo"],
            "titulo_seo": meta.get("titulo_seo", meta["titulo"]),
            "desc": meta["descripcion"],
            "fecha": meta["fecha"],
            "actualizado": meta.get("actualizado", meta["fecha"]),
            "categoria": meta.get("categoria", "Vending"),
            "autor": meta.get("autor", CONFIG["marca"]),
            "imagen": meta.get("imagen", "/assets/og.jpg"),
            "html": markdown.markdown(cuerpo_md, extensions=["extra", "sane_lists", "smarty"],
                                      extension_configs={"smarty": {"smart_quotes": False}}),
            "minutos": max(1, round(palabras / 220)),
        })
    return sorted(posts, key=lambda p: p["fecha"], reverse=True)


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_humana(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def tarjeta_post(p, h="h2") -> str:
    return (f'<li><p class="meta"><span class="etq">{E(p["categoria"])}</span> · <time datetime="{p["fecha"]}">{fecha_humana(p["fecha"])}</time></p>'
            f'<{h}><a href="/blog/{p["slug"]}/">{E(p["titulo"])}</a></{h}><p>{E(p["desc"])}</p>'
            f'<a class="textlink" href="/blog/{p["slug"]}/" style="align-self:flex-start;margin-top:auto">Leer artículo</a></li>')


# ═══════════════════════════════════════════════════════════
# 6 · Páginas
# ═══════════════════════════════════════════════════════════
def pagina_inicio(posts) -> str:
    ultimos = "".join(
        f'<li><a href="/blog/{p["slug"]}/"><p class="meta">{fecha_humana(p["fecha"])}</p><h3>{E(p["titulo"])}</h3></a></li>'
        for p in posts[:3])
    espacios = "".join(f'<li><a href="/sectores/{s["slug"]}/" style="text-decoration:none">{E(s["nombre"])}</a></li>' for s in SECTORES)
    cuerpo = f"""<div class="stage" aria-hidden="true">
  <video id="bg" muted playsinline disablepictureinpicture preload="none" poster="/assets/poster.webp" tabindex="-1"></video>
  <img class="poster" id="posterImg" src="/assets/poster.webp" alt="" width="1440" height="810">
</div>
<div class="carga" id="carga" aria-hidden="true"></div>
<div class="veil" aria-hidden="true"></div>
<div class="vignette" aria-hidden="true"></div>
<nav class="rail" aria-label="Secciones de la portada"><div class="rail-fill" id="railFill"></div></nav>

<section id="inicio" class="sec" data-label="Inicio"><div class="inner">
  <p class="eyebrow rise"><span>{CONFIG['ciudad']} · {CONFIG['region']}</span></p>
  <h1 class="rise">Máquinas expendedoras en Concepción, <em>instaladas y atendidas.</em></h1>
  <p class="lead rise">Snacks, bebidas y café para empresas e instituciones del Biobío. Nos hacemos cargo de la instalación, la reposición y la mantención: tu equipo solo las usa.</p>
  <div class="cta-row rise"><a class="btn solid" href="/contacto/">Cotizar instalación</a><a class="textlink" href="/servicio/">Ver el servicio</a></div>
</div><p class="cue">Desplázate para ver la máquina por dentro</p></section>

<section id="servicio" class="sec" data-label="Servicio"><div class="inner wide">
  <p class="eyebrow rise"><span class="num">01</span><span>Servicio</span></p>
  <h2 class="rise">Una máquina que <em>no te quita tiempo.</em></h2>
  <ul class="rows rise">
    <li><h3>Instalación sin costo</h3><p>Evaluamos el espacio, definimos el modelo adecuado y dejamos la máquina funcionando, en comodato.</p></li>
    <li><h3>Reposición</h3><p>Reponemos según lo que efectivamente se vende, para que no falte lo que la gente busca.</p></li>
    <li><h3>Mantención</h3><p>Revisiones periódicas y reparaciones a cargo de nuestro equipo, sin costo de gestión para ti.</p></li>
    <li><h3>Gestión remota</h3><p>Seguimos ventas y estado de la máquina a distancia, y actuamos antes de que se note una falla.</p></li>
  </ul>
  <p class="mas rise"><a class="textlink" href="/servicio/">Cómo funciona el comodato</a></p>
</div></section>

<section id="productos" class="sec" data-label="Productos"><div class="inner">
  <p class="eyebrow rise"><span class="num">02</span><span>Máquinas y productos</span></p>
  <h2 class="rise">Snacks, bebidas <em>y café.</em></h2>
  <p class="rise">Armamos el surtido según quiénes usan el espacio. No es lo mismo una oficina que una sala de espera, un gimnasio o una planta en turnos. Pago con tarjeta de débito o crédito en la misma máquina.</p>
  <dl class="ficha rise"><dt>Equipos</dt><dd>Snacks, bebidas frías, combinadas y café automático (GS 505).</dd></dl>
  <p class="mas rise"><a class="textlink" href="/maquinas/">Ver las máquinas</a> &nbsp; <a class="textlink" href="/productos/">Ver productos</a></p>
</div></section>

<section id="espacios" class="sec" data-label="Sectores"><div class="inner wide">
  <p class="eyebrow rise"><span class="num">03</span><span>Sectores</span></p>
  <h2 class="rise">Dónde <em>ya hace falta una.</em></h2>
  <ul class="places rise">{espacios}</ul>
  <p class="mas rise"><a class="textlink" href="/cotizador/">¿Qué máquina conviene en tu espacio?</a></p>
</div></section>

<section id="proceso" class="sec" data-label="Proceso"><div class="inner">
  <p class="eyebrow rise"><span class="num">04</span><span>Proceso</span></p>
  <h2 class="rise">Del primer contacto <em>a la máquina funcionando.</em></h2>
  <ol class="steps rise">
    <li><div><h3>Nos cuentas sobre tu espacio</h3><p>Ubicación, cantidad de personas y qué les gustaría encontrar.</p></div></li>
    <li><div><h3>Visitamos y proponemos</h3><p>Recomendamos modelo y ubicación, y enviamos la propuesta.</p></div></li>
    <li><div><h3>Instalamos y atendemos</h3><p>Dejamos la máquina lista y nos ocupamos de reponer y mantenerla.</p></div></li>
  </ol>
</div></section>

<section id="blog" class="sec" data-label="Blog"><div class="inner">
  <p class="eyebrow rise"><span class="num">05</span><span>Blog</span></p>
  <h2 class="rise">Guías para <em>decidir mejor.</em></h2>
  <ul class="mini-posts rise">{ultimos}</ul>
  <p class="mas rise"><a class="textlink" href="/blog/">Ver todas las entradas</a></p>
</div></section>

<section id="cotizar" class="sec" data-label="Cotizar"><div class="inner wide">
  <p class="eyebrow rise"><span class="num">06</span><span>Contacto</span></p>
  <h2 class="rise">Cotiza la instalación <em>en tu espacio.</em></h2>
  {formulario_corto()}
</div></section>
<script src="/assets/inicio.js" defer></script>"""
    return documento(
        ruta="/", home=True, cta=False,
        title="Máquinas expendedoras en Concepción y el Biobío | ASO Vending Machine",
        desc="Instalamos sin costo máquinas expendedoras de snacks, bebidas y café en empresas e instituciones de Concepción y el Biobío. Reposición y mantención a cargo nuestro.",
        cuerpo=cuerpo,
        head_extra='<link rel="preload" as="image" href="/assets/poster.webp" fetchpriority="high">\n<link rel="stylesheet" href="/assets/inicio.css">',
    )


def formulario_corto() -> str:
    return f"""<form class="form rise" data-wa="Hola, quiero cotizar la instalación de una máquina expendedora." novalidate>
    <div><label for="f-nombre">Tu nombre</label><input id="f-nombre" name="nombre" autocomplete="name" required data-etiqueta="Nombre"></div>
    <div><label for="f-empresa">Empresa o institución</label><input id="f-empresa" name="empresa" autocomplete="organization" required data-etiqueta="Empresa"></div>
    <div><label for="f-comuna">Comuna</label><input id="f-comuna" name="comuna" placeholder="Ej.: Concepción" required data-etiqueta="Comuna"></div>
    <div><label for="f-contacto">Teléfono o correo</label><input id="f-contacto" name="contacto" autocomplete="tel" data-etiqueta="Contacto"></div>
    <div class="full"><label for="f-mensaje">Cuéntanos del espacio (opcional)</label><textarea id="f-mensaje" name="mensaje" placeholder="Cantidad de personas, ubicación dentro del recinto, qué productos te interesan" data-etiqueta="Detalle"></textarea></div>
    <div class="hp" aria-hidden="true"><label for="f-web">No completar</label><input id="f-web" name="web" tabindex="-1" autocomplete="off"></div>
    <p class="err full" role="status" aria-live="polite"></p>
    <div class="form-pie full"><button class="btn solid" type="submit">Enviar por WhatsApp</button>
    <small>o escríbenos a <a href="mailto:{CONFIG['correo']}?subject=Cotizaci%C3%B3n%20de%20m%C3%A1quina%20expendedora">{CONFIG['correo']}</a></small></div>
  </form>"""


def pagina_servicio() -> str:
    pasos = """<ol class="pasos">
      <li><h3>Visita al lugar</h3><p>Vemos el espacio, el flujo de personas y el punto eléctrico.</p></li>
      <li><h3>Propuesta</h3><p>Proponemos máquina, surtido y precios de venta al público.</p></li>
      <li><h3>Instalación</h3><p>Coordinamos el ingreso y dejamos el equipo operativo.</p></li>
      <li><h3>Ajuste del surtido</h3><p>En las primeras semanas revisamos qué se vende y corregimos el mix.</p></li></ol>"""
    incluye = """<ul class="tarjetas">
      <li><h3>Instalación sin costo</h3><p>Llevamos, instalamos y configuramos el equipo. Solo necesitamos un punto eléctrico y un espacio de acceso libre.</p></li>
      <li><h3>Reposición programada</h3><p>Visitas según el consumo real del punto. Si un producto se agota antes, ajustamos la frecuencia.</p></li>
      <li><h3>Mantención incluida</h3><p>Limpieza, revisión del equipo y respuesta ante fallas, a cargo nuestro.</p></li>
      <li><h3>Pago con tarjeta</h3><p>Terminal de pago para débito y crédito en la misma máquina.</p></li>
      <li><h3>Surtido ajustable</h3><p>Definimos el mix con ustedes y lo corregimos con lo que efectivamente se vende.</p></li>
      <li><h3>Gestión remota</h3><p>Seguimos ventas y stock a distancia: la visita se hace cuando hace falta.</p></li></ul>"""
    cuerpo = hero("Servicio", "Cómo funciona <em>el servicio de vending</em>",
                  "Operamos el punto completo. La empresa no compra el equipo, no maneja stock, no cobra ni cuadra caja.")
    cuerpo += f'<section class="bloque"><div class="wrap"><h2>Qué incluye</h2>{incluye}</div></section>'
    cuerpo += bloque("Modalidad estándar: <em>comodato</em>", ps([
        "Instalamos la máquina sin costo para la empresa y vendemos directamente al usuario final. La empresa aporta el espacio y la energía; nosotros asumimos el equipo, el inventario, la reposición y el riesgo de merma.",
        "Es la modalidad que conviene cuando el objetivo es dar un beneficio a las personas sin abrir un centro de costos. Si quieres profundizar, lo explicamos en detalle en <a class=\"textlink\" href=\"/blog/comodato-maquinas-expendedoras/\">qué es el comodato de máquinas expendedoras</a>."]))
    cuerpo += bloque("Modalidad <em>subsidiada</em>", ps([
        "La empresa cubre parte del precio para que el usuario pague menos. Se usa en faenas, turnos de noche y como beneficio de bienestar. Las condiciones se acuerdan caso a caso."]))
    cuerpo += bloque("Qué te reportamos", lista([
        "Productos más y menos vendidos, para ajustar el surtido.",
        "Fechas de reposición y de mantención realizadas.",
        "Incidencias del equipo y cómo se resolvieron."]))
    cuerpo += bloque("Respuesta ante fallas", ps([
        f"Un equipo detenido no vende y molesta a quien lo usa. Cualquier persona del lugar puede reportar una falla por WhatsApp al número del adhesivo de la máquina ({CONFIG['telefono_visible']}), sin pasar por administración. Coordinamos la visita técnica y resolvemos devoluciones directamente con el usuario.",
        '<a class="textlink" href="/soporte/">Ver la página de soporte</a>']))
    cuerpo += f'<section class="bloque"><div class="wrap"><h2>Cómo partimos</h2>{pasos}</div></section>'
    servicio = {"@type": "Service", "@id": url("/servicio/#servicio"), "name": "Servicio de máquinas expendedoras en comodato",
                "serviceType": "Instalación, reposición y mantención de máquinas expendedoras",
                "provider": {"@id": url("/#negocio")},
                "areaServed": [{"@type": "City", "name": c} for c in CONFIG["comunas"]],
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "CLP",
                           "description": "Instalación sin costo en modalidad comodato"}}
    return documento(ruta="/servicio/", title="Servicio de máquinas expendedoras en comodato",
                     desc="Instalación sin costo, reposición, mantención y gestión remota de máquinas expendedoras para empresas del Gran Concepción. Modalidad comodato o subsidiada.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Servicio", "/servicio/")], extra_schema=[servicio])


def pagina_maquinas() -> str:
    cuerpo = hero("Máquinas", "Máquinas <em>expendedoras</em>",
                  "Elegimos el equipo según cuánta gente pasa por el punto y qué se consume en ese horario. Una máquina sobredimensionada se queda con producto vencido; una chica se agota el martes.",
                  imagen=("/assets/maquina-snacks.webp", "Máquina expendedora de snacks y bebidas con vitrina iluminada y terminal de pago con tarjeta", 500, 770))
    cuerpo += """<section class="bloque"><div class="wrap"><h2>Tipos de equipo</h2><ul class="tarjetas">
      <li><h3>Snacks</h3><p>Espirales para productos secos: galletas, frutos secos, barras y confites. Es el equipo base en oficinas y salas de espera.</p></li>
      <li><h3>Bebidas frías</h3><p>Refrigerada, para aguas, bebidas, jugos e isotónicas. Funciona bien en faenas y lugares de alto tránsito.</p></li>
      <li><h3>Café automático</h3><p>Trabajamos con la máquina GS 505: café, capuchino, chocolate y otras preparaciones calientes al momento. Reemplaza la cafetera compartida y el desorden que genera.</p></li>
      <li><h3>Combinada</h3><p>Snacks y bebidas en un solo cuerpo. La alternativa cuando hay poco espacio o un solo punto eléctrico.</p></li>
    </ul></div></section>"""
    cuerpo += bloque("Qué necesitas <em>tener en el lugar</em>", lista([
        "Un enchufe de 220 V cercano al lugar definitivo del equipo.",
        "Piso firme y nivelado, con acceso para ingresar la máquina (ascensor o puerta amplia).",
        "Un lugar bajo techo, ventilado y con tránsito de personas.",
        "Autorización para que nuestro equipo ingrese a reponer en un horario acordado."]))
    cuerpo += bloque("El consumo eléctrico", ps([
        "Lo asume el lugar donde se instala la máquina, igual que cualquier equipo de sala de café. Si necesitas el dato exacto para tu evaluación, te lo entregamos por escrito con la propuesta."]))
    cuerpo += bloque("Pago en la máquina", ps([
        "Los equipos cuentan con terminal de pago para tarjetas de débito y crédito. El uso es simple: se activa el terminal, se elige el producto, se presenta o inserta la tarjeta y se retira el producto.",
        '<a class="textlink" href="/soporte/">Ver instrucciones de uso</a>']))
    return documento(ruta="/maquinas/", title="Máquinas expendedoras de snacks, bebidas y café",
                     desc="Máquinas expendedoras de snacks, bebidas frías, combinadas y café automático GS 505 para empresas en Concepción. Requisitos de instalación y pago con tarjeta.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Máquinas", "/maquinas/")], imagen="/assets/og.jpg")


def pagina_productos() -> str:
    cuerpo = hero("Productos", "Snacks, bebidas <em>y café</em>",
                  "El surtido no es una lista fija. Partimos con un mix base según el tipo de lugar y lo corregimos con las ventas reales de las primeras semanas.")
    cuerpo += """<section class="bloque"><div class="wrap"><h2>Categorías</h2><ul class="tarjetas">
      <li><h3>Dulce</h3><p>Galletas, chocolates, barras de cereal y confites.</p></li>
      <li><h3>Salado</h3><p>Papas fritas, maní, mix de frutos secos y snacks horneados.</p></li>
      <li><h3>Bebidas</h3><p>Agua, bebidas, jugos, isotónicas y energéticas.</p></li>
      <li><h3>Café y bebidas calientes</h3><p>Café, capuchino, chocolate y otras preparaciones en máquina automática.</p></li>
      <li><h3>Sin sellos</h3><p>Alternativas sin sellos de advertencia para lugares que lo exigen por ley o por política interna.</p></li>
      <li><h3>Frutos secos</h3><p>Maní, almendras y mezclas en formato individual, para puntos con consumo estable.</p></li>
    </ul></div></section>"""
    cuerpo += bloque("Sobre los sellos <em>de advertencia</em>", ps([
        "La Ley 20.606 prohíbe vender alimentos con sellos \"ALTO EN\" dentro de establecimientos de educación parvularia, básica y media. En esos casos armamos el surtido completo con productos sin sellos: no es una opción, es el único mix que corresponde.",
        "En universidades, clínicas y empresas no hay esa restricción, pero varias instituciones aplican su propia política de alimentación. Si es tu caso, dinos el criterio y lo aplicamos.",
        '<a class="textlink" href="/blog/ley-20606-maquinas-expendedoras/">Leer la guía sobre la Ley 20.606</a>']))
    cuerpo += bloque("Precios", ps([
        "Los precios de venta al público se proponen y se acuerdan con el lugar antes de instalar. Si la empresa quiere un precio menor para su gente, se puede evaluar una modalidad subsidiada."]))
    return documento(ruta="/productos/", title="Productos para máquinas expendedoras",
                     desc="Snacks dulces y salados, bebidas, café y opciones sin sellos para máquinas expendedoras en empresas, clínicas y universidades del Biobío.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Productos", "/productos/")])


def pagina_sectores() -> str:
    items = "".join(
        f'<li><p class="num">{i:02d}</p><h2 style="font-family:var(--sans);font-size:1.1rem;font-weight:600;margin:0 0 .4rem">{E(s["nombre"])}</h2>'
        f'<p>{E(s["lead"])}</p><a class="mas" href="/sectores/{s["slug"]}/">Ver solución</a></li>'
        for i, s in enumerate(SECTORES, 1))
    cuerpo = hero("Sectores", "Vending según <em>el tipo de lugar</em>",
                  "El equipo, el surtido y el horario de reposición cambian según quién usa la máquina. Estas son las soluciones que operamos en el Biobío.")
    cuerpo += f'<section class="bloque"><div class="wrap"><ul class="tarjetas">{items}</ul></div></section>'
    lista_schema = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": url(f"/sectores/{s['slug']}/"), "name": s["nombre"]}
        for i, s in enumerate(SECTORES)]}
    return documento(ruta="/sectores/", title="Máquinas expendedoras por sector",
                     desc="Soluciones de vending para oficinas, clínicas, universidades, industria, sucursales y gimnasios en Concepción y la Región del Biobío.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Sectores", "/sectores/")],
                     extra_schema=[lista_schema], tipo="CollectionPage")


def pagina_sector(s) -> str:
    ruta = f"/sectores/{s['slug']}/"
    cuerpo = hero(f"Sectores · {E(s['corto'])}", s["h1"], E(s["lead"]))
    cuerpo += bloque("Qué resuelve", f"<p>{E(s['resuelve'])}</p>" + lista([E(p) for p in s["puntos"]]))
    for h2, textos in s["secciones"]:
        cuerpo += bloque(E(h2), ps([E(t) for t in textos]))
    otros = "".join(f'<li><a href="/sectores/{o["slug"]}/">{E(o["nombre"])}</a></li>' for o in SECTORES if o is not s)
    cuerpo += bloque("Otros sectores", f'<ul class="lista">{otros}</ul>')
    servicio = {"@type": "Service", "name": s["nombre"] + ": servicio de máquinas expendedoras",
                "serviceType": "Máquinas expendedoras", "provider": {"@id": url("/#negocio")},
                "audience": {"@type": "BusinessAudience", "name": s["nombre"]},
                "areaServed": {"@type": "AdministrativeArea", "name": "Región del Biobío"}, "url": url(ruta)}
    return documento(ruta=ruta, title=s["title"], desc=s["desc"], cuerpo=cuerpo,
                     crumbs=[("Inicio", "/"), ("Sectores", "/sectores/"), (s["nombre"], ruta)], extra_schema=[servicio])


def pagina_cobertura() -> str:
    comunas = "".join(f"<li><strong>{c}</strong></li>" for c in CONFIG["comunas"])
    cuerpo = hero("Cobertura", "Máquinas expendedoras <em>en el Gran Concepción</em>",
                  "Somos una empresa local, con base en Concepción. Operamos directamente, sin subcontratar la reposición a terceros, y eso define los tiempos de respuesta que podemos comprometer.")
    cuerpo += bloque("Comunas donde operamos", f'<ul class="lista">{comunas}</ul><p>Fuera de estas comunas evaluamos caso a caso según el volumen del punto: Coronel, Tomé, Lota y otras comunas de la región pueden ser viables si el punto lo justifica.</p>')
    cuerpo += bloque("Por qué importa que seamos locales", ps([
        "Una máquina detenida o vacía se nota en horas, no en días. Estar en la zona nos permite reponer según la venta real y atender fallas sin depender de un despacho desde otra región.",
        "También nos permite visitar el lugar antes de proponer, que es la única forma de recomendar bien el equipo y la ubicación."]))
    return documento(ruta="/cobertura/", title="Cobertura: Concepción, Talcahuano, San Pedro y más",
                     desc="Instalamos máquinas expendedoras en Concepción, Talcahuano, San Pedro de la Paz, Chiguayante, Hualpén y Penco. Empresa local de la Región del Biobío.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Cobertura", "/cobertura/")])


def pagina_nosotros() -> str:
    cuerpo = hero("Nosotros", "Quiénes <em>somos</em>",
                  f"ASO Vending Machine es la operación de vending de {CONFIG['razon_social']}, empresa de {CONFIG['ciudad']} enfocada en servicios no atendidos para empresas e instituciones del Biobío.", botones=False)
    cuerpo += bloque("Cómo trabajamos", ps([
        "Operamos con gestión remota del punto de venta: seguimos stock y ventas a distancia y vamos cuando hay algo que reponer o revisar. Eso significa menos visitas innecesarias, menos quiebres de stock y un servicio que no depende de que alguien de tu empresa avise.",
        "Somos locales: estamos en Concepción y operamos directamente."]))
    cuerpo += bloque("A quién atendemos", ps([
        "Oficinas, centros de salud y veterinarios, universidades, plantas industriales, sucursales de atención de público y recintos deportivos. Cada tipo de lugar tiene su propio patrón de consumo y lo operamos distinto."]) +
        '<p><a class="textlink" href="/sectores/">Ver sectores</a></p>')
    cuerpo += bloque("Datos de la empresa", lista([
        f"<strong>Razón social:</strong> {CONFIG['razon_social']}",
        f"<strong>RUT:</strong> {CONFIG['rut']}",
        "<strong>Giro:</strong> venta al por menor mediante máquinas expendedoras",
        f"<strong>Ciudad:</strong> {CONFIG['ciudad']}, {CONFIG['region']}"]) +
        "<p>Emitimos factura electrónica y podemos participar de procesos de compra y licitación.</p>")
    return documento(ruta="/nosotros/", title="Quiénes somos", tipo="AboutPage",
                     desc=f"ASO Vending Machine es la operación de vending de {CONFIG['razon_social']}, empresa local de Concepción. Datos de la empresa y forma de trabajo.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Nosotros", "/nosotros/")])


def pagina_faq() -> str:
    items = "".join(f"<details><summary>{E(q)}</summary><div><p>{E(a)}</p></div></details>" for q, a in FAQ)
    cuerpo = hero("Preguntas frecuentes", "Preguntas <em>frecuentes</em>",
                  "Lo que más nos preguntan antes de instalar. Si falta algo, escríbenos y lo agregamos.", botones=False)
    cuerpo += f'<section class="bloque"><div class="wrap faq" style="max-width:52rem">{items}</div></section>'
    faq_schema = {"@type": "FAQPage", "@id": url("/preguntas-frecuentes/#faq"), "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    return documento(ruta="/preguntas-frecuentes/", title="Preguntas frecuentes sobre máquinas expendedoras",
                     desc="Costos, comodato, reposición, pago con tarjeta, sellos de advertencia y cobertura: respuestas sobre la instalación de máquinas expendedoras en tu empresa.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Preguntas frecuentes", "/preguntas-frecuentes/")],
                     extra_schema=[faq_schema])


def pagina_contacto() -> str:
    tipos = ["Oficina", "Centro de salud o veterinario", "Universidad o instituto", "Industria o faena",
             "Sucursal o atención de público", "Gimnasio o recinto deportivo", "Colegio", "Otro"]
    opciones = "".join(f"<option>{t}</option>" for t in tipos)
    form = f"""<form class="form" data-wa="Hola, quiero solicitar una propuesta de máquina expendedora." novalidate>
      <div><label for="c-nombre">Nombre y cargo</label><input id="c-nombre" name="nombre" autocomplete="name" required data-etiqueta="Nombre y cargo"></div>
      <div><label for="c-empresa">Empresa o institución</label><input id="c-empresa" name="empresa" autocomplete="organization" required data-etiqueta="Empresa"></div>
      <div><label for="c-correo">Correo</label><input id="c-correo" name="correo" type="email" autocomplete="email" data-etiqueta="Correo"></div>
      <div><label for="c-fono">Teléfono</label><input id="c-fono" name="telefono" type="tel" autocomplete="tel" data-etiqueta="Teléfono"></div>
      <div><label for="c-comuna">Comuna donde iría la máquina</label><input id="c-comuna" name="comuna" required data-etiqueta="Comuna"></div>
      <div><label for="c-tipo">Tipo de lugar</label><select id="c-tipo" name="tipo" data-etiqueta="Tipo de lugar"><option value="">Elige una opción</option>{opciones}</select></div>
      <div class="full"><label for="c-personas">Personas que circulan al día (aproximado)</label><input id="c-personas" name="personas" inputmode="numeric" data-etiqueta="Personas al día"></div>
      <div class="full"><label for="c-msg">Algo más que debamos saber</label><textarea id="c-msg" name="mensaje" data-etiqueta="Detalle"></textarea></div>
      <div class="hp" aria-hidden="true"><label for="c-web">No completar</label><input id="c-web" name="web" tabindex="-1" autocomplete="off"></div>
      <p class="err full" role="status" aria-live="polite"></p>
      <div class="form-pie full"><button class="btn solid" type="submit">Enviar por WhatsApp</button>
      <small>El botón abre WhatsApp con tu solicitud ya escrita.</small></div>
    </form>"""
    datos = f"""<div class="contacto-datos">
      <div><h3>WhatsApp y teléfono</h3><p><a href="{wa()}" rel="noopener" target="_blank">{CONFIG['telefono_visible']}</a></p></div>
      <div><h3>Correo</h3><p><a href="mailto:{CONFIG['correo']}">{CONFIG['correo']}</a></p></div>
      <div><h3>Ubicación</h3><p>{CONFIG['ciudad']}, {CONFIG['region']}</p></div>
      <div><h3>Cobertura</h3><p>{', '.join(CONFIG['comunas'][:-1])} y {CONFIG['comunas'][-1]}. <a class="textlink" href="/cobertura/">Ver cobertura</a></p></div>
    </div>"""
    cuerpo = hero("Contacto", "Solicitar <em>propuesta</em>",
                  "Con estos datos podemos proponerte un equipo y un surtido concretos. Si el punto no da para una máquina, también te lo decimos.", botones=False)
    cuerpo += f'<section class="bloque"><div class="wrap dos-col" style="grid-template-columns:1.4fr .6fr">{form}{datos}</div></section>'
    return documento(ruta="/contacto/", title="Contacto y cotización", tipo="ContactPage", cta=False,
                     desc=f"Solicita una propuesta de máquina expendedora para tu empresa en Concepción. WhatsApp {CONFIG['telefono_visible']}.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Contacto", "/contacto/")])


def pagina_cotizador() -> str:
    def radios(nombre, opciones, tipo="radio"):
        return '<div class="opciones">' + "".join(
            f'<label><input type="{tipo}" name="{nombre}" value="{E(o)}">{E(o)}</label>' for o in opciones) + "</div>"
    form = f"""<form class="form" id="cotizador" novalidate>
      <fieldset class="full"><legend>1 · ¿Qué tipo de lugar es?</legend>{radios("lugar", ["Oficina", "Centro de salud", "Universidad o instituto", "Industria o faena", "Sucursal o atención de público", "Gimnasio", "Colegio", "Otro"])}</fieldset>
      <fieldset class="full"><legend>2 · ¿Cuántas personas circulan al día?</legend>{radios("personas", ["Menos de 30", "30 a 100", "100 a 300", "Más de 300"])}</fieldset>
      <fieldset class="full"><legend>3 · ¿En qué horario funciona?</legend>{radios("horario", ["Horario de oficina", "Horario extendido", "Turnos o 24 horas"])}</fieldset>
      <fieldset class="full"><legend>4 · ¿Qué les gustaría encontrar? (puedes marcar varias)</legend>{radios("quiere", ["Snacks", "Bebidas frías", "Café"], "checkbox")}</fieldset>
      <fieldset class="full"><legend>5 · ¿Cuánto espacio hay?</legend>{radios("espacio", ["Poco espacio o un solo enchufe", "Espacio suficiente"])}</fieldset>
      <p class="err full" role="status" aria-live="polite"></p>
      <div class="form-pie full"><button class="btn solid" type="submit">Ver recomendación</button></div>
    </form>
    <div class="resultado" id="recomendacion" hidden tabindex="-1" aria-live="polite">
      <h3>Recomendación orientativa</h3>
      <ul class="lista" data-equipos></ul>
      <ul class="lista" data-notas></ul>
      <p>Es una primera orientación. La propuesta definitiva la hacemos después de ver el lugar.</p>
      <button class="btn solid" type="button" id="enviarRecomendacion">Enviar esto por WhatsApp</button>
    </div>
    <noscript><p>El cotizador necesita JavaScript. También puedes <a class="textlink" href="/contacto/">solicitar una propuesta aquí</a>.</p></noscript>"""
    cuerpo = hero("Cotizador", "¿Qué máquina <em>conviene en tu espacio?</em>",
                  "Responde cinco preguntas y te mostramos qué tipo de equipo recomendaríamos. Luego puedes enviarnos el resumen por WhatsApp para recibir la propuesta.", botones=False)
    cuerpo += f'<section class="bloque"><div class="wrap" style="max-width:52rem">{form}</div></section>'
    return documento(ruta="/cotizador/", title="Cotizador: qué máquina expendedora conviene",
                     desc="Responde cinco preguntas y descubre qué máquina expendedora conviene en tu oficina, clínica, planta o recinto. Recomendación inmediata y propuesta por WhatsApp.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Cotizador", "/cotizador/")])


def pagina_soporte() -> str:
    form = f"""<form class="form" data-wa="Hola, tuve un problema con una máquina ASO." novalidate>
      <div class="full"><label for="s-lugar">¿Dónde está la máquina?</label><input id="s-lugar" name="lugar" required placeholder="Recinto, piso o sector" data-etiqueta="Ubicación de la máquina"></div>
      <div><label for="s-prod">Producto que intentaste comprar</label><input id="s-prod" name="producto" data-etiqueta="Producto"></div>
      <div><label for="s-hora">Día y hora aproximada</label><input id="s-hora" name="hora" data-etiqueta="Día y hora"></div>
      <div class="full"><label for="s-que">¿Qué pasó?</label><textarea id="s-que" name="que" required placeholder="Ej.: se cobró en la tarjeta pero no salió el producto" data-etiqueta="Problema"></textarea></div>
      <div class="hp" aria-hidden="true"><label for="s-web">No completar</label><input id="s-web" name="web" tabindex="-1" autocomplete="off"></div>
      <p class="err full" role="status" aria-live="polite"></p>
      <div class="form-pie full"><button class="btn solid" type="submit">Reportar por WhatsApp</button><small>o escribe directo al <a href="{wa()}" rel="noopener" target="_blank">{CONFIG['telefono_visible']}</a></small></div>
    </form>"""
    cuerpo = hero("Soporte", "¿La máquina no entregó <em>tu producto?</em>",
                  f"Escríbenos por WhatsApp al {CONFIG['telefono_visible']} con la ubicación de la máquina y lo que pasó. Lo resolvemos directamente contigo, sin pasar por la administración del lugar.", botones=False)
    cuerpo += f'<section class="bloque"><div class="wrap" style="max-width:52rem"><h2>Reportar un problema</h2>{form}</div></section>'
    cuerpo += bloque("Cómo comprar <em>en la máquina</em>", """<ol class="lista" style="list-style:none">
      <li><strong>1.</strong> Presiona el dispositivo de pago para activarlo.</li>
      <li><strong>2.</strong> Elige tu producto.</li>
      <li><strong>3.</strong> Presenta o inserta tu tarjeta.</li>
      <li><strong>4.</strong> Ingresa tu PIN si se solicita y espera la confirmación.</li>
      <li><strong>5.</strong> Retira tu producto cuando se encienda la luz.</li></ol>
      <figure class="figura"><img src="/assets/instrucciones-uso.webp" loading="lazy" width="1100" height="571" alt="Instrucciones de uso de la máquina: presiona el dispositivo de pago, elige tu producto, presenta o inserta tu tarjeta, ingresa tu PIN y retira tu producto. Si no se dispensa, escribe al +56 9 3736 8898."><figcaption>Adhesivo de instrucciones que llevan nuestras máquinas.</figcaption></figure>""")
    return documento(ruta="/soporte/", title="Soporte: problema con una máquina ASO",
                     desc=f"¿La máquina expendedora no entregó tu producto o falló el pago? Repórtalo por WhatsApp al {CONFIG['telefono_visible']} y lo resolvemos directamente.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Soporte", "/soporte/")], cta=False)


def pagina_blog(posts) -> str:
    lista_p = "".join(tarjeta_post(p) for p in posts) or "<li><p>Pronto publicaremos la primera entrada.</p></li>"
    cuerpo = hero("Blog", "Blog de <em>vending para empresas</em>",
                  "Guías prácticas para decidir si conviene una máquina expendedora, dónde ubicarla y qué exige la normativa.", botones=False)
    cuerpo += f'<section class="bloque"><div class="wrap"><ul class="posts">{lista_p}</ul></div></section>'
    blog_schema = {"@type": "Blog", "@id": url("/blog/#blog"), "name": "Blog ASO Vending", "url": url("/blog/"),
                   "publisher": {"@id": url("/#negocio")}, "inLanguage": "es-CL",
                   "blogPost": [{"@type": "BlogPosting", "headline": p["titulo"], "url": url(f"/blog/{p['slug']}/"),
                                 "datePublished": p["fecha"]} for p in posts]}
    return documento(ruta="/blog/", title="Blog: guías sobre máquinas expendedoras", tipo="CollectionPage",
                     desc="Guías sobre máquinas expendedoras para empresas: comodato, ubicación, normativa de sellos y café en la oficina. Blog de ASO Vending, Concepción.",
                     cuerpo=cuerpo, crumbs=[("Inicio", "/"), ("Blog", "/blog/")], extra_schema=[blog_schema])


def pagina_post(p, posts) -> str:
    ruta = f"/blog/{p['slug']}/"
    otros = [o for o in posts if o is not p][:3]
    rel = ('<section class="bloque"><div class="wrap"><h2>Sigue leyendo</h2><ul class="posts">'
           + "".join(tarjeta_post(o, "h3") for o in otros) + "</ul></div></section>") if otros else ""
    act = f' · actualizado el <time datetime="{p["actualizado"]}">{fecha_humana(p["actualizado"])}</time>' if p["actualizado"] != p["fecha"] else ""
    cuerpo = f"""<article>
  <header class="hero"><div class="wrap" style="max-width:52rem">
    <p class="eyebrow">{E(p['categoria'])}</p><h1>{E(p['titulo'])}</h1><p class="lead">{E(p['desc'])}</p>
    <p class="meta" style="margin-top:1.5rem"><time datetime="{p['fecha']}">{fecha_humana(p['fecha'])}</time>{act} · {p['minutos']} min de lectura · {E(p['autor'])}</p>
  </div></header>
  <div class="bloque"><div class="wrap articulo" style="max-width:52rem">{p['html']}</div></div>
</article>{rel}"""
    post_schema = {"@type": "BlogPosting", "@id": url(ruta) + "#articulo", "headline": p["titulo"],
                   "description": p["desc"], "datePublished": p["fecha"], "dateModified": p["actualizado"],
                   "image": url(p["imagen"]), "mainEntityOfPage": {"@id": url(ruta) + "#pagina"},
                   "author": {"@type": "Organization", "name": p["autor"], "url": url("/")},
                   "publisher": {"@id": url("/#negocio")}, "inLanguage": "es-CL",
                   "articleSection": p["categoria"], "isPartOf": {"@id": url("/blog/#blog")}}
    return documento(ruta=ruta, title=p["titulo_seo"], desc=p["desc"], cuerpo=cuerpo, og_tipo="article",
                     imagen=p["imagen"], crumbs=[("Inicio", "/"), ("Blog", "/blog/"), (p["titulo"], ruta)],
                     extra_schema=[post_schema],
                     head_extra=f'<meta property="article:published_time" content="{p["fecha"]}">\n<meta property="article:modified_time" content="{p["actualizado"]}">')


def pagina_404() -> str:
    cuerpo = hero("Error 404", "Esta página <em>no existe.</em>",
                  'Puede que el enlace esté mal escrito o que la página se haya movido. Vuelve al <a class="textlink" href="/">inicio</a> o revisa el <a class="textlink" href="/blog/">blog</a>.', botones=False)
    return documento(ruta="/404/", title="Página no encontrada", desc="La página que buscas no existe.",
                     cuerpo=cuerpo, indexar=False)


# ═══════════════════════════════════════════════════════════
# 7 · Archivos técnicos (sitemap, robots, RSS, llms.txt, headers)
# ═══════════════════════════════════════════════════════════
def sitemap(rutas: list[tuple[str, str]]) -> str:
    urls = "\n".join(f"  <url><loc>{url(r)}</loc><lastmod>{f}</lastmod></url>" for r, f in rutas)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n'


def rss(posts) -> str:
    def rfc822(iso):
        return dt.datetime.fromisoformat(iso).strftime("%a, %d %b %Y 09:00:00 -0300")
    items = "".join(
        f"<item><title>{E(p['titulo'])}</title><link>{url('/blog/' + p['slug'] + '/')}</link>"
        f"<guid>{url('/blog/' + p['slug'] + '/')}</guid><pubDate>{rfc822(p['fecha'])}</pubDate>"
        f"<description>{E(p['desc'])}</description></item>" for p in posts)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Blog ASO Vending</title>'
            f"<link>{url('/blog/')}</link><description>Guías sobre máquinas expendedoras para empresas en el Biobío</description>"
            f"<language>es-cl</language>{items}</channel></rss>\n")


def llms_txt(posts) -> str:
    lineas = [f"# {CONFIG['marca']}", "",
              f"> Instalación sin costo (comodato), reposición y mantención de máquinas expendedoras de snacks, bebidas y café para empresas e instituciones en {CONFIG['ciudad']} y la {CONFIG['region']}, Chile. Contacto: WhatsApp {CONFIG['telefono_visible']}, {CONFIG['correo']}.",
              "", "## Páginas principales"]
    for r, t in [("/servicio/", "Servicio y modalidad comodato"), ("/maquinas/", "Máquinas"), ("/productos/", "Productos"),
                 ("/sectores/", "Sectores"), ("/cobertura/", "Cobertura"), ("/preguntas-frecuentes/", "Preguntas frecuentes"),
                 ("/contacto/", "Contacto")]:
        lineas.append(f"- [{t}]({url(r)})")
    lineas += ["", "## Blog"] + [f"- [{p['titulo']}]({url('/blog/' + p['slug'] + '/')}): {p['desc']}" for p in posts]
    return "\n".join(lineas) + "\n"


HEADERS = """/assets/*
  Cache-Control: public, max-age=86400

/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
"""

REDIRECTS = """/index.html / 301
/servicios.html /servicio/ 301
/servicios /servicio/ 301
/maquinas.html /maquinas/ 301
/productos.html /productos/ 301
/nosotros.html /nosotros/ 301
/contacto.html /contacto/ 301
/preguntas-frecuentes.html /preguntas-frecuentes/ 301
/faq /preguntas-frecuentes/ 301
/vending-oficinas.html /sectores/oficinas/ 301
/vending-clinicas.html /sectores/clinicas-y-centros-medicos/ 301
/vending-universidades.html /sectores/universidades-e-institutos/ 301
/vending-industria.html /sectores/industria-y-faenas/ 301
"""


# ═══════════════════════════════════════════════════════════
# 8 · Construcción
# ═══════════════════════════════════════════════════════════
def escribir(ruta: str, contenido: str):
    destino = DIST / ruta.lstrip("/")
    if ruta.endswith("/"):
        destino = destino / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(RAIZ / "static", DIST)
    posts = leer_posts()

    paginas = {
        "/": pagina_inicio(posts),
        "/servicio/": pagina_servicio(),
        "/maquinas/": pagina_maquinas(),
        "/productos/": pagina_productos(),
        "/sectores/": pagina_sectores(),
        "/cobertura/": pagina_cobertura(),
        "/cotizador/": pagina_cotizador(),
        "/nosotros/": pagina_nosotros(),
        "/preguntas-frecuentes/": pagina_faq(),
        "/contacto/": pagina_contacto(),
        "/soporte/": pagina_soporte(),
        "/blog/": pagina_blog(posts),
    }
    for s in SECTORES:
        paginas[f"/sectores/{s['slug']}/"] = pagina_sector(s)
    for p in posts:
        paginas[f"/blog/{p['slug']}/"] = pagina_post(p, posts)

    for ruta, contenido in paginas.items():
        escribir(ruta, contenido)
    (DIST / "404.html").write_text(pagina_404(), encoding="utf-8")

    fechas = {f"/blog/{p['slug']}/": p["actualizado"] for p in posts}
    ult_post = posts[0]["fecha"] if posts else HOY
    rutas = [(r, fechas.get(r, ult_post if r in ("/", "/blog/") else HOY)) for r in paginas]
    (DIST / "sitemap.xml").write_text(sitemap(rutas), encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {url('/sitemap.xml')}\n", encoding="utf-8")
    (DIST / "blog" / "feed.xml").write_text(rss(posts), encoding="utf-8")
    (DIST / "llms.txt").write_text(llms_txt(posts), encoding="utf-8")
    (DIST / "_headers").write_text(HEADERS, encoding="utf-8")
    (DIST / "_redirects").write_text(REDIRECTS, encoding="utf-8")
    print(f"Listo: {len(paginas)} páginas + 404, {len(posts)} entradas de blog → {DIST}")


if __name__ == "__main__":
    main()
