ezid.py - 0.3
=============
[![Build Status](https://travis-ci.org/Brown-University-Library/ezid_api.svg)](https://travis-ci.org/Brown-University-Library/ezid_api)

API tools for [EZID API](http://ezid.cdlib.org). 

Start an API session with ezid_api.ApiSession(username, password, scheme, naa).
```python
real = ezid_api.ApiSession('myacct', 'mypass', 'ark', '12345/6A')
real.create('abc')        # ---->  'ark:/12345/6Aabc'
```

The ezid test api account can be used by calling the TestSession() constructor.
```python
    testArk = ezid_api.ApiSession.TestSession()
    testArk.mint()        # ---->  'ark:/99999/fk4wd4h51'
    testArk.create('abc') # ---->  'ark:/99999/fk4abc'
```
or
```python
testDoi = ezid_api.ApiSession.TestSession(scheme='doi')
testDoi.mint()        # ---->  'doi:10.5072/FK2B56MG3 | ark:/b5072/fk2b56mg3'
testDoi.create('abc') # ---->  'doi:10.5072/FK2ABC | ark:/b5072/fk2abc'
```


