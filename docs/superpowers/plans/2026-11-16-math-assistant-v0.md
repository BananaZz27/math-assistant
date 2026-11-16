# แผนงาน v0: ผู้ช่วยคณิตศาสตร์และวิเคราะห์ข้อมูล

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**เป้าหมาย:** โปรแกรมบรรทัดคำสั่ง (command line) ที่รับโจทย์คณิตศาสตร์หรือไฟล์ CSV คำนวณด้วยโค้ดจริง (SymPy / pandas) ตรวจคำตอบ แล้วให้โมเดลภาษาในเครื่อง (Ollama) เป็นคนเลือกเครื่องมือและอธิบายผล

**สถาปัตยกรรม:** v0 มีสองชั้น คือ `tools/` (โค้ดคำนวณที่ให้ผลแน่นอน) และ `brain/` (อะแดปเตอร์ LLM ที่สลับได้) เชื่อมกันด้วย `core.answer()` สมองไม่เคยสร้างตัวเลขสุดท้ายเอง แค่เลือกเครื่องมือและอธิบายผลที่ตรวจแล้ว ส่วน `api/`, `ui/`, `character/` เป็นของเวอร์ชันถัดไป และ **ไม่แตะในแผนนี้**

**เทคโนโลยี:** Python 3.11+, SymPy, pandas, requests, pytest และ Ollama ที่รันที่ `http://localhost:11434` (ใช้ตอนงานที่ 5 แบบทดสอบมือ และงานที่ 6 เท่านั้น)

**เอกสารออกแบบ:** `docs/superpowers/specs/2026-11-16-math-assistant-design.md` (หัวข้อ 2, 4, 7, 9, 11 ใช้กับ v0)

## ข้อจำกัดรวม (Global Constraints)

- Python 3.11 ขึ้นไป ต้องรันได้ทั้ง Windows และ Linux (เครื่องโบ๊ทคือ HP Victus 16)
- ไลบรารีตอนรันจำกัดแค่ `sympy`, `pandas`, `requests` ส่วนตอนพัฒนา: `pytest`
- ห้ามเชื่อมเน็ต ยกเว้น Ollama บน `localhost` ห้ามมี API key ใน repo หรือเอกสาร
- แยกหน้าที่เด็ดขาด: ห้ามมีโค้ด LLM หรือ HTTP ใน `tools/` ห้ามมีคณิตศาสตร์หรือการอ่านไฟล์ใน `brain/`
- ตัวเลขทุกตัวมาจากโค้ดเครื่องมือ ไม่ใช่จาก LLM (เป้าหมายข้อ 3 ของเอกสารออกแบบ)
- v0 แก้เฉพาะคำตอบที่เป็น **จำนวนจริง** (ผมตัดสินใจเอง ตามหัวข้อ 9)
- โครงโค้ด: แพ็กเกจ `src/assistant/` เทสต์อยู่ใน `tests/`
- ข้อความในเอกสารและ CLI เป็นไทยผสมอังกฤษ ชื่อในโค้ดเป็นอังกฤษ

## จุดที่ต้องตรวจเป็นพิเศษ (Review Focus)

1. คณิตศาสตร์ที่คนไทยพิมพ์จริง: `x² − 5x + 6 = 0`, `5x`, `x^2` ต้องอ่านได้เหมือน `x**2 - 5*x + 6 = 0` (งานที่ 1)
2. สมการไม่มีคำตอบหรือมีคำตอบทุกค่า (`x + 1 = x + 2`, `x + 1 = x + 1`) ต้องตอบชัดเจน ไม่ crash และไม่คืนลิสต์ว่างที่ดูเหมือนสำเร็จ (งานที่ 1)
3. ข้อความอันตรายหรือผิดรูป (`__import__('os').system('echo hi')`, `((((`) ต้องถูกปฏิเสธด้วย `ToolError` ไม่ถูกรัน (งานที่ 1)
4. CSV แปลกๆ: ไฟล์ว่าง, ไม่มีไฟล์, หัวคอลัมน์ภาษาไทย, คอลัมน์ที่ค่าหายทั้งหมด (งานที่ 2)
5. เครื่องมือที่ค้างต้องถูกตัดด้วย timeout และ Ollama ที่ติดต่อไม่ได้ต้องแจ้งเป็นข้อความที่อ่านเข้าใจ ไม่ใช่ stack trace (งานที่ 3 และ 5)

