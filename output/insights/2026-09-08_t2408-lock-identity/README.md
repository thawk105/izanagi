# [T-2408] B-10 限定受理の事前登録 identity を campaign lock の記録値から取る

2026-09-08。branch `worktree-dev-wave-t2408-b10-lock-identity`。統合 commit `5930932de`、
main 取り込み merge `4417ab275` (固定 SHA `d78667615`)。裁定 D1771 (射程は D1597 のまま)。

B-10 の集約 (`--phase report`) は 3 workload とも CLI から到達不能だった。本 wave は、限定受理が使う
事前登録 identity を **live な事前登録文書ではなく campaign lock に記録済みの値**から取る形へ
3 系列そろえて変えた。受理集合の literal は増やさず、緩めたのは「live 文書と一致すること」だけである。

## 止まっていた理由は 3 つあった (すべて現物で実測)

1. erratum 適用後、発効版 commit `77b33e37d` の事前登録文書 blob は `ea910de3…`、現行は `cdd715c9…` で
   不一致。発効版を指すと `prereg-blob` で止まる。
2. 現行文書の identity は歴史 literal と全て別値である。spec `3448edfe…` (歴史 `9c594114…`)、
   patch `a5e0710c…` (歴史 `36cd974c…`)、formula `1205b1ff…` (歴史 `5b3d8dee…`)。
   現行 commit を指すと、歴史 record を現行 era の identity で発行しうる。
3. **裁定当時に見えていなかった 3 つ目。** 3 系列の現物 lock は
   `authority.contract_loader_blob_sha256s` の key が 24 個 (pre-T733 grammar) で、現行
   `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` は 63 path を exact に要求する。
   したがって `decode_campaign_lock` は 3 本とも必ず拒否し、`_assert_report_lock_binding` は
   `resume-binding` で止まる。読める入口は D1653 が新設した `decode_historical_campaign_lock` だけである。

**「歴史 blob を git から読み直して parse する」route は存在しない。** 発効版 blob の machine spec は
`izanagi-b10-backoff-shape-preregistration/v4` だが、現行 module は v5 を exact に要求するため
`parse_preregistration` が `machine spec schema_version 不一致` で失敗する。lock の記録値が唯一の源である。

なお worklog 1324 が書いた「現行 commit を指すと限定受理の binding が live prereg の値を使うため
lock の旧値と exact 比較で落ちる」は、**現行コードでは成立しない**。`_legacy_*_binding()` は
commit `91a5bfca3` (静的 backoff 上限の拡張) の時点で既に module literal を返す形へ変わっており、
引数の `Preregistration` を使っていなかった。

## 変更の形

- report 専用の identity 型と入口を足し、3 系列の lock から binding / spec / calibration を復元する。
  歴史 decoder を使い、通常 decoder (`campaign_lock.py`) は union にしない (D1653 の必須条件)。
- D1653 が必須とする**記録 commit blob の 24 path 照合**を、既存の
  `contract_loader_binding.verify_committed_contract_loader_blobs` で行う。新機構は作らない。
  これは `artifact_admission._verify_committed_loader_binding` が pre-T733 grammar に使っている経路と同じ関数である。
- **系列ごとに lock 全体の SHA-256 を literal で exact 比較する** (下記「敵対レビューが見つけた穴」)。
- `space_version` は歴史値 `b10-backoff-shape/v2` と exact 比較し、`trial` をその固定値と固定 spec digest から
  導出する。攻撃者側の入力から期待値を組み立てる形をやめた。
- report では live 文書・live patch・applied tree・現在の計測サイト contract を読まない。
  build 専用の binary path policy 検査は report の後段へ移した。
- provenance を `b10-backoff-shape-provenance/v2` → `/v3` へ上げ、測定時 identity (locked spec /
  calibration / 3 系列 binding / 歴史 space_version・formula・patch) と現行解析 identity を分けて記録する。
- 現物 3 系列の lock を `orchestrator/tests/fixtures/b10_backoff_shape_locks/` へ収載した。

**135 個の record digest literal と 3 つの digest 集合比較は 1 byte も変えていない** (両レビューが独立に確認)。

## 敵対レビューが見つけた穴と、閉じ方の選択

段 6 の 2 レンズが、lock を歴史 decoder に通しただけでは identity の真正性に届かないことを独立に示した。
現物 fixture を出発点に inner と outer を再 canonical 化すると、次がすべて通った。

- 3 系列そろえて `search_config.calibration` の値を改変する (系列間比較は攻撃者がそろえた値同士を見るだけ)。
- `space_version` と `trial` を対で改変する (stem しか固定していなかった)。
- 別系列の**実在する** authority と交換する (authority と workload / binding が結び付いていなかった)。
- 未検査の `search_config` key (`build_admission` の削除、`decision.alpha` の改変) を触る。

