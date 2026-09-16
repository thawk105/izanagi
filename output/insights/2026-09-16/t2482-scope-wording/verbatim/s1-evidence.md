# 段 1 brief — [T-2482] campaign_verifier_epoch の保証文言を現物の被覆範囲へ合わせる

wave: dev-wave-t2482-scope-wording / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2482-scope-wording
基準: local main e667c8c139004221723ee223b7d8f09fba5f9be1

## 研究前進と完了判定
材料レポート (oracle report・layer3・s1・p2_2・backoff sweep・critic digest) の `campaign_verifier_epoch.identity_scope` / `excluded_scope` が、実際に束縛する集合と違う集合 (62 path / 発見 131 / 未収載 69) を名乗る状態を止める。完了 = 2 定数が現物実測と一致し、live copy の test pin 2 か所が追随し、受入全走緑。

## scope (実アンカー)
| # | path:line | 変更 |
|---|---|---|
| A1 | orchestrator/campaign/artifact_admission.py:73-77 `CAMPAIGN_VERIFIER_EPOCH_SCOPE` | 数値と内訳を現物へ |
| A2 | orchestrator/campaign/artifact_admission.py:78-83 `CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` | 未収載数を現物へ |
| A3 | orchestrator/tests/test_artifact_admission.py:1160-1170 (test_real_e0_is_rejected_only_by_certified_epoch_gate の literal) | A1/A2 の独立 literal を追随 |
| A4 | orchestrator/tests/test_s1_9pair_figure_provenance.py:74-89 `CURRENT_E0_EPOCH` | live view の literal を追随 |
触らない: `PRE_T733_*`、`FROZEN_E0_EPOCH` (生成時凍結 receipt)、insight の歴史記録、記録済み `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/reports/layer3_report.json`、`CONTRACT_LOADER_RELATIVE_PATHS`、受理述語。

## 確定済みの裁定
- ユーザー直接指示 (2026-09-16、本 wave 引数): 文言修正であって verifier の対象拡大ではない。被覆を広げる仕事へ変えない。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。実装面は Codex author。
- D1651: 文言は path 数・推移閉包でないこと・未収載 module 数・非 import 委譲の除外・完全性非主張を書く。docstring は定数を参照するだけで再掲しない。
- D1884: 閉包が閉じるまで名乗りを広げない。
- D1896 (「D1884 実装単位で同時に直す。単独で先に直さない」) は上記ユーザー指示が上書きする。新事実: 収載 63 のまま発見集合が 2026-09-09→09-16 に 140→162 へ動いた。drift 源は収載の段階実装だけではない。

