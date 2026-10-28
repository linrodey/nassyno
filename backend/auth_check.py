"""Explicit interactive login/logout test, no credential storage or automatic retry."""
import argparse
import asyncio
import getpass
import json
import ssl
from pathlib import Path
import httpx
from .config import Device
from .dsm import DsmProbe, ProbeError

async def check_auth(device, account, password, otp='', transport=None, encoding='form'):
    if encoding not in ('form', 'multipart'):
        raise ValueError('Unsupported credential encoding')
    discovery = await DsmProbe(transport).probe(device)
    auth = next(c for c in discovery['capabilities'] if c['api']=='SYNO.API.Auth')
    if not auth['path'] or not (auth['min_version'] <= 6 <= auth['max_version']):
        return {'authentication':'unsupported_auth_descriptor','logout':'not_attempted'}
    params={'api':'SYNO.API.Auth','version':'6','session':'FileStation'}
    context=ssl.create_default_context(cafile=device.ca_file)
    async with httpx.AsyncClient(verify=context,transport=transport,follow_redirects=False,timeout=10) as client:
        async def call(fields):
            body = {**params, **fields}
            # Multipart text fields preserve proxy binding placeholders verbatim.
            # URL-encoded form bodies can transform placeholders before substitution.
            kwargs = {'files': {k:(None,v) for k,v in body.items()}} if encoding == 'multipart' else {'data':body}
            async with client.stream('POST',device.endpoint.rstrip('/')+'/webapi/'+auth['path'],**kwargs) as r:
                if r.status_code != 200:
                    raise ProbeError('http_error',r.status_code)
                content=bytearray()
                async for chunk in r.aiter_bytes():
                    content.extend(chunk)
                    if len(content)>262144: raise ProbeError('response_too_large')
            value=json.loads(content)
            if not isinstance(value,dict): raise ProbeError('dsm_response_invalid')
            return value
        try:
            fields={'method':'login','account':account,'passwd':password,'format':'sid','enable_syno_token':'yes'}
            if otp:fields['otp_code']=otp
            result=await call(fields)
        except (httpx.HTTPError, ProbeError, ValueError):
            return {'authentication':'indeterminate','logout':'not_possible_without_session',
                    'next_step':'Do not retry automatically; a login may have reached DSM. Check DSM sessions.'}
        if result.get('success') is not True:
            error=result.get('error');code=error.get('code') if isinstance(error,dict) else None
            return {'authentication':'rejected','dsm_error_code':code if type(code) is int else None,'logout':'not_attempted'}
        data=result.get('data')
        if not isinstance(data,dict) or not isinstance(data.get('sid'),str) or not data['sid']:
            return {'authentication':'indeterminate','logout':'not_possible_without_session'}
        logout={'method':'logout','_sid':data['sid']}
        if isinstance(data.get('synotoken'),str):logout['SynoToken']=data['synotoken']
        try:
            closed=await call(logout)
            status='confirmed' if closed.get('success') is True else 'unconfirmed'
        except (httpx.HTTPError, ProbeError, ValueError):
            status='unconfirmed'
        return {'authentication':'succeeded','logout':status,'permissions':'not_tested'}

def main():
    parser=argparse.ArgumentParser(description='Explicit DSM login/logout check; prompts locally, no secret in arguments')
    parser.add_argument('--config',required=True);parser.add_argument('--device',required=True)
    args=parser.parse_args()
    try:
        devices=[Device(**d) for d in json.loads(Path(args.config).read_text())['devices']]
        device=next(d for d in devices if d.id==args.device)
    except (OSError,ValueError,KeyError,TypeError,StopIteration):
        print('Invalid inventory/device');return 1
    # Abort rather than let getpass fall back to echoed input.
    import sys
    if not sys.stdin.isatty():
        print('Interactive terminal required; secrets cannot be piped or supplied as arguments.');return 1
    account=input('DSM account: ');password=getpass.getpass('DSM password: ');otp=getpass.getpass('OTP if required, otherwise Enter: ')
    try:result=asyncio.run(check_auth(device,account,password,otp))
    except ProbeError as exc:result={'authentication':'not_attempted',**exc.public()}
    finally:password=otp=''
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result.get('authentication')=='succeeded' and result.get('logout')=='confirmed' else 2

if __name__=='__main__':raise SystemExit(main())