**親は個別の構造比較を足すのではなく、系列ごとに lock 全体の SHA-256 を pin する形を採った。**
理由は 3 つ。(1) 上の 4 型を一度に閉じる。(2) D1597 が名指しした「系列ごとの有限な内容 digest 集合へ
exact に閉じる」の形そのものである。(3) 個別の構造比較を足すと、その多くが digest 照合に含意されて
恒真になる (裁定 N1 の「恒真な述語を足さない」に反する)。
**この結果、raw lock 由来の既存 predicate と系列間比較は独立した変異防壁としては数えない。**
値の取り出し口と診断として残してある。

## 変異 matrix

`tools/mutation_harness.py --runner-mode dispatch --detached`、runner は
`tools/run_tests.py --force-dispatch orchestrator/tests/test_b10_backoff_shape_sweep.py -q -rf`。
HEAD `5930932de`。spec `mutation/mutation-final.json` (sha256 `e09b52e1fd7fdda019e176a6edb23b328b2dc9fe8572306059186fb5a6cfc86a`)。
probe (全件 SURVIVED 登録で観測 node を集める) → 本走の 2 段で行い、期待 node は probe の観測値を登録した。

**8 件すべて KILLED、期待 node と完全一致 (rc=0)。生存ゼロ。** 計算ノード上の baseline は `190 passed`。

| 変異 | 赤になった node 数 | 主診断 |
|---|---|---|
| M1 歴史 decoder を通常 decoder へ戻す | 11 | 現物 fixture の系列別正例 |
| M2 記録 commit blob の 24 path 照合を削除 | 1 | 偽造 authority の負例 |
| M3 binding の module literal 比較を削除 | 2 | 解析コード drift の負例 |
| M4 collector の系列 binding を交換 | 3 | collector 正例 |
| M5 locked calibration を厳密復元しない | 5 | 系列別正例と orchestration 正例 |
| M6 report へ live 事前登録を再導入 | 2 | orchestration 正例 |
| M7 locked spec digest 検査を削除 | 1 | spec drift の負例 |
| M8 lock 全体 digest 検査を削除 | 1 | 偽造 lock の負例 |

M2 / M7 / M8 は 1 node だけを赤にする (単一理由)。M8 の「space/trial を対で改変した偽造」部分だけは
F2 の exact 比較とも重なるため、M8 単独の帰属としては数えない。

## 限界 (主張しないこと)

- **`--phase report` の実走はしていない。** 計測サイトを要求するため login では起動できず、加えて
  この file 自身が `ANALYSIS_REL` であるため、編集を commit した状態で実走すると新しい binding 配下へ
  新しい report を発行してしまう。到達確認は `run_formal(phase="report")` の orchestration test までである。
- **この file を編集すると live campaign の identity は必ず回転する** (`analysis_code_sha256` が変わり、
  binding digest と campaign ID に伝播する)。実測では現に走っている B-10 campaign は無く
  (official campaigns の最終更新は 2026-09-05)、drain も resume 放棄も要らなかった。
  同じ性質は同 file を編集する他の wave にも等しく当てはまる。
- fixture 3 本は現物と byte 一致する snapshot であり、保証するのは byte 互換性だけである。
  対応する block record / receipt / WAL との結合までは保証しない。
- login node の焦点走では `test_t1905_a5_tmp_official_root_is_rejected_by_real_durable_policy` が赤になる。
  原因は別ユーザーが 2026-09-07 に作った `/tmp/.git` で、`/tmp` が repository 内と判定されるため
  (F457 の再発)。計算ノードでは 190 passed で緑になる。本変更に帰属しない。

## 逐語

- `verbatim/s1-brief.md` — 段 1 brief
- `verbatim/s2-plan.md` — 段 2 プラン (read-only codex)
- `verbatim/s3-sol.md` / `verbatim/s3-luna.md` — 段 3 敵対相談 2 レンズ
- `verbatim/s4-ruling.md` — 段 4 裁定 (プラン v2 と変異事前登録)
- `verbatim/s5-author.md` — 段 5 実装子の報告
- `verbatim/s6-sol.md` / `verbatim/s6-luna.md` — 段 6 敵対レビュー 2 レンズ
- `verbatim/s6-fix-ruling.md` — 段 6 fix 裁定
- `verbatim/s6-fix1.md` — fix 子の報告
- `verbatim/s6-refocus.md` — 段 6 焦点再レビュー (所見対応表)
- `mutation/` — 変異 spec と probe / 本走の台帳

## 並行 wave との調整

同じ file の WAL 読取側を [T-2409] (D1772) が並行実装していた。相手の実測により
「既存 2 系列の literal を再発行せずに追加 exact 条件として重ねられる」= 再発行 0 個と判明したため、
D1772 が定める「同じ変更単位で一度に行う」条件は成立せず、2 本を別単位のまま進めた。
編集面は相手が `_verification_source_disclosure` の内部、本 wave が限定受理の identity 側で分けた。
本 wave は `_collect_report_inputs` 内の `_verification_source_disclosure` 呼出しと戻り値の受け 2 行を
動かしていない (差分で確認済み)。