---

## โครงไฟล์

```
pyproject.toml
src/assistant/__init__.py
src/assistant/errors.py          ToolError, BrainError
src/assistant/config.py          DEFAULT_MODEL, OLLAMA_HOST, TOOL_TIMEOUT_S
src/assistant/tools/__init__.py
src/assistant/tools/parse.py     แปลงและอ่านข้อความคณิตศาสตร์อย่างปลอดภัย
src/assistant/tools/algebra.py   solve_equation
src/assistant/tools/dataframe.py summarize_csv
src/assistant/tools/registry.py  ToolSpec, TOOLS, run_tool (มี timeout)
src/assistant/brain/__init__.py
src/assistant/brain/base.py      ToolCall, Brain protocol
src/assistant/brain/fake.py      FakeBrain (ไว้ทดสอบ)
src/assistant/brain/local.py     LocalBrain (Ollama)
src/assistant/core.py            Answer, answer()
src/assistant/cli.py             python -m assistant.cli
scripts/benchmark_models.py      เทียบโมเดลบนเครื่องโบ๊ท
scripts/benchmark_questions.json
tests/ (หนึ่งไฟล์ต่อหนึ่งโมดูล)
README.md
```

---

### Task 1: โครงโปรเจกต์ + เครื่องมือแก้สมการ

**ไฟล์:**
- สร้าง: `pyproject.toml`, `src/assistant/__init__.py`, `src/assistant/errors.py`, `src/assistant/config.py`, `src/assistant/tools/__init__.py`, `src/assistant/tools/parse.py`, `src/assistant/tools/algebra.py`
- เทสต์: `tests/test_parse.py`, `tests/test_algebra.py`

**อินเทอร์เฟซ:**
- ให้ผู้อื่นใช้:
  - `errors.ToolError(Exception)`, `errors.BrainError(Exception)`
  - `parse.normalize_math_text(text: str) -> str` (แทน `²`→`**2`, `³`→`**3`, `−`→`-`, `×`→`*`, `÷`→`/`, `^`→`**`)
  - `parse.parse_expression(text: str) -> sympy.Expr` (อ่านอย่างปลอดภัย รองรับการคูณโดยปริยายเช่น `5x` ถ้าไม่ใช่นิพจน์คณิตศาสตร์ให้ raise `ToolError`)
  - `algebra.SolveResult` frozen dataclass: `equation: str`, `variable: str`, `solutions: list[str]`, `kind: Literal["finite","none","all"]`, `verified: bool`
  - `algebra.solve_equation(text: str, variable: str = "x") -> SolveResult` (ข้อความที่ไม่มี `=` ถือว่า "= 0")

- [ ] **ขั้นที่ 1: เขียนเทสต์ที่ยังไม่ผ่าน**

```python
# tests/test_parse.py
def test_normalize_unicode_math():
    assert normalize_math_text("x² − 5x + 6") == "x**2 - 5x + 6"

def test_parse_implicit_multiplication():
    assert parse_expression("5x") == 5 * Symbol("x")

def test_parse_rejects_code_injection():
    with pytest.raises(ToolError):
        parse_expression("__import__('os').system('echo hi')")

def test_parse_rejects_garbage():
    with pytest.raises(ToolError):
        parse_expression("((((")
```

