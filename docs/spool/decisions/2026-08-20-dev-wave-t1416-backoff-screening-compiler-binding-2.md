---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1416-backoff-screening-compiler-binding
seq: 2
---

## {{D:site-toolchain-binding-scope}}. backoff_sweep.py/p2_2.py へ D293 同型の site 依存 compiler 解決 + toolchain 束縛検査を実装し、ENV_TAG/Pegasus 公式実行有効化は次wave scope とする

**決定:** D293 (`docs/decisions.md` の床値 campaign 決定) と同型の「site 依存 compiler
解決 + toolchain 束縛検査を同じ変更単位で入れる」原則を、`backoff_sweep.py`/`p2_2.py`
(D58 bench-first screening v2 の初回 ablation 対象) へ適用する。今回実装したのは
次の4点である。

1. `backoff_sweep.py`/`p2_2.py`: campaign 開始時に一度だけ site compiler の完全
   manifest を観測し (`buildcache.observed_toolchain_manifest`)、通常経路・screening
   経路の両方 (baseline・各 candidate) へ一貫して伝播する。
2. `screening_driver.py`: `evaluate_candidate` から `pipeline.evaluate()` への
   `env_contract`/`expected_toolchain_manifest`/`declared_use_class` 伝播の欠落を
   修正した。
3. `buildcache.py`: `declared_use_class == "official"` の v2 build では
   `expected_toolchain_manifest` を必須化し、欠落時は build 前に fail-closed で停止
   する。
4. `pipeline.py`: trace/perf 両 build の toolchain 一致を検査し (不一致は
   `STAGE_BUILD_DONE` 記録前に abort)、成功時は実 toolchain と
   `toolchain_record_sha256` (v2 identity hash とは別キー) を `STAGE_BUILD_DONE` へ
   記録する。

**scope 境界 (今回は実装しない、次wave へ明示的に送る):** `ENV_TAG` を Pegasus
runtime tag へ切り替え、Pegasus 公式実行そのものを可能にすること。理由は次のとおり
実測で確認した。

- `execution_guard.py` が build 前の認可検査で、`ENV_TAG="linux-baremetal"` のままの
  Pegasus official run を構造的に拒否する。折衷案「compiler だけ site 依存化し
  ENV_TAG は Linux のまま」も、authorization contract の不一致で別の検査に落ちる —
  段3 敵対相談の実コード裏取りで、現行認可構造ではこの折衷は通らないと確認済み。
- `ENV_TAG` は `p2_2.py` の共有定数であり、`s8b_floor_campaign.py`/
  `s8b_oracle_driver.py` 等の machine pin・calibration・floor 出力・noise floor の
  複数箇所から共有 import されている (段3 レンズB が独自 grep で段2プランの想定より
  広い波及範囲を実測)。単純な値変更は S8b 側へ波及する。
- Pegasus 用 calibration は `p2_2.py` が要求する固定ファイル名では存在せず
  (registered 形式のみ)、追加の実測が要る。本wave は「実装のみ、Pegasus 実機再実行は
  scope外」の前提のため、この実測はここでは行わない。

**却下した選択肢:**

- **今回のwave で ENV_TAG 対応まで含めてフルスコープ実装する** — 規律5 (段階導入・
  盛らない) に反し、S8b machine pin への波及を伴う変更を1waveに詰め込むリスクが
  高いため見送った。段3 レンズBも縮小スコープを明示的に推奨した。
- **cache 機構自体 (buildcache.py の completion.json) を拡張して cache hit 時の
  toolchain 束縛も同時に完全化する** — {{D:cache-hit-toolchain-drift-waiver}} で
  別途扱う。

## {{D:cache-hit-toolchain-drift-waiver}}. v2 build の cache hit 時 toolchain 束縛欠落を明示的な scope waiver として記録する

**決定:** {{D:site-toolchain-binding-scope}} で実装した toolchain 束縛検査
(`buildcache.py` の `expected_toolchain_manifest` 完全一致検査、`pipeline.py` の
`STAGE_BUILD_DONE` への `toolchain_record_sha256` 記録) は、**新規 build 時にのみ
完全に機能する**。cache hit 時の限界を、段6 焦点再レビューの要求
(「明示的な次wave waiver なしに完全受入として land すべきでない」) に従いここへ
記録する。

**限界の内容:** `buildcache.py` の v2 build cache identity (`_v2_identity` の
pre-image) は `version_first_line` までの短い toolchain manifest しか含まない。
completion.json への保存も同様に短い。したがって、compiler の先頭行 (`version_first_line`)
が同じで完全 version だけが異なる旧 cache entry を hit した場合、`STAGE_BUILD_DONE`
へ記録される `toolchain_record_sha256` は「今回の build 呼び出し時点で観測した
toolchain」の値であり、「そのcache entry (binary) を実際に生成した toolchain」の
証跡ではない。新規 build 時は expected との完全一致検査 (完全 version 込み) が
機能するため、この限界は cache hit 時に限られる ({{F:cache-hit-toolchain-drift}})。

**緩和と運用注記:** `STAGE_BUILD_DONE` には既存の `trace_cached`/`perf_cached`
フィールドが記録されている。consumer は `toolchain_record_sha256` を、
`trace_cached`/`perf_cached` が両方 False (= 新規 build) の場合にのみ「その build を
実際に生成した toolchain の証跡」として信頼してよい。cached=True の記録は
「build 呼び出し時点の観測値」として扱う。

**次の一手:** 完全な解決 (cache entry 自体に完全 version 込み manifest を保存し、
hit 時に expected と照合する) は `buildcache.py` の cache 機構自体の拡張を要し、
scope外の既存 campaign 全体 (S 系検証・S8b floor 等) に影響しうる規模のため、
別 wave の scope とする ({{T:buildcache-cache-hit-toolchain-binding}})。

**却下した選択肢:**

- **今回の wave で cache 機構を拡張する** — 規律5、影響範囲の広さにより見送った。
- **cache hit を無効化し常に新規 build する** — 既存の buildcache 全体の設計方針
  (cache-first) を局所的に覆すことになり、他の caller への影響が読めないため見送った。
