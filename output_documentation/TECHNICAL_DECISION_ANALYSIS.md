# Technical Decision Analysis: Table Extraction Strategy
**Date:** 2025-12-15
**Project:** Chilean Pesticide Label Data Extraction for RAG Database
**Decision:** MinerU Modification vs. Semi-Automatic Claude Vision Approach

---

## Executive Summary

**Recommendation: Use semi-automatic Claude Vision approach instead of modifying MinerU.**

**Key Reasons:**
- Dataset size: ~20-50 documents (not thousands)
- Accuracy requirement: Critical (safety/regulatory data)
- Complex table structures: Multi-level merged cells
- Time to production: Days vs. Months
- Cost-effectiveness: $10 vs. months of engineering

---

## Problem Statement

Chilean pesticide labels contain highly complex tables with:
- Irregular merged cell patterns (rowspan/colspan)
- Multi-level nesting
- Variable column structures
- Critical data requiring 100% accuracy (crop doses, safety info)

**Example complexity:** AFALON 50 SC table has:
- Header with 4-column MALEZAS span
- Data rows with 3-col, 2-col, 1-col variations
- 9-row merged cell for weed lists
- Inconsistent column alignment

**MinerU's current output:** Structurally broken - data in wrong columns, missing information, unusable for production.

---

## Option 1: Modify MinerU

### Complexity Assessment: ⚠️ EXTREMELY HIGH

#### Technical Requirements

**1. Deep Learning Model Modifications**
```
Current pipeline:
- Layout Detection (pre-trained CNN)
- Table Structure Recognition (SLANet+/UNet)
- OCR (PaddleOCR)
- Post-processing (rule-based)

Required changes:
- Retrain table structure models on complex merged-cell datasets
- Improve grid regularization algorithms
- Better column alignment heuristics
- Handle irregular patterns
```

**2. Expertise Required**
- Computer vision / deep learning expertise
- PyTorch model training
- Dataset creation and labeling (100+ complex tables)
- Model architecture understanding
- Debugging inference pipelines

**3. Development Timeline**

| Phase | Estimated Time |
|-------|---------------|
| Dataset creation (label 100-200 complex tables) | 2-3 weeks |
| Model retraining experiments | 4-6 weeks |
| Post-processing improvements | 2-3 weeks |
| Testing and debugging | 2-4 weeks |
| **Total** | **3-6 months** |

**4. Success Probability**

- ⚠️ **Uncertain** - Complex irregular tables are notoriously hard
- Even specialized commercial tools struggle with these
- May require iterative retraining (add more months)
- Still may need manual review layer

**5. Maintenance Burden**

- Model updates when MinerU releases new versions
- Continued training as new edge cases discovered
- Technical debt in custom modifications

---

### Cost Analysis: Option 1

**Engineering Time:**
- 3-6 months × engineering salary
- Plus infrastructure (GPU training, storage)

**Opportunity Cost:**
- Delayed RAG deployment
- Other features not built

**Risk:**
- May still not achieve required accuracy
- Sunk cost if approach fails

**Estimated Total Cost: $30,000 - $60,000** (engineering time + infrastructure)

---

## Option 2: Semi-Automatic Claude Vision

### Complexity Assessment: ✅ LOW

#### Technical Requirements

**1. Prompt Engineering**
```
Components needed:
- Clear extraction instructions
- JSON schema specification
- Edge case handling rules
- Validation criteria

Time required: 1-2 hours to perfect
```

**2. Expertise Required**
- Prompt writing (straightforward)
- JSON schema design (already done)
- Basic API integration (optional)

**3. Development Timeline**

| Phase | Estimated Time |
|-------|---------------|
| Prompt development & testing | 2-4 hours |
| Process 2-3 test documents | 1-2 hours |
| Build simple workflow/validation script | 4-6 hours |
| **Total setup** | **1-2 days** |
| **Per document processing** | **5-10 minutes + review** |
| **50 documents total** | **1-2 days of processing** |

**4. Success Probability**

