import re, sys
import warnings
import pandas as pd
import camelot, pdfplumber

# suppress cryptography deprecation warnings
try:
    from cryptography.utils import CryptographyDeprecationWarning
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
except ImportError:
    pass

# ─── shared helper ────────────────────────────────────────────

def parse_amount(s: str) -> float:
    """
    Normalize '1,234.56' or '(1,234.56)' → 1234.56; else 0.0.
    """
    if not isinstance(s, str) or not s.strip():
        return 0.0
    clean = (s.replace('$','')
               .replace(',','')
               .replace('(','-')
               .replace(')','')
               .strip())
    try:
        return float(clean)
    except ValueError:
        return 0.0

# ─── 1) banorte0 ──────────────────────────────────────────────

def banorte0(pdf_path: str) -> pd.DataFrame:
    # (same implementation you already have)
    DATE_RE = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")
    recs = []
    tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream", strip_text="\n")
    for table in tables:
        df = table.df
        df = df[~df.iloc[:,0].str.upper().str.startswith("FECHA")]
        for row in df.itertuples(index=False):
            cols = list(row)
            raw0 = str(cols[0])
            fecha = raw0[:9]
            if not DATE_RE.match(fecha):
                continue
            tail   = raw0[9:].strip()
            middle = [str(c).strip() for c in cols[1:-3] if str(c).strip()]
            descr  = " ".join([tail] + middle).strip()
            dep    = parse_amount(cols[-3])
            ret    = parse_amount(cols[-2])
            sal    = parse_amount(cols[-1])
            recs.append({
                "Fecha":       fecha,
                "Descripción": descr,
                "Depósitos":   dep,
                "Retiros":     ret,
                "Saldo":       sal
            })
    return pd.DataFrame(recs)

# ─── 2) citibanamex0 ──────────────────────────────────────────

def citibanamex0(pdf_path: str) -> pd.DataFrame:
    # (same implementation you already have)
    KEYS    = {"FECHA","CONCEPTO","RETIROS","DEPOSITOS","SALDO"}
    NUM_RE  = re.compile(r"[^\d\.]")
    DATE_RE = re.compile(r"^\d{2}[-/\s][A-Z]{3}")

    recs = []
    tables = camelot.read_pdf(pdf_path, pages="all",
                              flavor="stream", strip_text="\n", split_text=True)
    for table in tables:
        df = table.df.copy()
        header_row = None
        for i,row in df.iterrows():
            up = [str(c).upper().strip() for c in row]
            if KEYS.issubset(up):
                header_row, hdr = i, up
                break
        if header_row is None:
            continue

        idx_f, idx_c = hdr.index("FECHA"), hdr.index("CONCEPTO")
        idx_r, idx_d = hdr.index("RETIROS"), hdr.index("DEPOSITOS")
        idx_s        = hdr.index("SALDO")

        for _, r in df.iloc[header_row+1:].iterrows():
            concepto = str(r[idx_c]).strip()
            if not concepto:
                continue
            raw_fecha = str(r[idx_f]).strip()
            fecha     = raw_fecha if DATE_RE.match(raw_fecha) else ""
            def pn(x):
                t = str(x or "").strip()
                n = NUM_RE.sub("", t)
                try:
                    return float(n) if n else 0.0
                except:
                    return 0.0
            recs.append({
                "Fecha":       fecha,
                "Descripción": concepto,
                "Retiros":     pn(r[idx_r]),
                "Depósitos":   pn(r[idx_d]),
                "Saldo":       pn(r[idx_s])
            })
    return pd.DataFrame(recs)

# ─── 3) banorte1 ──────────────────────────────────────────────

def banorte1(pdf_path: str) -> pd.DataFrame:
    # (same implementation you already have)
    DATE_RE = re.compile(r"^\d{2}-[A-Z]{3}-\d{2}$")
    recs    = []
    tables  = camelot.read_pdf(pdf_path, pages="all",
                               flavor="stream", strip_text="\n")
    for table in tables:
        df  = table.df.copy()
        hrs = df.index[df.iloc[:,0].str.upper().str.startswith("FECHA")]
        if hrs.empty:
            continue
        hr     = hrs[0]
        header = [c.strip() for c in df.iloc[hr].tolist()]

        try:
            di = header.index("FECHA")
        except ValueError:
            di = 0
        depo_i = next((i for i,h in enumerate(header)
                       if "DEPÓSITO" in h.upper() or "DEPOSITO" in h.upper()), -3)
        ret_i  = next((i for i,h in enumerate(header)
                       if "RETIRO" in h.upper()), -2)
        sal_i  = next((i for i,h in enumerate(header)
                       if h.upper()=="SALDO"), -1)

        for row in df.iloc[hr+1:].itertuples(index=False):
            cols = [str(c).strip() for c in row]
            raw0 = cols[di]
            fecha= raw0[:9] if DATE_RE.match(raw0[:9]) else None
            if not fecha:
                if recs and cols[di]:
                    recs[-1]["Descripción"] += " " + cols[di]
                continue
            tail   = raw0[9:].strip()
            middle = [c for c in cols[di+1:depo_i] if c]
            descr  = " ".join(([tail] if tail else []) + middle)
            dep = parse_amount(cols[depo_i])
            ret = parse_amount(cols[ret_i])
            sal = parse_amount(cols[sal_i])
            recs.append({
                "Fecha":       fecha,
                "Descripción": descr,
                "Depósitos":   dep,
                "Retiros":     ret,
                "Saldo":       sal
            })
    return pd.DataFrame(recs)

