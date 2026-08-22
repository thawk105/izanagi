# 段4 裁定 — [T-646] floor_protocol.json master_seed TOCTOU

## 裁定サマリ

| 所見 | 裁定 | 根拠 |
|---|---|---|
| P1: 主経路 (`run_campaign`/CLI) の TOCTOU | **refuted (再現しない)** | commit `cca78d3d` (2026-08-17) で既に fail-closed 化。lens A/B とも崩せず |
| P2: `s8b_holdout_freeze.py:1348-1378` の raw working tree 読込み | **real、採用** | 段2 codex 発見、親が独立追試、lens A/B とも崩せず |
| lens A 所見 4.1〜4.3 (fix 実装の HEAD-commit 未検証・mode 未検査・replace object 未衛生化) | **real だが本 wave scope 外、backlog へ送る** | 既存 `_blob_at_head`/`head` 捕捉 (`s8b_holdout_freeze.py:280-330,1687-1689`) が測定closure等 4 箇所で共有する既存の弱さであり、本 fix が新たに導入するものではない。DW-G02 (初回blockerの限定)・DW-G03 (族一般化には独立2例)・研究最優先方針により今回は見送る |
| T-647 | **scope 外 (ユーザー指示)** | 独立の未裁定論点 |

## P1 の根拠 (real/refuted 判定に使った一次資料)

- `orchestrator/campaign/s8b_floor_campaign.py:5588-5625` `_require_supplied_protocol_authority`
  が `run_campaign` (`:5672-5675`) から無条件で呼ばれ、`resolve_current_floor_protocol`
  (`:889-896`、HEAD の git blob 由来) と供給 protocol の document/bytes/sha256 を突合し、
  不一致は `_run_campaign_core` (副作用開始点、`:5676-5688`) より前に `FloorCampaignError`
  で拒否する。
- 実測: `$CLAUDE_JOB_DIR/tmp/repro_t646.py` (使い捨て、repo 非追跡) で commit 済み protocol
  (master_seed=A) の working tree だけを commit せず master_seed=B へ書換え、本物の
  `load_protocol`→`validate_protocol`→`run_campaign` を通したところ
  `FloorCampaignError: ... document mismatch; bytes mismatch; sha256 mismatch` で拒否、
  `out_root.exists() == False` (副作用ゼロ) を確認。
- 実測 (非破壊): 本物の repo (`root=ROOT`、HEAD=main) に対し
  `resolve_current_floor_protocol(root=ROOT)` を実行し、`external/ccbench` gitlink 解決・
  複数候補の曖昧性解消・`env_tag` contract lookup を含む実経路が現に成功することを確認
  (resolved path = `output/s8b-freeze/floor-protocols/e576e9cd...--511c9538....json`,
  commit_oid = `0199afaa61...`)。lens B が指摘した「scratch fixture の一般化可能性」を
  この非破壊実測で追加裏取りした。
- `s8b_ratified_freeze.py:1666-1688,3126-3135` `_capture_g_h_worktree` は generation commit
  blob (G) / validation HEAD blob (H) / working tree bytes の三者一致に加え、generation record
  の pinned sha256 との四者目の一致まで要求する (campaign 経路より厳格)。親が直接読んで確認。
- `s8b_holdout_admission.py:607-666,1199-1225` `_authority` は resolver 経由で HEAD blob を
  再取得し、`build_schedule` に渡す `fixed_protocol` は blob 由来の `protocol_document` そのもの
  (raw 供給値ではない) である。親が直接読んで確認。
- `tools/pegasus/floor_campaign.sh:1160-1186` (実 PBS job) も `resolve-current-protocol`
  サブコマンド経由で `PROTOCOL_PATH` を得ており静的パス直渡しではない。`:731-745` で
  `CURRENT_COMMIT == receipt.source_commit` も別途検査済み。dirty 検査 (`:765-774`) が
  `output/` を除外するのは事実だが、上記の別経路が同じ攻撃を独立に閉じている。
- `build_schedule` (master_seed 消費点) の全 production caller を sink 側から検索
  (`grep -rn "build_schedule(" orchestrator --include=*.py`、test 除く) し、floor protocol
  namespace の4経路 (campaign / ratified_freeze / holdout_admission / holdout_freeze) を
  網羅した。`s8b_holdout_admission.py` はパス文字列を直接参照しないため path-literal grep
  では見つからない (resolver 関数呼出しのみ) と判明— lens B の「exact literal grep は別名
  consumer を検出しない」指摘は妥当であり、sink 関数検索で閉じた。

## P2 の根拠と fix 仕様

`s8b_holdout_freeze.py:1362-1378` (`_validate_floor_inputs`) は working tree の
`floor_protocol.json` を `_capture_regular_nofollow` で raw 読込みし、`validate_protocol`
(shape 検証) と `protocol_sha256 != protocol_raw_sha256` (bytes と canonical 再直列化の
自己整合性検査) だけを行う。**どちらも git-commit への束縛ではない。** working-tree-only
mutation (T-646 と同型) は検出できず、`:1444-1447` の `build_schedule` が改変
`master_seed` を消費し、`build_v2_g1_candidate` (`:1681-1718`) の g1 candidate へ波及する。

