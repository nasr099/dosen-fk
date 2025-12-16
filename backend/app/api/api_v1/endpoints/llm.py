from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_staff_user
from app.core.config import settings

router = APIRouter()

# Module-level deterministic MCQ/MULTI parser used by scanner
import re as _re_mod
def parse_mcq_blocks_det(raw: str):
    rows = []
    if not raw:
        return rows
    text_n = _re_mod.sub(r"\u00A0", " ", raw)
    # Join hyphenated line wraps like "kata-\nkata" -> "kata kata"
    text_n = _re_mod.sub(r"([A-Za-z0-9])\-\n([A-Za-z0-9])", r"\1 \2", text_n)
    lines = [ln.strip() for ln in text_n.splitlines()]
    buffer = []
    opts = {}
    def flush():
        nonlocal buffer, opts
        if len([k for k in opts.keys() if k in ['A','B','C']]) >= 3:
            stem = " ".join([x for x in buffer if x]).strip()
            def getopt(ch): return opts.get(ch, "")
            ca = ''
            tail = ' '.join(list(opts.values())[-2:]) + ' ' + stem[-200:]
            m = _re_mod.search(r"(?:Jawaban|Answer)\s*[:\-]?\s*([A-E](?:\s*,\s*[A-E])*)", tail, _re_mod.I)
            if m:
                ca = m.group(1).upper().replace(' ', '')
            else:
                for ch in ['A','B','C','D','E']:
                    if _re_mod.search(r"\*", opts.get(ch,'') or ''):
                        ca = ch; opts[ch] = _re_mod.sub(r"\*", "", opts[ch]).strip(); break
            rows.append({
                'type': 'mcq',
                'question_text': stem,
                'question_img': '',
                'option_a_text': getopt('A'), 'option_a_img': '',
                'option_b_text': getopt('B'), 'option_b_img': '',
                'option_c_text': getopt('C'), 'option_c_img': '',
                'option_d_text': getopt('D'), 'option_d_img': '',
                'option_e_text': getopt('E'), 'option_e_img': '',
                'correct_answer': ca,
                'explanation': '',
                'reading_id': '', 'reading_title': '', 'reading_content': '',
            })
        buffer = []
        opts = {}
    for ln in lines:
        if not ln:
            if opts:
                flush()
            else:
                if buffer and len(' '.join(buffer))>0:
                    buffer.append('')
            continue
        m = _re_mod.match(r"^\(?([A-Ea-e])\)\s*(.*)$", ln)
        if m:
            ch = m.group(1).upper(); text = (m.group(2) or '').strip(); opts[ch] = text; continue
        m2 = _re_mod.match(r"^([A-Ea-e])[\.|:]\s*(.*)$", ln)
        if m2:
            ch = m2.group(1).upper(); text = (m2.group(2) or '').strip(); opts[ch] = text; continue
        if opts:
            flush()
        buffer.append(ln)
    if opts:
        flush()
    return rows