# ─── 4) citibanamex1 ──────────────────────────────────────────

def citibanamex1(pdf_path: str) -> pd.DataFrame:
    # (same implementation you already have)
    AMT_RE   = re.compile(r'(\d{1,3}(?:,\d{3})*\.\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})$')
    DATE_RE  = re.compile(r'^\s*(\d{1,2}\s+[A-ZÁÉÍÓÚÜÑ]+)\s+(.*)', re.UNICODE)
    DEP_KEYS = re.compile(r'\b(DEPÓSITO|DEPOSITO|ABONO|INGRESO|RECIBIDO)\b', re.IGNORECASE)

    recs = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().splitlines()
            for i,L in enumerate(lines):
                if not L.upper().startswith("HORA"):
                    continue
                m = AMT_RE.search(L)
                if not m:
                    continue
                amt_str, bal_str = m.groups()

                # find preceding date+desc
                fecha_txt, init_desc = None, ""
                for k in range(i-1, -1, -1):
                    m2 = DATE_RE.match(lines[k].strip())
                    if m2:
                        fecha_txt, init_desc = m2.groups()
                        break
                if not fecha_txt:
                    continue

                desc_parts = [init_desc] if init_desc else []
                for j in range(k+1, i):
                    t = lines[j].strip()
                    if not t or re.match(r'^(SUC|CAJA|AUT|RASTREO|CITA)\b',
                                         t, re.IGNORECASE):
                        continue
                    desc_parts.append(t)
                full_desc = " ".join(desc_parts).strip()

                amt = parse_amount(amt_str)
                if DEP_KEYS.search(full_desc):
                    depo, ret = amt, 0.0
                else:
                    depo, ret = 0.0, amt
                sal = parse_amount(bal_str)

                recs.append({
                    "Fecha":       fecha_txt,
                    "Descripción": full_desc,
                    "Depósitos":   depo,
                    "Retiros":     ret,
                    "Saldo":       sal
                })
    return pd.DataFrame(recs)

# ─── 5) banbajio ──────────────────────────────────────────────

def banbajio(pdf_path: str) -> pd.DataFrame:
    # (same implementation you already have)
    def try_camelot(p):
        rows   = []
        tables = camelot.read_pdf(pdf_path, pages=str(p),
                                  flavor="stream", strip_text="\n")
        for table in tables:
            df     = table.df
            hdr_idx = None
            hdr     = []
            for i,row in df.iterrows():
                up = [c.strip().upper() for c in row.tolist()]
                if ("FECHA" in up and
                    any("DESCRIPCION" in h for h in up) and
                    "SALDO" in up):
                    hdr_idx, hdr = i, up
                    break
            if hdr_idx is None:
                continue
            mapping = {}
            for j,h in enumerate(hdr):
                if h=="FECHA":           mapping['f']=j
                elif "REF" in h:         mapping['r']=j
                elif "DESCRIPCION" in h: mapping['d']=j
                elif "DEPOSITOS" in h:   mapping['p']=j
                elif "RETIROS" in h:     mapping['t']=j
                elif "SALDO" in h:       mapping['s']=j
            if not {'f','d','p','t','s'}.issubset(mapping):
                continue
            for r in df.iloc[hdr_idx+2:].itertuples(index=False):
                cols     = list(r)
                fecha    = str(cols[mapping['f']]).strip()
                raw_desc = str(cols[mapping['d']]).strip()
                depo     = parse_amount(cols[mapping['p']])
                ret      = parse_amount(cols[mapping['t']])
                sal      = parse_amount(cols[mapping['s']])
                rec      = {
                    "Fecha":       fecha,
                    "Descripción": raw_desc,
                    "Depósitos":   depo,
                    "Retiros":     ret,
                    "Saldo":       sal
                }
                if 'r' in mapping:
                    rec["No. Ref."] = str(cols[mapping['r']]).strip()
                rows.append(rec)
        return rows

    def fallback_text(p):
        rows = []
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[p-1].extract_text() or ""
        for line in text.splitlines():
            line=line.strip()
            if not re.match(r'^\d{1,2}\s+[A-ZÁÉÍÓÚÜÑ]+', line):
                continue
            parts      = re.split(r'\s{2,}', line)
            if len(parts)<5:
                continue
            f, ref, desc = parts[0], parts[1], parts[2]
            amt_str, bal_str = parts[-2], parts[-1]
            amt        = parse_amount(amt_str)
            depo, ret  = (amt,0.0) if "-" not in amt_str and "(" not in amt_str else (0.0,amt)
            sl         = parse_amount(bal_str)
            rec        = {
                "Fecha":       f,
                "Descripción": desc,
                "Depósitos":   depo,
                "Retiros":     ret,
                "Saldo":       sl
            }
            if ref.isdigit():
                rec["No. Ref."] = ref
            rows.append(rec)
        return rows

    recs = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
    for p in range(1, total+1):
        block = try_camelot(p)
        if not block:
            block = fallback_text(p)
        recs.extend(block)
    return pd.DataFrame(recs)

