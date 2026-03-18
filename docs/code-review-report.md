# Code Review Report — eml_to_mailmd

**Data**: 2026-03-18
**Revisione**: Completa (qualità, test, sicurezza)
**File analizzato**: `eml_to_mailmd.py` (~573 righe)

---

## Punteggi

| Area | Score | Valutazione |
|------|-------|-------------|
| Qualità & Architettura | **7 / 10** | Buona struttura, naming coerente, alcune duplicazioni |
| Copertura Test | **0%** | Nessun test presente — rischio critico |
| Sicurezza & Resilienza | **6.5 / 10** | Buone basi, gap su input validation e gestione risorse |

---

## Executive Summary

Il progetto è un tool CLI single-file ben strutturato che usa correttamente `pathlib`, `dataclass`, e type hints moderni. Le dipendenze sono minime e appropriate (`rich`, `send2trash`). I punti deboli principali sono: **assenza totale di test**, **eccezioni troppo ampie** (`except Exception` ovunque), **duplicazione di logica** in `pick_body()`, e **mancanza di escape per newline** in `yaml_escape()` che può causare YAML malformato.

---

## Findings Critici e Ad Alta Priorità

### 1. CRITICO — Nessun test automatizzato

**Impatto**: Tutto il codice non ha copertura. Il tool esegue operazioni distruttive (trash dei sorgenti) senza alcuna verifica automatica.

**Rischio**: Regressioni non rilevate, bug silenziosi nelle conversioni, data loss potenziale.

**Raccomandazione**: Creare test suite con pytest. Priorità P0:
- `pick_body()` — plain text, HTML fallback, multipart, encoding fallback, empty body
- `build_mail_md()` — YAML frontmatter con caratteri speciali
- `validate_mail_md()` — file valido, file mancante, mismatch di coerenza
- `yaml_escape()` — backslash, virgolette, stringa vuota
- `safe_filename()` / `unique_path()` — caratteri speciali, collisioni
- End-to-end: `.eml` → `.md` con verifica contenuto

### 2. HIGH — `yaml_escape()` non gestisce newline (sicurezza + qualità)

**Righe**: 55-57
**Problema**: La funzione escapa `\` e `"` ma non `\n` e `\r`. I campi `from`, `to`, `cc`, `bcc` non vengono sanitizzati per newline (solo `subject` ha `.replace("\n", " ")`).

**Vettore di attacco**: Un'email con header `From: "Name\nmalicious_key: value" <a@b.com>` può iniettare chiavi YAML aggiuntive nel frontmatter.

**Fix**:
```python
def yaml_escape(value: str) -> str:
    value = value.replace("\n", " ").replace("\r", "")
    return value.replace("\\", "\\\\").replace('"', '\\"')
```

### 3. HIGH — Logica di decode duplicata in `pick_body()` (qualità)

**Righe**: 123-131 vs 155-171
**Problema**: I branch non-multipart e multipart contengono catene try/except quasi identiche per `get_content()` → fallback a `get_payload(decode=True)`.

**Fix**: Estrarre un helper `_decode_part(part: EmailMessage) -> str | None`.

### 4. HIGH — `except Exception` troppo ampio (sicurezza + qualità)

**Righe**: 112, 123-131, 155-168, 338, 445
**Problema**: Cattura ogni eccezione indiscriminatamente. Mascheratura bug reali, dati persi silenziosamente (es. body vuoto senza warning), debugging reso molto difficile.

**Fix specifici**:
| Funzione | Catch attuale | Catch corretto |
|----------|--------------|----------------|
| `parse_date_raw_to_dt` | `Exception` | `ValueError` |
| `load_eml` | `Exception` | `(OSError, email.errors.MessageError)` |
| `trash_source` | `Exception` | `OSError` |
| `pick_body` decode | `Exception` | `(LookupError, UnicodeDecodeError, KeyError)` |

---

## Findings a Media Priorità

### 5. MEDIUM — Nessun limite dimensione file (sicurezza)

**Righe**: 206-209
**Problema**: `load_eml()` carica interamente il file in memoria. Un `.eml` da 2GB causa OOM.

**Fix**: Controllare `path.stat().st_size` prima del parsing, rifiutare file oltre soglia (es. 50MB).

### 6. MEDIUM — Tutti gli `EmailMessage` tenuti in memoria (sicurezza)

**Righe**: 524, 539, 546
**Problema**: La lista `msgs` trattiene tutti gli oggetti `EmailMessage` (inclusi allegati) fino a fine esecuzione. Con 100 email da 10MB l'una → ~1GB RAM.

**Fix**: Ristrutturare per validare immediatamente dopo ogni conversione, poi rilasciare il riferimento.

### 7. MEDIUM — `main()` ha troppe responsabilità (qualità)

**Righe**: 470-568
**Problema**: ~100 righe che gestiscono arg parsing, file discovery, progress bar, conversione, validazione, trashing e summary. Difficile da testare.

**Fix**: Estrarre `run_conversions(emls, console, keep) -> list[Result]`.

### 8. MEDIUM — TOCTOU race condition in `unique_path()` (sicurezza)