- ✅ **Very High** - Claude 3.5 Sonnet excels at vision tasks
- Can handle complex merged cells
- Reasoning about ambiguities
- Consistent with good prompts

**5. Maintenance Burden**

- Minimal - just prompt refinement
- Claude updates improve quality automatically
- No model training or infrastructure

---

### Cost Analysis: Option 2

**Development:**
- 2 days × engineering time = ~$1,000-2,000

**Processing:**
- Claude API: $0.20-0.50 per document (estimated)
- 50 documents × $0.50 = **$25**
- Alternative: Use chat interface (included in subscription)

**Human Review Time:**
- 5 minutes per document
- 50 documents × 5 min = ~4 hours = $200-400

**Estimated Total Cost: $1,200 - $2,500**

**Savings vs. Option 1: $27,500 - $57,500**

---

## Comparison Matrix

| Factor | Modify MinerU | Claude Vision | Winner |
|--------|--------------|---------------|---------|
| **Development Time** | 3-6 months | 1-2 days | ✅ Claude |
| **Cost** | $30K-60K | $1.2K-2.5K | ✅ Claude |
| **Accuracy** | Uncertain | Very High | ✅ Claude |
| **Maintenance** | High (ongoing) | Low (minimal) | ✅ Claude |
| **Success Risk** | Medium-High | Low | ✅ Claude |
| **Time to Production** | 3-6 months | 1 week | ✅ Claude |
| **Scalability** | Better (once working) | Good enough | 🤝 Tie |
| **Quality Control** | Still needs review | Built-in review | ✅ Claude |

---

## Why Claude Vision is Better for This Use Case

### 1. Dataset Size Reality

**Your situation:**
- ~20-50 pesticide labels total
- Not 10,000+ documents
- Small corpus doesn't justify months of ML engineering

**Rule of thumb:**
- If documents < 1,000 → Semi-automatic
- If documents > 10,000 → Invest in automation

**Your case:** Semi-automatic is the right choice

---

### 2. Accuracy is Critical

**Safety/Regulatory Data:**
- Wrong dose → crop damage or safety issues
- Wrong weed → ineffective application
- Missing restrictions → legal problems

**Implication:**
- **Manual review required regardless of tool**
- 100% accuracy needed
- Cannot trust fully-automated extraction

**With Claude Vision:**
- Human validates every output
- Catches errors immediately
- High-stakes data gets appropriate scrutiny

---

### 3. Complex Edge Cases

**Your tables have:**
- Irregular patterns (not standardized)
- Different layouts per product
- Nested merges
- Ambiguous text

**ML Models struggle because:**
- Each document is slightly different
- Not enough similar examples to learn from
- Hard to generalize irregular patterns

**Claude Vision excels because:**
- Reasons about each case individually
- Can handle "one-off" structures
- Doesn't need training examples
- Can ask clarifying questions (in chat mode)

---

### 4. Time to Value

**Business perspective:**

```
Option 1 (MinerU):
Month 0-3: Development
Month 3-6: Testing/fixing
Month 6+: Maybe production ready
Total: 6+ months to first value

Option 2 (Claude):
Week 1: Setup & testing
Week 2: Process 50 documents
Total: 2 weeks to production database
```

**6 months earlier to market = significant business value**

---

## Recommended Approach: Hybrid Workflow

### Phase 1: Initial Extraction (Claude Vision)

**For each PDF:**

```
1. Upload to Claude (claude.ai or API)
2. Use standardized prompt
3. Claude extracts → JSON output
4. Human reviews in 5-10 minutes
5. Make corrections if needed
6. Validate against schema
7. Save to RAG database
```

**Estimated time:** 10-15 min per document (including review)

---

### Phase 2: Validation Layer

**Build simple Python validators:**

```python
# Check completeness
def validate_extraction(json_data):
    - All required fields present
    - Dose values are numbers
    - Weed lists not empty
    - Cross-reference crop names
    - Flag suspicious values

# Human reviews only flagged items
```

---

### Phase 3: Quality Assurance

**Sampling strategy:**
- 100% review for first 10 documents
- Random 20% sample for next 20 documents
- 100% review for any flagged items

