# [T-2288] B-4 床値 spec 凍結の binder precheck — placeholder spec 3 本で `place` と `--validate-only` を実 checkout で通した (実装差分ゼロ)

`authority: none`
`default_effect: no-state-change`

2026-09-17。wave `dev-wave-t2288-binder-precheck`、branch `worktree-dev-wave-t2288-binder-precheck`。
起点 local main `abc7085ae6e1a69dc294c4f827ed7949e6df5305`、段 4 前に `ad12ba35b14bce39ce8e2804d806f2506cd1bb67`
(rulings 第 20 回) を ff-only で取り込んだ。**実装面 (D95 決定 2) の差分は 0。** 本 wave の成果物は本スナップショットと
worklog fragment だけである。可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。

**本書に載る spec は placeholder であり、凍結でも正式 evidence でもない (事前登録 §11.1)。** spec の bytes は
捨て branch `precheck-t2288-placeholder-specs` にだけ在り、本 wave はその branch を land しない。

## 依頼と答え

依頼は「A-5 (2 窓・campaign_id・seed_hex・relpath) はユーザー裁定待ちなので値は決めず、捨て branch に placeholder
値の 3 spec (`floor-pair-spec/v3`、D2088 の perf_config・D2089 の 3 cell・D2090 の較正) を commit し、凍結 checkout
での binary `place` と `floor_pair_driver.py --validate-only` (binder 全体) を通し、成否と落ちた箇所を insight に返す。
準備が本番一式の再構築になるなら中止して理由だけ返す。gate・検査の追加は scope 外」だった。

**答え: binder 全体が実 checkout・実 record・実較正・実 binary で通った。落ちた箇所は無い。** 3 spec (rr95 / rr50 /
rr5) とも `--validate-only` が rc=0・stderr 空で `floor-pair-plan/v2` (248 session・496 測定・2 窓 × 124) を返した。
再構築は要らなかった — record (T-2636)・durable binary・較正 3 件 (D2089 / D2090) が現物として揃っていた。
併せて負対照 5 本を同じ checkout で実走し、binder の各検査が実際に拒否することを確かめた (gate・test は足していない)。

**本 precheck は凍結時の成功を保証しない。** A-5 の実値・凍結 wave の HEAD・policy の世代 (D2069 項 6) が変われば
結果は変わりうる。価値は binder 欠陥の早期発見に限る (段 1 brief のとおり)。

## binder の検査鎖と、各検査が実際に読んだ現物