同一ファイル内の `measurement_closure` (`:1650-1664`)・`known_axes_freeze`/`generator`/
`design_source` (`_v1_source_record_at_head`、`:1668-1678`) は同種の `head` 束縛
(`_blob_at_head`、`:319-330`) を既に使っており、floor protocol の読込みだけがこの
idiom から漏れている。

**fix (Codex `role=author` へ渡す仕様):**
1. `build_v2_g1_candidate` が既に捕捉している `head` (`:1687-1689`) を `_validate_floor_inputs`
   の必須 keyword-only 引数として渡す (`_validate_floor_inputs` 内で HEAD を再捕捉しない —
   再捕捉すると `head` 捕捉と working tree 読込みの間に新たな race を生む。lens A 指摘)。
2. `protocol_raw = _capture_regular_nofollow(...)` (`:1362-1364`) の直後、
   `_strict_load_object_bytes`/`validate_protocol` (parse) より前に、既存 `_blob_at_head`
   (`:319-330`) で `head:FLOOR_PROTOCOL_REL` の blob を取得し、`protocol_raw` と
   byte-exact 比較する。不一致は `FreezeError` で fail-closed 拒否する
   (`build_schedule` `:1444` および candidate 書込み `:1854` 付近より確実に前)。
3. 比較には既存の `_blob_at_head` をそのまま使う (`s8b_floor_campaign.py` 相当の
   commit-verify・exact-mode・replace-object 衛生化は**今回は追加しない** — 既存 4 箇所と
   実装を不揃いにしない。理由は上表参照)。
4. **正例 (壊してはいけない):** 正当な reseal 直後、working tree の
   `floor_protocol.json` bytes が新しい HEAD commit の blob と一致する場合は今までどおり
   受理される。
5. **禁止する変異の署名:** 「working tree の `floor_protocol.json` bytes が captured HEAD の
   blob と異なるのに `_validate_floor_inputs` が例外を出さず先へ進む」を禁止する。
6. テスト: (a) working tree だけ書換え (commit しない) → `FreezeError`、副作用ゼロ
   (candidate 未生成) を確認する回帰、(b) 正当な reseal 後は従来どおり成功する正例、
   (c) 対象は `orchestrator/tests/test_s8b_holdout_freeze.py` (`build_v2_g1_candidate` 経由。
   `_validate_floor_inputs` を直接呼ぶ既存 test は無いため private 呼出し規約破壊なし)。

## 変異事前登録 (DW-M01)

- 位置: 上記 fix 2 で挿入する `if protocol_raw != head_raw: raise FreezeError(...)` 相当の
  1 分岐。
- 前後に同じ入力を拒否する層が無いこと: 既存 `protocol_sha256 != protocol_raw_sha256` 検査は
  「読んだ bytes 自身の内部整合性」のみを見ており、working-tree-only mutation (内部整合な
  改変 JSON) は通過するため重複拒否ではない (親確認済み、上記根拠節)。
- 無効化時の赤理由: 新設回帰テスト (b) の working-tree-only mutation ケースが
  `FreezeError` を期待するところ、無効化後は candidate 生成が成功してしまう1点に絞れる。
- 過剰拒否の正例 (承認外の過剰拒否検出): 正当 reseal 直後の成功ケース (fix仕様4) を
  変異 harness の SURVIVED 側 anti-example として同時に登録する。

## scope 外・backlog 送り (記録用、今回は実装しない)

lens A 所見 4.1〜4.3 (HEAD が commit である保証がない、HEAD tree entry の exact mode 未検査、
git replace object 未衛生化) は `s8b_holdout_freeze.py` の `_blob_at_head`/`head` 捕捉
(`:280-330,1687-1689`) 共有の既存弱点であり、`measurement_closure`/`known_axes_freeze`/
`generator`/`design_source` の既存 4 箇所にも及ぶ。本 wave の fix はこの既存 idiom を
そのまま再利用するだけで新たな弱点を導入しない。攻撃には repo への特権的な git 操作
(replace object 設定・HEAD を非 commit へ向ける等) が要り、T-646 が想定する「working tree
だけの誤編集/事故」よりはるかに強い脅威モデルである。DW-G02 (初回サイクル前の hardening は
correctness を実際に変える欠陥だけ blocker)・DW-G03 (族一般化には独立2例、本件は同一ファイル
内の再発だが repo 全体での独立2件目ではない)・2026-08-12 ユーザー方針 (研究最優先・
プロトタイプ基準、防御的堅牢化は既定で見送り) に従い、新規 carry 項目として次の一手へ
記録するに留め、実装は見送る。
