authority: none
default_effect: no-state-change

# T-126 qualification-first — focused re-review 2 裁定

## 判定

NO-GO。A/B/F/G/I/K は closed。C/J は regressed、D/E/H/L/M は partial。
focused review は `DW-O16` 上限3巡のうち2巡を消費した。第3 fix は下記6件だけに固定し、
focused re-review 3 で閉じる。無制限の追加 fix は行わない。

review 正本:

- `.codex/dev-wave-t126-qualification-jobs/s6-focused-review2/output.md`

fix 3 前 snapshot:

- `.codex/dev-wave-t126-qualification-jobs/s6-pre-fix3-integrated.patch`
- SHA-256:
  `d4447f971b7ef479ccb6208d2fb738a1b980b4dc8374c71e92351a29af47a32c`

## 最終 fix scope

| ID | 裁定 | 最小修正 |
|---|---|---|
| F2-1 | real / BLOCKER | public verifier が receipt/series から expected observations、terminal、failure_class を再導出し、pending/final ledger payload と exact 比較する。ledger hash/identity/state だけでは valid にしない。 |
| F2-2 | real / HIGH | series reservation / duplicate check を qsub 前に行う。qsub 非0だけを exact cancel。bound attempt は同 nonce で receipt publication を再開し、scheduler terminal/cancel evidenceなしに old jobを取消さない。 |
| F2-3 | real / BLOCKER | submit receipt と job-result を `create_bytes()` 同等の `.create-*` full-write loop→fsync→link publish→exact-existing verify へ統一する。partial canonical targetをclosed-table recoveryし、short writeを扱う。 |
| F2-4 | real / BLOCKER | post verifier は normal submission の pointed job-result bytesを canonical `attempt/job-result.json` と必須一致させる。series/job 共通 start、job completion≥series completion、Wmax を検証する。RC30 coherent swap fixtureを追加。 |
| F2-5 | real / HIGH | collector が `submissions/<nonce>` からleafまで全 componentをlstatし、既存静的parent symlinkをread前に拒否する。非協力的同一UID syscall間raceはscope外のまま。 |
| F2-6 | real / HIGH | M6b/M6c の producer/consumer semantic gateを共通 helper/単一実効anchorへ集約する。M7c terminalも共通 retry-admission predicateへ集約し、各単一 mutationでfixtureが受理差分まで到達する。 |

## 回帰禁止

- closed の A/B/F/G/I/K と NR-1のmissing/pending closureを回帰させない。
- dry-run/qsub非0がledgerを消費しないこと、CLI job-result省略がcanonicalを採用することを維持。
- transaction recovery、late signal closure、deadline、identity、Layer3/formal nonintersectionを維持。
- final fix 後に parent independent test、focused re-review 3、commit後 mutationを行う。
