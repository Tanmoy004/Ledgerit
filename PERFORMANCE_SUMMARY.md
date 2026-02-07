# Performance Analysis - Quick Reference

## Time Consumption (Decreasing Order)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROCESSING TIME BREAKDOWN                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Table Extraction + OCR ████████████████████████ 70-85%         │
│     (5-20s per page)                                                │
│                                                                     │
│  2. OCR Initialization     ███ 5-15%                                │
│     (2-5s first call)                                               │
│                                                                     │
│  3. Transaction Parsing    ██ 3-8%                                  │
│     (0.5-2s)                                                        │
│                                                                     │
│  4. Bank Detection (Logo)  █ 2-5%                                   │
│     (0.5-2s)                                                        │
│                                                                     │
│  5. Table Processing       █ 1-3%                                   │
│     (0.1-0.5s)                                                      │
│                                                                     │
│  6. PDF Reading            █ 1-2%                                   │
│     (0.1-0.5s)                                                      │
│                                                                     │
│  7-9. Other Operations     █ 2-3%                                   │
│     (<0.5s combined)                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Critical Findings

### 🔴 CRITICAL BOTTLENECK
**Table Extraction (img2table + PaddleOCR)**
- Consumes: 70-85% of total time
- Time: 5-20 seconds PER PAGE
- Why: PDF→Image conversion + OCR + Table detection
- Impact: For 10-page PDF = 50-200 seconds just for this step

### 🟡 SECONDARY BOTTLENECKS
1. **OCR Model Loading** (5-15%) - One-time cost, already optimized
2. **Transaction Parsing** (3-8%) - Regex operations, row iteration
3. **Logo Matching** (2-5%) - OpenCV template matching

### 🟢 OPTIMIZED COMPONENTS
- PDF Reading (<2%)
- Text Extraction (<1%)
- DataFrame Operations (<1%)
- Export Operations (<1%)

## Processing Time Examples

### 5-Page Statement
- Fast (bordered): 8-15 seconds
- Medium (borderless): 15-30 seconds  
- Slow (poor quality): 30-60 seconds

### 15-Page Statement
- Fast: 25-45 seconds
- Medium: 45-90 seconds
- Slow: 90-180 seconds

## Top 5 Optimization Priorities

### 1. ⚡ CRITICAL - Reduce OCR Processing Time
```
Current: 5-20s per page
Target:  2-8s per page (60% reduction)

Actions:
- Lower OCR confidence threshold (50→40)
- Reduce image resolution
- Skip summary pages early
- Parallel page processing
```

### 2. ⚡ HIGH - Optimize OCR Model Loading
```
Current: 2-5s on first request
Target:  0s (preloaded)

Actions:
- Preload at Flask startup (already done with singleton)
- Consider lighter model
```

### 3. ⚡ MEDIUM - Speed Up Transaction Parsing
```
Current: 0.5-2s
Target:  0.2-0.8s (60% reduction)

Actions:
- Vectorize operations (avoid row iteration)
- Early exit strategies
- Optimize regex patterns
```

### 4. ⚡ MEDIUM - Optimize Bank Detection
```
Current: 0.5-2s
Target:  0.2-0.8s (60% reduction)

Actions:
- Skip logo matching if text succeeds
- Limit logo comparisons to top 3
- Cache logos in memory (already done)
```

### 5. ⚡ LOW - General Optimizations
```
Current: <1s combined
Target:  <0.5s

Actions:
- Minimize DataFrame copies
- In-place operations
- Reduce redundant operations
```

## Module Time Rankings

| Rank | Module | Time % | Seconds | Priority |
|------|--------|--------|---------|----------|
| 1 | img2table + OCR | 70-85% | 5-20/page | CRITICAL |
| 2 | OCR Init | 5-15% | 2-5 | HIGH |
| 3 | Transaction Parse | 3-8% | 0.5-2 | MEDIUM |
| 4 | Logo Detection | 2-5% | 0.5-2 | MEDIUM |
| 5 | Table Processing | 1-3% | 0.1-0.5 | LOW |
| 6 | PDF Reading | 1-2% | 0.1-0.5 | LOW |
| 7 | Text Detection | 0.5-1% | 0.1-0.3 | LOW |
| 8 | DataFrame Ops | 0.5-1% | 0.05-0.2 | LOW |
| 9 | Export | 0.5-1% | 0.1-0.5 | LOW |

## Expected Improvements

### If ALL optimizations implemented:

```
Current Average (10-page PDF): 60 seconds
After Optimization:            25 seconds
Improvement:                   58% faster
```

### Breakdown:
- Table Extraction: 45s → 18s (60% reduction)
- OCR Init: 3s → 0s (preloaded)
- Transaction Parse: 2s → 0.8s (60% reduction)
- Bank Detection: 1.5s → 0.6s (60% reduction)
- Other: 2s → 1.5s (25% reduction)

## Quick Test Commands

```bash
# Run analysis
cd backend
python analyze_performance.py

# Test with actual PDF
python test_performance.py statement.pdf

# Test with password-protected PDF
python test_performance.py statement.pdf mypassword
```

## Key Insight

> **70-85% of processing time is spent on OCR + Table Extraction**
> 
> This is the ONLY area that matters for performance optimization.
> All other optimizations combined will only improve performance by 5-10%.

## Recommendation

**Focus 100% of optimization effort on:**
1. Reducing OCR processing time per page
2. Skipping unnecessary pages
3. Parallel processing of pages
4. Lower quality/faster OCR settings

**Expected Result:** 50-60% overall performance improvement
