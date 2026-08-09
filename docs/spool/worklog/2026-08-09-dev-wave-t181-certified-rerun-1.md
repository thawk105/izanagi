---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t181-certified-rerun
seq: 1
title: [T-181] の reasoning A/B を認証付きで再走した — aggregate/verify とも rc=0 / experiment_complete=true、両読者一致 10/10。機械 decision 行は採点器の欠陥を含む (実装差分なし、branch worktree-dev-wave-t181-certified-rerun)
---

## 本文

- 依頼は「mismatch の原因を修正して 10 run を認証付きで再走し、[T-184] の判定根拠に使える
  aggregate / verify を返す」。**装置 `tools/codex_reasoning_ab.py` は 1 byte も変更していない。**
  段 1 の実測で、直すべきは装置ではなく運用と manifest の形だと判明したため。
- **未認証の原因は 3 つあり、うち 2 つは装置外だった。**
  (i) F61 (実走後の装置修正) は fix9 の時点で装置側では解消済み。本 wave の生死確認
  (`build-snapshot` → `verify-snapshot` を POS/NEG 各 2 回) で replay 出力の byte 完全一致を実測した。
  (ii) 旧 manifest が指す prompt / receipt / score / packet_state / verdict 系は
  `~/.claude/jobs/c94644e8/tmp/t181-wave/` にあり削除済み。2026-08-09 に旧 manifest を `verify` すると
  失敗理由は `snapshot oracle replay mismatch` **ですらなく** `prompt cannot be read` ×10 になる。
  **旧成果物はもはや再検証できない。**
  (iii) 旧 manifest は top-level の `schedule_sha256` と `judgments` を欠いており、
  snapshot 問題が無くても認証は通らない形だった。旧 `aggregate` の失敗理由にも両方が出ている。
- 本走は (ii) を全ファイル `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/` 配下へ
  置くことで、(iii) を規定どおりの manifest を組むことで塞いだ。home と job tmp には置いていない。
- 実走前に装置版を pin した (F61 恒久対応 (a))。装置 sha256 `58f1176e`、repo HEAD `34957a24`、
  `codex-cli 0.146.0`、schedule sha256 `7a865c74`。事前登録の block/arm 配置をそのまま再利用した。
- **10 run すべて exit 0、再試行ゼロ、snapshot は run 前後とも不変**で、
  記録値が実走前に凍結した schedule の `snapshot_manifest_sha256` と一致した。
  `aggregate` / `verify` はともに **rc=0 / `experiment_complete=true` / `failure_reasons=[]`**。
  `manifest_sha256=afd5cf40c94dafd63b60a1fa21de2144b9e1cd03cf48280dbb698d3b65a5c196`。
- **label-masked 裁定は両読者 10/10 一致** (rate 1.0、保守側裁定は不発)。
  正例で R-1 を must-fix 相当と裁定したのは **high 3/3・max 3/3**。
  負例は両 arm とも偽 R-1 が 0 件で、4 run すべて GO (2026-07-30 は high 1 本が別理由で NO-GO だった)。
  新規 finding 0 件。事前登録表の該当行により許される裁定は
  **「この 6 run で劣化を観測しなかった」だけ**であり、非劣性・同等・採用の証明にはしない。
- **機械 `decision` 行は採点器の欠陥を含む。** `quality_decision="benchmarkまたはmax基準が不安定"`
  は s03 (POS/max) が `post-treatment` に落ちて `max=2/3` になったためで、
  両読者は s03 の R-1 を true と裁定している。原因は
  {{F:frozen-scorer-decision-regex}}。**実走後に採点器を直すと F61 が再発する**ため直していない。
  当該行を実質的知見として引用してはならない旨を insight に明記した。
- 資源 (全 attempt): CLI reported 合計 3,410,229、wall 合計 8,807 秒。正例中央値は
  high が model_calls 27 / CLI 182,038 / wall 505 秒、max が 35 / 226,285 / 809 秒。
  logical turn は測れておらず (`logical_turns_reported=false`)、「turn 削減」の根拠にしてはならない。
  全 run で `compaction_observed=true` / `rate_limited=true`、
  `zero_component_total_only` は NEG 4 run に各 1 件 (POS 0 件)。前回と同条件ではない。