**Righe**: 74-85
**Problema**: Gap tra `path.exists()` e la scrittura effettiva. Con invocazioni concorrenti, due run possono scegliere lo stesso path e una sovrascrive l'altra.

**Fix**: Usare `open(path, 'x')` (creazione esclusiva atomica) con retry.

### 9. MEDIUM — `Result` dataclass fa doppio servizio (qualità)

**Problema**: `Result` è sia risultato di conversione che di post-processing (validation + trash). I campi crescono (`validated`, `trashed`, `trash_message`, `validation_errors`).

**Fix**: Separare in `ConversionResult` e `PostResult`, oppure usare un metodo `result.with_validation(...)`.

---

## Findings a Bassa Priorità

| # | Area | Descrizione | Righe |
|---|------|-------------|-------|
| 10 | Qualità | Type hints misti: `List`/`Optional` vs `list`/`str \| None`. Con `from __future__ import annotations` usare sempre lowercase | 17 |
| 11 | Qualità | Import inutilizzati: `Iterable`, `Any` da `typing` | 17-18 |
| 12 | Qualità | `join_addrs` → meglio `format_addresses` per chiarezza | 87 |
| 13 | Qualità | Costante `EML_EXTENSIONS = {".eml", ".elm"}` mancante (check ripetuto) | 465, 512 |
| 14 | Qualità | Magic number `len(emls) > 5` per progress bar → costante `PROGRESS_THRESHOLD` | 525 |
| 15 | Qualità | Exit code (0/1/2/3) non documentati → usare `IntEnum` | 568 |
| 16 | Sicurezza | Scrittura non atomica: `write_text()` diretto → file parziale se interruzione | 369 |
| 17 | Sicurezza | Dipendenze con floor pin (`>=13.0`) senza lock file | pyproject.toml |
| 18 | Sicurezza | Nessun `resolve()` dopo `expanduser()` sul path folder | 500 |
| 19 | Test | `_HTMLStripper` non filtra contenuto `<script>`/`<style>` — CSS/JS leak nel testo | 31-52 |
| 20 | Test | `validate_mail_md`: `content.split("---")` si rompe se il body contiene `---` | 396-401 |
| 21 | Test | `safe_filename()` non tronca — filename lunghi possono superare 255 byte | 65-71 |
| 22 | Test | `unique_path()` senza limite massimo tentativi → loop infinito teorico | 74-85 |

---

## Bug Potenziali Identificati

| # | Severità | Funzione | Descrizione |
|---|----------|----------|-------------|
| B1 | **Medium** | `_HTMLStripper` | Non sopprime contenuto `<script>`/`<style>`. CSS o JS nelle email HTML finiscono nel testo plain. |
| B2 | **Medium** | `yaml_escape` | Non escapa `\n`/`\r`. Header con newline letterali producono YAML malformato. |
| B3 | **Low** | `validate_mail_md` | `split("---")` over-split se il body contiene `---`. Mitigato da `"---".join(parts[2:])` per il body, ma il frontmatter potrebbe essere mal-parsato. |
| B4 | **Low** | `safe_filename` | Nessun troncamento. Subject molto lunghi → filename oltre il limite filesystem. |
| B5 | **Low** | `build_mail_md` | Tipo parametro `msg: Message` dovrebbe essere `EmailMessage` (più specifico). |

---

## Punti di Forza

- **Approccio single-file appropriato** per la dimensione del progetto
- **Buon uso di `pathlib`** in tutto il codebase
- **`safe_filename()` robusto** — regex pulisce efficacemente i caratteri pericolosi
- **`send2trash` per trash sicuro** — no cancellazione permanente
- **Rich `escape()` per markup injection** — filename con `[` non rompono l'output
- **Validazione prima del trash** — ordine corretto che previene data loss
- **Gestione graceful dei fallimenti trash** — errore catturato, file sorgente preservato
- **Dipendenze minime e appropriate**

---

## Piano d'Azione Raccomandato

| Priorità | Azione | Effort | Impatto |
|----------|--------|--------|---------|
| **P0** | Creare test suite pytest (P0 test plan sopra) | Alto | Critico |
| **P1** | Fix `yaml_escape()` per newline (#2) | Basso | Alto |
| **P1** | Estrarre `_decode_part()` da `pick_body()` (#3) | Basso | Medio |
| **P1** | Restringere `except Exception` (#4) | Basso | Alto |
| **P2** | Limite dimensione file in `load_eml()` (#5) | Basso | Medio |
| **P2** | Validazione immediata per file per ridurre memoria (#6) | Medio | Medio |
| **P2** | Estrarre loop conversione da `main()` (#7) | Basso | Medio |
| **P3** | Fix atomicità scrittura + unique_path (#8, #16) | Medio | Basso |
| **P3** | Cleanup type hints e import (#10, #11) | Basso | Basso |
| **P3** | Costanti per magic values (#13, #14, #15) | Basso | Basso |

---

*Report generato da team di 3 agent specializzati (qualità, test, sicurezza) con sintesi automatica.*