```python
# tests/test_algebra.py
def test_quadratic_two_roots():
    r = solve_equation("x² − 5x + 6 = 0")
    assert r.kind == "finite" and r.solutions == ["2", "3"] and r.verified is True

def test_expression_without_equals_means_zero():
    assert solve_equation("x**2 - 5*x + 6").solutions == ["2", "3"]

def test_caret_and_implicit_multiplication():
    assert solve_equation("2x + 4 = 0").solutions == ["-2"]
    assert solve_equation("x^2 = 9").solutions == ["-3", "3"]

def test_no_real_solution():
    r = solve_equation("x**2 + 1 = 0")
    assert r.kind == "none" and r.solutions == []

def test_contradiction_has_no_solution():
    assert solve_equation("x + 1 = x + 2").kind == "none"

def test_identity_is_all_reals():
    assert solve_equation("x + 1 = x + 1").kind == "all"

def test_bad_input_raises_tool_error():
    with pytest.raises(ToolError):
        solve_equation("__import__('os').system('echo hi')")
```

- [ ] **ขั้นที่ 2: รันเทสต์ ต้อง FAIL** — `pytest tests/test_parse.py tests/test_algebra.py -v` (ได้ ImportError / NameError)
- [ ] **ขั้นที่ 3: เขียนโค้ด** `pyproject.toml` (แพ็กเกจ `assistant`, โครง src, ไลบรารีตามข้อจำกัดรวม), `errors.py`, `config.py` ที่มี `DEFAULT_MODEL = "qwen2.5:7b"` (ค่าชั่วคราวจนกว่าจะรัน benchmark ในงานที่ 6), `OLLAMA_HOST = "http://localhost:11434"`, `TOOL_TIMEOUT_S = 10.0` จากนั้นเขียน `normalize_math_text`, `parse_expression`, `solve_equation`
  - อ่านนิพจน์ด้วย `sympy.parsing.sympy_parser.parse_expr` โดยกำหนด `local_dict` ให้มีแค่สัญลักษณ์ตัวแปรกับฟังก์ชันใน whitelist (`sqrt`, `sin`, `cos`, `tan`, `log`, `exp`, `pi`, `E`) และ `global_dict={}` ใส่ transformations `implicit_multiplication_application` และ `convert_xor` ปฏิเสธข้อความที่มี `_` หรือชื่อนอก whitelist ก่อนเข้า parser
  - แก้ด้วย `solveset(lhs - rhs, symbol, S.Reals)` แปลง `EmptySet`→`none`, `Reals`→`all`, `FiniteSet`→`finite` (เรียงตามค่าตัวเลข) ชุดคำตอบแบบอื่น (ช่วง, ConditionSet) → `ToolError("unsupported equation")`
  - `verified` = แทนทุกคำตอบกลับแล้วได้ศูนย์ (`simplify(lhs-rhs).subs == 0`) ส่วน `none`/`all` ให้เป็น `True`
- [ ] **ขั้นที่ 4: รันเทสต์ ต้อง PASS** — คำสั่งเดิม
- [ ] **ขั้นที่ 5: commit** — `git init` (เฉพาะงานแรก) เพิ่ม `.gitignore` (venv, `__pycache__`, `.env`) แล้ว `git add -A && git commit -m "feat: skeleton and safe algebra solver"`

---

### Task 2: เครื่องมือสรุปไฟล์ CSV

**ไฟล์:**
- สร้าง: `src/assistant/tools/dataframe.py`
- เทสต์: `tests/test_dataframe.py`

**อินเทอร์เฟซ:**
- ใช้: `errors.ToolError`
- ให้ผู้อื่นใช้:
  - `ColumnSummary` frozen dataclass: `name: str`, `dtype: str`, `missing: int`, `minimum: float | None`, `maximum: float | None`, `mean: float | None` (เฉพาะคอลัมน์ตัวเลข นอกนั้นเป็น `None`)
  - `CsvSummary` frozen dataclass: `rows: int`, `columns: list[ColumnSummary]`
  - `summarize_csv(path: str) -> CsvSummary` (รองรับ UTF-8 และ UTF-8-BOM)

- [ ] **ขั้นที่ 1: เขียนเทสต์ที่ยังไม่ผ่าน** (ใช้ `tmp_path`)

