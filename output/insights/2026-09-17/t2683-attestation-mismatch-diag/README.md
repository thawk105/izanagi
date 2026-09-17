# [T-2683] T126 attestation の不一致で比較行を失敗時の診断 sidecar へ残した

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-t2683-attestation-mismatch-diag`
- 基準 commit: `abc7085ae6e1a69dc294c4f827ed7949e6df5305` (local main、wave 開始時) → 段 4 直前に main `b4631a92ee57227e9d1d13227896f723895bce35` (docs のみ、第 20 回 rulings の fold) を ff で取り込んだ
- 実装 commit: `1444d5030808d1c74625d0633e8eb0eb0952281b` (Codex `role=author`、2 file、+377/−9)
- 起票: worklog archive `docs/archive/worklog-phase3-0916-1540.md` の [T-2683] 項 (T-541 wave の段 6 レビュー A の real 所見)
- 裁定: D2104 項 14 (規律 3 の射程、局所修正、新 gate なし、受理集合不変) と項 15 (成功時の receipt は書かない)。wave 開始時は branch `worktree-rulings-all-20260917` の fragment (placeholder) で、段 4 直前に main で D2104 として fold 済みを確認した
- 設計判断: 本 wave の decisions fragment (slug `t126-attestation-mismatch-sidecar`、D 番号は land の fold が付ける)
- job dir (prompt・log・patch・変異 container の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2683-attestation-mismatch-diag/` (prompt・子出力の逐語は本 dir の `verbatim/`)

## 何をしたか

T126 資格判定 driver (`orchestrator/qualification/t126_driver.py`) の attestation が不一致で終わるとき、
`env_attestation.compare_profiles` が返す比較行 (field / expected / observed / verdict) は `_attest` が固定文言の
`QualificationDriverError` に畳み、fork した子は `os._exit(31)` で file を 1 つも残さず、`run_series` の
`fsm.reject("attestation", …)` には stage / type / message しか渡らなかった。

- `_attest` は不一致 (空比較を含む) で `AttestationMismatchError(QualificationDriverError)` を上げる。message は現行の
  全文 `attestation comparison contains a mismatch` のまま (既存 test の `match=` と型を維持)。比較行の全行・expected /
  observed profile の sha256・projection schema を属性に持つ。比較の述語 (非空かつ全行 pass) と probe 例外の包み方は不変。
- 子側処理を module-level `_run_attestation_child(*, repo_root, contract, capability, relative, stage, round_index) -> int`
  に抽出した。不一致時だけ accepted path の隣に `{stage}-{n}.mismatch.json` (schema
  `t126-qualification-attestation-mismatch/v1`、`status: rejected`、stage / round_index、両 sha256、projection schema、
  `comparisons` = 無加工の全行、`failed_fields` = verdict≠pass の field 名) を既存の `create_json` (create-only) で 1 つ
  書いてから `RC_ATTESTATION` (31) を返す。成功時は従来と同じ payload を同じ path へ書き (bytes 不変)、sidecar は
  書かない。診断の書込み失敗・create-only 衝突・probe 例外では sidecar を書かず rc=31 のまま (D474)。
- closure の子分岐は `os._exit(_run_attestation_child(...))`。親の非ゼロ終了分岐は
  `_attestation_rejection_message(*, capability, relative, attempt_dir)` で、sidecar が実在すれば
  `attestation child rejected; diagnostic=<attempt 相対 path>; failed_fields=<JSON list>`、読取り不能・形不正は
  `failed_fields=unavailable`、不在なら従来文言。例外は外へ出さず、表示以外に使わない。
- `run_series` の reject evidence の key 集合 (stage / type / message)、`verify()`、成功 series の evidence manifest、
  `attestation_records` (未使用)、`execution_guard.py` は非接触。新しい gate・validator・schema file 登録は無い。

## 依頼の前提のうち覆った点 (段 1 実測 → 段 4 P1、段 3・6 の 4 本が反証せず)