`load_frozen_spec` (`orchestrator/campaign/floor_pair_driver.py`) の順に並べる。すべて worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-binder-precheck` (捨て branch、HEAD `3ec30125f`) で通した。

| # | 検査 | 実際に読んだ現物 | 結果 |
|---|---|---|---|
| 1 | spec path が repo_root 内の canonical relpath | `output/env/pegasus/floor-pair/precheck-placeholder-t2288/spec-rr{95,50,5}.json` | 通過 |
| 2 | spec bytes の sha256 == `--expected-sha256` | rr95 `73da760f…c143` / rr50 `80c24b61…e9e9` / rr5 `a231b45c…ded7d2` (`verbatim/placeholder-specs.sha256`) | 通過 |
| 3 | spec bytes == loaded HEAD の tracked blob | `git show 3ec30125f:<relpath>` | 通過 |
| 4 | schema と全 section の exact parse | `floor-pair-spec/v3`、11 section、定数 ID (`hmac-sha256-rank/v1` 等) は driver の定数と一致 | 通過 |
| 5 | 出力 relpath (窓 2 + summary) の相異と parent dir の実在 | spec と同じ dir (tracked file があるので実在) | 通過 |
| 6 | calibration が tracked かつ sha256 一致 | `output/env/pegasus/calibration/registered/calibration-{5c836a22,94a4b79f,2b7ba072}….json` | 通過 |
| 7 | binary が regular file で bytes sha256 一致 | `output/env/pegasus/binaries/7cdf0dc345f7…274a4` (701,760 bytes、`place` の配置物) | 通過 |
| 8 | build receipt が tracked・sha256 一致・strict 検証 (`validate_portable_binary_record(expected_policy=None)`)・`binary_sha256` 一致・`subject.trace` false | `output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json` (sha256 `760287f6…`) | 通過 |
| 9 | calibration admission (`load_verified_calibration`、mode required)・accepted・saturation.records | 3 件とも ADMITTED、records 1,000,000 / 1,000,000 / 2,000,000 | 通過 |
| 10 | cell ⇔ calibration の exact 一致 (env_tag / threads / clocks / workload / records) | pegasus / 48 / 2100 / `{rmw 0, rratio N, skew 0.9}` / records | 通過 |
| 11 | `source_commit` ≠ HEAD かつ HEAD の真の祖先 | `ad12ba35b` (spec commit `3ec30125f` の親) | 通過 |

`place` (`b4_binary_record.py place`) は `store_binaries` を経由し、record の validator・現行 policy 一致
(`949ddcc2…`、T-2697 時点と同じ)・source sha256・書込後 sha256 を通して rc=0 で
`output/env/pegasus/binaries/<sha256>` を返した (`verbatim/place.out`)。配置物は `.gitignore:20` で ignored、mode 0744。

## 実走の記録 (すべて login node、計算ノード job なし)

| 走 | rc | 観測 |
|---|---|---|
| `place` (record → worktree) | 0 | 配置 path 1 行、stderr 空 |
| `--validate-only` rr95 | 0 | plan 150,223 bytes、`plan_sha256` `a8c037d8…`、stderr 空 |
| `--validate-only` rr50 | 0 | plan 150,223 bytes、`plan_sha256` `bc29ba11…`、stderr 空 |
| `--validate-only` rr5 | 0 | plan 147,743 bytes、`plan_sha256` `290a216a…`、stderr 空 |
| `--validate-only` rr95 (HEAD を `d587547b6` へ 2 commit 進めた後) | 0 | plan bytes は `3ec30125f` 時と byte 同一 |

plan の要約は `verbatim/plan-summary.txt`。各 spec で session 248 (窓ごと 124 = 62 標本 × 2 side)、測定 496
(candidate 248・reference 248)、`session_id` は `<window>.<pair>.s<sample:06d>.<side>`。これは事前登録 §11.2
「1 pair・1 セルあたり 248 side session・496 測定」の名目と一致する。plan 全文は job dir と捨て branch から
再生成できるので本書へは複製しない (placeholder の plan を正式 evidence と誤読させないため)。

`--validate-only` が login node で走るのは、`load_frozen_spec` + `make_measurement_plan` だけを呼び
`_assert_live_environment` (`run_window` 専用) を通らないため。`store_binaries` にも site gate は無い。
計算ノード・新規 Pegasus 実行体 (F660) は要らなかった。

## 負対照 5 本 — binder の各検査が実際に拒否した (gate・test は足していない)

| 対照 | 操作 | rc | 落ちた検査 (stderr 末尾、`verbatim/negative-*.err`) |
|---|---|---|---|
| (a) | rr95 の `--expected-sha256` 末尾 1 桁を `3`→`4` | 1 | `frozen spec sha256 不一致: expected=…c144, observed=…c143` |
| (b) | rr95 spec に改行 1 byte を追記 (未 commit)、実 sha256 を expected に渡す | 1 | `frozen spec が loaded HEAD tracked blob と byte 一致しない` |
| (c') | `source_commit` を HEAD の祖先でない `3201227dd` に替えた spec を commit (`b84275b6`) | 1 | `provenance.source_commit が loaded HEAD の祖先でない` |
| (d) | 配置 binary を job dir へ一時退避 | 1 | `binary b4-candidate を lstat できない: …/binaries/7cdf0dc3…: No such file or directory` |
| (e) | 出力 relpath の dir を存在しないものに替えた spec を commit (`d587547b6`) | 1 | `output[0].parent を lstat できない: …/precheck-placeholder-t2288-missing-dir` |

(b) は `git checkout --` で復元し sha256 が `73da760f…c143` に戻ることを、(d) は退避物を戻して sha256・mode 0744 が
不変であることを確認した (DW-O19)。brief が挙げた「(c) `source_commit` == HEAD」は実走していない — spec は tracked
file なので自分を含む commit の hash を自分に書く不動点になり、正規の手順では到達できない。driver の同一 commit 拒否は
その不動点を機械的に塞ぐ belt-and-braces であり、代わりに到達可能な (c') を実走した。

## 凍結 wave への注意点 (本 precheck で実測した順序と落ち方)

1. **順序:** local main を取り込む → 使用する checkout で `place` (ignored なので checkout ごと、D2069 項 7) → 出力
   relpath の parent dir を checkout に用意する (git は空 dir を持たないので tracked file か spec と同じ dir に置く、負対照 (e))
   → spec を commit (`source_commit` = その commit の**親** = 直前の HEAD) → `--validate-only` を `--expected-sha256` =
   spec bytes の sha256 で実行。
2. **`source_commit` は spec commit の親を書く。** 同一 commit は構成上到達不能かつ拒否される。spec commit の後に
   commit が積まれても、spec blob が同じなら通り plan bytes も変わらない (HMAC 入力は `spec_sha256` で HEAD を含まない)。
3. **`place` は receipt の policy が現行と一致する record にしか効かない** (D2069 項 6)。本日 `949ddcc2…` で一致。
   policy を変える commit を取り込んだ後は再確認が要る。
4. **spec の置き場・命名 (`output/env/pegasus/floor-pair/…` と `spec-rr*.json`) は本 wave の placeholder であって
   先例ではない。** D1641 決定 3 が定めるのは成果物 (窓・summary) の命名 (env_tag・protocol・threads・workload・campaign
   識別子) だけで、spec path は凍結 wave の決定である。
5. candidate と reference は別 `artifact_id` が必須で、同じ binary path・sha256・receipt を指してよい (D2069 項 1)。
   本 precheck は `b4-candidate` / `b4-reference` の 2 entry で通した。
6. 3 spec は cell が 1 つずつで、各 spec の `provenance.calibration` は当該 workload の較正 1 件を指す
   (D2089「各 spec は 1 cell」。1 spec 複数 workload は binder が拒否する — 2026-09-09 の [T-2288] cellset wave の実測)。

## 主張しないこと

- **凍結時の成功を保証しない。** A-5 の実値 (窓・campaign_id・seed・relpath・実行設定) は未起草で、本 precheck は
  それらを placeholder (2030 年の窓、`precheck-placeholder-*`、ゼロ seed、`timeout_s 600`、`probe_timeout_s 30`、
  `numactl_argv []`、`extra_env {}`) で埋めて通しただけである。実行設定の値は plan には効かないが `run_window` には効く。
- **`run_window`・`finalize`・issuer・材料レポートへの接続は実行していない。** 通したのは loader と plan 生成まで。
- **placeholder spec・plan を凍結にも証拠にも使わない。** 捨て branch は land せず、bytes を本 insight に複製しない。
- **binder が正しいことを証明しない。** 通ったことと、5 本の負対照で拒否したことを観測しただけで、driver 自身の
  「証明していないこと」(module docstring) はそのまま残る。

## 捨て branch

`precheck-t2288-placeholder-specs` (起点 `ad12ba35b`)。commit は `3ec30125f` (3 spec) → `b84275b6` (負対照 c') →
`d587547b6` (負対照 e)。**land しない。** 削除はユーザー指示時のみ (本 wave は消さない)。再現は同 branch を
checkout し、`place` の後に `--validate-only` を `verbatim/placeholder-specs.sha256` の値で走らせる。

## 生証拠

| path | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親)。(P1)〜(P6) と段 1 前の棚卸し |
| `verbatim/s4-ruling.md` | 段 4 裁定 (親)。軽量版・子ゼロの根拠、main 取り込み、中止条件の判定 |
| `verbatim/place.out` | `place` の stdout (配置 relpath)。stderr は空 |
| `verbatim/placeholder-specs.sha256` | 3 spec の sha256 と record / binary の sha256 |
| `verbatim/plan-summary.txt` | 3 plan の要約 (schema・plan_sha256・session / 測定数・窓別件数・先頭 session) |
| `verbatim/negative-{a,b,c,d,e}-*.err` | 負対照 5 本の stderr (traceback 全文) |
| `verbatim/negative-{c,e}-spec.sha256` | 負対照 spec の sha256 |

`--validate-only` の stdout (plan 全文 3 本) と生成 script は job dir にだけ置いた (script は `.py` で実装面 suffix に
当たり、plan は placeholder)。

## 受入・検査

| 検査 | 結果 |
|---|---|
| `python3 tools/check_docs.py` | rc=0 (違反なし)。本記録 commit 前、wave 木 (main `ad12ba35b` + 本 insight + fragment) |
| `python3 tools/spool_fold.py --dry-run --show-diff` | rc=0。本 fragment は仮番号 (1596)、[T-2288] の `更新` は base digest `5a5b935f…` で適用 (実採番は land の fold が行う) |
| `python3 -m orchestrator.campaign.s8b_holdout_freeze search` (三軸語走査、27,078 file) | rc=0。本 insight に hit なし |
| 変異 matrix | 実装面差分 0 につき免除 (DW-S04) |
| 受入全走 | 本記録 commit を含む最終 tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない (受領証は job dir) |