```python
def test_basic_numeric_and_text(tmp_path):
    p = tmp_path / "a.csv"; p.write_text("name,score\nA,1\nB,3\n", encoding="utf-8")
    s = summarize_csv(str(p))
    assert s.rows == 2
    score = next(c for c in s.columns if c.name == "score")
    assert (score.minimum, score.maximum, score.mean) == (1.0, 3.0, 2.0)
    assert next(c for c in s.columns if c.name == "name").mean is None

def test_thai_headers(tmp_path):
    p = tmp_path / "t.csv"; p.write_text("อุณหภูมิ\n30\n32\n", encoding="utf-8-sig")
    assert summarize_csv(str(p)).columns[0].name == "อุณหภูมิ"

def test_missing_values_counted(tmp_path):
    p = tmp_path / "m.csv"; p.write_text("v\n1\n\n3\n", encoding="utf-8")
    assert summarize_csv(str(p)).columns[0].missing == 1

def test_all_missing_column_has_no_stats(tmp_path):
    p = tmp_path / "n.csv"; p.write_text("a,b\n1,\n2,\n", encoding="utf-8")
    b = next(c for c in summarize_csv(str(p)).columns if c.name == "b")
    assert b.missing == 2 and b.mean is None

def test_empty_file_raises(tmp_path):
    p = tmp_path / "e.csv"; p.write_text("", encoding="utf-8")
    with pytest.raises(ToolError): summarize_csv(str(p))

def test_missing_path_raises():
    with pytest.raises(ToolError): summarize_csv("no/such/file.csv")
```

- [ ] **ขั้นที่ 2: รัน ต้อง FAIL** — `pytest tests/test_dataframe.py -v`
- [ ] **ขั้นที่ 3: เขียน `summarize_csv`** ด้วย `pandas.read_csv(..., encoding="utf-8-sig")` แปลง `FileNotFoundError`, `EmptyDataError`, `ParserError` เป็น `ToolError` พร้อมข้อความที่อ่านเข้าใจ คำนวณสถิติเฉพาะคอลัมน์ที่ `pandas.api.types.is_numeric_dtype` เป็นจริงและมีค่าที่ไม่หายอย่างน้อยหนึ่งค่า แปลงค่า numpy เป็น `float` ของ Python
- [ ] **ขั้นที่ 4: รัน ต้อง PASS**
- [ ] **ขั้นที่ 5: commit** — `git commit -m "feat: csv summary tool"`

---

### Task 3: ทะเบียนเครื่องมือพร้อม timeout

**ไฟล์:**
- สร้าง: `src/assistant/tools/registry.py`
- เทสต์: `tests/test_registry.py`

**อินเทอร์เฟซ:**
- ใช้: `solve_equation`, `summarize_csv`, `ToolError`, `config.TOOL_TIMEOUT_S`
- ให้ผู้อื่นใช้:
  - `ToolSpec` frozen dataclass: `name: str`, `description: str`, `parameters: dict` (แบบ JSON-schema), `func: Callable[..., Any]`
  - `TOOLS: dict[str, ToolSpec]` มีเพียง `"solve_equation"` (พารามิเตอร์ `text: string`, `variable: string` ไม่บังคับ) และ `"summarize_csv"` (พารามิเตอร์ `path: string`)
  - `run_tool(name: str, args: dict, timeout_s: float = TOOL_TIMEOUT_S) -> dict` คืน `dataclasses.asdict(result)` และ raise `ToolError` เมื่อเครื่องมือไม่รู้จัก, อาร์กิวเมนต์ผิด, เครื่องมือล้มเหลว (เก็บข้อความเดิมไว้) และหมดเวลา (ข้อความมีคำว่า `"timed out"`)

- [ ] **ขั้นที่ 1: เขียนเทสต์ที่ยังไม่ผ่าน**

