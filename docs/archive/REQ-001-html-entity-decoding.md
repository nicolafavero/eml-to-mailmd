# REQ-001: Decodifica HTML entity in strip_html()

**Implements:** UR-002
**Status:** completed

## Descrizione

`strip_html()` non decodifica le HTML entity (`&nbsp;`, `&amp;`, `&lt;`, ecc.).
Aggiungere `html.unescape()` per convertirle in testo leggibile.

## Checklist

- [x] Importare `html` (stdlib)
- [x] Applicare `html.unescape()` sull'output dopo lo stripping (non prima, per evitare che `&lt;` venga interpretato come tag)
- [x] Verificare che `&nbsp;` → spazio, `&amp;` → `&`, `&lt;` → `<`

## Note di completamento

- Data: 2026-03-18
- `html.unescape()` applicato DOPO `HTMLParser` (non prima) per evitare che entity come `&lt;` vengano interpretate come tag HTML reali
