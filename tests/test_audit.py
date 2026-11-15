import unittest
from us_mail_extraction_claim_audit import phrases
EXPECTED_POS = ('us mail extraction', 'extract us mail', 'extracts us mail', 'extracting us mail', 'us mail parsing', 'us mail parser', 'parse us mail', 'parses us mail', 'us mail scanning', 'us mail scanner', 'scan us mail', 'scans us mail', 'usps mail extraction', 'extract usps mail', 'extracts usps mail', 'extracting usps mail', 'usps mail parsing', 'usps mail parser', 'parse usps mail', 'parses usps mail', 'usps mail scanning', 'usps mail scanner', 'scan usps mail', 'scans usps mail', 'united states mail extraction', 'extract united states mail', 'extracts united states mail', 'extracting united states mail', 'united states mail parsing', 'united states mail parser', 'parse united states mail', 'parses united states mail', 'united states mail scanning', 'united states mail scanner', 'scan united states mail', 'scans united states mail', 'us mail envelope extraction', 'extract us mail envelopes', 'extracts us mail envelopes', 'extracting us mail envelopes', 'us mail envelope parsing', 'us mail envelope parser', 'parse us mail envelopes', 'parses us mail envelopes', 'us mail envelope scanning', 'us mail envelope scanner', 'scan us mail envelopes', 'scans us mail envelopes', 'us mail data extraction', 'extract us mail data')
EXPECTED_NEG = ('no us mail extraction', 'does not extract us mail', 'does not support us mail extraction', 'without us mail extraction', 'no us mail parser', 'does not parse us mail', 'no us mail scanner', 'us mail extraction not supported', 'no usps mail extraction', 'does not extract usps mail', 'does not support usps mail extraction', 'without usps mail extraction', 'no usps mail parser', 'does not parse usps mail', 'no usps mail scanner', 'usps mail extraction not supported', 'no united states mail extraction', 'does not extract united states mail', 'does not support united states mail extraction', 'without united states mail extraction', 'no united states mail parser', 'does not parse united states mail', 'no united states mail scanner', 'united states mail extraction not supported')
EXPECTED_GENERIC = ('extract_us_mail', 'parse_us_mail', 'extract_us_mails', 'parse_us_mails', 'us_mail_extraction', 'us_mail_extractor', 'us_mail_parser', 'extract_usps_mail', 'parse_usps_mail', 'extract_usps_mails', 'parse_usps_mails', 'usps_mail_extraction', 'usps_mail_extractor', 'usps_mail_parser', 'extract_united_states_mail', 'parse_united_states_mail', 'united_states_mail_extraction', 'united_states_mail_extractor', 'united_states_mail_parser', 'extract_us_mail_data', 'parse_us_mail_data', 'us_mail_scan', 'us_mail_scanner', 'scan_us_mail')
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from us_mail_extraction_claim_audit.audit import audit, module_evidence, paragraphs
from us_mail_extraction_claim_audit.__main__ import main

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def put(self, path, text):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(['audit', str(self.root)] + list(args))
        return code, out.getvalue()
    def test_phrase_oracle(self):
        self.assertEqual(phrases.USMAILEXTRACTION, EXPECTED_POS)
        self.assertEqual(phrases.NOUSMAILEXTRACTION, EXPECTED_NEG)
        self.assertEqual(phrases.GENERIC_NAMES, EXPECTED_GENERIC)
        self.assertEqual(len(set(EXPECTED_POS)), 50)
        self.assertEqual(len(set(EXPECTED_NEG)), 24)
        self.assertEqual(len(set(EXPECTED_GENERIC)), 24)
    def test_good(self):
        self.put('README.md', 'Extract us mail')
        self.put('app.py', 'x.extract_us_mail()')
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
    def test_bad(self):
        self.put('README.md', 'Extract us mail')
        code, output = self.cli('--json')
        self.assertEqual(code, 2)
        report = json.loads(output)
        self.assertEqual(report['verdict'], 'FAIL')
        finding = report['findings'][0]
        self.assertEqual(finding['rule'], 'documented-us-mail-extraction-claim-false')
        self.assertEqual(finding['severity'], 'HIGH')
        self.assertTrue(finding['message'])
    def test_test_only(self):
        self.put('README.md', 'Extract us mail')
        self.put('tests/test_app.py', 'x.extract_us_mail()')
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual(self.cli('--fail-on', 'medium')[0], 2)
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')
    def test_denial(self):
        self.put('README.md', 'Does not extract us mail')
        self.put('app.py', 'x.extract_us_mail()')
        self.assertEqual(self.cli()[0], 2)
        self.assertEqual(audit(self.root)['findings'][0]['rule'], 'documented-no-us-mail-extraction-claim-false')
        self.assertEqual(len(audit(self.root)['claims']), 1)
    def test_denial_no_source(self):
        self.put('README.md', 'No us mail extraction')
        self.assertEqual(self.cli()[0], 0)
    def test_no_claim(self):
        self.put('README.md', 'A useful tool')
        self.assertEqual(self.cli()[0], 0)
    def test_fences(self):
        self.put('README.md', '   ```text\nextract us mail\n   ```\n\n~~~\nextract us mail\n~~~')
        self.assertEqual(audit(self.root)['claims'], [])
    def test_inline(self):
        self.put('README.md', '`extract us mail`')
        self.assertEqual(self.cli()[0], 2)
    def test_normalization(self):
        self.put('README.md', "Doesn't extract US-mail")
        self.assertEqual([c['family'] for c in audit(self.root)['claims']], ['NOUSMAILEXTRACTION'])
    def test_split_module(self):
        self.put('README.md', 'Extract us mail')
        self.put('one.py', 'import mindee\nc = mindee.Client()')
        self.put('two.py', 'import mindee\nc.parse(product.UsMailV2, source)')
        self.assertEqual(self.cli()[0], 2)
    def test_symlinks(self):
        self.put('README.md', 'Extract us mail')
        with tempfile.TemporaryDirectory() as external:
            target = Path(external)/'app.py'
            target.write_text('x.extract_us_mail()')
            (self.root/'app.py').symlink_to(target)
            (self.root/'linked').symlink_to(external, target_is_directory=True)
            self.assertEqual(self.cli()[0], 2)
    def test_ignore(self):
        self.put('README.md', 'Extract us mail')
        self.put('vendor/a.py', 'x.extract_us_mail()')
        self.put('other/a.py', 'x.extract_us_mail()')
        self.assertEqual(self.cli('--ignore', 'vendor', '--ignore', 'other')[0], 2)
    def test_docs_selection(self):
        self.put('nested/docs/guide.md', 'Extract us mail')
        self.assertEqual(self.cli()[0], 2)
        self.assertEqual(self.cli('--ignore', 'nested')[0], 0)
    def test_non_docs_markdown(self):
        self.put('other.md', 'Extract us mail')
        self.assertEqual(self.cli()[0], 0)
    def test_bound_import(self):
        for statement in ['extract_us_mail = other', 'extract_us_mail: object = other', 'with cm() as extract_us_mail:\n    pass', 'async with cm() as extract_us_mail:\n    pass']:
            with self.subTest(statement=statement):
                self.assertFalse(module_evidence('from sdk import extract_us_mail\n' + statement + '\nextract_us_mail()'))
    def test_bad_path(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['audit', str(self.root/'absent')]), 1)
    def test_usage(self):
        for args in [[], ['oops'], ['audit', '--fail-on', 'HIGH'], ['audit', '--ignore']]:
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 1)
    def test_version_and_module_entry(self):
        result = subprocess.run([sys.executable, '-m', 'us_mail_extraction_claim_audit', '--version'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '0.1.0')
    def test_self_audit(self):
        self.assertEqual(audit(Path(__file__).resolve().parents[1])['verdict'], 'PASS')

# Each vector is a separate discoverable test, making coverage and counts visible.
def vector(name, source, expected):
    def test(self):
        self.assertEqual(bool(module_evidence(source)), expected, source)
    setattr(AuditTests, 'test_' + name, test)

for index, name in enumerate(EXPECTED_GENERIC):
    vector('generic_attribute_%02d' % index, 'x.' + name + '()', True)
    vector('generic_import_%02d' % index, 'from sdk import ' + name + ' as f\nf()', True)
    vector('generic_bare_%02d' % index, name + '()', False)
    vector('generic_shadow_%02d' % index, 'from sdk import ' + name + '\ndef ' + name + '(): pass\n' + name + '()', False)

for version in ['UsMailV2', 'UsMailV3']:
    for index, product in enumerate([version, 'product.' + version, 'mindee.product.' + version, 'mindee.product.us.' + version, 'mindee.product.us.us_mail.' + version]):
        vector('mindee_' + version + '_%d' % index, 'import mindee\nc = mindee.Client()\nc.parse(' + product + ', source)', True)
        vector('mindee_keyword_' + version + '_%d' % index, 'from mindee import Client as C\nc = C()\nc.parse(product_class=' + product + ', input_source=source)', True)
    vector('mindee_from_' + version, 'from mindee import Client\nfrom mindee.product.us import ' + version + '\nc=Client()\nc.parse(' + version + ', source)', True)
    vector('mindee_alias_' + version, 'from mindee import Client as C\nfrom mindee.product.us import ' + version + ' as P\nc=C()\nc.parse(P, source)', True)
    vector('mindee_no_client_' + version, 'import mindee\nc.parse(product.' + version + ', source)', False)

OTHER_PRODUCTS = 'InvoiceV4 ReceiptV5 PassportV1 FinancialDocumentV1 BankCheckV1 BankAccountDetailsV1 BankAccountDetailsV2 PayslipV2 PayslipV3 NutritionFactsLabelV1 HealthcareCardV1 BusinessCardV1 CustomV1 GeneratedV1 BillOfLadingV1 ResumeV1 DeliveryNoteV1 DriverLicenseV1 IdCardV1 InternationalIdV2 CarteGriseV1 EnergyBillV1 MaterialCertificateV1 BarcodeReaderV1 CropperV1 UsMailV1 TypeUsMailV1'.split()
for product in OTHER_PRODUCTS:
    vector('wrong_product_' + product, 'import mindee\nc=mindee.Client()\nc.parse(product.' + product + ', source)', False)

AZURE_MODELS = 'invoice receipt layout read idDocument check.us tax.us bankStatement.us payStub.us healthInsuranceCard.us businessCard creditCard contract mortgage.us.1003 vaccinationCard'.split()
for index, model in enumerate(AZURE_MODELS):
    vector('azure_model_%02d' % index, 'from azure.ai.documentintelligence import DocumentIntelligenceClient\nc=DocumentIntelligenceClient()\nc.begin_analyze_document("prebuilt-' + model + '", source)', False)

NEGATIVE = [
'import mindee', 'import veryfi', 'import azure.ai.documentintelligence', 'from google.cloud import documentai',
'import mindee\nc=mindee.Client()', 'from azure.ai.documentintelligence import DocumentIntelligenceClient\nc=DocumentIntelligenceClient()',
'import veryfi\nc=veryfi.Client()', 'requests.post("https://api.veryfi.com/api/v8/partner/documents")',
'c.process_document(source)', 'c.batch_process_documents(source)', 'c.analyze_document(source)', 'c.analyze_expense(source)', 'c.analyze_id(source)', 'c.start_document_analysis(source)', 'c.get_expense_analysis(source)',
'c.universal_ai("ocr/invoice_parser/affinda")', 'c.universal_ai("ocr/resume_parser/affinda")', 'LlamaParse().load_data(source)',
'c.ocr(model_id="opaque")', 'c.upload(source)', 'c.extract_mail(source)', 'c.extract_email(source)', 'usps.verify_address(address)', 'usps.track(package)', 'lob.send_mail(source)', 'smartystreets.verify(address)',
'pdfplumber.open(source).extract_text()', 'pytesseract.image_to_string(source)', 'pandas.read_csv(source)', 'pandas.read_excel(source)', 'camelot.read_pdf(source)', 'tabula.read_pdf(source)', 'pdfplumber.open(source).extract_table()',
're.search("sender", pytesseract.image_to_string(source))', 'str(source).split("sender")', 'subprocess.run(["mindee", "parse", source])', 'subprocess.run(["veryfi", source])',
'"x.extract_us_mail()"', '# x.extract_us_mail()', 'x.extract_us_mail', 'invalid !!!',
'def extract_us_mail(): pass\nx.extract_us_mail()', 'class extract_us_mail: pass\nx.extract_us_mail()', 'class C:\n    def extract_us_mail(self): pass\nx.extract_us_mail()',
'from sdk import extract_us_mail as f\nf=other\nf()',
'import mindee\ndef Client(): pass\nmindee.Client()\nx.parse(product.UsMailV2, source)',
'from mindee import Client\nClient = other\nClient()\nx.parse(product.UsMailV2, source)',
'import mindee\nwith cm() as mindee:\n    mindee.Client()\nx.parse(product.UsMailV2, source)',
'import mindee\nc=mindee.Client()\nUsMailV2=other\nc.parse(UsMailV2, source)',
'c.extract(model_id="opaque")', 'c.run_skill("opaque")', 'c.queue("opaque")', 'c.template("opaque")', 'c.workflow("opaque")',
]
for method in 'process_any_document process_any_document_url process_document process_document_url process_w2_document process_w9_document process_w8_document process_check process_check_url process_check_with_remittance process_check_with_remittance_url process_bank_statement_document process_bank_statement_document_url process_bussines_card_document process_bussines_card_document_url classify_document get_business_cards get_business_card delete_business_card process_us_mail_document process_us_mail_document_url'.split():
    NEGATIVE.append('import veryfi\nc=veryfi.Client()\nc.' + method + '(source)')
for index, source in enumerate(NEGATIVE):
    vector('not_evidence_%03d' % index, source, False)

for index, phrase in enumerate(EXPECTED_POS):
    def test(self, phrase=phrase):
        self.put('README.md', phrase)
        self.assertEqual(self.cli()[0], 2)
    setattr(AuditTests, 'test_positive_phrase_%02d' % index, test)
for index, phrase in enumerate(EXPECTED_NEG):
    def test(self, phrase=phrase):
        self.put('README.md', phrase)
        self.assertEqual(self.cli()[0], 0)
        self.assertEqual({c['family'] for c in audit(self.root)['claims']}, {'NOUSMAILEXTRACTION'})
    setattr(AuditTests, 'test_denial_phrase_%02d' % index, test)
for index, path in enumerate(['fixtures/a.py', 'docs/a.py', 'examples/a.py', 'tests/a.py', 'test_a.py', 'a_test.py']):
    def test(self, path=path):
        self.put('README.md', 'Extract us mail')
        self.put(path, 'x.extract_us_mail()')
        result = audit(self.root)
        self.assertFalse(result['evidence']['production'])
        self.assertEqual(bool(result['evidence']['tests']), path in ['tests/a.py','test_a.py','a_test.py'])
    setattr(AuditTests, 'test_exclusion_%02d' % index, test)

if __name__ == '__main__':
    unittest.main()