- **凍結境界の逸脱を自己申告する。** 実走 driver (`setup_run.py` / `run_blocks.py` /
  `build_manifest.py` / `probe_snapshot.sh` 他) を親が書いた。所在は repo 外で commit しないため
  provenance checker は発火しないが、「repo 外なら凍結境界を満たした」ことにはならない ([T-317] 未裁定)。
  正しさ gate は装置側にあり、manifest を誤って組めば `verify` が
  `adjudication ... mismatch` で `experiment_complete=false` を返すため、誤りが認証済みとして通る経路は無い。
- provenance: full-history 監査の rc=1 は既知 23 件 ([T-139] 22 + [T-682] 1) 由来で別 wave が処置中。
  本 wave は調査も手当もしていない。自 wave の range 監査は別途実施した。
- 計算資源: 10 run はログインノードの codex 実行で計算ノードを使っていない。
  R4 probe ([T-139]) の計測とは競合していない (同 wave は本走中に land 済み)。
- 受入全走 **7570 passed / 20 skipped、rc=0** (計算ノード、1334 秒、request 896773)。
  lease は 30 秒間隔の待ちで 18 回目に取得した (先行 holder の解放待ち約 9 分)。
  変異 matrix は実装差分ゼロのため DW-S04 により免除。
- 段 8 の改善候補は 1 件で、実装子権限の境界に当たるため契約どおり実装せず [T-317] へ返した。

## 次の一手差分

### 更新

- [T-181] **P1・部分達成**: 認証済み台帳を取得した
  (`output/insights/2026-08-09_t181-certified-rerun/`、`aggregate`/`verify` とも rc=0、
  `experiment_complete=true`、両読者一致 10/10、正例 high 3/3・max 3/3、負例の偽 R-1 は両 arm 0)。
  残るのは機械 `decision` 行が {{F:frozen-scorer-decision-regex}} を含むことであり、
  [T-184] へ渡す前に {{T:score-decision-extraction-defect}} の裁定が要る。
  2026-07-30 の成果物は job tmp 削除により再検証不能であり、以後の引用は本走の台帳を使う。
  base: d95f08ec2ced6721ccc02fb179792e2a767cb05683f049ea19ebeb26263ec0fe

- [T-317] **P3・独立 2 例目を観測**: dev-wave の凍結境界は「実行可能な probe / harness / script」を
  実装面とし Codex `role=author` が書くと定めるが、親の責務 (`DW-S01` の前提実測、実走の運転) の
  手段が script になる場合の担当が入口・reference のどちらにも無い。
  1 例目は [T-316] wave で親が段 1 probe を直接書いた件。**2 例目が本 wave** で、
  親が実走 driver 一式 (setup / block runner / manifest builder) を書いた。所在は repo 外で
  commit していないため provenance checker は発火しないが、凍結境界を満たしたことにはならない。
  択一は (a) 前提実測・実走運転用の使い捨て script を明示的に例外にする、
  (b) 例外を作らず親は必ず子に書かせる、(c) 文言だけ明確化する。推奨は依然 (b) だが、
  本 wave のように実走が数時間かかる場合の実行可能性は (b) の検討材料に含める。
  base: 0f45414c192f44484eed035ea8135a98d1ffe3908f5ab82498375b1c1456d376

### 新規

- {{T:score-decision-extraction-defect}} **P1・ユーザー裁定待ち**:
  `codex_reasoning_ab.score_run` の decision 抽出欠陥 ({{F:frozen-scorer-decision-regex}}) を
  Codex `role=author` で是正し、同義だが表記の異なる決定文を採点器 control へ追加する。
  そのうえで **(a) 是正版で 10 run を再走して `decision` 行を取り直す**か、
  **(b) 本走の台帳を「s03 は採点器欠陥による post-treatment、人手裁定は max 3/3」という
  erratum 付きで [T-184] へ渡す**かを裁定する。(a) は約 2.5 時間の実走と CLI reported 340 万規模の
  再消費を伴う。**是正を実走前の凍結装置へ遡って適用してはならない** (F61)。
