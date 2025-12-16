# Session Summary: MinerU Table Extraction Pipeline
**Date:** 2025-12-15

---

## Objective
Extract structured data from Chilean pesticide label PDFs (with complex tables) for RAG database ingestion.

---

## What We Built

### 1. MinerU Processing (GPU)
- **Tool:** Gradio interface at http://localhost:7860
- **Status:** ✅ Running (PID 2238152)
- **Hardware:** NVIDIA RTX 4090 (GPU 0)
- **Backend:** pipeline (OCR-based)
- **Language:** latin (Spanish)

### 2. Table Flattening Script
- **File:** `flatten_and_convert.py`
- **Purpose:** Convert HTML tables with merged cells → RAG JSON
- **Status:** ✅ Created and tested
- **Algorithm:** Occupancy matrix to expand rowspan/colspan

### 3. Complete Pipeline
```
PDF → [MinerU GPU] → Markdown (HTML tables)
    → [flatten_and_convert.py CPU] → RAG JSON
```

---

## Files Created

```
flatten_and_convert.py                           (Main conversion script)
docs/assets/afalon_50_sc_adama.json             (Target schema example)
output_documentation/
  ├── AFALON_50_SC_Processing_Results.md        (Full documentation)
  ├── AFALON_50_SC_Table.html                   (HTML table viewer)
  └── SESSION_SUMMARY.md                         (This file)
```

---

## Test Case: AFALON 50 SC

**Input:** `docs/lentejas/afalon_50_sc_21-07-2021.pdf`

**Processing:**
1. MinerU extracted 2 tables
2. Table 1: 21 rows → 20 crop instructions
3. Flattened merged cells
4. Generated RAG JSON (15 KB)

**Output:** `docs/lentejas/output/afalon_50_sc_21-07-2021_RAG.json`

---

## Critical Problems Discovered

### ❌ MinerU Table Structure Issues

**The HTML table from MinerU is structurally broken:**

1. **Inconsistent colspan:** MALEZAS column uses 4, 3, 2, or 1 columns randomly
2. **Complex rowspan:** Cells span multiple rows unpredictably
3. **Column misalignment:** Data bleeds into wrong columns
4. **Missing data:** Observations truncated or empty
5. **OCR errors:** "Aveja"→"Arveja", "omatillo"→"tomatillo"

**Example issues in output:**
- Row 2 (Apio): Dose column shows weed names
- Row 3 (Aveja): Weed data in dose column
- Row 12 (Lupino): Dose shows "Jel" (garbage)
- Many observation fields empty

**Root cause:** Original PDF table is extremely complex with multi-level merged cells. MinerU's pipeline backend cannot accurately extract this structure.

---

## Solutions Attempted

### ✅ What Works
- Basic merged cell expansion (rowspan=9 for rows 12-20)
- European number format parsing (1,2-1,5 → 1.2-1.5)
- Weed list splitting (comma-separated → objects)
- JSON schema generation

### ❌ What Failed
- Complex table structure with irregular colspan/rowspan patterns
- Column alignment with duplicate headers (4x "MALEZAS")
- Data in wrong columns due to MinerU extraction errors

---

## Recommendations

### Option 1: Try VLM Backend (Better Accuracy)
```bash
# Stop current Gradio
# Restart with VLM backend:
mineru-gradio --enable-vllm-engine
# or
mineru-gradio  # then select "vlm-transformers" in UI
```

**VLM advantages:**
- Vision-based (understands visual layout)
- Better with complex merged cells
- More accurate than OCR pipeline

**Tradeoff:** Slower processing

### Option 2: Manual Table Reconstruction
- Use VLM to extract raw text
- Manually structure the table
- Then apply flattening script

### Option 3: Hybrid Approach
- Use MinerU for simple tables
- Manual correction for complex ones
- Build validation layer

---

## GitHub Commits

**Commit 1:** `ac652bd0`
- Added `flatten_and_convert.py`
- Added `afalon_50_sc_adama.json` schema

**Commit 2:** `dd4268d7`
- Added lentejas PDF collection (22 files)
- Added test outputs

**Repository:** https://github.com/lfleon9b/MinerU_lleon

---

## Current Status

### ✅ Working
- Gradio server running
- Flattening script functional
- Pipeline documented
- Code in GitHub

### ⚠️ Needs Attention
- Table extraction accuracy (MinerU limitation)
- Column alignment logic
- Data validation layer
- OCR error correction

### 📋 Next Steps
1. Test VLM backend for better accuracy
2. Add validation to detect misaligned columns
3. Build OCR correction layer
4. Create batch processing script
5. Set up RAG database ingestion

---

## Key Learning

**Complex tables with irregular merged cell patterns require:**
- Vision-based models (VLM) not just OCR
- Post-processing validation
- Manual review for critical data
- Possibly manual table reconstruction for very complex cases

**The "pipeline" backend is good for:**
- Simple tables
- Regular grid structures
- Standard rowspan/colspan

**Not suitable for:**
- Irregular multi-level merges
- Complex nested structures
- Variable column layouts

---

## Quick Reference Commands

```bash
# Start Gradio
mineru-gradio

# Process PDF
mineru -p input.pdf -o output --lang latin --backend pipeline

# Flatten tables
python3 flatten_and_convert.py \
  output/file/auto/file.md \
  -o output.json \
  --product "NAME" \
  --debug

# Check GPU
nvidia-smi

# View output
firefox output_documentation/AFALON_50_SC_Table.html
```

---

**End of Summary**
