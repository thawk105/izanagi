# [T-2025] attempt 単位の測定値選別を materialize で塞ぐ

- 日付: 2026-09-08
- branch: `worktree-dev-wave-t2025-attempt-selection`
- 実装 commit: `967159da4701744ccc0b43d6ea7b87000b60b798`
- 対象: `orchestrator/campaign/paper_story_a2_certification.py` (A-2 / A-6 認証)
- source_measurement: 該当なし (性能計測を伴わない)。本 wave は受理集合を狭める変更だけを行う。

## 何が開いていたか

`preregister_attempt` が attempt root へ書く `preregistration.json` には
`"automatic_retry": false` が入るが、**この field を読む consumer が repo 内に 1 つも無かった。**
`preregistration.json` 自体は投入 driver
(`tools/pegasus/submit_paper_story_a2_certification.sh` の finish-group 経路) が読むが、
参照するのは `attempt_root` と `current_pin` だけである。

結果として、同じ policy・同じ commit pin で attempt を何個でも事前登録して走らせ、
数字を見てから良い attempt だけ `collect` して materialize できた。
fan-out の交差束縛は workload を跨ぐ混成を防ぐが、attempt 全体の選別は防がない。

## 実測 — 穴は実際に使える状態だった

2026-09-08 に durable base を直接列挙した (`ls` と `cat`、および
`find <attempt>/jobs -maxdepth 2 -name raw`)。

A-2 base `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/` に
attempt root **12 個**、A-6 base
`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/` に **3 個**。
全 15 個が `preregistration.json` を持ち、全部 `automatic_retry: false` を記録していた。

| attempt_id | policy_sha256 (先頭 8) | current_pin | receipts | raw-manifest | raw file 数 |
|---|---|---|---|---|---|
| a2gate-20260902a | 42bfee48 | 511c953 | submission | 無 | 0,0 |
| a2gate-20260902b | 42bfee48 | 511c953 | submission | 無 | 0,0 |
| d1100-20260902a | 42bfee48 | 511c953 | submission | 無 | 0 |
| t1647-20260825 | b586e2e1 | 511c9538e4e8… | (空) | 無 | (raw dir 無) |
| t1647-20260825b | b586e2e1 | 511c9538e4e8… | submission | 無 | (raw dir 無) |
| t2022-20260827 | cd6522e6 | 511c9538e4e8… | submission | 無 | 2,2 |
| t2022-20260828 | cd6522e6 | 511c9538e4e8… | acq+comp+sub | 無 | 2,2 |
| t2022-20260828b | 42bfee48 | 511c9538e4e8… | acq+comp+sub | 無 | 2,2 |
| t2022-20260828c | 42bfee48 | 511c953 | acq+comp+sub | 有 | 2,2 |
| t2228-20260904a | 42bfee48 | 511c953 | acq+comp+sub | 無 | 1,1 |
| t2364-20260907a | 42bfee48 | 511c953 | acq+comp+sub | 無 | 0,0 |
| t2364-20260907b | 67dce5a7 | 511c953 | acq+comp+sub+cg2 | 有 | 2,2 |
| a6-20260902a | 4ca15d07 | 511c953 | acq+comp+sub | 無 | 0 |
| a6-20260908a | 8969a7e4 | 511c953 | submission | 無 | 0 |
| a6-20260908b | 8969a7e4 | 511c953 | acq+comp+sub+cg1 | 有 | 2 |

**同じ (policy_sha256, pin) の組に、結果を出した attempt が 4 個並んでいる組が実在した**
(`42bfee48…` + `511c953`: t2022-20260828b / t2022-20260828c / t2228-20260904a /
t2364-20260907a)。`cd6522e6…` の組も 2 個 (t2022-20260827 は receipts が submission だけだが
raw file を 4 個持つ)。選別の余地は理論上の話ではなかった。