## 実測 (いずれも実物、模擬なし)
- 閉包寸法: T-2344 の probe 原本 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/probe_closure_v2.py` (sha256 e4843f31d68071568752140830e08c6791c45c16f427096497d2415571570fbf、repo の逐語 `output/insights/2026-09-09/t2344-closure-reachability/verbatim/probe-closure.md` のコード部と bit 一致) を新規に書かずに実行。
  - e667c8c13: 収載 63 / 発見 162 / 未収載 99 / 1 段展開 83 (未収載 20)。出力 job dir `closure-head-e667c8c13.json`。
  - 正例対照 2143a49c0: 63 / 140 / 77 で T-2344 記録 `closure-head.json` と一致。
  - 未収載の増分は +22 / -0 (2143a49c0→e667c8c13)。
  - `orchestrator/verifier/__main__.py`・`cli.py`・`orchestrator/verify.py` は発見集合 162 に含まれない (除外欄の別記は二重計上でない)。63 本目は T-2429 の `orchestrator/campaign/verify_fanout_worker.py` (発見集合の member)。
- 文言と digest: E1 preimage は `_CAMPAIGN_VERIFIER_EPOCH_DOMAIN` + path + blob だけ (artifact_admission.py:1056-1064)。scope 文字列は読み取り時の既定値で lock に記録されない。`CampaignVerifierEpoch.__post_init__` (:186-190) は定数との一致を検査する。
- 記録済み成果物で scope 欄を持つもの: repo `output/` (insight 除く) は 6f169f90 layer3_report.json の 1 本 (certifying_input=false、E0、2026-09-16 f47876014 保存、読む test なし)。外部実測定 root 23 dir の JSON は 0 本 (grep rc=1)。
- 文言を bytes 一致で照合する consumer: `autonomous_trial_completeness._require_compatible_layer3_epoch` (:4740-4757、記録済み layer3 の epoch を現行 validator と比較)。照合対象になる記録実物は上記の通り 0 本。
- `s8b_oracle_artifacts.validate_campaign_verifier_epochs` は scope を非空文字列としか検査しない (:181-184)。
- artifact_admission.py の bytes pin: B-4 事前登録の projection hash 欄は「未記入」(docs/phase3-b4-reflux-ablation-preregistration.md の表)。他は AST・関数名ベースか記録 commit の blob 照合で、凍結 pin は見つからない。収載 path なので未 commit 編集中は contract-loader drift で焦点走が赤になる (commit 後に走らせる)。
- 並行 wave [T-2483] (worktree dev-wave-t2483-exact62-historical-grammar、未 land) が `T733_EXACT62_CAMPAIGN_VERIFIER_EPOCH_*` に現行の旧文言を逐語複製して歴史 exact-62 用に追加中。編集 hunk は :91 以降と test :305 / :2904 付近で A1-A4 と重ならない。両者 land 後、A1/A2 を直さなければ歴史 exact-62 と現行 63 が同一文字列を名乗る。

## DW-O10 producer 棚卸し (出力 bytes が変わるもの)
s8b_oracle_report.py:582-617 (JSON)、layer3_report.py:332-333 (JSON)、s1_report.py:122-133、p2_2_report.py:107-108、backoff_sweep_report.py:103-104,169-170、s6_sort_sweep.py:613-614 (md)、s8a_trigger_sweep.py:718-719 (md)、critic/digest.py:1261-1262、artifact_admission.py:254 (例外 message)、tools/plotting/plot_backoff.py:358-359、tools/plotting/plot_s1_9pair.py:537-538。いずれも定数を参照し独自 literal を持たない。

## 不変条件
- E1 値・lock decode・受理述語・`CONTRACT_LOADER_RELATIVE_PATHS` を変えない。`__post_init__` の一致検査を残す (規律 2)。
- 新文言は旧文言より強い保証を読ませない (D1884)。数値の更新は未束縛部分を大きく見せる方向 (69→99) だけ。
- 記録済み成果物・歴史定数・凍結 receipt を書き換えない (規律 7)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 数値は日付と commit を付けた snapshot として書く (例: 「2026-09-16 (e667c8c13) に収載 tuple を起点として静的 import を辿った発見集合 162 module のうち 63 を収載」「同発見集合の未収載 99 module」)。将来また古くなるが、日付付きの測定事実として偽にならない。実行時計算などの機構は足さない。
- (P2) 除外欄へ「発見集合は収載 tuple から辿った集合であり、tuple から import で辿れない module (認証成果物の発行器を含む) を含まない」旨を 1 句足す。T-2344 の実測 (発行器起点 160、和 165) を根拠にした名乗りの限定で、保証は広げない。scope 外の追加と見るべきかを攻撃せよ。
- (P3) 収載の内訳は「T-733 の既存 24・明示 import 先 36・実行時 package 初期化 2」に「T-2429 の fan-out worker 1」を足して残す。内訳を落とす案との比較を攻撃せよ。
- (P4) D1896 を上書きする判断は段 7 で decisions fragment に残す。

## 成果物影響 (DW-G05)
放置すると上記 producer の出す材料レポートが、束縛していない「62 path」と「未収載 69」を名乗り、未束縛部分を 30 module 過小に見せ続ける。[T-2483] land 後は歴史 exact-62 と現行 63 の epoch が文面で区別できなくなる。

## 分割と環境
- 設計択一 (P1-P3) と正しさ防壁の exact 照合入力に触るので、段 2 plan・段 3 敵対 2 レンズ・段 6 レビュー 2 本を回す。実装子は 1 本 (A1-A4 の小差分)。
- 受入全走は `tools/dev_wave_wait.py acceptance` の既定経路 (worklog (1551) と同じ)。変異 matrix は実装差分があるので免除しない。

## 追加実測 (段 2 投入後、2026-09-16 18:45 JST)
- `closure-head-e667c8c13.json` の `edges` で `orchestrator/campaign/verify_fanout_worker.py` を target に持つ member は 0 本。`enrolled` の index 62 (末尾) に直接収載。
- 起動経路: `orchestrator/campaign/pipeline.py:836` の `"-B -m orchestrator.campaign.verify_fanout_worker "` (ssh 経由で兄弟ノードに起動する subprocess)。production で他に参照なし (git grep)。
- 収載 commit: 2a9ba783f ([T-2429]、2026-09-08) の本文「verify_fanout_worker: … campaign lock の enforcement closure に追加」。
- 含意: 63 本目は「明示 import 先」でも「package 初期化」でもなく、非 import (subprocess) 委譲先を明示収載したもの。現行 EXCLUDED_SCOPE の「subprocess … を含む非 import 委譲は本 map の外」は、この 1 本について事実と食い違う。

## 追加実測 2 (段 3 投入中、2026-09-16)
- T-2344 README「候補集合そのものの欠落」の表の 5 module を現行 `closure-head-e667c8c13.json` の `discovered` で照合:
  `s8b_oracle_report.py` 不在 / `s8b_abort_reason_contract.py` 不在 / `s8b_outcome_stage_contract.py` 不在 /
  `autonomous_trial_completeness.py` **在 (index 15、09-09 以降に入った)** / `b10_backoff_shape_sweep.py` 不在。
- 含意: (P2) は「発行器すべてが発見集合の外」とは書けない。「tuple から辿れない module (oracle report 発行器 等) を含まない」の形なら事実どおり。
- 段 2 plan の指摘 (妥当と判定): E1 不変は記録済み map に限る。artifact_admission.py は収載 path なので新規 lock の blob は変わる。62→63 は被覆記述の追随であり「弱める方向だけ」ではない。
