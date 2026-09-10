# 段 1 brief — dev-wave-t513-trigger-exact

## scope

1. [T-513] `orchestrator/campaign/pipeline.py` の `_require_materialized_trigger_predicate` が
   materialized source の hole 行を `.strip()` して比較している受理集合の穴を、exact 比較で閉じる。
   実装面 = `pipeline.py` 本体 + `orchestrator/tests/` のテスト。
2. [T-515] `diffq_variant_id` の raw hash による reject variant 重複の **影響実測のみ**。
   実装しない。再裁定用に構造化して親が返す。

## 確定済みユーザー裁定

- 裁定源: `dev-wave-jobs/rulings-inbox/2026-08-12-coarse-provenance-45rulings.md` 36 行
  「T-513: exact 比較へ (T-515 と同時、影響実測つき)。T-515: T-513 後に再判断。」
- したがって T-513 の実装方向 (exact 比較) は裁定済みで、非同値な択一へ戻さない。
  exact の **具体形** (下記 P1) だけが未確定。

## brief 前の実測 (親が実行、probe = job tmp/probe_t513_indent.py)

- 骨格 (`patches/silo-backoff-trigger-gating-variant.patch`) の hole 行は
  `'  izanagi_gate_pass = true;'` — **先頭 2 空白**。
- `p3_s4_loop.render_hole` は「元 hole 行のインデントを保って implementation を挿入する」と
  docstring に明記し、実際に `_indent_of(hole 行)` を前置する。
- よって正規 materialization 後の hole 行の逐語 =
  `'  ' + emit_predicate(TriggerGateIR(mask))`。
- 実測 (mask=20):
  - 現行 `.strip()` 比較: 正規形 **通る**
  - 素朴 exact (`hole == emit_predicate` bytes): 正規形 **通らない = 本番破壊**
  - インデント付き exact (`hole == '  ' + emit_predicate`): 正規形 **通る**
  - 攻撃 4 形 (`'  X  '` / `'\tX'` / `'X '` / `'    X'`): strip 比較は全て通り、
    インデント付き exact は全て閉じる
- 既存テスト `orchestrator/tests/test_campaign.py` の fixture は hole を**インデント無し**で書く
  (`f"{predicate_a}\n"`)。実 materializer の出力と乖離しており、現在は `.strip()` が両方救っている。
  exact 化ではこの fixture を実形へ直す必要がある (期待値の弱体化ではなく、実形への是正)。
- 正準集合は `emit_predicate(mask)` の 32 通りちょうど。`canonicalize_predicate` は
  `strip()` 一致で正準 bytes へ解決するため、quarantine 経路を通った source は必ず正準 bytes。
  T-513 の穴は **既 materialize 済み source を直接渡す経路** でのみ到達する (canonical 定義と一致)。

## 判断が割れうる前提 (親の provisional 裁定 = 攻撃対象)

- **(P1)** 期待 bytes の作り方。候補: (a) 骨格由来インデントを軸定数として pin し
  `INDENT + emit_predicate` を期待する / (b) `patches/` の骨格 patch から実行時に導出する /
  (c) 先頭空白だけ許し末尾空白を閉じる部分 exact。
  親の provisional 裁定は **(a)** — (c) は受理集合の穴を残し裁定の意図を満たさない、
  (b) は admission が izanagi repo の patch ファイルに実行時依存する新規結合を作る。
  (a) を採るなら、pin が骨格の実バイトと一致することを検査するテスト (drift 検出) を同時に置く。
- **(P2)** 既存テスト fixture の是正は「テストを実形へ直す」修正であり、期待値の緩和ではない。
  fixture を実 materializer (`render_hole`) の出力から導出する形にすれば、以後の乖離が構造的に消える。
  親の provisional 裁定は **fixture を render_hole 由来へ書き換える**。

## 不変条件

- 規律 2: 受理集合は **縮む方向のみ**。exact 化で新たに通るものを作らない。
- `emit_predicate` / `canonicalize_predicate` / 正準集合そのものは変えない。
- admission の失敗は既存の `BuildAdmissionError(_TRIGGER_PREDICATE_REJECTION)` を保つ
  (WAL の `error` 逐語をテストが assert しているため、文言を変えない)。
- 8c 結線 wave (`dev-wave-8c-formal-consumer-wiring`) の編集面
  (`reflux_origin_artifacts.py` / `reflux_source_closure.py` / `s8b_descriptor.py` / `wal.py`) に触らない。

## 成果物影響 (DW-G05)

直さない場合: 外周空白を保持した materialized source が build admission を通り、
WAL に焼かれる trigger binding は「materialized source は emitter 出力そのもの」という
byte 単位の主張を保証できない。すなわち certified 選択の proof chain における
source 同一性の主張が、emitter が生成しえない bytes まで受理したまま残る。

## 成果物の形

- `pipeline.py` の exact 比較 + (P1) 採用案に伴う軸定数/drift 検査。
- 攻撃 4 形を閉じる positive/negative テスト、正規形が通る正例テスト。
- [T-515] の影響実測を構造化した裁定パッケージ (実装なし)。

## 分割方針

- 段 5 実装子 1 本 (pipeline.py + テスト、所有分離不要)。
- 段 6 敵対レビュー 2 本 (受理集合の縮小が正規経路を壊していないか / 攻撃面が本当に閉じたか)。
