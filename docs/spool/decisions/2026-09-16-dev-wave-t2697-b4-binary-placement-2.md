---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2697-b4-binary-placement
seq: 2
---

## {{D:b4-floor-binary-placement}}. B-4 凍結 spec の binary は `output/env/<env_tag>/binaries/<binary_sha256>` へ ignored 複写で置き、凍結するのは bytes の可用性でなく path・期待 sha256・receipt とする

**決定:**

1. **配置規則:** 凍結 spec の `artifacts[].binary_relpath` は
   `output/env/<env_tag>/binaries/<binary_sha256>` とする。candidate と reference は同じ bytes
   (D1641 決定 3) なので、同じ path・sha・receipt を共有してよい。
2. **複写を採る。** 調達済み record と repo 外の durable store から、
   `python3 -m orchestrator.campaign.b4_binary_record place --record <r> --source-root <s> --env-tag <t>`
   で置く。実装は `s8b_floor_campaign.store_binaries()` を呼び、同関数が既に持つ検査
   (record validator、source sha、既存 destination sha、書込み後 sha) を入口で複製しない。
3. **tracked 化しない。** `.gitignore` に `output/env/*/binaries/` を置く。
4. **凍結の射程を明示する。** 凍結されるのは path・期待 sha256・receipt であって bytes の可用性ではない。
   全複製を失えば消費側は正しく拒否するが、bit 同一の復旧は保証しない。
5. **path の env 成分は検査されない。** 消費側は `binary_relpath` の env 成分と
   `environment.env_tag` を照合しない。`--env-tag` を spec と一致させるのは呼び手の責任であり、
   この規則を環境整合の gate と説明しない。
6. **配置による復旧は、receipt の policy が現行と一致する record に限る。** 配置経路は
   `store_binaries` が現行 policy を要求するので、古い policy で発行された record は置けない。
   消費側 (`expected_policy=None`) より厳しいが、緩めない。
7. **測定を投入する担当が、投入前に、使用する各 checkout へ配置する。** ignored file は merge で
   他 checkout へ移らない。

**理由:**
- **同種の物の既存規約があった。** `s8b_floor_campaign.py:7669` が測定用 binary を
  `env_scope_dir(env_tag)/binaries/<sha>` へ置いている。`env_tag` の実値は `pegasus` と
  `linux-baremetal` だけで、`output/env/pegasus/` には既に `calibration` と `profile` が並ぶ。
  `binaries` はその兄弟であり、新しい分類を起こさずに済む。
- **消費側は binary の tracked を要求しない。** `floor_pair_driver.py:614 _read_tracked_bound` は
  spec・build receipt・calibration にだけ loaded HEAD blob との byte 一致を課し、binary は
  `_resolve_regular` + sha + trace symbol 検査だけを通る。
- repo の tracked executable に ELF は 1 件も無い (段 3 の実測、58 件中 0 件)。
- 再 build は凍結 sha との bit 一致を保証しない。T-2636 の build は計算ノード 3 回でようやく成功した。
- 入口で上流の検査を複製すると、変異が上流に mask されて「検証省略を殺した」という判定が偽になる。
- 現物で確かめた。701,760 byte を置き、`_relative_path` / `_resolve_regular` /
  `assert_binary_sha256` / `_assert_no_trace_symbols` の 4 検査を通した。700KB を置いても
  `git status` は汚れない。

**却下した選択肢:**
- **新 namespace `output/b4-binaries/<sha256>`** (段 2 plan の案) — 既存規約と二重化し、
  二軸 (D13) の外に「campaign 横断の実験補助 store」という新分類を要する。
- **tracked 化** — 消費側が要求せず、repo に ELF の前例が無い。bytes の可用性は得られるが、
  それを要求する consumer が無い。
- **測定ごとの再 build** — 凍結 sha との bit 一致を保証しない。
- **path の env 成分を `environment.env_tag` と照合する gate を足す** — 依頼が scope 外とした
  仮想リスク向けの検査である。照合しないことを明記するに留める。
- **配置経路の policy 要求を消費側に合わせて緩める** — 規律 2 に反する。
