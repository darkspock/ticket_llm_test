# AI Engineer Assignment - Requirements Analysis

## Executive Summary

This is a take-home assignment for an AI Engineer position that evaluates the candidate's ability to work with LLM APIs, process data, and write clean Python code. The task involves building an automated evaluation system for customer support ticket replies.

---

## Functional Requirements

### FR-01: CSV Input Processing
- **Description**: Read a CSV file named `tickets.csv`
- **Input Columns**:
  - `ticket`: Customer support message (string)
  - `reply`: AI-generated response (string)
- **Considerations**:
  - Handle missing/empty data
  - Handle malformed CSV
  - Handle encoding issues (UTF-8)

### FR-02: LLM Integration
- **Description**: Use LLM to evaluate each ticket/reply pair
- **Evaluation Dimensions**:
  | Dimension | Criteria |
  |-----------|----------|
  | Content | Relevance, correctness, completeness |
  | Format | Clarity, structure, grammar/spelling |
- **Scoring**: Scale 1-5 for both dimensions
- **Output per evaluation**:
  - `content_score` (integer 1-5)
  - `content_explanation` (string, 1-2 sentences)
  - `format_score` (integer 1-5)
  - `format_explanation` (string, 1-2 sentences)

### FR-03: CSV Output Generation
- **Description**: Generate `tickets_evaluated.csv` with original data plus evaluation results
- **Output Columns**:
  1. `ticket` (original)
  2. `reply` (original)
  3. `content_score` (new)
  4. `content_explanation` (new)
  5. `format_score` (new)
  6. `format_explanation` (new)

---

## Non-Functional Requirements

### NFR-01: Error Handling
- Handle missing data in input CSV
- Handle API failures (rate limits, timeouts, network errors)
- Handle invalid LLM responses (parsing failures)
- Graceful degradation or retry logic

### NFR-02: Security
- No API keys committed to repository
- Use environment variables or `.env` file
- `.env` excluded from version control

### NFR-03: Code Quality
- PEP-8 compliance
- Clean, maintainable code
- Well-documented
- Proper structure/organization

### NFR-04: Documentation
- README with:
  - Setup instructions
  - How to run the code
  - Dependencies list
  - Environment variables needed

---

## Deliverables Checklist

| Deliverable | Required | Description |
|------------|----------|-------------|
| Python Script/Notebook | Yes | `.py` or `.ipynb` with solution |
| tickets_evaluated.csv | Yes | Output file with evaluations |
| README | Yes | Setup and run instructions |
| requirements.txt/pyproject.toml | Yes | Dependencies |
| Tests | Optional | pytest/unittest for core functions |
| .env.example | Implied | Template for API keys |

---

## Technical Analysis

### Key Technical Decisions

#### 1. LLM Response Parsing Strategy
**Options**:
- **A) Structured Output (JSON mode)** - Recommended
  - Use JSON mode or function calling
  - Guarantees parseable response
  - Less error-prone
- **B) Free-text parsing with regex**
  - More fragile
  - Requires careful prompt engineering

#### 2. Processing Strategy
**Options**:
- **A) Sequential processing** - Simpler, slower
- **B) Batch/async processing** - Faster, more complex
  - Consider rate limits
  - asyncio + aiohttp for concurrent calls

#### 3. Retry Logic
- Implement exponential backoff for API failures
- Consider using `tenacity` library

### Prompt Engineering Considerations

The evaluation prompt should:
1. Clearly define the scoring rubric (1-5 scale)
2. Provide examples for each score level
3. Request structured output (JSON)
4. Be specific about explanation length (1-2 sentences)

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits | High | Implement rate limiting, batch processing |
| Inconsistent LLM output | Medium | Use JSON mode, structured outputs |
| High API costs | Medium | Use faster models for testing, cache results |
| Invalid score values | Low | Validate output, clamp to 1-5 range |
| CSV encoding issues | Low | Specify UTF-8 encoding explicitly |

---

## Evaluation Criteria Mapping

| Criterion | Weight | How to Excel |
|-----------|--------|--------------|
| Code Quality | High | PEP-8, type hints, clean structure, error handling |
| Prompt Engineering | High | Clear rubric, examples, structured output |
| Correctness of Output | High | Valid scores, proper CSV format, complete data |
| Documentation & Tests | Medium | Clear README, good test coverage |
