import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from pydantic import ValidationError
from backend.survey_report import SurveyReport, main

TEMPLATE=Path(__file__).resolve().parents[1]/'survey/template.json'
class SurveyTests(unittest.TestCase):
    def template(self):return json.loads(TEMPLATE.read_text())
    def observed(self):
        data=self.template();data['observed_at']='2026-10-27T15:00:00+07:00'
        data['observations'][0].update(status='observed',ui_path='Control Panel / Info Center',summary='Model checked on UI')
        return data
    def test_empty_template_is_not_live_evidence(self):
        report=SurveyReport.model_validate(self.template())
        self.assertFalse(report.readiness()['backend_authenticated'])
        self.assertTrue(all(x['api_support']=='not_verified' for x in report.readiness()['observations']))
    def test_valid_ui_observation_never_proves_backend_api(self):
        result=SurveyReport.model_validate(self.observed()).readiness()
        self.assertEqual(result['observations'][0]['reported_status'],'observed')
        self.assertFalse(result['backend_functions_verified'])
    def test_missing_timestamp_or_ui_path_rejected(self):
        for mutate in [lambda d:d.update(observed_at=None),lambda d:d.update(observed_at='2026-10-27T15:00:00'),lambda d:d['observations'][0].update(ui_path=None)]:
            data=self.observed();mutate(data)
            with self.assertRaises(ValidationError):SurveyReport.model_validate(data)
    def test_secret_fields_and_direct_evidence_claim_rejected(self):
        for field in ['password','cookie','sid','backend_authenticated']:
            data=self.template();data[field]='FAKE-SENSITIVE'
            with self.assertRaises(ValidationError):SurveyReport.model_validate(data)
        data=self.template();data['source_type']='live_backend'
        with self.assertRaises(ValidationError):SurveyReport.model_validate(data)
    def test_duplicate_or_omitted_feature_rejected(self):
        data=self.template();data['observations'][1]=copy.deepcopy(data['observations'][0])
        with self.assertRaises(ValidationError):SurveyReport.model_validate(data)
    def test_changes_or_blocked_without_limitation_rejected(self):
        data=self.template();data['changes_made']=True
        with self.assertRaises(ValidationError):SurveyReport.model_validate(data)
        data=self.observed();data['observations'][0]['status']='blocked'
        with self.assertRaises(ValidationError):SurveyReport.model_validate(data)
    def test_cli_failure_does_not_echo_secret(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'report.json';data=self.template();data['password']='FAKE-SENSITIVE';path.write_text(json.dumps(data))
            output=io.StringIO()
            with contextlib.redirect_stdout(output):code=main([str(path)])
            self.assertEqual(code,1);self.assertNotIn('FAKE',output.getvalue())