**Accuracy tracking:**
- Log corrections needed
- Identify common error patterns
- Refine prompt based on learnings

---

### Phase 4: RAG Ingestion

**Once validated:**
- Batch upload to vector database
- Each crop instruction = 1 document chunk
- Include metadata for filtering
- Build query interface

---

## When to Use Each Tool

### Use Claude Vision For:
✅ Complex tables (merged cells, irregular structure)
✅ Small datasets (<1,000 documents)
✅ High accuracy requirements
✅ Regulatory/safety-critical data
✅ One-off or variable layouts
✅ Quick time-to-production needed

### Use MinerU For:
✅ Simple tables (regular grid)
✅ Large datasets (>10,000 documents)
✅ Standardized formats
✅ When accuracy can be 85-90%
✅ Batch processing with review layer
✅ When you have CV expertise in-house

### Use Fully Manual For:
✅ <10 documents
✅ Extremely complex layouts
✅ When automation cost > manual cost

---

## Implementation Plan

### Week 1: Setup & Testing

**Day 1-2: Prompt Development**
- Draft extraction prompt
- Define JSON schema (already done: `afalon_50_sc_adama.json`)
- Test on 2-3 sample documents
- Refine based on results

**Day 3-4: Validation Tools**
- Build JSON validator
- Create completeness checker
- Set up review interface (simple)

**Day 5: Process Test Batch**
- Extract 5 documents end-to-end
- Measure accuracy
- Time per document
- Identify issues

---

### Week 2: Production Processing

**Day 1-5: Bulk Extraction**
- Process remaining 45 documents
- ~10 documents per day
- Track issues and corrections
- Refine prompt as needed

**Review cadence:**
- Morning: Process 5 documents
- Afternoon: Review + corrections

---

### Week 3: Quality Assurance & Ingestion

**Day 1-2: Final QA**
- Random sample validation (20%)
- Check inter-document consistency
- Flag anomalies

**Day 3-4: RAG Ingestion**
- Format for vector database
- Upload to RAG system
- Test queries

**Day 5: Documentation**
- Document any edge cases
- Update extraction guidelines
- Finalize workflow

---

## Sample Claude Vision Prompt

```markdown
You are extracting data from a Chilean pesticide label for a RAG database.
This data is CRITICAL for safety and regulatory compliance.

INPUT: PDF image of pesticide label
OUTPUT: JSON matching exact schema below

CRITICAL RULES:
1. Extract EVERY row from the usage table completely
2. If weeds are in a merged cell spanning multiple crops:
   → REPEAT the full weed list for EVERY crop in that span
3. Never leave fields empty:
   → Use "Not specified" if truly missing
   → Extract partial data rather than skip
4. Verify column alignment before outputting:
   → Cultivo | Malezas | Dosis | Observaciones
   → If columns seem wrong, re-examine the table
5. Include COMPLETE observation text (don't truncate)
6. Parse doses carefully:
   → "1,2-1,5 L/ha" → {min: 1.2, max: 1.5, unit: "L/ha"}

WEED HANDLING (MOST IMPORTANT):
- If a weed cell spans rows 5-10:
  → Rows 5, 6, 7, 8, 9, 10 ALL get the SAME weed list
- Split comma-separated weeds into individual objects
- Keep original spelling (even if OCR errors present)

VALIDATION BEFORE OUTPUT:
□ Every crop row has weeds listed
□ Every dose is a number (not weed names)
□ Every observation field filled or "Not specified"
□ Row count matches visual table
□ All crops from table included

OUTPUT FORMAT:
{
  "identificacion_producto": {
    "nombre_comercial": "...",
    "ingredientes_activos": [...]
  },
  "instrucciones_uso_desagregadas": [
    {
      "id_fila": 1,
      "cultivo_autorizado": "Ajo",
      "malezas_objetivo": [
        {"nombre_comun": "Yuyo"},
        {"nombre_comun": "Bledo"}
      ],
      "dosis": {
        "valor_min": 1.2,
        "valor_max": 1.5,
        "unidad": "L/ha"
      },
      "observaciones_especificas": "Complete text here"
    }
  ]
}

If anything is ambiguous, include a "notes" field explaining the uncertainty.
```

