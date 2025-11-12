from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_staff_user
from app.core.config import settings

router = APIRouter()

@router.post("/generate-xlsx")
def generate_questions_xlsx(
    file: UploadFile = File(...),
    question_count: int = Query(20, ge=1, le=500),
    topic: str = Query(""),
    difficulty: str = Query("mixed"),
    questions_per_chunk: int = Query(10, ge=1, le=50),
    max_pages: int = Query(30, ge=1, le=1000),
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

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    system = (
        "You are a question generation assistant. Produce diverse, unambiguous, well-structured questions. "
        "Use the provided document only to infer TOPIC and STYLE. "
        "Do NOT copy or paraphrase anything from the document. "
        "Generate subject-matter questions — never meta-questions about exams, questions, or assessment processes. "
        "Return ONLY valid JSON, no commentary."
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

    all_rows = []
    chunks = chunk_text(text)
    # Determine per-chunk target
    per_chunk = max(1, min(int(questions_per_chunk or 10), 50))
    remaining = max(1, min(int(question_count or 20), 500))
    for i, ch in enumerate(chunks):
        if remaining <= 0:
            break
        want = min(per_chunk, remaining)
        user_prompt = user_prompt_template.format(count=want, topic=(topic or 'the material'), difficulty=difficulty, chunk_text=ch)
        try:
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
            # Skip this chunk on failure
            continue

        try:
            m = re.search(r"\{[\s\S]*\}\s*$", content)
            blob = m.group(0) if m else content
            data = json.loads(blob)
            rows = list((data or {}).get('rows') or [])
        except Exception:
            rows = []
        # Append
        if isinstance(rows, list):
            for r in rows:
                all_rows.append(r)
                if len(all_rows) >= question_count:
                    break
        remaining = question_count - len(all_rows)

    if not all_rows:
        raise HTTPException(status_code=400, detail="No rows generated by LLM")

    # Optional post-filter: remove obvious meta-questions
    wb = Workbook(); ws = wb.active; ws.title = "questions"; ws.append(headers)
    def get(d, k):
        v = d.get(k, "")
        return "" if v is None else str(v)
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
