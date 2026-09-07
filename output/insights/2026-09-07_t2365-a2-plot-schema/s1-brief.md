# 段 1 brief — dev-wave-t2365-a2-plot-schema

base main `cf4273f5671ecda87c6f1b76148df239ce043ead`。Codex author = D95。

## scope

1. **[T-2365]** `tools/plotting/plot_a2_certification.py` を、現行 producer が出す新版成果物でも
   図を作れるようにする。凍結済みの旧 attempt (`certification-result/v3` + `raw-manifest/v3` +
   `cell-result/v2`) は従来どおり読める。
2. **[T-2364]** 新しい identity (D1644 の src_token 束縛) で A-2 attempt を取り直し、その成果物から
   図と新しい日付の results 節を作る。順序は 1 → 2 で固定 (図が作れないと取り直しの成果が使えない)。

scope 外: 仮想リスク向けの gate・検査・台帳・一般化の追加 (ユーザー明示)。
`full` certification の exact 再導出 ([T-2366])。partial 系 schema への図化対応。

## 確定済みユーザー裁定

- **D1644**: A-2 の canonical identity は pin + patch 束縛の src_token で計算する。**実装後に A-2 を
  新 attempt で取り直す。**
- **D1645**: 既完走の reject は内蔵 backoff の有効/無効を測っていた。正しい identity で取り直した
  attempt が出るまで A-2 の結論を論文素材から外す。訂正は追記のみ、bytes は変えない。
- **D1693**: 凍結物に束縛された golden を張り直すときは、凍結物の所定手続きで行い、過去結果と
  現行 policy の同一性がずれる旨を成果物へ明記する。

## 不変条件

- `output/insights/2026-08-24_paper-story-a2-certification/`、
  `docs/paper-story/figures/fig5_a2_certification_reject.*`、`docs/paper-story/results/*.md` は
  1 byte も変えない (絶対規律 7、D1631 の append-only)。
- **規律 2 を緩めない。** schema 対応は「新版も読む」であって「検査を外す」ではない。新旧いずれの
  経路でも bytes pin・identity 照合・crosscheck・fail-closed を通す。旧経路の受理集合は不変。
- `orchestrator/campaign/paper_story_a2_certification.py` の **.py 本体は t2341 系が予定編集面に
  挙げている**。触る必要が生じたら段 4 で再裁定する。
- AI 作業 provenance、fragment 経由の台帳記録、push 禁止は入口の正本どおり。

## 段 1 の実測 (親が実走、2026-09-07)

- plotter は schema 3 定数だけでなく `CANONICAL_SHA256` に凍結 2 件の SHA-256 を直接持つ。CLI から
  差し替えられず、python の kwargs だけが経路である (`plot_a2_certification.py:33-37,538`)。
  既定 path と既定測定 root も旧 attempt に固定されている (同 `38-41`)。
- caption の `GATE_NOTE` が「D1198 の条件関門は当てていない」を決め打ちしている (同 `43-45`)。
  新 attempt は関門を通すので、そのままだと**図が偽の文を載せる**。
- 現行 producer の schema は certification `v4`、full raw manifest
  `paper-story-a2-full-raw-manifest/v4`、raw cell `v3`
  (`paper_story_a2_certification.py:46-60`)。
- `materialize` は `tracked_destination` が既存だと拒否する
  (`tracked destination is not a fresh exact leaf`、同 `4452-4456`)。現行 policy の宛先は凍結済みの
  `output/insights/2026-08-24_paper-story-a2-certification` なので、**policy を変えずに取り直すと
  必ず失敗する。** これは起動時の引数が触れていない新事実である。
- `canonical_policy_path` は出荷 policy を A-2 と A-6 の 2 本に限定する (同 `304-316`)。3 本目を足すと
  .py 本体の編集が要る。
- `_protocol_preimage` は `tracked_destination` と `durable_measurement_base` を**含まない**
  (同 `290-301`)。宛先を変えても `protocol_sha256` は変わらない。変わるのは policy file の
  `bytes_sha256` だけで、pin は `orchestrator/tests/test_paper_story_a2_certification.py:1767-1770`。
- plotter の test は `plot.CANONICAL_SHA256` を dict 等価で pin し
  (`test_plot_a2_certification.py:405`)、凍結 caption が landed README と一致することも要求する
  (同 `443`)。

## (P1) 親の provisional 裁定・攻撃対象

- **(P1-1)** 取り直しの宛先は、既存 policy の `tracked_destination` を新しい insight dir へ改めて
  作る。3 本目の policy は足さない (.py 本体を触らずに済み、t2341 との編集面重複を避けられる)。
  `protocol_sha256` は不変なので、張り直すのは policy の byte hash golden 1 本である。
- **(P1-2)** plotter の bytes pin は CLI 引数で渡せるようにし、未指定時の既定は現行の凍結 2 件の
  ままとする。pin を「省略できる」形にはしない。
- **(P1-3)** `GATE_NOTE`・`CELLS`・`WORKLOADS`・既定 path は成果物から導出する。決め打ちを残さない。
- **(P1-4)** 対応する新 schema は full 系 (`certification/v4` + `full-raw-manifest/v4` + `cell/v3`) に
  限る。取り直しは 4 cell 揃った full を出す前提である。

## 成果物の形

plotter の改修 + test 追加、新 attempt の materialize 済み insight dir、新しい日付の図一式
(`.png` / `.pdf` / `.provenance.json`)、新しい日付の results 節、spool fragment 一式。

## 分割方針

実装子 2 系統。A = plotter 本体 + `test_plot_a2_certification.py`。
B = policy の `tracked_destination` 変更 + `test_paper_story_a2_certification.py` の golden 張り直し。
編集 file が交わらないので並列でよい。

## 受入・実測環境

受入全走は計算ノード。A-2 attempt は login から
`tools/pegasus/submit_paper_story_a2_certification.sh --attempt-id <新 ID>`、
job は `gen_S` / walltime `06:00:00` を 2 workload。durable base は policy の
`durable_measurement_base` が固定する。