@router.post("/generate-xlsx")
def generate_questions_xlsx(
    file: UploadFile = File(...),
    question_count: int = Query(20, ge=1, le=500),
    topic: str = Query(""),
    difficulty: str = Query("mixed"),
    questions_per_chunk: int = Query(10, ge=1, le=50),
    max_pages: int = Query(30, ge=1, le=1000),
    latexify: bool = Query(True),
    language: str = Query("auto"),
    db: Session = Depends(get_db),
    _=Depends(get_current_staff_user),
):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the server")
    try:
        from openpyxl import Workbook
    except Exception:
        raise HTTPException(status_code=500, detail="openpyxl is not installed on the server")
    try:
        from openai import OpenAI
    except Exception:
        raise HTTPException(status_code=500, detail="openai python package is not installed on the server")

    # Read body
    content_type = (file.content_type or '').lower()
    filename = (file.filename or '').lower()
    text = ""
    try:
        if content_type != 'application/pdf' and not filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for generation.")
        # Extract text from PDF with pypdf
        try:
            from pypdf import PdfReader
        except Exception:
            raise HTTPException(status_code=500, detail="pypdf is not installed on the server")
        data = file.file.read() or b""
        try:
            import io
            reader = PdfReader(io.BytesIO(data))
            pages = reader.pages[:max_pages]
            parts = []
            for p in pages:
                try:
                    parts.append(p.extract_text() or "")
                except Exception:
                    continue
            text = "\n\n".join([t for t in parts if t])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")
    except Exception:
        text = ""

    if not (text or '').strip() or len((text or '').strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="PDF text extraction returned empty/too-short content. If this PDF is scanned (image-based), please use a text-based PDF or run OCR first.",
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _detect_lang(t: str) -> str:
        s = (t or '').lower()
        if not s.strip():
            return 'en'
        id_hits = 0
        for w in ['yang','dan','atau','dengan','untuk','pada','dari','sebagai','maka','jika','tidak','adalah','dalam','sehingga','karena','bukan','bahwa','apa','berapa','tentukan','pilih','jawaban']:
            if f' {w} ' in f' {s} ':
                id_hits += 1
                if id_hits >= 3:
                    return 'id'
        return 'en'

    lang = (language or 'auto').strip().lower()
    if lang in ('auto', 'detect'):
        lang = _detect_lang(text)
    if lang not in ('id', 'en'):
        lang = 'en'

    system = (
        "You are a question generation assistant. Produce diverse, unambiguous, well-structured questions. "
        "Use the provided document only to infer TOPIC and STYLE. "
        "Do NOT copy or paraphrase anything from the document. "
        "Generate subject-matter questions — never meta-questions about exams, questions, or assessment processes. "
        "Return ONLY valid JSON, no commentary. "
        + ("Write ALL questions and explanations in Indonesian." if lang == 'id' else "Write ALL questions and explanations in English.")
    )
    headers = [
        'type','question_text','question_img',
        'option_a_text','option_a_img',
        'option_b_text','option_b_img',
        'option_c_text','option_c_img',
        'option_d_text','option_d_img',
        'option_e_text','option_e_img',
        'correct_answer','explanation',
        'reading_id','reading_title','reading_content',
    ]
    user_prompt_template = """
You are given a source document (below) for calibration only. Create approximately {count} brand-new subject-matter questions about '{topic}' at {difficulty} difficulty. If 'topic' is blank, infer a concise topic from the document and use that.

Language requirement:
- Write the questions and explanations in {lang_name}.

Before generating, do this planning internally (do not output the plan):
1) Detect 1–5 key sub-themes present in the document (e.g., FPB dan KPK, Aritmetika Sosial, dll.).
2) Estimate the style distribution in the document between short questions vs. story/word-problem questions.
3) Allocate the total questions roughly evenly across the detected sub-themes (e.g., if 3 themes and 15 questions → 5 per theme). If {count} is not divisible, distribute the remainder starting from the most prominent theme.

Then generate the questions accordingly.

Output JSON with this exact shape:
{{
  "rows": [
    {{
      "type": "mcq|multi",
      "question_text": "rich text allowed (plain text). Use LaTeX fragments when math appears, using $...$ for inline and $$...$$ for block.",
      "question_img": "" ,
      "option_a_text": "", "option_a_img": "",
      "option_b_text": "", "option_b_img": "",
      "option_c_text": "", "option_c_img": "",
      "option_d_text": "", "option_d_img": "",
      "option_e_text": "", "option_e_img": "",
      "correct_answer": "A|B|C|D|E for mcq, or comma letters like A,B for multi",
      "explanation": "short explanation",
      "reading_id": "", "reading_title": "", "reading_content": ""
    }}
  ]
}}

Constraints:
- Only produce MCQ and MULTI questions. Do NOT produce ESSAY questions.
- Do NOT produce meta-questions about exams, questions, generating questions, assessments, pedagogy, or test design.
- Generate entirely new content: do NOT copy, paraphrase, or quote the document’s text, numbers, names, or specific facts.
- Ensure MCQ has exactly one correct letter. MULTI should use comma-separated letters.
- Avoid images; leave *_img fields blank.
- Keep rows self-contained; do not rely on external context from the document.

Style & Coverage:
- Match the style proportion found in the document: if many story problems, most generated questions should be story problems with realistic analogies and necessary data.
- Balance questions across the detected sub-themes. For each row, set reading_title to the chosen sub-theme label (e.g., "FPB & KPK"). You may leave reading_content blank.

Self-check before answering:
- If any question mentions words like 'question', 'questions', 'assessment', 'test', 'generate', 'creating questions', rewrite it into a subject-matter question tied to the topic.

Source document (for calibration of topic/pattern only; do not copy):
-----
{chunk_text}
-----
"""
    import json, re
    # Chunk text into roughly 8000-character pieces to keep prompt size reasonable
    def chunk_text(s: str, size: int = 8000):
        s = s or ""
        return [ s[i:i+size] for i in range(0, len(s), size) ] or [""]

    def _extract_json(text_value: str):
        raw = (text_value or '').strip()
        if not raw:
            raise ValueError('empty model output')
        # Prefer ```json fenced blocks if present
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
        candidate = (m.group(1).strip() if m else raw)
        # Try strict parse (with mild cleanup for common model mistakes)
        cleaned = candidate
        cleaned = re.sub(r",\s*(\]|\})", r"\1", cleaned)  # trailing commas
        cleaned = re.sub(r"\u0000", "", cleaned)
        try:
            return json.loads(cleaned)
        except Exception:
            pass
        # Try to extract the first JSON object in the text
        m2 = re.search(r"\{[\s\S]*?\}", candidate)
        if m2:
            piece = m2.group(0)
            piece = re.sub(r",\s*(\]|\})", r"\1", piece)
            return json.loads(piece)
        # Try trailing object
        m3 = re.search(r"\{[\s\S]*\}\s*$", candidate)
        if m3:
            piece = m3.group(0)
            piece = re.sub(r",\s*(\]|\})", r"\1", piece)
            return json.loads(piece)
        raise ValueError('could not locate JSON object in model output')

    # 1) Deterministic regex-based extractor to avoid losing question stems
    import re
    def parse_mcq_blocks(raw: str):
        rows = []
        if not raw:
            return rows
        # Normalize newlines and collapse excessive spaces
        text_n = re.sub(r"\u00A0", " ", raw)
        lines = [ln.strip() for ln in text_n.splitlines()]
        buffer = []
        opts = {}
        def flush():
            nonlocal buffer, opts
            # Require at least A,B,C to count as a question
            if len([k for k in opts.keys() if k in ['A','B','C']]) >= 3:
                stem = " ".join([x for x in buffer if x]).strip()
                def getopt(ch):
                    return opts.get(ch, "")
                # Detect explicit answer markers
                ca = ''
                # Marker line like "Jawaban: B" or "Answer: B" near the end
                tail = ' '.join(list(opts.values())[-2:]) + ' ' + stem[-200:]
                m = re.search(r"(?:Jawaban|Answer)\s*[:\-]?\s*([A-E](?:\s*,\s*[A-E])*)", tail, re.I)
                if m:
                    ca = m.group(1).upper().replace(' ', '')
                else:
                    # Option with asterisk indicates correct
                    for ch in ['A','B','C','D','E']:
                        if re.search(r"\*", opts.get(ch,'') or ''):
                            ca = ch; opts[ch] = re.sub(r"\*", "", opts[ch]).strip(); break
                rows.append({
                    'type': 'mcq',
                    'question_text': stem,
                    'question_img': '',
                    'option_a_text': getopt('A'), 'option_a_img': '',
                    'option_b_text': getopt('B'), 'option_b_img': '',
                    'option_c_text': getopt('C'), 'option_c_img': '',
                    'option_d_text': getopt('D'), 'option_d_img': '',
                    'option_e_text': getopt('E'), 'option_e_img': '',
                    'correct_answer': ca,
                    'explanation': '',
                    'reading_id': '', 'reading_title': '', 'reading_content': '',
                })
            buffer = []
            opts = {}
        for ln in lines:
            if not ln:
                # blank line likely separates items
                if opts:
                    flush()
                else:
                    if buffer and len(' '.join(buffer))>0:
                        buffer.append('')
                continue
            m = re.match(r"^\(?([A-Ea-e])\)\s*(.*)$", ln)
            if m:
                ch = m.group(1).upper(); text = (m.group(2) or '').strip()
                # If we see first option and buffer not empty, this starts options for current stem
                opts[ch] = text
                continue
            # If options already started and we meet a line starting with label patterns like 'D.' etc
            m2 = re.match(r"^([A-Ea-e])[\.|:]\s*(.*)$", ln)
            if m2:
                ch = m2.group(1).upper(); text = (m2.group(2) or '').strip(); opts[ch] = text; continue
            # Otherwise, part of stem
            if opts:
                # A new non-option line after options likely indicates question end
                flush()
            buffer.append(ln)
        if opts:
            flush()
        return rows

    all_rows = parse_mcq_blocks(text)
    chunks = chunk_text(text)
    per_chunk = max(1, min(int(questions_per_chunk or 10), 50))
    remaining = max(1, min(int(question_count or 20), 500))
    max_rounds = max(1, (remaining + per_chunk - 1) // per_chunk) * max(1, len(chunks))
    no_progress = 0
    last_error = None
    for i in range(int(max_rounds)):
        if remaining <= 0:
            break
        ch = chunks[i % len(chunks)] if chunks else ""
        want = min(per_chunk, remaining)
        user_prompt = user_prompt_template.format(
            count=want,
            topic=(topic or 'the material'),
            difficulty=difficulty,
            chunk_text=ch,
            lang_name=("Bahasa Indonesia" if lang == 'id' else "English"),
        )
        try:
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.6,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role":"system","content":system},
                        {"role":"user","content":user_prompt},
                    ],
                )
            except TypeError:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.6,
                    messages=[
                        {"role":"system","content":system},
                        {"role":"user","content":user_prompt},
                    ],
                )
            content = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            last_error = f"OpenAI error: {type(e).__name__}: {e}"
            no_progress += 1
            if no_progress >= 3:
                break
            continue

        try:
            data = _extract_json(content)
            rows = list((data or {}).get('rows') or [])
        except Exception as e:
            last_error = f"Parse error: {type(e).__name__}: {e}"
            rows = []

        before = len(all_rows)
        if isinstance(rows, list):
            for r in rows:
                all_rows.append(r)
                if len(all_rows) >= question_count:
                    break
        after = len(all_rows)
        if after <= before:
            no_progress += 1
        else:
            no_progress = 0
        if no_progress >= 3:
            break
        remaining = question_count - len(all_rows)

    if not all_rows:
        raise HTTPException(
            status_code=400,
            detail=(
                "No rows generated by LLM. "
                + (f"Last error: {last_error}" if last_error else "")
            ).strip(),
        )

    # Optional post-filter: remove obvious meta-questions
    # Optional post-pass to convert math to LaTeX without changing other text
    if bool(latexify) and client and all_rows:
        try:
            prompt = {
                "role": "user",
                "content": (
                    "Convert any mathematical expressions in the following JSON rows into LaTeX ($ ... $ for inline, $$ ... $$ for block) without altering other wording, punctuation, or casing. Return ONLY JSON with the same schema and keys.\n\n" +
                    str({"rows": all_rows})
                )
            }
            resp2 = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.0,
                messages=[
                    {"role":"system","content":"You strictly transform math to LaTeX without changing any other text or adding/removing rows."},
                    prompt,
                ],
            )
            import json as _json, re as _re
            content2 = (resp2.choices[0].message.content or '').strip()
            m2 = _re.search(r"\{[\s\S]*\}\s*$", content2)
            blob2 = m2.group(0) if m2 else content2
            data2 = _json.loads(blob2)
            rows2 = list((data2 or {}).get('rows') or [])
            if rows2:
                all_rows = rows2
        except Exception:
            pass

    wb = Workbook(); ws = wb.active; ws.title = "questions"; ws.append(headers)
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    def get(d, k):
        v = d.get(k, "")
        if v is None:
            return ""
        s = str(v)
        # OpenPyXL rejects certain control chars (0x00-0x1F excluding \t\n\r)
        return ILLEGAL_CHARACTERS_RE.sub("", s)
    import re as _re
    meta_pattern = _re.compile(r"\b(question|questions|assessment|assessments|generate|generating|exam|test|testing)\b", _re.IGNORECASE)
    filtered_rows = [r for r in all_rows if not meta_pattern.search(str(r.get('question_text','')))] or all_rows
    for r in filtered_rows:
        qtype = (get(r,'type') or 'mcq').lower()
        if qtype not in ('mcq','multi'): qtype = 'mcq'
        ca = get(r, 'correct_answer').upper().replace(' ', '')
        if qtype == 'mcq':
            if ca not in ['A','B','C','D','E']:
                ca = 'A'
        else:  # multi
            parts = [p for p in re.split(r"[,;]", ca) if p]
            parts = [p for p in parts if p in ['A','B','C','D','E']]
            ca = ','.join(sorted(set(parts))) or 'A'
        ws.append([
            qtype,
            get(r,'question_text'), get(r,'question_img'),
            get(r,'option_a_text'), get(r,'option_a_img'),
            get(r,'option_b_text'), get(r,'option_b_img'),
            get(r,'option_c_text'), get(r,'option_c_img'),
            get(r,'option_d_text'), get(r,'option_d_img'),
            get(r,'option_e_text'), get(r,'option_e_img'),
            ca,
            get(r,'explanation'),
            get(r,'reading_id'), get(r,'reading_title'), get(r,'reading_content'),
        ])

    from io import BytesIO
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={
        'Content-Disposition': 'attachment; filename="llm_generated_questions.xlsx"'
    })

