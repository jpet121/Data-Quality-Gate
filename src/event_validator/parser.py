"""Finite-state pipe key=value lexer, bounded by caller, rejects unrecognized escapes."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ParseFault(Exception):
    code:str


def tokenize(text:str,max_tokens:int)->list[tuple[str,str]]:
    result=[]; i=0;n=len(text)
    if not n:raise ParseFault('empty_event')
    while i<n:
        while i<n and text[i].isspace():i+=1
        start=i
        while i<n and (text[i].isascii() and (text[i].isalnum() or text[i]=='_')):i+=1
        key=text[start:i]
        if not key:raise ParseFault('invalid_key')
        while i<n and text[i].isspace():i+=1
        if i>=n or text[i]!='=':raise ParseFault('missing_equals')
        i+=1
        while i<n and text[i].isspace():i+=1
        if i<n and text[i]=='"':
            i+=1;chars=[];closed=False
            while i<n:
                c=text[i];i+=1
                if c=='"':closed=True;break
                if c=='\\':
                    if i>=n or text[i] not in ('"','\\','|') :raise ParseFault('invalid_escape')
                    c=text[i];i+=1
                chars.append(c)
            if not closed:raise ParseFault('unclosed_quote')
            value=''.join(chars)
            while i<n and text[i].isspace():i+=1
            if i<n and text[i]!='|':raise ParseFault('trailing_garbage')
        else:
            start=i
            while i<n and text[i]!='|':
                if text[i]=='"' or text[i]=='\\':raise ParseFault('invalid_unquoted_character')
                i+=1
            value=text[start:i].strip()
            if any(ch.isspace() for ch in value):raise ParseFault('unquoted_whitespace')
        if not value:raise ParseFault('empty_value')
        result.append((key,value))
        if len(result)>max_tokens:raise ParseFault('token_limit')
        if i==n:break
        i+=1
        if i==n or not text[i:].strip():raise ParseFault('trailing_delimiter')
    seen=set()
    for key,_ in result:
        if key in seen:raise ParseFault('duplicate_key')
        seen.add(key)
    return result