```python
def test_run_solve_equation():
    out = run_tool("solve_equation", {"text": "x**2 - 5*x + 6 = 0"})
    assert out["solutions"] == ["2", "3"] and out["verified"] is True

def test_unknown_tool():
    with pytest.raises(ToolError, match="unknown tool"):
        run_tool("rm_rf", {})

def test_bad_arguments():
    with pytest.raises(ToolError):
        run_tool("solve_equation", {"wrong": 1})

def test_tool_error_message_is_preserved():
    with pytest.raises(ToolError, match="empty"):
        run_tool("summarize_csv", {"path": EMPTY_CSV_PATH})  # ไฟล์ว่างจาก tmp_path

def test_timeout_stops_a_hanging_tool(monkeypatch):
    monkeypatch.setitem(TOOLS, "sleeper", ToolSpec("sleeper", "", {}, sleeper))
    with pytest.raises(ToolError, match="timed out"):
        run_tool("sleeper", {"secs": 5}, timeout_s=0.5)
```

(`sleeper(secs)` เป็นฟังก์ชันระดับโมดูลในไฟล์เทสต์ที่เรียก `time.sleep(secs)` เพื่อให้ทำงานได้กับ spawn)

- [ ] **ขั้นที่ 2: รัน ต้อง FAIL**
- [ ] **ขั้นที่ 3: เขียน `run_tool`** ด้วย `multiprocessing.get_context("spawn").Process` + `Queue` โปรเซสลูกเรียก `func(**args)` แล้วส่ง `("ok", asdict(result))` หรือ `("err", message)` โปรเซสแม่รอ `timeout_s` แล้ว `terminate()` และ raise `ToolError("tool timed out")` ต้องทำงานบน Windows ได้ (ฟังก์ชันตัวทำงานอยู่ระดับโมดูล ห้ามใช้ lambda)
- [ ] **ขั้นที่ 4: รัน ต้อง PASS** (เทสต์ timeout ควรจบภายใน ~1 วินาที)
- [ ] **ขั้นที่ 5: commit** — `git commit -m "feat: tool registry with timeout"`

---

### Task 4: อินเทอร์เฟซสมอง, FakeBrain, core.answer

**ไฟล์:**
- สร้าง: `src/assistant/brain/__init__.py`, `src/assistant/brain/base.py`, `src/assistant/brain/fake.py`, `src/assistant/core.py`
- เทสต์: `tests/test_core.py`

**อินเทอร์เฟซ:**
- ใช้: `ToolSpec`, `TOOLS`, `run_tool`, `ToolError`
- ให้ผู้อื่นใช้:
  - `base.ToolCall` frozen dataclass: `name: str`, `args: dict`
  - `base.Brain` Protocol: `plan(self, question: str, tools: list[ToolSpec]) -> ToolCall` และ `explain(self, question: str, call: ToolCall, result: dict) -> str`
  - `fake.FakeBrain(call: ToolCall, explanation: str)` ทำตาม `Brain` และเก็บ `explain_calls: list`
  - `core.UNVERIFIED_NOTICE: str` (ไทย+อังกฤษ: "ยังตรวจคำตอบไม่ผ่าน / could not verify the answer")
  - `core.Answer` frozen dataclass: `text: str`, `call: ToolCall`, `result: dict`, `verified: bool | None` (`None` เมื่อผลลัพธ์ไม่มีคีย์ `verified`)
  - `core.answer(question: str, brain: Brain, tools: dict[str, ToolSpec] = TOOLS) -> Answer`

- [ ] **ขั้นที่ 1: เขียนเทสต์ที่ยังไม่ผ่าน**

