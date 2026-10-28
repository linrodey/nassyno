"""Validate an operator-provided UI report; never upgrades it to live API evidence."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

FEATURES = ('system','resources','storage_disks','smart','storage_pools','volumes',
            'ssd_cache','iscsi','file_station','identities','acl','firewall','connectivity','directory_snmp')
class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class Observation(StrictModel):
    feature: Literal['system','resources','storage_disks','smart','storage_pools','volumes',
                     'ssd_cache','iscsi','file_station','identities','acl','firewall','connectivity','directory_snmp']
    status: Literal['observed','not_found','not_checked','blocked']
    ui_path: str | None = Field(default=None, max_length=250)
    summary: str | None = Field(default=None, max_length=1500)
    limitation: str | None = Field(default=None, max_length=1000)

    @model_validator(mode='after')
    def evidence_required(self):
        if self.status in ('observed','not_found') and (not self.ui_path or not self.ui_path.strip() or not self.summary or not self.summary.strip()):
            raise ValueError('UI path and summary required for observed/not_found')
        if self.status == 'blocked' and not self.limitation:
            raise ValueError('Blocked observation needs a limitation')
        return self

class SurveyReport(StrictModel):
    schema_version: Literal[1]
    source_type: Literal['operator_ui_report']
    device_id: Literal['nas-site']
    observed_at: str | None = None
    model: str | None = Field(default=None,max_length=100)
    dsm_version: str | None = Field(default=None,max_length=100)
    changes_made: Literal[False]
    observations: list[Observation] = Field(min_length=14,max_length=14)

    @field_validator('observed_at')
    @classmethod
    def aware_time(cls,value):
        if value is not None:
            parsed=datetime.fromisoformat(value)
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError('Timestamp needs timezone')
        return value

    @model_validator(mode='after')
    def all_features_once(self):
        if sorted(o.feature for o in self.observations) != sorted(FEATURES):
            raise ValueError('Each feature must occur once')
        if any(o.status!='not_checked' for o in self.observations) and self.observed_at is None:
            raise ValueError('Actual observations need a timestamp')
        return self

    def readiness(self):
        return {'device_id':self.device_id,'evidence_source':self.source_type,
                'backend_authenticated':False,'backend_functions_verified':False,
                'observations':[{ 'feature':o.feature,'reported_status':o.status,
                                  'api_support':'not_verified'} for o in self.observations]}

def main(argv=None):
    parser=argparse.ArgumentParser(description='Validate sanitized NAS UI report, no network or credential input')
    parser.add_argument('report');args=parser.parse_args(argv)
    try:
        path=Path(args.report)
        if path.stat().st_size>131072:raise ValueError('Oversized')
        report=SurveyReport.model_validate_json(path.read_bytes())
    except (OSError,ValueError):
        # Validation errors can contain submitted values; never print them.
        print(json.dumps({'status':'invalid','error':'report_schema_or_file_invalid'}))
        return 1
    print(json.dumps({'status':'valid',**report.readiness()},ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
