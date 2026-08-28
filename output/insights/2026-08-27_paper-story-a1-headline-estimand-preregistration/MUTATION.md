# T-1817 最終変異台帳

## 結論

- 固定 tip: `cb9eeb4b6824249cc4c350ad46639e81ec493ee8`
- broad spec: `mutation-spec.final.json`、SHA-256
  `6d10323b30644074b7f306fbf2094d7576cba12edb3514de1ea5a0a705becc77`
- broad ledger: `mutation-ledger.final.json`、SHA-256
  `13e5e27695aede3ea8ef40f5ce11f23e3ca41f33d8faffdfa25d43453dea4148`
- baseline: PASSED
- broad: 9 KILLED / 1 MISMATCH / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0
- M06 correction: 1 KILLED / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0
- 実効 matrix: **10/10 KILLED**

## M06 erratum

初回 M06 は alpha spending を `1/(60*j*(j+1))` から `1/(30*j*(j+1))` へ反転した。
事前登録は alpha spending test 1 nodeだけを期待したが、実測では同じ反転を verifier が
`certification condition alpha differs` として拒否し、replay receipt binding testも失敗した。
このため初回を MISMATCH のまま保存し、2 nodeを完全な期待集合として別 specへ再登録した。

- correction spec: `mutation-spec.m06-correction.json`、SHA-256
  `d48c7cb2fb4e551f67da131053d73131be0a242471ce020d42c965618f2a0fd2`
- correction ledger: `mutation-ledger.m06-correction.json`、SHA-256
  `ec507c8f5e72e62c7271664fd1ccd68743ea35dd6a45a920f064108a9e95daa2`
- 補正結果: expected 2 node完全一致で KILLED

## timeout / orphan 復旧

wrapper attempt 5 の M03 は dispatch queue / Pre-running が180秒を超え、request
`954432.nqsv` を残してorphan-holdになった。TIMEOUTを変異のhangとは読まず、request不在を
`qstat`で確認後、scratch sourceを固定HEADへ復元し、repo hold、request hold、job-dir側
orphan-stop sidecarを削除してwrapper attempt 7で再開した。M03以降は結果を失わず完走した。

初回 wrapper のsource/main共有木postconditionは、固定scratchの変化でなく並行main前進を検出して
rc=125になった。固定scratch commit、spec SHA、各mutationのsource復元検査は不変であり、変異判定は
各dispatch receiptとledgerの完全failure集合を根拠とする。

## raw 証拠

- `mutation-attempts.final.json`、SHA-256
  `0d7e844c74228d26a3db3440b3de9f3e8f17eebbd79653dc29be39fbf7a60f6a`
- 初回 M06 MISMATCH、orphan-hold、復旧後の各attemptを削除せず保持する。
