# ASO Vending — sitio asoexpendedoras.cl (v3, multipágina + blog)

Sitio estático: cada pestaña es una página HTML propia con su URL, título, descripción,
datos estructurados (schema.org) y migas de pan. Google lo lee completo sin ejecutar JavaScript.

## Estructura

```
build.py              generador (aquí se cambian teléfono, correo, sectores y FAQ)
contenido/blog/*.md   entradas del blog (una por archivo)
static/assets/        logo, íconos, video de la portada, CSS y JS
wrangler.jsonc        configuración del Worker de Cloudflare
dist/                 SITIO GENERADO — esto es lo que se publica (no editar a mano)
```

## Generar el sitio

Requiere Python 3.10 o superior.

```
pip install markdown
python build.py
```

Para verlo en tu PC antes de publicar:

```
cd dist
python -m http.server 8000
```

y abre http://localhost:8000 (abrir el index.html con doble clic NO funciona: los enlaces son del tipo /servicio/).

## Publicar en Cloudflare

```
npx wrangler deploy
```

Usa `wrangler.jsonc`, que sirve la carpeta `dist/`. Incluye `_headers` (caché y seguridad) y
`_redirects` (redirige las URL .html del sitio anterior a las nuevas).

## Escribir una entrada del blog

1. Crea un archivo en `contenido/blog/`, por ejemplo `cafe-en-la-oficina.md`. El nombre del archivo es la URL: `/blog/cafe-en-la-oficina/`.
2. Encabezado obligatorio:

```
---
titulo: Título completo que se ve en la página
titulo_seo: Título corto para Google (máx. ~60 caracteres, opcional)
descripcion: Resumen de 120 a 160 caracteres para Google y redes
fecha: 2026-10-05
categoria: Guías
actualizado: 2026-10-20        (opcional)
imagen: /assets/og.jpg         (opcional, 1200x630)
borrador: si                   (opcional: no se publica)
---
```

3. Escribe el texto en Markdown debajo (## para subtítulos, - para listas, [texto](/contacto/) para enlaces).
4. Ejecuta `python build.py` y vuelve a publicar. El blog, la portada, el sitemap y el RSS se actualizan solos.

## Páginas

Inicio (video con scroll) · Servicio · Máquinas · Productos · Sectores (6 páginas) · Cobertura ·
Cotizador interactivo · Blog · Nosotros · Preguntas frecuentes · Contacto · Soporte (reporte de fallas) · 404.

## SEO incluido

- Título y descripción únicos por página; canonical; Open Graph.
- JSON-LD: LocalBusiness/Organization, WebSite, BreadcrumbList, Service, FAQPage, Blog y BlogPosting.
- sitemap.xml con fechas, robots.txt, RSS del blog (/blog/feed.xml) y llms.txt (resumen para buscadores con IA).
- Enlazado interno entre sectores, servicio y blog.

## Pendiente fuera del código (lo que más pesa en SEO local)

1. **Google Business Profile**: crear la ficha de ASO Vending Machine en Concepción con el mismo teléfono y enlazar el sitio.
2. **Google Search Console**: verificar el dominio y enviar https://asoexpendedoras.cl/sitemap.xml.
3. **Dirección**: el sitio solo dice "Concepción". Si agregas calle y número en `build.py` (org_schema → address), mejora la ficha local.
4. **Fotos reales** de máquinas instaladas (sin mostrar marcas ni nombres de clientes).
5. **Publicar en el blog** con regularidad (una entrada al mes es un buen ritmo).

## Afirmaciones que debes confirmar antes de publicar

- Instalación sin costo en modalidad comodato.
- Modalidad subsidiada disponible.
- Mantención incluida sin costo para la empresa.
- Reporte de ventas y mantenciones a la empresa.
- Cobertura en las seis comunas listadas.
- Máquina de café GS 505 con café, capuchino y chocolate.