```python
def test_answer_uses_tool_result_not_brain():
    brain = FakeBrain(ToolCall("solve_equation", {"text": "x**2-5*x+6=0"}), "แยกตัวประกอบ ...")
    a = answer("แก้สมการ", brain)
    assert a.result["solutions"] == ["2", "3"] and a.verified is True
    assert a.text == "แยกตัวประกอบ ..."

def test_unverified_result_gets_notice(monkeypatch):
    monkeypatch.setattr(core, "run_tool", lambda n, a, **k: {"solutions": ["9"], "verified": False})
    a = answer("q", FakeBrain(ToolCall("solve_equation", {}), "ตอบ 9"))
    assert a.verified is False and a.text.startswith(UNVERIFIED_NOTICE)

def test_csv_result_has_no_verified_flag(tmp_path):
    p = tmp_path / "a.csv"; p.write_text("v\n1\n", encoding="utf-8")
    a = answer("สรุป", FakeBrain(ToolCall("summarize_csv", {"path": str(p)}), "ok"))
    assert a.verified is None

def test_tool_error_becomes_plain_text_not_crash():
    a = answer("q", FakeBrain(ToolCall("solve_equation", {"text": "(((("}), "unused"))
    assert "ToolError" not in a.text and a.verified is False
    assert a.result == {}
```

- [ ] **ขั้นที่ 2: รัน ต้อง FAIL**
- [ ] **ขั้นที่ 3: เขียน `answer`**: `call = brain.plan(...)`; `result = run_tool(...)`; ถ้าเกิด `ToolError` คืน `Answer(text=<ข้อความไทย+อังกฤษที่มีข้อความ error>, call, {}, False)` โดยไม่เรียก `explain` ถ้าสำเร็จ `text = brain.explain(...)` และเติม `UNVERIFIED_NOTICE + "\n"` นำหน้าเมื่อ `result.get("verified") is False`
- [ ] **ขั้นที่ 4: รัน ต้อง PASS**
- [ ] **ขั้นที่ 5: commit** — `git commit -m "feat: brain interface and core answer flow"`

---

### Task 5: LocalBrain (Ollama)

**ไฟล์:**
- สร้าง: `src/assistant/brain/local.py`
- เทสต์: `tests/test_local_brain.py`

**อินเทอร์เฟซ:**
- ใช้: `Brain`, `ToolCall`, `ToolSpec`, `BrainError`, `config.DEFAULT_MODEL`, `config.OLLAMA_HOST`
- ให้ผู้อื่นใช้: `LocalBrain(model: str = DEFAULT_MODEL, host: str = OLLAMA_HOST, timeout_s: float = 60.0)` ที่ทำตาม `Brain`

- [ ] **ขั้นที่ 1: เขียนเทสต์ที่ยังไม่ผ่าน** (monkeypatch `requests.post` ใช้ตัวช่วย `fake_response(content: str)` ที่คืนอ็อบเจกต์มี `.json()` → `{"message": {"content": content}}` และ `.raise_for_status()`)

```python
def test_plan_parses_json_tool_call(monkeypatch):
    patch_post(monkeypatch, ['{"tool": "solve_equation", "args": {"text": "x^2=9"}}'])
    call = LocalBrain().plan("แก้ x^2 = 9", list(TOOLS.values()))
    assert call == ToolCall("solve_equation", {"text": "x^2=9"})

def test_plan_retries_once_on_malformed_json(monkeypatch):
    posts = patch_post(monkeypatch, ["not json", '{"tool": "solve_equation", "args": {"text": "x=1"}}'])
    assert LocalBrain().plan("q", list(TOOLS.values())).name == "solve_equation"
    assert len(posts) == 2

def test_plan_gives_up_after_retry(monkeypatch):
    patch_post(monkeypatch, ["bad", "still bad"])
    with pytest.raises(BrainError): LocalBrain().plan("q", list(TOOLS.values()))

def test_plan_rejects_tool_not_in_list(monkeypatch):
    patch_post(monkeypatch, ['{"tool": "delete_everything", "args": {}}', '{"tool": "delete_everything", "args": {}}'])
    with pytest.raises(BrainError): LocalBrain().plan("q", list(TOOLS.values()))

def test_explain_includes_result_and_question_in_prompt(monkeypatch):
    posts = patch_post(monkeypatch, ["คำอธิบาย"])
    out = LocalBrain().explain("แก้ x^2=9", ToolCall("solve_equation", {}), {"solutions": ["-3", "3"]})
    assert out == "คำอธิบาย" and '"-3"' in posts[0]["messages"][-1]["content"]

def test_ollama_unreachable_is_friendly(monkeypatch):
    monkeypatch.setattr(requests, "post", raise_connection_error)
    with pytest.raises(BrainError, match="Ollama"): LocalBrain().plan("q", [])
```