依頼は「呼び手 (`execution_guard.py:612`、`t126_driver.py:459`) が捨てずに」と 2 箇所を名指したが、
`execution_guard.attest_and_build_receipt` は 2026-07-19 (commit `950757e20a`) から非 pass 行を `json.dumps` で例外
message に載せており、production 呼び手 4 本 (`loop.py:187`、`s8b_oracle_driver.py:968/1147`、`screening_driver.py:336`、
`s8b_floor_campaign.py:7379`) は `str(exc)` を伝播する。floor campaign は失敗時に出力 root を作らないことを
`test_required_attestation_comparison_failure_has_zero_side_effects` で固定しており (開始前・副作用ゼロ)、file の
sidecar は既存契約と衝突する。捨てていたのは T126 driver だけ。段 3 レンズ A は「正規比較値に非 JSON 型が来て
`json.dumps` が別例外に化ける経路」を探し反証 (schema_v2 の型検査、cache / NUMA は `dataclasses.asdict`)、レンズ B は
呼び手 4 本の message の到達先 (stderr traceback / CLI stdout JSON / session の `deviation.message`) を辿り、捨てる経路は
無いが永続保存は外側の実行環境に依存すると限定した。**execution_guard 側は変更なし。** 開始前拒否の比較行の永続保存は
裁定パッケージ候補として worklog fragment に新規起票した。

## 段 3・段 6 の所見 (逐語は `verbatim/`)

- 段 2 plan (`s2-plan.md`): driver 7 hunk + test 2 hunk、新規 test 10、変異 M1〜M9 + E1。留保 1 = `create_json` は fsync
  するので D474 の「fsync しない」とは一致しない。
- 段 3 レンズ A (`s3-lensA.md`、正しさ境界): real 3 / refuted 6 / must-fix 2。A2 (fsync stall で timeout 文言に化ける・親の
  同期読取りも stall しうる) → scope 外、限界として D に記録。A8 (親 brief の「live 比較なし」は一般化しすぎ —
  `_identity_files` の HEAD blob 比較・prologue hash・wrapper の hash 採取は live 照合) → brief を訂正 (新規実走は変更を
  含む commit・source stage を要する通常運用、過去 attempt は記録 commit の blob で verify されるので無効化されない)。
  A7 (E1 の等価は helper 挙動に限る) nit。P1・P4 は反証されず維持。
- 段 3 レンズ B (`s3-lensB.md`、整合・実効性): real 2 / refuted 5 / must-fix 2。B1 (helper 直呼び test は production
  配線を証明しない — closure が helper を呼ばない変異が生存する) → AST 配線 pin + 実 `os.fork` の helper test を採用し、
  配線変異 M10・M11 を登録。B2 (SIGKILL 後に create-only の staging file が残り collector の「abandoned staging bytes」
  拒否で failure receipt が発行できない) → accepted payload の `create_json` に元からある窓と同型、scope 外・限界記録。
  読み手不在 (refuted: sidecar は failure receipt の `closure_manifest` に入る) → collector `_manifest` の consumer 正例
  test を採用。
- 段 4 裁定 (`s4-adjudication.md`): 所見ごとの real/refuted・採否、plan v2 (T3 AST pin、T4 実 fork、T5 collector)、
  変異 M1〜M11 + E1 の事前登録と DW-M08 の報告枠 (境界 = M2 / M6 / M9、診断 pin = 他 8 件)、裁定パッケージ候補 2 件。
- 段 5 author (`s5-author.md`): 2 file、13 test 関数 / 24 case。sandbox では hook 拒否 + `qstat -Q` preflight rc=1 で
  pytest 未実走 (closed と申告せず)。
- 段 6 レビュー A (`s6-reviewA.md`): must-fix 0 / GO。nit 3 = AST pin が分岐所属・引数を見ない、`Path.exists` の全体
  patch、M1/M5 の赤は strict loader 例外 (明示 assertion の前)。
- 段 6 レビュー B (`s6-reviewB.md`): must-fix 0 / GO。nit 1 = AST pin の引数・分岐 (A と同じ)。配線・fork・台帳契約・
  collector・構造 pin・報告と実体の一致は refuted。
- 段 6 fix (`s6-fix.md`、test file のみ): AST pin を `if is_child:` body 直下 + keyword exact + 非ゼロ分岐 body 直下 +
  keyword exact へ補強、`Path.exists` は `.mismatch.json` だけ失敗させ他は委譲 + `monkeypatch.context()`、M1/M5 の
  killer に `assert sidecar.is_file()` を読取り前に追加。既存 assertion 不変。

## 親の実走 (すべて計算ノード dispatch、`python3 tools/run_tests.py`)