もう 1 つ重要な実測がある。**`current_pin` は短縮 sha (`511c953`) と 40 桁 full sha の
両方が実在する** (`_COMMIT_RE = [0-9a-f]{7,64}`)。同一 policy `42bfee48…` に
`t2022-20260828c` (7 桁) と `t2022-20260828b` (40 桁) が両方在る。
pin を文字列一致で組分けすると、書き方を変えるだけで組を割って逃げられる。

## 入れたもの

認証成果物を作る唯一の関数 `materialize` の内側に判定を **1 箇所だけ** 置いた
(`_require_materialization_attempt_selection`)。`_validate_certification_result` の直後、
`_require_materializable_authority` の直前に呼ぶ。

1. **記録の消費。** 対象 attempt の `preregistration.json` を読み、exact 8 key、
   schema_version、study、attempt identity、そして **`automatic_retry is False`** を要求する。
   不在・不一致・extra key・非 bool はすべて fail-closed。
2. **組の結果一意性。** 組の key は
   `(study, 記録された policy_sha256, current_pin の先頭 7 桁)`。
   durable base 直下を `os.scandir` で fail-closed に列挙し (symlink・非 directory・
   名前不正・preregistration 欠落/破損はすべて拒否)、同じ組の sibling が結果 footprint を
   1 つでも持てば拒否する。
3. **結果 footprint。** `receipts/acquisition.json`、`receipts/completion.json`、
   `raw-manifest.json`、`jobs/<workload>/raw/` 直下の regular file のいずれか。
   `compute-result.json` と空の `raw/` は測定前に作られるので footprint に数えない。
4. **診断 (規律 3)。** 拒否 message に sibling の `attempt_id` と検出した footprint 種別を入れる。
   footprint 検査自体が異常型 (symlink / FIFO / directory) で落ちる場合も
   `sibling_attempt_id` と `problem_path` を付けて再送出する。

## 入れなかったもの (段 4 で scope 外に落とした)

段 2 プランは cohort claim 台帳 (連番 + hash 鎖)、事前登録時の `qstat` による前 attempt の
終端観測、`record_completion_receipt` / `record_acquisition_receipt` への gate、
disposition schema と CLI、bundle への census file 追加を提案した。段 3 のレビューが
「本題を越え、肝心の `automatic_retry` 消費検査のほうが薄い」「台帳の無い既存 attempt が
production 経路で事故停止する」と指摘したため、すべて落とした。

**記録された `policy_sha256` が現行 policy と一致することも要求していない。**
稼働中の `a6-20260908b` の記録は `8969a7e4…` で、repo 現行 A-6 policy の `682e0f4e…` と
異なる。一致を要求すると現に走っている A-6 が止まる。

## 帰結

- 稼働中の A-6 は通る。組 `8969a7e4…` の結果保持者は `a6-20260908b` の 1 個だけで、
  `a6-20260908a` は footprint ゼロである。**正当な再試行 (前が何も結果を出さずに終わった場合) は
  通る**という性質が、実在の運用列 `a6-20260908a` → `a6-20260908b` で確認できる。
- A-2 の組 `42bfee48…` (結果 4 個) と `cd6522e6…` (結果 2 個) は、どの attempt も
  materialize できなくなる。これは事故ではなく本 wave が塞ぐ当の状態である。
  現行 A-2 policy の sha は `cacfdd5d…` でどちらの組にも属さないので、新しい認証は妨げない。

## 閉じていないこと (主張しない限界)

**filesystem を自由に書ける主体は止められない。** attempt root と結果 footprint を
durable base の外へ退避してから測り直せば、判定は「組に結果は 1 個」と見る。
`O_EXCL` は最初の作成競走を閉じるが、後からの削除・再構成を防ぐ外部の append-only authority
ではない。D387 と同じ限界であり、repo 内の gate と検査を同じ主体が変更できる限り、
意図的な弱体化への完全な防壁にはならない。**「選別を閉じた」とは主張しない。**
本 wave が達成したのは「記録が production の必須経路で消費されるようになり、
無加工の運用では選別ができなくなった」ことである。