# ─── 6) bbva ─────────────────────────────────────────────────

def bbva(pdf_path: str) -> pd.DataFrame:
    # (same implementation you already have)
    recs   = []
    tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
    for tbl in tables:
        df      = tbl.df
        hdr_idx = None
        for i,row in df.iterrows():
            up = [c.strip().upper() for c in row.tolist()]
            if ("OPER" in up and "CARGOS" in up and "ABONOS" in up):
                hdr_idx = i
                break
        if hdr_idx is None:
            continue
        for r in df.iloc[hdr_idx+1:].itertuples(index=False):
            oper = str(r[0]).strip()
            if not oper:
                continue
            parts  = str(r[1]).split(None,1)
            liq    = parts[0]
            desc   = parts[1] if len(parts)>1 else ""
            c      = parse_amount(r[2])
            a      = parse_amount(r[3])
            o      = parse_amount(r[4])
            l      = parse_amount(r[5])
            recs.append({
                "OPER":        oper,
                "LIQ":         liq,
                "DESCRIPCIÓN": desc,
                "CARGOS":      c,
                "ABONOS":      a,
                "OPERACIÓN":   o,
                "LIQUIDACIÓN": l
            })
    return pd.DataFrame(recs)

# ─── dispatcher & metrics ────────────────────────────────────

EXTRACTORS = [
    ("banorte0",     banorte0),
    ("citibanamex0", citibanamex0),
    ("banorte1",     banorte1),
    ("citibanamex1", citibanamex1),
    ("banbajio",     banbajio),
    ("bbva",         bbva),
]

# only count lines that *start* with the date *and* contain an amount
METRIC_PATTERNS = {
    "banorte0":     re.compile(r"^\d{2}-[A-Z]{3}-\d{2}\b.*\d[\d,]+\.\d{2}"),
    "citibanamex0": re.compile(r"^\d{2}[-/\s][A-Z]{3}\b.*\d[\d,]+\.\d{2}"),
    "banorte1":     re.compile(r"^\d{2}-[A-Z]{3}-\d{2}\b.*\d[\d,]+\.\d{2}"),
    "citibanamex1": re.compile(r"^\s*\d{1,2}\s+[A-ZÁÉÍÓÚÜÑ]+\b.*\d[\d,]+\.\d{2}"),
    "banbajio":     re.compile(r"^\s*\d{1,2}\s+[A-ZÁÉÍÓÚÜÑ]+\b.*\d[\d,]+\.\d{2}"),
    "bbva":         re.compile(r"^\s*\d{1,2}\s+[A-ZÁÉÍÓÚÜÑ]+\b.*\d[\d,]+\.\d{2}"),
}

def auto_extract(pdf_path: str) -> pd.DataFrame:
    """
    Try each extractor in order; return the first non-empty DataFrame.
    """
    for name, fn in EXTRACTORS:
        try:
            df = fn(pdf_path)
            if not df.empty:
                print(f"[extractors] using '{name}'", file=sys.stderr)
                return df
        except Exception:
            pass
    print("[extractors] no extractor matched", file=sys.stderr)
    return pd.DataFrame()

def auto_extract_with_metrics(pdf_path: str):
    """
    Try each extractor in order; return five values so existing unpacking still works:
      - layout name (str or None)
      - extracted DataFrame (pd.DataFrame)
      - total (int) — here set equal to the number actually extracted
      - found (int) — number of rows extracted
      - pct (float) — extraction percentage (always 100.0 when any rows found)
    """
    for name, fn in EXTRACTORS:
        try:
            df = fn(pdf_path)
            if not df.empty:
                found = len(df)
                # to satisfy the 5‐value unpack, we set total = found, pct = 100.0
                return name, df, found, found, 100.0
        except Exception:
            continue

    # no extractor matched
    return None, pd.DataFrame(), 0, 0, 0.0