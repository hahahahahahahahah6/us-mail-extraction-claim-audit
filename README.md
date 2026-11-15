# Documentation claim auditor

An offline static auditor comparing documentation promises with source call patterns.
It reads the root README and Markdown beneath any docs component, ignores fenced
examples, and parses source with the standard AST library without executing it.
No network calls, telemetry, or file writes occur during an audit.

## Install and use

```sh
python3 -m pip install .
us-mail-extraction-claim-audit audit . --json
python3 -m us_mail_extraction_claim_audit audit . --verbose
us-mail-extraction-claim-audit audit . --ignore vendor --ignore build --fail-on medium
us-mail-extraction-claim-audit --version
python3 -m unittest discover
python3 -m build
```

The optional repository defaults to the current directory. Ignore prefixes match
whole relative path components. The default failure threshold is high; medium
also fails on evidence found only in tests. Exit codes are 0 for PASS (or findings
below the threshold), 2 for threshold failures, and 1 for usage or I/O errors.
JSON contains verdict, findings with message and severity, claims, and evidence.
Verbose text includes locations. One finding is emitted per claim family.

## Rules and vocabulary

A positive promise without production evidence produces HIGH, or MEDIUM when only
tests contain evidence. A denial contradicted by production evidence produces HIGH.
A positive promise with no source still fails; a denial without source passes.

```text
documented-us-mail-extraction-claim-false
documented-no-us-mail-extraction-claim-false
us mail extraction
extract us mail
extracts us mail
extracting us mail
us mail parsing
us mail parser
parse us mail
parses us mail
us mail scanning
us mail scanner
scan us mail
scans us mail
usps mail extraction
extract usps mail
extracts usps mail
extracting usps mail
usps mail parsing
usps mail parser
parse usps mail
parses usps mail
usps mail scanning
usps mail scanner
scan usps mail
scans usps mail
united states mail extraction
extract united states mail
extracts united states mail
extracting united states mail
united states mail parsing
united states mail parser
parse united states mail
parses united states mail
united states mail scanning
united states mail scanner
scan united states mail
scans united states mail
us mail envelope extraction
extract us mail envelopes
extracts us mail envelopes
extracting us mail envelopes
us mail envelope parsing
us mail envelope parser
parse us mail envelopes
parses us mail envelopes
us mail envelope scanning
us mail envelope scanner
scan us mail envelopes
scans us mail envelopes
us mail data extraction
extract us mail data
no us mail extraction
does not extract us mail
does not support us mail extraction
without us mail extraction
no us mail parser
does not parse us mail
no us mail scanner
us mail extraction not supported
no usps mail extraction
does not extract usps mail
does not support usps mail extraction
without usps mail extraction
no usps mail parser
does not parse usps mail
no usps mail scanner
usps mail extraction not supported
no united states mail extraction
does not extract united states mail
does not support united states mail extraction
without united states mail extraction
no united states mail parser
does not parse united states mail
no united states mail scanner
united states mail extraction not supported
```

## Source matching and limitations

The two supported routes are a same-module client/product pair and the named
calls listed below. Imports alone never suffice. Aliases of imported call names
are resolved; assignments, annotated assignments, context-manager targets, and
local function, method, or class definitions shadow those names. Test paths count
separately. Fixtures, docs, examples, symlinks, and invalid source provide no
production evidence. Routes cannot be combined across modules. Paragraphs use
lowercase, contraction expansion, hyphen replacement, whitespace collapse, and
word boundaries; longer phrases win and denial spans are removed first.

```text
extract_us_mail
parse_us_mail
extract_us_mails
parse_us_mails
us_mail_extraction
us_mail_extractor
us_mail_parser
extract_usps_mail
parse_usps_mail
extract_usps_mails
parse_usps_mails
usps_mail_extraction
usps_mail_extractor
usps_mail_parser
extract_united_states_mail
parse_united_states_mail
united_states_mail_extraction
united_states_mail_extractor
united_states_mail_parser
extract_us_mail_data
parse_us_mail_data
us_mail_scan
us_mail_scanner
scan_us_mail
```

The following reference records the precise scope, vendor exclusions, field
limits, and known false positives. It documents matching limits rather than
promising runtime API compatibility.

