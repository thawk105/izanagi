---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2654-t316-hydrate-base
seq: 2
---

## {{D:t316-hydrate-prepare-base}}. t316 は job 内で hydrate した pristine staging を prepare_masstree_fetchcontent で準備してから関門と両 build に渡し、永続 cache は hydrate の入力にだけ使う

**決定:** t316 probe の S6 を次の形にする (D2044 項 27 の実装手番)。

1. `observe_s6` は scratch の兄弟に staging S を作り、実 CLI `tools/pegasus/fetch_third_party.py hydrate` を
   `--cache-root <永続 cache> --staging-root <S>` で 1 回走らせる。cache を `FETCHCONTENT_SOURCE_DIR_*` で直指ししない。
   hydrate の失敗 (rc≠0 / timeout / JSON 解読不能) は `failure_stage="third-party-hydrate"` で fail-closed にし、
   identity を採らずに返す (verdict は既存の `S6_SOURCE_IDENTITY_INVALID`)。
2. third-party 3 本の `source_heads` / `source_identities` は hydrate 後・prepare 前に S から採る。
3. outside の gflags / glog install 後・関門の前に `buildcache.prepare_masstree_fetchcontent` を 1 回呼ぶ
   (ccbench_dir = patch 済み requested 木、base = `<scratch>/fetchcontent`、source dirs = S、dependency_prefix =
   outside の install prefix、site は既定解決)。失敗は `masstree-prepare*` で fail-closed にし、prepare の後に改めて
   `if failure_stage is None` で関門へ入る (verdict は既存の `S6_CONDITION_GATE_UNPROVEN`)。inside では prepare しない。
4. 関門・outside・inside の configure には `-DFETCHCONTENT_SOURCE_DIR_*=<S>/<name>` だけを渡し、`-DFETCHCONTENT_BASE_DIR`
   は渡さない。S は S6 profile の `readonly_roots` に加える (sandbox 内で読めて書けない)。
5. 受領証の S6 に `third_party_staging` と `masstree_prepare` (呼び出し入力・timeout・成功時 argv・所要・失敗 stage) を
   足す。既存 field・schema・`verdict_s6`・関門の受理集合は変えない。
6. `.pbs` の `BOUND_PATHS` と `_BOUND_RELATIVE_PATHS` に `orchestrator/campaign/buildcache.py` と
   `tools/pegasus/fetch_third_party.py` を同期追加する (直接利用する実行入力の正本だけ。推移的 import は束縛しない)。
   旧受領証の 7 path 記録には遡及しない (絶対規律 7)。
7. `condition_meaning_gate.py` / `buildcache.py` / `fetch_third_party.py` / `silo_ladder_rung1.py` / policy JSON は変えない。

**理由:**

- 関門の緑が永続 cache の残留生成物 (`config.h` / archive) に依存していた (D2032 の却下欄が別項へ送った点)。cache を掃除
  すれば赤へ戻り、成果物が機械証拠を失う。緑の既知 2 例 (A-2、backoff_sweep driver 段) はどちらも
  `prepare_masstree_fetchcontent` で準備した source を関門へ供給しており、同じ形へ揃えるのが最小差分である。
- hydrate は生成時に `reject_ignored=True` で pristine を検証する。A-2 の `<name>-src` 複製と
  `_verify_pristine_floor_dependency_sources` は本経路に無いので導入しない (追加の gate は依頼で scope 外。D2085 は
  同種の scope 判断の先例であり、二重検査一般の禁止ではない)。
- masstree の custom command は OUTPUT が source dir に実在すれば再実行しないので、host の prepare 1 回で sandbox 内
  (S は ro-bind) の build も通る。`-DFETCHCONTENT_BASE_DIR` を関門・両 build へ渡すと inside の binary dir が ro の S か
  scratch 内の共有 base になる。前者は書けず、後者は outside / inside で build 生成物を共有する。渡さない形が最も単純。
- S を scratch 内に置くと、後続の writable scratch bind が S を覆い、sandbox 内から source を書ける。requested 木と同じく
  scratch の兄弟に置く。
- job 内 hydrate は新しい submit 入力・env・argv を足さない (D2084 と同じ方針)。親が login で hydrate して渡す A-2 /
  certify 型は新 env を要する。
- 生の `cmake --build --target masstree_build` を probe に書くと `test_ccbench_spawn_sites.py` の direct-cmake-target sink に
  なる。既存 helper を呼ぶ形は必要な依存準備を既存機構で行うためであり、sink 不検出は安全性の根拠ではない。
- 計算ノードの実経路で S6 go に到達した (request `0:4163.nqsv`: hydrate 1.37 秒、prepare 11.39 秒、両 build の configure が
  S を指す)。login の配線テストは実 hydrate CLI (symlink) + 実 prepare + 実 bwrap で通す。

**却下した選択肢:**

- **親が login で hydrate して新 env var で staging を渡す** (A-2 / certify 型) — 新しい submit 入力を足す。
- **関門・両 build に `-DFETCHCONTENT_BASE_DIR` を渡す** (A-2 と argv まで同一にする) — inside の binary dir 問題 (上記)。
  緑の 2 例と「同じ準備済み source を供給する」合流であって、argv まで同一ではないことを明記する。
- **S を scratch 内に置く** — writable bind に覆われる。
- **`_verify_pristine_floor_dependency_sources` を足す** — hydrate 自身の検証と二重で、追加 gate は scope 外。
- **inside でも prepare する** — 二重 build。S は sandbox 内 ro で、host からの prepare は成功しうるため test は call 数 exact 1 で検出する。
- **hydrate の rc 検査だけの変異を KILLED 期待に置く** — JSON 解読失敗の層が先に遮るので冗長 gate 対照 (SURVIVED) とし、
  rc 検査 + JSON 失敗処理の 2 置換を負例にした。
- **fixture の git seed を session 共有にして test 時間を削る** — 削れるのは 2.8 秒/本で実 hydrate CLI の 3.3 秒は残る。本 wave では
  実装せず backlog へ。
- **prepare の timeout / 子孫停止 / 関門例外時の観測保持を helper 側で直す** — 共有 helper と既存の例外設計を変える。限界として記録。