- [ ] **ขั้นที่ 2: รัน ต้อง FAIL**
- [ ] **ขั้นที่ 3: เขียน `LocalBrain`** ส่ง POST ไปที่ `{host}/api/chat` ด้วย `stream: False` `plan` ส่ง system prompt ที่ลิสต์ชื่อ คำอธิบาย และพารามิเตอร์ของแต่ละเครื่องมือ แล้วบังคับให้ตอบเป็น JSON `{"tool": ..., "args": {...}}` ด้วย `format: "json"` ถ้า parse ไม่ได้หรือเครื่องมือไม่รู้จัก ให้ลองใหม่หนึ่งครั้งโดยแนบข้อความ error แล้วถ้ายังไม่ได้ให้ raise `BrainError` ส่วน `explain` ส่งคำถามกับผลลัพธ์ของเครื่องมือเป็น JSON และสั่งว่า: ตอบเป็นภาษาเดียวกับคำถาม อธิบายทีละขั้น **ใช้เฉพาะตัวเลขที่อยู่ในผลลัพธ์ ห้ามคำนวณตัวเลขใหม่** แปลง `requests.ConnectionError`/`Timeout` เป็น `BrainError("ติดต่อ Ollama ไม่ได้ ... / cannot reach Ollama at <host>")`
- [ ] **ขั้นที่ 4: รัน ต้อง PASS**
- [ ] **ขั้นที่ 5: ทดสอบมือ (บนเครื่องโบ๊ท ต้องเปิด Ollama และ pull โมเดลไว้):** `python -c "from assistant.core import answer; from assistant.brain.local import LocalBrain; print(answer('แก้ x² − 5x + 6 = 0', LocalBrain()).text)"` ผลที่ต้องได้: คำอธิบายภาษาไทยที่พูดถึง 2 และ 3
- [ ] **ขั้นที่ 6: commit** — `git commit -m "feat: local ollama brain"`

---

### Task 6: CLI, สคริปต์ benchmark, README

**ไฟล์:**
- สร้าง: `src/assistant/cli.py`, `scripts/benchmark_models.py`, `scripts/benchmark_questions.json`, `scripts/sample.csv`, `README.md`
- เทสต์: `tests/test_cli.py`

**อินเทอร์เฟซ:**
- ใช้: `answer`, `LocalBrain`, `FakeBrain`, `ToolCall`, `BrainError`
- ให้ผู้อื่นใช้:
  - `cli.main(argv: list[str] | None = None, brain: Brain | None = None) -> int` (ฉีด brain เข้ามาได้เพื่อทดสอบ คืน exit code 0 สำเร็จ 1 ผิดพลาด) วิธีใช้: `python -m assistant.cli "คำถาม" [--model ชื่อ] [--file พาธ]` ตัวเลือก `--file` จะต่อท้ายคำถามด้วย `\nไฟล์: พาธ`
  - `scripts/benchmark_models.py MODEL [MODEL ...]` พิมพ์ผลต่อโมเดล: เลือกเครื่องมือถูกกี่ข้อ (x/N), ตรวจคำตอบผ่านกี่ข้อ (x/N), เวลาเฉลี่ย (วินาที)

- [ ] **ขั้นที่ 1: เขียนเทสต์ที่ยังไม่ผ่าน**

