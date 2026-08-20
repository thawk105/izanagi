---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1416-backoff-screening-compiler-binding
seq: 3
---

## 新規

### {{F:cache-hit-toolchain-drift}}. buildcache.py の v2 build cache は cache hit 時に toolchain 完全 version を束縛しない [恒真ゲート]

- 事象: `expected_toolchain_manifest` の完全一致検査 (`buildcache.py` の `build_v2`)
  は、build 呼び出し時点で観測した現在の toolchain と expected を比較するだけで、
  実際に hit した cache entry (旧 binary) がどの toolchain で生成されたかは記録・
  照合していない。`_v2_identity` の pre-image は `version_first_line` までの短い
  manifest しか含まないため、先頭行が同じで完全 version だけ異なる toolchain は
  同一 cache key になり、旧 entry を hit しうる。
- 根本原因: v2 build cache の identity/completion.json スキーマが、当初 toolchain の
  完全 version を束縛対象に含めない設計だった (床値 campaign 系列で `expected_toolchain_manifest`
  が導入された時点から存在する既存の限界。T-1416 が `STAGE_BUILD_DONE` へ
  `toolchain_record_sha256` を記録する機能を新設したことで、この限界が
  「不正確な証跡を生成しうる」という具体的なリスクとして顕在化した)。
- 恒久対応: 未実装。{{D:cache-hit-toolchain-drift-waiver}} が緩和策 (cached フィールドと
  組み合わせた運用注記) と scope waiver を記録し、完全解決は
  {{T:buildcache-cache-hit-toolchain-binding}} へ送った。
- 再発検知: cache hit 時に `toolchain_record_sha256` が現在観測値であることを示す
  positive control テスト (未実装、次wave の scope)。

## 再発

### F358

- **再発: 2026-08-20** — `pipeline.py`/`loop.py` (enforcement source closure member)
  への変異 matrix (T-1416) で、`ratified_enforcement_source` fixture 経由の
  contract-loader-drift 偽陽性 (共通核 9〜12件) に加え、**`run_campaign` が内部で
  呼ぶ `ident.verify_against_lock` → `contract_loader_binding.verify_live_contract_loader_binding`
  経由でも同型の ERROR (fixture setup ではなく test 実行中の IdentityMismatch) が
  起きる**ことを実測確認した。この経路の ERROR は `tools/mutation_harness.py` の
  `failed_nodes` 抽出 (FAILED のみを対象、ERROR は含まない) から漏れるため、
  この経路を通るテストを変異の `expected_nodes` に含めると、実際には対象コードに
  到達せず ERROR で落ちているだけなのに `SURVIVED` にも `KILLED` にもならず
  静かに `MISMATCH` の中に紛れる (原因の切り分けに実 stdout の grep が必要だった)。
  判定手順は F358 既載のとおり「共通核 (failed_nodes の交差) を差し引いた delta が
  expected と一致するか」で行うが、**delta 不一致の原因が (a) 単なる過大な
  expected_nodes なのか (b) 対象コードに到達しない設計ミスなのかは、実際の
  stdout (pytest 標準の `short test summary info` セクションと ERROR excerpt) を
  読まないと区別できない** (ledger の `failed_nodes` だけでは FAILED/ERROR の別が
  失われる)。