段 3 はもう 1 つ real 所見を出した — **policy を 1 byte 変えれば別の組になる。**
`--policy` は `canonical_policy_path` で shipped 2 path に限定されているので、
これを使うには tracked な policy JSON を書き換える必要があり、git diff に現れる。
本 wave が作った穴ではなく、policy identity の既存の性質である。裁定パッケージへ回す。

## 変異 (逐語)

spec: `mutation-spec-v2.json` sha256 = `5d5f88ae9e7709670ca7a6de38b0dd0c4c5a48a96cd66a8a0f0a02f566a2b3a6`
repo_head = `967159da4701744ccc0b43d6ea7b87000b60b798`
runner = `python3 tools/run_tests.py orchestrator/tests/test_paper_story_a2_certification.py -q -rf -p no:cacheprovider`

```text
summary = {"KILLED": 7, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 0,
           "TIMEOUT": 0, "completed": 7, "matching": 7, "recorded": 7, "registered": 7}
M1prime-validator-automatic-retry-inverted -> KILLED
M2-validator-automatic-retry-check-removed -> KILLED
M3-materialize-gate-call-removed           -> KILLED
M4-cohort-pin-normalization-removed        -> KILLED
M5prime-census-drops-siblings-only         -> KILLED
M6-completion-footprint-removed            -> KILLED
M7-writer-automatic-retry-true             -> KILLED
```

### 変異の erratum (初回走行を消さない)

初回走行 (spec sha256 `2fbf8ab85e23d62172822850a26a4043d329b42c564745e4d12b983d5daf5f0f`) は
`KILLED 1 / MISMATCH 6` だった。**登録した殺し手 node は 7 件すべて実際に赤になっている**
(`expected_nodes ⊆ failed_nodes` が全件成立)。MISMATCH になったのは harness の判定が
`failed_keys == expected_keys` の完全一致であり、判定が必須経路に載っているために
他の materialize test も同時に赤になったためである (最大 27 node)。
2 回目は実測した node 集合をそのまま登録し直して全件 KILLED になった。
初回結果は `mutation-out-run1.json` に残してある。

### 変異事前登録の初版 (段 4 時点) と再照準

初版の M1 (`preregister_attempt` の `False`→`True` を T1 で殺す) と
M5 (census を空 tuple にして T4 で殺す) は**不成立**だった。
段 6 レビューが静的に指摘し、親が fix 前に再照準した。

- M1 不成立の理由: 当時の T1 は実在 literal を validator へ渡すだけで writer を通らないため
  赤にならない。→ 段 6 fix で T1 を writer の実出力の読み戻しまで通す形に強化し、
  writer 変異は M7 として別に登録した。
- M5 不成立の理由: census を空 tuple にすると sibling 衝突を迂回するが `target_seen == 0` が
  先に拒否するので、T4 は受理へ反転せず診断文字列の差で赤になる (単一理由でない)。
  → 対象は数えるが sibling だけを落とす `(target_root,)` へ再照準した (M5')。

## テスト

新規 test file は作らず `orchestrator/tests/test_paper_story_a2_certification.py` へ足した。
positive control は実在 `a6-20260908b` の `preregistration.json` の 8 field を逐語 literal 化し、
`preregister_attempt` が実際に書いた出力の読み戻しと合わせて検査する (D431)。
正当な再試行が通る正例 (`a6-20260908a` と同形の resultless sibling) では
`_result_footprints` が対象 sibling について呼ばれ空 tuple を返したことも確認する
(gate 呼び出しを削除しただけで緑にならないようにするため)。

## 実走

- 焦点走 (親): `PYTHONPATH=. python3 orchestrator/tests/test_paper_story_a2_certification.py`
  → 実装後 `201 passed in 420.37s`、段 6 fix 後は子の自走で `207 passed in 294.95s`。
- 変異 baseline (dispatch): rc=0。
- 受入全走: 記録 commit 後に実施し、結果を worklog に書く。