---

## Risk Mitigation

### Potential Issues & Solutions

**Issue 1: Claude misreads complex merge**
- **Mitigation:** Human review catches it immediately
- **Fix:** Correct in JSON, note edge case
- **Impact:** Minimal (5 min correction)

**Issue 2: Inconsistent extraction between docs**
- **Mitigation:** Clear prompt + examples
- **Fix:** Sample validation catches inconsistencies
- **Impact:** Low (refine prompt)

**Issue 3: API cost higher than expected**
- **Mitigation:** Use chat interface (included)
- **Fallback:** Claude Pro subscription = $20/month unlimited
- **Impact:** Negligible vs. engineering cost

**Issue 4: Takes longer than estimated**
- **Mitigation:** 15 min/doc buffer in estimates
- **Worst case:** 2 weeks → 3 weeks (still << 6 months)
- **Impact:** Minor

---

## Success Metrics

### After Processing 50 Documents:

**Quality:**
- Target: <5% correction rate after initial extraction
- Target: 100% completeness (no missing fields)
- Target: 0 critical errors (wrong doses, missing weeds)

**Efficiency:**
- Target: <10 minutes per document (including review)
- Target: <2 weeks total processing time
- Target: <$50 API costs (if using API vs. chat)

**Business Value:**
- RAG database operational in 3 weeks vs. 6+ months
- High-confidence data for production use
- Extensible to new documents

---

## Conclusion

**Final Recommendation: Implement semi-automatic Claude Vision approach**

**Rationale:**
1. ✅ **Right tool for dataset size** - 50 docs doesn't justify ML engineering
2. ✅ **Matches accuracy requirements** - Manual review built-in
3. ✅ **Fast time to production** - 3 weeks vs. 6+ months
4. ✅ **Cost-effective** - $2K vs. $50K
5. ✅ **Lower risk** - Proven technology, clear fallbacks
6. ✅ **Better engineering** - Optimizes for actual constraints

**This is the pragmatic engineering decision.**

**Do NOT attempt to modify MinerU** for this use case. It's over-engineering for the problem at hand.

---

## Next Steps

### Immediate Actions:

1. **Finalize extraction prompt** (2 hours)
   - Test on AFALON 50 SC document
   - Validate against known-good manual extraction
   - Refine edge case handling

2. **Set up simple workflow** (4 hours)
   - Python script to validate JSON schema
   - Checklist for human review
   - Storage structure for outputs

3. **Process test batch** (1 day)
   - Extract 5 diverse documents
   - Measure time and accuracy
   - Adjust workflow as needed

4. **Scale to production** (2 weeks)
   - Process all 50 documents
   - Build RAG database
   - Deploy query interface

**Timeline to production RAG: 3 weeks**

---

## Appendix: Decision Framework

### When evaluating extraction approaches, consider:

**Dataset Size Factor:**
- <100 docs → Semi-automatic
- 100-10,000 docs → Hybrid (tool + review)
- >10,000 docs → Invest in automation

**Accuracy Requirement:**
- Critical (medical, legal, safety) → Human-in-loop mandatory
- High (business) → Automated with sample review
- Moderate (analytics) → Automated with validation

**Document Complexity:**
- Simple/standard → Automated tools work well
- Moderate → Tools + validation layer
- Complex/irregular → Semi-automatic or manual

**Time Constraint:**
- Urgent (weeks) → Semi-automatic
- Normal (months) → Automated if justifiable
- Flexible (6+ months) → Can invest in custom ML

**For this project:**
- Dataset: Small ✓
- Accuracy: Critical ✓
- Complexity: Very High ✓
- Timeline: Urgent ✓

**All factors point to: Semi-automatic Claude Vision**

---

**Document prepared by:** Claude Code (Sonnet 4.5)
**Date:** 2025-12-15
**Status:** Final Recommendation
**Confidence Level:** High