@router.post("/scan-xlsx")
def scan_questions_xlsx(
    file: UploadFile = File(...),
    questions_per_chunk: int = Query(20, ge=1, le=100),
    max_pages: int = Query(100, ge=1, le=2000),
    max_questions: int = Query(500, ge=1, le=2000),
    use_llm: bool = Query(False),
    latexify: bool = Query(True),
    db: Session = Depends(get_db),
    _=Depends(get_current_staff_user),
):
    try:
        from openpyxl import Workbook
    except Exception:
        raise HTTPException(status_code=500, detail="openpyxl is not installed on the server")
    # Initialize OpenAI client only if needed
    client = None
    if use_llm or latexify:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the server")
        try:
            from openai import OpenAI
        except Exception:
            raise HTTPException(status_code=500, detail="openai python package is not installed on the server")
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Validate and read PDF
    content_type = (file.content_type or '').lower()
    filename = (file.filename or '').lower()
    if content_type != 'application/pdf' and not filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for scanning.")
    try:
        from pypdf import PdfReader
    except Exception:
        raise HTTPException(status_code=500, detail="pypdf is not installed on the server")

    try:
        data = file.file.read() or b""
        import io
        reader = PdfReader(io.BytesIO(data))
        pages = reader.pages[:max_pages]
        parts = []
        for p in pages:
            try:
                parts.append(p.extract_text() or "")
            except Exception:
                continue
        text = "\n\n".join([t for t in parts if t])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")
    # If PDF has no selectable text (e.g., scanned images), pypdf returns empty
    if not (text or '').strip():
        raise HTTPException(status_code=400, detail="No selectable text found in PDF. This may be a scanned/image PDF. Try enabling LLM fallback or provide a text-based PDF.")

    system = (
        "You are a precise question extraction assistant. Extract existing questions from the provided text exactly as written. "
        "Preserve wording, numbers, and structure. If options/answers are present, keep them verbatim. "
        "If an image/table is referenced, ignore it and proceed with text only. "
        "Output ONLY valid JSON."
    )
    headers = [
        'type','question_text','question_img',
        'option_a_text','option_a_img',
        'option_b_text','option_b_img',
        'option_c_text','option_c_img',
        'option_d_text','option_d_img',
        'option_e_text','option_e_img',
        'correct_answer','explanation',
        'reading_id','reading_title','reading_content',
    ]
    user_prompt_template = """
Extract up to {limit} multiple-choice questions from the source text below. Reproduce each question and its options EXACTLY as written (do not paraphrase). Include every question you can find in this chunk (not just the last). Questions often have options labeled (A) (B) (C) (D) (E). If multiple correct options are indicated, set type="multi" and use comma letters like A,B. If a single correct option is indicated, set type="mcq" and a single letter. If the correct answer is marked by an asterisk or phrases like "Jawaban: B" / "Answer: B", detect it. If not indicated, leave correct_answer blank.

Math handling: When you detect mathematical expressions, rewrite them in LaTeX. Use inline math with $ ... $ for short expressions; use block math with $$ ... $$ for standalone equations.

Ignore images/tables/figures (leave *_img blank). Leave explanation blank unless an explicit explanation is present in the text.

Output JSON with exactly this shape:
{{
  "rows": [
    {{
      "type": "mcq|multi",
      "question_text": "original question text (with LaTeX where appropriate)",
      "question_img": "",
      "option_a_text": "", "option_a_img": "",
      "option_b_text": "", "option_b_img": "",
      "option_c_text": "", "option_c_img": "",
      "option_d_text": "", "option_d_img": "",
      "option_e_text": "", "option_e_img": "",
      "correct_answer": "A or A,B,...",
      "explanation": "",
      "reading_id": "", "reading_title": "", "reading_content": ""
    }}
  ]
}}

Source chunk:
-----
{chunk_text}
-----
Return only JSON.
"""

    import json, re
    def chunk_text(s: str, size: int = 8000, overlap: int = 1000):
        s = s or ""
        if size <= 0: size = 8000
        if overlap < 0: overlap = 0
        if overlap >= size: overlap = size // 4
        chunks = []
        i = 0
        n = len(s)
        step = max(1, size - overlap)
        while i < n:
            chunks.append(s[i:i+size])
            i += step
        return chunks or [""]

    all_rows = []
    # Deterministic parse first (module-level helper)
    all_rows = parse_mcq_blocks_det(text)
    # Optional LLM fallback to capture anything missed
    if use_llm and client and len(all_rows) < max_questions:
        chunks = chunk_text(text)
        per_chunk = max(1, min(int(questions_per_chunk or 20), 100))
        remaining = max(1, min(int(max_questions or 500), 2000)) - len(all_rows)
        for ch in chunks:
            if remaining <= 0:
                break
            want = min(per_chunk, remaining)
            user_prompt = user_prompt_template.format(chunk_text=ch, limit=want)
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.1,
                    messages=[
                        {"role":"system","content":system},
                        {"role":"user","content":user_prompt},
                    ],
                )
                content = (resp.choices[0].message.content or "").strip()
            except Exception:
                # fallback to next chunk
                continue

            try:
                m = re.search(r"\{[\s\S]*\}\s*$", content)
                blob = m.group(0) if m else content
                data = json.loads(blob)
                rows = list((data or {}).get('rows') or [])
            except Exception:
                rows = []
            if isinstance(rows, list):
                for r in rows:
                    all_rows.append(r)
                    if len(all_rows) >= max_questions:
                        break
            remaining = max_questions - len(all_rows)

    if not all_rows:
        raise HTTPException(status_code=400, detail="No questions detected from the PDF")

    wb = Workbook(); ws = wb.active; ws.title = "questions"; ws.append(headers)
    def get(d, k):
        v = d.get(k, "")
        return "" if v is None else str(v)
    # Write rows as-is, with minimal normalization for type and correct_answer letters
    for r in all_rows:
        qtype = (get(r,'type') or 'mcq').lower()
        if qtype not in ('mcq','multi'): qtype = 'mcq'
        ca = get(r,'correct_answer').upper().replace(' ', '')
        if qtype == 'mcq':
            if ca not in ['A','B','C','D','E']:
                ca = ''
        else:
            parts = [p for p in re.split(r"[,;]", ca) if p]
            parts = [p for p in parts if p in ['A','B','C','D','E']]
            ca = ','.join(sorted(set(parts)))
        ws.append([
            qtype,
            get(r,'question_text'), get(r,'question_img'),
            get(r,'option_a_text'), get(r,'option_a_img'),
            get(r,'option_b_text'), get(r,'option_b_img'),
            get(r,'option_c_text'), get(r,'option_c_img'),
            get(r,'option_d_text'), get(r,'option_d_img'),
            get(r,'option_e_text'), get(r,'option_e_img'),
            ca,
            get(r,'explanation'),
            get(r,'reading_id'), get(r,'reading_title'), get(r,'reading_content'),
        ])

    from io import BytesIO
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={
        'Content-Disposition': 'attachment; filename="scanned_questions.xlsx"'
    })
