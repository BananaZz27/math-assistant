# ผู้ช่วยคณิตศาสตร์และวิเคราะห์ข้อมูล (v0) / Math & Data Assistant (v0)

ผู้ช่วยแบบบรรทัดคำสั่ง: รับโจทย์คณิตศาสตร์หรือไฟล์ CSV แล้ว **คำนวณด้วยโค้ดจริง** (SymPy, pandas) ตรวจคำตอบ
จากนั้นให้โมเดลในเครื่อง (Ollama) เลือกเครื่องมือและอธิบายผลทีละขั้น
A command-line assistant: real code does the math, a local LLM only plans and explains.

กฎสำคัญ / Key rule: โมเดลไม่เคยสร้างตัวเลขเอง ตัวเลขมาจากเครื่องมือเท่านั้น
(the model never makes up numbers; they come from the tools).

## ติดตั้ง / Install

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

ติดตั้ง [Ollama](https://ollama.com) แล้วดึงโมเดล (pull) มาเก็บในเครื่อง / install Ollama and pull a model:

```bash
ollama pull qwen2.5:7b
```

`qwen2.5:7b` เป็นแค่ค่าเริ่มต้นชั่วคราว ดูหัวข้อ benchmark ด้านล่าง
(it is only a placeholder default; see the benchmark section).

## ใช้งาน / Usage

```bash
python -m assistant.cli "แก้สมการ x² − 5x + 6 = 0"
python -m assistant.cli "สรุปข้อมูลให้หน่อย" --file scripts/sample.csv
python -m assistant.cli "Solve x^2 = 9" --model qwen2.5:7b
```

ถ้าเปิด Ollama ไม่ได้ จะขึ้นข้อความภาษาไทย/อังกฤษบอกให้เปิดโปรแกรมก่อน และโปรแกรมจบด้วย exit code 1
(exit code 1 also means the answer could not be verified).

## ไฟล์ CSV: ข้อจำกัดด้านความปลอดภัย / CSV safety rules

เครื่องมืออ่านได้เฉพาะไฟล์ในเครื่อง **ภายในโฟลเดอร์ที่รันโปรแกรม** (หรือโฟลเดอร์ที่กำหนดด้วยตัวแปร `ASSISTANT_DATA_DIR`)
และไม่รับ URL เพราะชื่อไฟล์อาจมาจากโมเดล รองรับ UTF-8 และ cp874 (CSV จาก Excel บน Windows ภาษาไทย)
(only local files inside the working folder or `ASSISTANT_DATA_DIR`; no URLs; UTF-8 and cp874 supported).

## ทดสอบ / Tests

```bash
pytest
```

เทสต์ทั้งหมดไม่ต้องใช้ Ollama / the test suite does not need Ollama.

## เลือกโมเดลบนเครื่องของคุณ (benchmark)

รันที่โฟลเดอร์หลักของโปรเจกต์ / run from the repo root:

```bash
python scripts/benchmark_models.py qwen2.5:7b llama3.1:8b
```

จะแสดงต่อโมเดล: เลือกเครื่องมือถูกกี่ข้อ, ตรวจคำตอบผ่านกี่ข้อ, **ได้คำตอบตรงกับเฉลยกี่ข้อ** (สำคัญที่สุด เพราะจับกรณีที่โมเดลคัดลอกสมการผิด), เวลาเฉลี่ยต่อข้อ
เลือกตัวที่ดีที่สุดแล้วแก้ `DEFAULT_MODEL` ใน `src/assistant/config.py`
(pick the best model and set `DEFAULT_MODEL` in `src/assistant/config.py`).

## โครงสร้าง / Layout

- `src/assistant/tools/` คณิตศาสตร์และข้อมูล (ไม่มี LLM) / math and data, no LLM
- `src/assistant/brain/` อะแดปเตอร์ LLM (ไม่มีคณิตศาสตร์) / LLM adapters, no math
- `src/assistant/core.py` ลำดับการทำงานหลัก / main flow
- `scripts/` benchmark และไฟล์ตัวอย่าง / benchmark and sample data

ขอบเขตของ v0: แก้เฉพาะคำตอบที่เป็นจำนวนจริง และทีละตัวแปร (real solutions, one variable).
หน้า Console, API และตัวละครอยู่ในเวอร์ชันถัดไป / UI, API and the character come in later versions.
