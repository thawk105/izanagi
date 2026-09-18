# Q2 の arm 定義 (job dir probe/arms-q2.json)

sha256 `8d9c91af7a60a4772ef9e825f5c40ac2d8402de2489291e64186af62158742c6`、1147 byte。

```json
[
  {"name": "p058-plain", "pin": "058d0c4e5f237d88ec1c2ebe0739113d82906e47", "patches": [], "witness": false, "observational_only": false},
  {"name": "e9-plain-nowit", "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290", "patches": [], "witness": false, "observational_only": false},
  {"name": "e9-instr-nowit", "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290", "patches": ["/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/verbatim/instr-mocc-lock-coverage.patch"], "witness": false, "observational_only": false},
  {"name": "e9-instr-wit", "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290", "patches": ["/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/verbatim/instr-mocc-lock-coverage.patch"], "witness": true, "observational_only": false},
  {"name": "e9-diag-wit", "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290", "patches": ["/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/verbatim/instr-mocc-lock-coverage.patch", "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/probe/mocc-close-version-counter-gap.patch"], "witness": true, "observational_only": true}
]
```
