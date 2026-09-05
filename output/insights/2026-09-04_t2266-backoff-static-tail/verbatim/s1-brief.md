# 段 1 brief — [T-2266] 静的 backoff の tail 実測

## 依頼 (ユーザー、逐語)

> [T-2266] b = 150, 200, 300, 500, 750, 1000 µs の静的 `T(b)` と abort 率を、同一ビルド・同一
> job 割付けで測る。現在は未測定の tail が非単調応答の説明を供給している状態で、これを実測で閉じる。新規
> Pegasus 実行体は要らない (既存の backoff sweep 経路を使う)。絶対規律 1 に従い性能計測は trace-disabled
> build で行い、baseline と variant を揃える。計測は条件を割って複数ノードへ同時投入する。正本は worklog
> carry [T-2266] (entry 1228)。起動時に backoff 系の稼働 wave (t2189-adaptive-serializability)
> との編集面重複を検査し、`tools/pegasus/admission_registry.json` に触る必要が出たら着手前に報告する。規律
> 2 を緩めない。Codex author = D95。本題の測定だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
> scope 外。

## 確定済みユーザー裁定 (不変)

- 規律 1: 性能計測は trace-disabled build。baseline と variant を揃える。
- 規律 2: 正しさゲートを緩めない。
- 計測は条件を割って複数ノードへ同時投入する。
- 本題の測定だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- `tools/pegasus/admission_registry.json` に触る必要が確定したら、実装着手前にユーザーへ報告する。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

**(P1-a) 依頼の前提「b > 100 µs の静的 `T(b)` は未測定」は誤りである。**
親が repo 外の一次資料で実測確認した。`/work/1/SFC/tanab/b10-backoff-grid-runs5/` に
2026-08-26 投入の 3 workload 完走成果物がある (job 951689 / 951690 / 951691、
`completion.json` = `status: complete`)。格子は `EXTENDED_SWEEP_US` の 29 点で、
**1 job 内・同一ビルドキャッシュ・trace-disabled**。
`campaigns/<id>/reports/b10-backoff-grid-<workload>.dat` が
`backoff_us throughput_tps abort_rate latency_ns cv` を持つ。
write-heavy: 150 = 2,048,271 / 0.1128、200 = 1,848,960 / 0.0976、300 = 1,594,451 / 0.0794、
500 = 1,304,759 / 0.0612、700 = 1,145,115 / 0.0512、800 = 1,083,966 / 0.0478、
900 = 1,035,161 / 0.0449。**依頼 6 点のうち 4 点は既に依頼どおりの条件で測られている。**

**(P1-b) b = 1000 µs は現行符号化では測定不能である (F718)。**
`patches/silo-backoff-fixed.patch` の合成枝は供給値を単一量として扱わず、
商 (`値 / 1000`) をモード選択、剰余 (`値 % 1000`) を振幅にする。商 0 = 固定値、商 1・2 = 乱択モード。
1000 は「モード 1・振幅 0」= 実質 0 µs。2026-08-26 の走行でも 1000 µs 行は
2,386,090 / 0.7847 で 0 µs 行 (2,361,787 / 0.7896) と同一域だった。F718 は当該点を除外し
有効 28 点で特徴づけ、**符号化の修正は変異軸の設計判断として別 wave へ送っている。**
親の provisional 読解では 999 は商 0・剰余 999 なので現行符号化で表現できる (**未実測、要検証**)。

**(P1-c) 真に未測定なのは b = 750 の 1 点だけである。** 700 と 800 が両側から挟む。

**(P1-d) 既存 2 格子はいずれも凍結物に pin されており、書き換えられない。**
- `EXTENDED_SWEEP_US` (`orchestrator/campaign/backoff_extended_sweep.py:37`) は
  campaign spec の `sweep_us` (同 :337) を通じ campaign identity を決め、その identity が
  着地済み論文図の provenance に束縛されている
  (`docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json`、
  `docs/paper-story/figures/README.md:177-179`)。test も上端を pin
  (`orchestrator/tests/test_backoff_extended_sweep.py:161`)。
- `SWEEP_US` (`orchestrator/campaign/backoff_sweep.py:59`) は **S1 freeze の一部**である
  (`orchestrator/campaign/s1_known_axes_freeze.py:398,408,423,772` — :423 は
  `_module_source(backoff_sweep, "_BASE and SWEEP_US")` の source hash pin)。
  golden は `orchestrator/tests/s1_expected_goldens.py:31`、
  検査は `orchestrator/tests/test_s1_known_axes_freeze.py:549`。
  さらに `output/s1-freeze` の bytes は `tools/pegasus/b10_backoff_grid.sh` の
  `EXPECTED_FREEZE_TREES_SHA256` が job 内で 2 度検算する。

**(P1-e) 親の推奨する scope。** 上記より、依頼の目的「未測定 tail が説明を供給している状態を
実測で閉じる」は**既存データで大半が達成済み**である。親の provisional 裁定は次のとおり。
1. **必須:** T-2216 材料文書 §5 の誤った主張を訂正し、実測 tail を歩行 model の混合仮定へ突き合わせる。
2. **要裁定:** b = 750 (+ 999) を新規測定するか。新規測定を行う場合、
   既存格子を触らない新しい driver / 新しい job body が要り、
   `tools/pegasus/admission_registry.json` への新規 path 追加が発生する見込み。
   その場合は実装着手前にユーザーへ報告する (依頼の明示条件)。

## 不変条件

- `EXTENDED_SWEEP_US`、`SWEEP_US`、`orchestrator/tests/s1_expected_goldens.py`、
  `output/s1-freeze` / `output/s8b-freeze` の bytes、
  `docs/paper-story/figures/` の provenance を **1 バイトも変えない**。
- `patches/silo-backoff-fixed.patch` の符号化を変えない (F718 が別 wave へ送った設計判断)。
- 性能計測は trace-disabled build のみ。正しさ主張はしない (本 wave の成果物は非認証)。
- 既存の測定値を「現行コードと違う」だけの理由で無効化しない (規律 7)。

## 成果物の形

- (必須) `output/insights/2026-09-03_t2266-backoff-static-tail/` — 既存 tail 実測値の逐語表、
  T-2216 §5 の訂正、F718 による b=1000 の測定不能の記録、歩行 model の混合仮定への影響。
- (裁定次第) 新規測定の driver / job body / submitter とその成果物。
- worklog / decisions / failures は `docs/spool/` の fragment として書く (段 7)。

## 実測環境

Pegasus 計算ノード、queue `gen_S`、機体固有事実は `docs/pegasus-runbook.md`。
所在の記録は worklog。作図は計測機の外 (`tools/plotting/FIGURE_CONVENTIONS.md`)。
新規測定を行う場合は workload ごとに 3 job へ割り、同時投入する。

## 編集面重複

`worktree-dev-wave-t2189-adaptive-serializability` (tip 409423393) が触る 6 file:
`orchestrator/tests/test_ccbench_spawn_sites.py`、`orchestrator/tests/test_hooks.py`、
`orchestrator/tests/test_t2187_adaptive_const_probe.py`、
`tools/pegasus/admission_registry.json`、
`tools/pegasus/probes/t2187_adaptive_const_probe.pbs`、`.py`。
worktree の未 commit 差分はゼロ。**重複面は `admission_registry.json` の 1 file。**

## 分割方針

段 2 は 1 本 (read-only plan)。段 3 は 2 レーン (sol / luna) で
(P1-a)〜(P1-e) を別レンズから攻撃させる。段 5 以降は段 4 の裁定次第。
