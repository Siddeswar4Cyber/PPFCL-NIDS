import importlib.util
import tempfile
import unittest
import json
from unittest.mock import patch
from pathlib import Path

spec=importlib.util.spec_from_file_location('audit',Path(__file__).parents[1]/'scripts'/'audit_datasets.py')
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def test_resume_after_interruption_preserves_completed_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);file=base/'sample.csv';out=base/'out.json'
            file.write_text('x,Label\n1,benign\n1,benign\n')
            with patch.object(audit,'duplicate_summary',side_effect=RuntimeError('simulated interruption')), patch('shutil.rmtree'):
                with self.assertRaises(RuntimeError):
                    audit.audit_family([file],out,memory='256MB',threads=1)
            prior=json.loads(out.read_text())
            result=audit.resume_family([file],out,prior,'256MB',1)
            self.assertEqual(result['status'],'COMPLETED')
            self.assertEqual(result['file_profiles'],prior['file_profiles'])
            self.assertEqual(result['duplicates_all_nonlabel_fields']['duplicate_row_excess'],1)
            self.assertFalse(Path(result['staging_directory']).exists())

    def test_quality_duplicates_conflicts_and_malformed_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            file=base/'sample.csv'
            file.write_text(' A, A,Label\n1,1,BENIGN\n1,1,BENIGN\n1,1,ATTACK\nNaN,Infinity,BENIGN\n,-Infinity,BENIGN\noops,2,BENIGN\n1,2,3,4\n',encoding='utf-8')
            original=file.read_bytes()
            result=audit.audit_family([file],base/'out.json',memory='256MB',threads=1)
            self.assertEqual(file.read_bytes(),original)
            self.assertEqual(result['rows'],6)
            self.assertEqual(result['files'][0]['parsing']['rejected_physical_line_locations'],1)
            self.assertEqual(result['duplicates_all_nonlabel_fields']['duplicate_row_excess'],1)
            self.assertEqual(result['duplicates_all_nonlabel_fields']['conflicting_feature_groups'],1)
            cols=result['file_profiles'][0]['columns']
            self.assertEqual(cols[0]['nan'],1)
            self.assertEqual(cols[0]['blank'],1)
            self.assertEqual(cols[0]['non_numeric_nonblank'],1)
            self.assertEqual(cols[1]['negative_infinity'],1)
            self.assertEqual(result['duplicate_trimmed_headers'],{'A':2})

    def test_temporal_and_cross_file_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            header='FLOW_START_MILLISECONDS,FLOW_END_MILLISECONDS,IPV4_SRC_ADDR,x,Label,Attack\n'
            first=base/'one.csv'; second=base/'two.csv'
            first.write_text(header+'2000,1900,1.2.3.4,2,0,Benign\n1000,1100,1.2.3.4,3,1,Scan\n')
            second.write_text(header+'2000,1900,1.2.3.4,2,0,Benign\n')
            result=audit.audit_family([first,second],base/'out.json',memory='256MB',threads=1)
            self.assertEqual(result['temporal']['end_before_start'],2)
            self.assertEqual(result['temporal']['backward_steps_in_file_order'],1)
            self.assertEqual(result['duplicates_all_nonlabel_fields']['cross_file_feature_groups'],1)
            self.assertEqual(result['duplicates_all_nonlabel_fields']['duplicate_row_excess'],1)

    def test_lossless_encoding_and_quoted_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            file=base/'latin.csv'
            file.write_bytes(b'x,Label\n1,"caf\xe9, attack"\n2,"O\x27Hare"\n3,""\n')
            result=audit.audit_family([file],base/'out.json',memory='256MB',threads=1)
            self.assertEqual(result['files'][0]['encoding'],'latin-1')
            self.assertEqual(result['rows'],3)
            self.assertEqual(result['files'][0]['parsing']['error_events'],0)
            self.assertEqual(result['file_profiles'][0]['columns'][1]['blank'],1)


if __name__=='__main__':
    unittest.main()