| 走 | 対象 | 結果 |
|---|---|---|
| 焦点走 1 (段 5 直後、2747.nqsv) | 変更 test file 単独 | 65 passed、4.90 s |
| 焦点走 2 (commit 前、2751.nqsv) | consumer 7 file (pegasus_tools / qualification_artifacts / campaign / official_perf_closure / artifact_admission / env_contract / ccbench_spawn_sites) | 32 failed / 1155 passed / 3 skipped — 赤 32 件はすべて `test_campaign.py` の `contract-loader-drift: disk bytes が記録 commit blob と不一致: orchestrator/qualification/t126_driver.py` (未 commit の identity file、既知の型、回帰ではない) |
| 焦点走 3 (fix 後、2764.nqsv) | 変更 test file 単独 | 65 passed、4.98 s |
| 焦点走 4 (実装 commit 後、2783.nqsv) | campaign / t671_source_binding / pegasus_tools / qualification_artifacts | 1062 passed / 3 skipped、46.65 s (drift 赤は消えた) |
| provenance full (実装 commit 後) | 導入 commit〜HEAD | 10,910 件、新規違反なし |
| 受入全走 | docs commit 後に `tools/dev_wave_wait.py acceptance` で投入 (`child-green` だけが受領証になり、land が tested tip と照合する) | 受領証は job dir |

## 変異 matrix

container worktree `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2683-attestation-mismatch-diag/mutation-tree` (実装 commit
`1444d5030` の detached worktree、submodule 再帰初期化済み) に `tools/mutation_harness.py --runner-mode dispatch --detached`
を直接当てた (wrapper の共有木検査は並行 wave 下で成立しないため)。runner は `python3 tools/run_tests.py --force-dispatch`
+ 変更 test file 1 本 + `-q -rf -p no:cacheprovider`。D612 の queue-wait / grace 上書き 1800 / 600。spec と台帳は本 dir の
`mutation-spec-probe.json` (sha256 `9862afa9…`) / `mutation-ledger-probe.json`、`mutation-spec-final.json` (sha256
`9c387192…`) / `mutation-ledger-final.json`。

- probe 走 (全件 SURVIVED 登録、観測 node を集める): baseline PASSED、M1〜M11 は全部 MISMATCH (= 赤 node を観測)、E1
  SURVIVED。観測 node は段 4 の静的予測と一致 (M1 は 11 node だが赤理由は「sidecar 不在」の 1 つ、M6 の 4 node 目は
  create-only 衝突経路の rc)。観測 node を本走 spec の `expected_nodes` へそのまま写した。
- 本走: **baseline PASSED (27.7 s)、M1〜M11 すべて KILLED で期待 node と観測 node が完全一致 (matching 12/12)、等価変異
  E1 (docstring だけ) は SURVIVED、MISMATCH 0、TIMEOUT 0**。全変異の anchor は 1 箇所。走行後の container は clean・HEAD
  `1444d5030` を親が確認した。所要は 13 run で 377 s (queue 待ち除く)。
- DW-M08 の報告枠: **受理集合 / fail-closed 境界 3/3 KILLED** (M2 成功時にも sidecar → 2 node、M6 書込み失敗時の rc 31→34
  → 4 node、M9 reader 例外の再 raise → 4 node)、**診断感度 pin 8/8 赤** (M1・M3・M4・M5・M7・M8・M10・M11)。

| ID | 変異 (single-site) | 枠 | 赤 node 数 | 主な killer |
|---|---|---|---|---|
| M1 | mismatch 分岐の `create_json` を削除 | 診断 pin | 11 | `mismatch_preserves_all_comparison_rows` (実在 assertion)、他 10 本 (sidecar 不在の単一理由) |
| M2 | 成功時にも `.mismatch.json` を書く | 境界 | 2 | `match_preserves_accepted_bytes_without_sidecar[pre-round-1 / post-series-None]` (専属) |
| M3 | `failed_fields` を常に `[]` | 診断 pin | 4 | `mismatch_preserves_all_comparison_rows`、`parent_message_names_…` ×2、`forked_child_…` |
| M4 | `comparisons` を非 pass 行だけに | 診断 pin | 1 | `mismatch_preserves_all_comparison_rows` (専属) |
| M5 | 空比較では sidecar を書かない | 診断 pin | 1 | `empty_comparisons_writes_rejected_sidecar` (専属) |
| M6 | 汎用失敗の return を 34 | 境界 | 4 | `sidecar_write_failure_preserves_rc` ×2、`probe_failure_has_no_sidecar`、`existing_sidecar_is_not_overwritten` |
| M7 | 汎用失敗でも空 sidecar を書く | 診断 pin | 3 | `probe_failure_has_no_sidecar`、`sidecar_write_failure_preserves_rc` ×2 (2 度目の試行を検出) |
| M8 | 親 message helper を固定文言化 | 診断 pin | 6 | `parent_message_names_…` ×2、`…unreadable_sidecar…[json/shape/read]`、`forked_child_…` |
| M9 | reader の例外を再 raise | 境界 | 4 | `…unreadable_sidecar…[json/read]`、`…ledger_contract[unreadable-pre-round / -post-series]` |
| M10 | production の raise を固定文言に | 診断 pin | 1 | `run_attest_closure_wires_…` (AST、専属) |
| M11 | closure 子分岐を旧インライン処理に | 診断 pin | 1 | `run_attest_closure_wires_…` (AST、専属) |
| E1 | helper の docstring 1 語 | 等価対照 | — (SURVIVED) | — |