```text


- The bare phrases "us mail envelope extraction" / "extract
  us mail envelopes" / "us mail envelope parsing" / "us mail
  envelope parser" are deliberately USMAILEXTRACTION phrases: in
  document-tool docs they almost always name US mail extraction.
  But "us mail envelope" can also name a record the tool merely
  stores, displays, or tracks (an envelope archive entry, a mail
  piece display, a sender document record) without extracting
  fields from a mail piece: a doc that means storing, displaying,
  or tracking mail pieces, not extracting fields from one, is a
  false positive; the tool flags the claim, only the code decides.
- "us mail data extraction" / "extract us mail data" are
  deliberately phrases: "US mail data" is the common short name
  for the structured fields pulled from a mail piece. But "US mail
  data" can also name tracking or delivery data (a delivery
  scan event, a tracking feed) rather than fields extracted from
  a mail-piece document: a doc that means delivery data, not
  field extraction from a mail piece, is a false positive; the
  tool flags the claim, only the code decides.
- "us mail scanning" / "scan us mail" are deliberately phrases:
  "scanning" US mail can mean merely photographing an envelope
  or OCRing it into raw text, with no structured field extraction.
  The tool flags the claim; only the code decides.
- "us mail parsing" / "us mail parser" are deliberately phrases:
  a doc can say "us mail parser" about a tool that only renders a
  mail piece as formatted text, or a "us mail parser" that is
  really a keyword highlighter over plain text. The tool flags the
  claim; only the code decides.
- "us mail" can also name a delivery channel ("send via US mail",
  "US mail delivery") rather than a document to extract from — but
  the phrase lists require an extraction / parsing / scanning verb,
  so a bare delivery-channel mention is not a phrase. Say so in
  the README.
- UsMailV2 / UsMailV3 carry the field set listed in the mindee
  names section above (sender name, sender address, recipient
  names, recipient addresses, plus is-return-to-sender in V3):
  they have no postage amount, no postmark date, no tracking
  number, and no barcode field. A tool that extracts those does so
  through some other route; this family checks for the
  UsMailV2 / UsMailV3 call, not for those fields. Say so in the
  README.
- A generic `extract_us_mail(` / `parse_us_mail(` /
  `extract_usps_mail(` / `extract_united_states_mail(` call can
  name a string parser for text the user typed in rather than a
  document extractor: the tool counts the call, the claim plus
  the code decide — and a subprocess call invoking an external CLI
  is NOT evidence by design, so a thin wrapper that only calls
  subprocess fails.
- Mindee `parse` with UsMailV2 / UsMailV3 counts as evidence: the
  product exists in mindee 4.22.0 (wheel inspected 2026-11-14). The
  tool detects the call in source, not whether the call succeeds
  against a current API version. Say so in the README.
- Mindee `parse` with UsMailV2 / UsMailV3 is a 4.x-only fingerprint:
  unlike the bank account details product, mindee 5.x removed the
  US mail product (5.4.0 wheel inspected 2026-11-14 — zero
  "us_mail" files and zero "UsMail" hits in any .py file; its
  v1/product/us/ directory holds only bank_check). Say so in the
  README.
- Mindee `parse` with InvoiceV4 / ReceiptV5 / PassportV1 /
  FinancialDocumentV1 / BankCheckV1 / BankAccountDetailsV1 /
  BankAccountDetailsV2 / PayslipV2 / PayslipV3 / NutritionFactsLabelV1 /
  HealthcareCardV1 / BusinessCardV1 / CustomV1 / GeneratedV1 /
  BillOfLadingV1 / ResumeV1 / DeliveryNoteV1 / DriverLicenseV1 /
  IdCardV1 / InternationalIdV2 / CarteGriseV1 / EnergyBillV1 /
  MaterialCertificateV1 / BarcodeReaderV1 / CropperV1 is NOT
  detected: those are other document types. Say so in the
  README.
- Mindee `parse` with BarcodeReaderV1 is NOT detected: reading a
  barcode is a different operation from extracting US mail
  fields, even though a mail piece may carry a barcode as an
  identifier. Say so in the README.
- Azure `begin_analyze_document` with ANY model id is NOT
  detected: Azure Document Intelligence has no US mail model (the
  Learn v4.0 GA prebuilt-model pages list no such model, verified
  2026-11-14). Say so in the README.
- Veryfi calls of ANY kind are NOT detected: veryfi has no US mail
  method (5.1.0 wheel inspected 2026-11-14 — the word "mail" does
  not appear anywhere in the wheel outside email-address strings),
  and its document APIs post to a generic documents endpoint
  shared across document types. Say so in the README.
- Google Document AI `process_document` / `batch_process_documents`
  with ANY processor is NOT detected: Document AI has no US mail
  processor (the processors list page contains no such processor,
  verified 2026-11-14). Say so in the README.
- Eden AI universal-ai calls with ANY model id are NOT detected:
  Eden AI documents no US mail parser model. Say so
  in the README.
- LlamaParse calls are NOT detected: its parsing API is
  generative with no fixed static fingerprint naming US mail.
  Say so in the README.
- Nanonets / Docsumo / ABBYY Vantage / Rossum / Klippa / Parseur /
  Extend calls are NOT detected: opaque model / skill / queue /
  template / workflow IDs, or a generic upload endpoint with the
  document type configured outside the call — no fixed fingerprint.
  Say so in the README.
- Textract `analyze_document` / `analyze_expense` / `analyze_id` /
  `start_document_analysis` / `get_expense_analysis` are NOT
  detected: generic document, expense, and identity analysis are
  not US mail extraction, and Textract has no US mail operation.
  Say so in the README.
- Generic "mail extraction" calls (extract_mail /
  parse_mail / mail_extraction with no "us" qualifier) are NOT
  detected: a bare mail call could name email extraction, not US
  mail extraction. Say so in the README.
- Email extraction calls (extract_email / parse_email /
  email_extraction) are NOT detected: email is a different medium
  from a US mail piece. Say so in the README.
- USPS address verification calls, USPS package tracking calls,
  Lob mail-sending calls, and SmartyStreets address verification
  calls are NOT detected: validating an address, tracking a parcel,
  and sending a letter are different operations from extracting
  fields from a mail piece. Say so in the README.
- A hand-rolled extraction from OCR text (`re.search` /
  `re.findall` on extracted text plus manual field assembly, no
  listed call) is NOT detected: the tool requires a listed call.
  Say so in the README.
- The mindee CLI, the veryfi CLI, and any other external US mail
  tool invoked through subprocess are NOT detected: subprocess
  calls invoking an external CLI are NOT evidence by design. Say so
  in the README.
- Azure Document Intelligence, Mindee, and Veryfi are cloud APIs:
  the tool detects the client call in source, not whether
  credentials are configured or the call succeeds. Say so in the
  README.
- "extract postage" / "postage extraction" / "extract postmark" /
  "postmark extraction" / "extract tracking number" claims are NOT
  in the phrase lists: extracting a single field value alone is not
  US mail field extraction — a postage or tracking lookup reads a
  value the caller already holds. Say so in the README.
- "extract email" / "email extraction" / "extract emails" claims
  are NOT in the phrase lists: email extraction is a different
  medium from US mail piece extraction. Say so in the README.
- "extract us mail text" / "extract text from us mail" claims are
  NOT in the phrase lists: extracting plain text from a mail piece
  is text extraction, not US mail field extraction. Say so in the
  README.
- "mailroom automation" / "mail sorting" / "mail routing" claims
  are NOT in the phrase lists: sorting or routing mail is a
  different operation from extracting fields from a mail piece.
  Say so in the README.
- "us mail delivery" / "send via us mail" / "us mail shipping"
  claims are NOT in the phrase lists: delivering or sending mail
  is a different operation from extracting fields from a mail
  piece. Say so in the README.
- "address verification" / "verify addresses" / "address
  validation" claims are NOT in the phrase lists: verifying an
  address against a database is a different operation from
  extracting sender / recipient fields from a mail piece document.
  Say so in the README.
- Invoice extraction claims ("extract invoices", "invoice
  extraction"), receipt extraction claims ("extract receipts",
  "receipt extraction"), ID document extraction claims ("extract
  passports", "passport extraction"), bank check extraction claims
  ("extract bank checks", "check extraction"), bank statement
  extraction claims ("extract bank statements", "statement
  extraction"), tax form extraction claims ("extract tax forms",
  "extract w2 forms", "1099 extraction"), pay stub extraction
  claims ("extract pay stubs", "payslip extraction"), health
  insurance card extraction claims ("extract health insurance
  cards", "health insurance card extraction"), business card
  extraction claims ("extract business cards", "business card
  extraction"), credit card extraction claims ("extract credit
  cards", "credit card extraction"), contract extraction claims
  ("extract contracts", "contract extraction"), mortgage
  extraction claims ("extract mortgages", "mortgage extraction"),
  resume extraction claims ("extract resumes", "resume
  extraction"), bill of lading extraction claims ("extract
  bills of lading", "bill of lading extraction"), delivery
  note extraction claims ("extract delivery notes", "delivery
  note extraction"), carte grise extraction claims ("extract
  carte grises", "carte grise extraction"), energy bill extraction
  claims ("extract energy bills", "energy bill extraction"),
  marriage certificate extraction claims ("extract marriage
  certificates", "marriage certificate extraction"), bank
  account details extraction claims ("extract bank account details",
  "bank details extraction", "rib extraction"), nutrition
  facts label extraction claims ("extract nutrition facts labels",
  "nutrition facts label extraction"), and material certificate
  extraction claims ("extract material certificates", "material
  certificate extraction", "extract mill test certificates",
  "mill test certificate extraction") are NOT in
  the phrase lists: this family covers US mail only.
  Say so in the README.
- As with every family: static pattern matching, not semantic
  judgement; dead code counts; alias chains the tracer cannot follow
  are missed; exact phrases only, not semantics; denial handling
  depends on the denial phrase list; each route must sit in a single
  module.

```

## Product reference

The product identifiers and historical SDK details are recorded here for source
matching. No SDK dependency is installed or called by this auditor.

```text


mindee Client construction + parse call passing UsMailV2 or UsMailV3
(Name exactly UsMailV2 or UsMailV3, or Attribute with attr exactly
UsMailV2 or UsMailV3 such as product.UsMailV2 /
mindee.product.UsMailV2 / mindee.product.us.UsMailV2 /
mindee.product.us.us_mail.UsMailV2, and the same four forms for
UsMailV3) as any argument; import gate
mindee. UsMailV2 / UsMailV3 is a 4.x-only fingerprint (4.22.0 wheel inspected 2026-11-14:
mindee/product/us/us_mail/us_mail_v2.py
defines class UsMailV2(Inference), endpoint_name
"us_mail", endpoint_version "2", and
mindee/product/us/us_mail/us_mail_v3.py
defines class UsMailV3(Inference), endpoint_name
"us_mail", endpoint_version "3", both exported at
mindee.product.us and via mindee.product.us.us_mail;
their documents are "US Mail API version 2.0" and "US Mail API
version 3.0" with fields recipient_addresses, recipient_names,
sender_address, sender_name (V2) plus is_return_to_sender (V3);
there is NO UsMailV1 — the 4.22.0 wheel contains only
us_mail_v2* and us_mail_v3* files — and no TypeUsMailV1 form;
the 5.4.0 wheel inspected 2026-11-14 contains zero "us_mail"
files and zero "UsMail" hits in any .py file — the product was
removed in 5.x, like the material certificate / energy bill /
delivery note / bill of lading / resume products). The tool
detects the call in source, not the installed SDK version. A parse
call passing any other product (InvoiceV4, ReceiptV5,
PassportV1, FinancialDocumentV1, BankCheckV1, BankAccountDetailsV1,
BankAccountDetailsV2, PayslipV2, PayslipV3, NutritionFactsLabelV1, HealthcareCardV1,
BusinessCardV1, CustomV1, GeneratedV1, BillOfLadingV1, ResumeV1,
DeliveryNoteV1, DriverLicenseV1, IdCardV1, InternationalIdV2,
CarteGriseV1, EnergyBillV1, MaterialCertificateV1, BarcodeReaderV1, CropperV1, or any other)
is NOT evidence.


V2 recipient_addresses: city, complete, is_address_change, postal_code,
private_mailbox_number, state, street.
V2 sender_address: city, complete, postal_code, state, street.
V2 document: recipient_addresses, recipient_names, sender_address, sender_name.
V3 document adds is_return_to_sender.
No postage amount, postmark date, tracking number, or barcode field.
```
