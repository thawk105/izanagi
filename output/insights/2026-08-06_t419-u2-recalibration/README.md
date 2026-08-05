# [T-419] U-2 取得サイクルの防壁 — 逐語と変異台帳

dev-wave (2026-08-06)。branch `worktree-dev-wave-t419-u2-recalibration`、起点 main `cfda4abe`。
本 wave の所有 = 較正取得経路の clock 防壁と、その裏取り。**新較正の取得・登録は本 wave の到達点ではない。**

## 収録物

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (前提実測を含む)。**誤り 2 件は `s4-adjudication.md` を参照** |
| `s2-plan.md` | 段 2 codex プラン (read-only, reasoning=max) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 2 レンズ (両者 NO-GO) |
| `s4-adjudication.md` | 段 4 親裁定 + 追記 1〜4 (是正・変異再登録の正本) |
| `s5-impl.md` | 段 5 実装子 (codex role=author) の報告 |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー 2 本 (両者 NO-GO) |
| `s6-fix.md` → `s6-refocus.md` | fix 1 巡目 → 焦点再レビュー 1 巡目 (NO-GO) |
| `s6-fix2.md` → `s6-refocus2.md` | fix 2 巡目 → 焦点再レビュー 2 巡目 (NO-GO) |
| `s6-fix3.md` | fix 3 巡目 (上限)。親が変異で裏取りして閉じた |
| `mutation-spec.json` / `mutation-ledger.json` | 変異の事前登録 (再登録版) と本走台帳 |
| `mutation-spec-v1-erratum.json` / `mutation-ledger-v1-erratum.json` | 初回登録と初回台帳 (erratum) |
| `prompts/` | 各段の prompt 全文 |

## 実装したもの

`orchestrator/calibrator/cli.py` と `orchestrator/campaign/execution_guard.py`。

- 帯評価を 1 箇所の evaluator へ集約し `input_valid` / `policy_matches` / `band_pass` を分離した。
  canonical 述語は 3 者の連言で、shape → policy → band の短絡順と戻り値は従来どおり。
  診断 projection を足したが、**診断値は受理判断に使わない**。
- `_acquisition_reasons` へ effective clock の自己整合検査を **追加**した (benchmark 前)。
  **benchmark 後の既存 gate は残している。**
- publish 直前に「attempt 開始時 policy == publish 時 policy」を独立検査する。
- publish (rename) 後に publish 先 bytes を読み直し、内部 profile を参照せずに canonical 述語を
  適用して `published-self-comparison.json` へ記録する。不一致は非 0 終了。published artifact は削除しない。
- early 拒否の `rejection.json` に、評価に使った clock 入力・`attestation_profile` 全体・
  canonicalization 識別子・その SHA-256・`not_evaluated` を残す。成果物だけから再計算できる。
- `_write_exclusive` は本 wave 以前と**バイト一致**。書込み失敗時の temp は消さず、
  path 付きの構造化 reason として申告する。

## 実装していないもの (射程)