```python
def test_cli_prints_answer(capsys):
    brain = FakeBrain(ToolCall("solve_equation", {"text": "x**2=9"}), "คำตอบคือ ±3")
    assert main(["แก้ x^2=9"], brain=brain) == 0
    assert "คำตอบคือ ±3" in capsys.readouterr().out

def test_cli_brain_error_exit_code_and_friendly_message(capsys):
    class Broken:
        def plan(self, q, t): raise BrainError("ติดต่อ Ollama ไม่ได้")
    assert main(["q"], brain=Broken()) == 1
    assert "ติดต่อ Ollama ไม่ได้" in capsys.readouterr().err

def test_cli_file_option_is_added_to_question():
    seen = {}
    class Spy(FakeBrain):
        def plan(self, q, t): seen["q"] = q; return super().plan(q, t)
    main(["สรุป", "--file", "data.csv"], brain=Spy(ToolCall("summarize_csv", {"path": "data.csv"}), "x"))
    assert "data.csv" in seen["q"]
```

- [ ] **ขั้นที่ 2: รัน ต้อง FAIL**
- [ ] **ขั้นที่ 3: เขียน `cli.main`** ด้วย `argparse` สมองเริ่มต้นคือ `LocalBrain(model=args.model or DEFAULT_MODEL)` พิมพ์ `Answer.text` ออก stdout และข้อผิดพลาดออก stderr
- [ ] **ขั้นที่ 4: รัน ต้อง PASS**
- [ ] **ขั้นที่ 5: เขียน `scripts/benchmark_questions.json`**: 10 ข้อ รูปแบบ `{"question": ..., "expected_tool": ...}` ได้แก่ โจทย์พีชคณิต 7 ข้อ (ไทย 3, อังกฤษ 2, แบบมี `²`/`−`/`^` 2), สมการไม่มีคำตอบ 1 ข้อ, และคำถามเกี่ยวกับ CSV 2 ข้อที่ชี้ไปที่ `scripts/sample.csv` (สร้างไฟล์ตัวอย่าง 5 แถว มีหัวคอลัมน์ภาษาไทย 1 คอลัมน์) เขียน `scripts/benchmark_models.py` ให้วนทุกโมเดล × ทุกคำถามด้วย `LocalBrain` + `answer` นับจำนวนที่เลือกเครื่องมือถูก, จำนวนที่ `verified` และจับเวลา
- [ ] **ขั้นที่ 6: เขียน `README.md`** (ไทย+อังกฤษ): วิธีติดตั้ง (`pip install -e .[dev]`), ติดตั้ง Ollama และ `ollama pull <โมเดล>`, ตัวอย่างการรัน, วิธีรันเทสต์, วิธีรัน benchmark และการตั้ง `DEFAULT_MODEL` ใน `config.py` ตามผลที่ได้
- [ ] **ขั้นที่ 7: รันเทสต์ทั้งหมด** — `pytest -v` ต้อง PASS ทุกข้อ
- [ ] **ขั้นที่ 8: commit** — `git commit -m "feat: cli, benchmark script and readme"`

---

## บันทึกการตรวจทานตัวเอง

- ความครอบคลุมตามเอกสารออกแบบ: เป้าหมายข้อ 1-3 และข้อ 5 (API อยู่ v1) กับสิ่งที่ถือว่าล้มเหลวเรื่องคำตอบที่ไม่ผ่านการตรวจ ครอบคลุมในงาน 1-5 เป้าหมายข้อ 4 (ออฟไลน์) ครอบคลุมด้วย LocalBrain เป็นค่าเริ่มต้น เป้าหมายข้อ 6 ครอบคลุมด้วยกฎแยกโฟลเดอร์ในข้อจำกัดรวม ส่วนหัวข้อ "ทดสอบโมเดล" ที่ยังเปิดอยู่คืองานที่ 6 ส่วน `ui/`, `api/`, `character/`, CloudBrain เป็น v1-v3 จึงไม่อยู่ในแผนนี้โดยตั้งใจ
- ตรวจความสอดคล้องของชนิดข้อมูลข้ามงานแล้ว: `ToolSpec`, `ToolCall`, `Answer`, ลายเซ็นของ `run_tool` และ `verified: bool | None` ใช้ตรงกันในงาน 3-6
- ความยาวแผนสมเหตุสมผล: ใส่เฉพาะเทสต์และลายเซ็น ส่วนเนื้อโค้ดปล่อยให้ผู้สร้างเขียนเอง
