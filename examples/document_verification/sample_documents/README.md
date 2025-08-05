# Sample Documents for Testing

This directory contains sample documents for testing the document verification workflow. These are mock documents created for demonstration purposes only.

## Available Documents

### Identity Documents
- **sample_drivers_license.txt** - California driver's license
- **sample_passport.txt** - US passport

### Financial Documents  
- **sample_bank_statement.txt** - Monthly bank statement
- **sample_w2.txt** - W-2 tax form

### Proof of Address
- **sample_utility_bill.txt** - PG&E utility bill

## Document Types Supported

The system can classify and process various document types:

1. **Identity Documents**
   - Driver's licenses
   - Passports
   - National ID cards
   - Visas

2. **Financial Documents**
   - Bank statements
   - Tax documents (W-2, 1099, etc.)
   - Pay stubs
   - Financial reports

3. **Proof of Address**
   - Utility bills
   - Bank statements
   - Government correspondence
   - Lease agreements

## Testing Different Scenarios

### Valid Documents
Use the provided sample documents to test successful verification workflows.

### Error Scenarios
Create test files with issues to test error handling:
- Empty files (processing failures)
- Corrupted content (parsing errors)  
- Missing required fields (compliance failures)
- Suspicious patterns (fraud detection)

### Custom Documents
You can create your own test documents by following the patterns in the samples. The system uses pattern matching to extract entities, so including realistic data patterns will produce better results.

## Usage

The main application will automatically create these sample documents if they don't exist:

```bash
python main.py --create-samples
```

Or run verification on a specific document:

```bash
python main.py --document-path sample_documents/sample_drivers_license.txt
```

## Important Notes

- These are **mock documents** for testing only
- Real personal information should never be used in examples
- The OCR and classification systems use pattern matching on these text files
- In production, you would process actual PDF, image, and other binary document formats