新較正の取得・登録、pin の更新、`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の空化、
loader / registry / consumer の self-pass、活性化権限、取得経路の source acquisition proof、
campaign 群の CMake argv、`tools/pegasus/` 配下、別 process の独立 verifier。

## 段 1 の前提実測と、その 2 件の誤り

親は 6 件を実測したが、**2 件が誤りだった**。

1. **「取得経路に自己整合検査が無い」は誤り。** canonical 述語を呼ぶ gate が benchmark 後に
   既にあり、現 HEAD は自己不整合な較正を accepted で publish しない。段 2 が file:line で是正した。
2. **「D176 の fuse により accepted publish receipt も取れない」は誤り。** publish 経路は
   `env_contract` を一切呼ばない。fuse が阻むのは current への活性化と pin 切替だけ。段 3 レンズ B が是正した。

正しかった実測: login node での α probe 実行 (method は D181 宣言値と一致、96 CPU、
median 2101.0、tolerance 2% 帯外 1 件)、登録済み較正の CPU 40 = 3080.935、
2 世代目登録が `validate_generations` で機械拒否されること、pin 閉包の所在。
**login node の 1 回測定は計算ノードの帯内性の根拠にならない** (段 3 レンズ A・B が独立に指摘)。

## 段 3 / 段 6 の敵対検証が変えたもの

- **別 job の生死 driver を取り下げた。** allocation・host・boot・時刻が異なる job の 1/1 pass は
  後続 certify の許可証にならない。同一 allocation 内の early gate が同じ役割を果たす。
  新出力先・PBS・guard registry 項目・`run_probe.py` 改造の負債がまとめて消えた。
- **本 wave の refactor が入れた回帰を検出した。** evaluator 抽出で public 述語の短絡が失われ、
  巨大整数 tolerance や後続 sample で旧版が `False` を返していた入力が `OverflowError` を
  送出するようになっていた。receipt 再検算を通る campaign / floor / oracle / ratified freeze の
  fail-closed 性を壊す。短絡順を復元し、2 反例を negative vector で固定した。
- **衛生所見への fix が 2 巡続けて破壊経路を新設した。** 一時ファイルの orphan を消しに行き、
  無条件 unlink → `stat` と `unlink` が分離した TOCTOU、と悪化した。3 巡目で helper を
  wave 前へバイト一致で戻し、「消さずに申告する」縮退で閉じた (failures 台帳を参照)。
- **自己参照 oracle を潰した。** 新規テストが `not_evaluated` の期待値へ production 定数を
  差し込んでいたため、定数から項目を削っても緑になっていた。test 側 literal へ変えた。
- **拒否成果物の proof を自己完結させた。** 当初は導出値 (中央値・上下限・違反位置) しか残らず、
  第三者が失敗 profile を再計算できなかった。

## 変異 matrix

事前登録 10 件 (負例 9・過剰拒否を検出する正例 1)。**再登録版で 10/10 KILLED、
期待 node 完全一致、SURVIVED 0 / MISMATCH 0**。

初回走行は全件で赤が出た (検出は成立) が **5 件が MISMATCH** だった。原因は親の登録が過少で、
観測された赤 node 集合が期待集合の真の上位集合だったこと。二重 gate を意図的に併存させた設計では、
片方を消すと両方を踏むテストが同時に赤くなるのが正常である。初回 spec と台帳は erratum として残した。

M1 (early gate 削除) と M2 (late gate 削除) は受理集合を変えないため、`DW-M08` の
**diagnostic sensitivity pin** として記録する。M1 は「benchmark 未開始・`rejection.json` のみ」を、
M2 は「reason が self-failure から policy-changed へ変わる」ことを固定する。

## 成果物影響と限定

- **certified 受理集合は閉鎖のまま変わらない。** 本 wave は取得経路の防壁だけを扱い、
  登録済み較正・contract・pin・凍結 bytes を 1 件も動かしていない。
- **通常の policy 固定時の publish 受理集合は不変。** 縮小したのは
  attempt 開始時と publish 時で policy が異なる再束縛経路と、publish 済み bytes 不一致だけ。
- **benchmark 中・後の clock は依然として未検査。** 外側の post probe は publish より後に走り、
  publish を取り消さない。この窓は本 wave の対象外で、裁定へ返した。
- **取得経路の source acquisition proof は依然として束縛されない。** 第三者 source の head・
  cache identity・transport は receipt に無い。新しく取得する較正も g1 と同じ欠落を持つ。
- **certify の予約式は実際の逐次 timeout 合計と一致しない。** header と receipt は build 上限
  1080 秒を記録するが、実際の cap 合計は 2340 秒である。裁定へ返した。

## 受入

- fix 3 巡目後の対象 9 file: 669 passed / 2 skipped (計算ノード)。
- 受入全走: 6668 passed / 20 skipped (計算ノード、request 892166.nqsv、local main `7c2a2cf1` 取り込み済み)。
- 変異 matrix: 10/10 KILLED (再登録版)。
- **certify job の結果は本 README の commit 時点で未取得。** worklog の後続 fragment を参照。