## 残存限界・scope 外 (記録のみ、decisions fragment の「射程」と同じ)

- `create_json` は fsync する。stall は子の `attestation_cap_s` timeout に入り mismatch 文言が timeout 文言に置き換わる。
  子が SIGKILL されると create-only の staging file が残り、collector の staging 拒否で failure receipt が発行できない。
  accepted payload の `create_json` に元からある窓と同型 (mismatch 経路の露出が accepted 経路と同数になるだけ)。外側
  wrapper の timeout (rc=124) も保証外。裁定パッケージ候補 1 (推奨 = 現状維持)。
- 比較行と 2 つの sha256 だけでは、凍結 profile 全体・照合時 policy を含む自己完結の再計算 (D2056 決定 5 相当) は
  できない。主張は「比較時の全行と判定値の保存」に限る。
- `run()` 全体を通す E2E test は attempt bootstrap 全体を要するため作っていない。配線の保証は AST pin + 実 fork の helper
  test まで。
- 開始前・副作用ゼロで拒否する execution_guard 経路の比較行は例外 message (stdout / stderr) にしか残らない。裁定
  パッケージ候補 2 (推奨 = 行動なし)。
- driver bytes が変わるので新規 T126 実走の code identity・series ID・prologue hash は変わる (通常運用: 変更を含む commit と
  source stage が要る)。過去 attempt の `verify()` は記録 commit の blob で照合するので無効化されない。歴史 snapshot の
  hash 記録 (fixture lock・insight json) は更新しない (規律 7)。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` は `git diff --check` に触れる行末空白 (Codex 出力の Markdown 二重空白改行) を除き、末尾改行の
無い file には改行を 1 byte 足してある。可視文字は不変。原文 bytes は `verbatim/originals.json` (sha256
`ffdb4fff019bf07c0f56fcfc91f0778598ccde6de22009d74a2990ee9cf89cd0`) に UTF-8 text として収め、各 `text` をそのまま
書き出せば原文 bytes を復元できる。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `s1-brief.md` | 5301 | `c5923d065fef4a82…` | 0 (末尾の空行 1 行を除いた) | 5300 |
| `s2-plan.md` | 17296 | `8012737ca98c8101…` | 6 | 17285 |
| `s3-lensA.md` | 11567 | `ad886a7e8f96b4c6…` | 0 | 11568 |
| `s3-lensB.md` | 14575 | `f25238aa3af33657…` | 0 | 14576 |
| `s4-adjudication.md` | 9580 | `50a87fe1a1d0fc01…` | 0 | 9580 |
| `s5-author.md` | 4673 | `8b76cd6b84bd3953…` | 0 | 4674 |
| `s6-reviewA.md` | 12028 | `651e01143c7e1eb4…` | 11 | 12007 |
| `s6-reviewB.md` | 9894 | `9a8b62c8d8c0c635…` | 9 | 9877 |
| `s6-fix.md` | 2300 | `87db1afc30015bd3…` | 0 | 2301 |
| `prompt-plan.md` | 5685 | `38f565f6151e6370…` | 0 | 5685 |
| `prompt-consult-A.md` | 5792 | `8fd9e272ad44fe36…` | 0 | 5792 |
| `prompt-consult-B.md` | 6312 | `b16b01b72ccb658d…` | 0 | 6312 |
| `prompt-author.md` | 9871 | `e32e9a5a717a1f62…` | 0 | 9871 |
| `prompt-review-A.md` | 4924 | `5708b6189b3340a8…` | 0 | 4924 |
| `prompt-review-B.md` | 5478 | `c87ef949d4c9e728…` | 0 | 5478 |
| `prompt-fix.md` | 4536 | `e0a27e39326d2a34…` | 0 | 4536 |

三軸語・placeholder の機械走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc=0、本 wave の file に
hit なし。
