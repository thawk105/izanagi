# 段 1 前提実測 — [T-244] P3 ever-issued cell 台帳 (U-3)

親が段 1 brief の前に自分で測った事実だけを書く。値は測った checkout
(`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u3-ever-issued`、
base = local main `29ae9975`) のもの。

## N1 — production authority は空のまま

`orchestrator/campaign/reflux_origin_authority_v2.json` の全 bytes は
`{"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[]}` + LF の 1 行である。
entry は 0 件。

## N2 — authority document に「世代」の field が無い

`_AUTHORITY_KEYS` は `{"authority_schema", "origins"}` の exact 2 key。
`generation` / `supersedes` / `epoch` / `active pointer` に相当する field は無い。
authority entry の key も `{"cell_key", "manifest", "origin_id"}` の exact 3 key で、
世代・発行時刻・前任への参照を持たない。

## N3 — ledger に epoch router が無い

`reflux_origin_ledger.py` (3485 行) 内に `epoch` と `generation` の綴りは 0 件。
`series` の綴りは manifest field `authority_series_id` の定義・parse・canonical 化の
4 箇所だけで、series を跨ぐ状態も series 単位の台帳も存在しない。
D179 決定 3 / 設計 §4.2 が推奨した epoch router は**未実装**である。

## N4 — genesis は一度きりで、origin を後から足す event 型が無い

`_initialize_locked` は `store.fixture` が偽なら `production runtime initialization is
forbidden` で拒否する。fixture でも既初期化なら拒否する。genesis は authority の全 entry を
その場で焼き込み、以後の読み出しは authority blob の完全一致と entry 件数一致を要求する。

## N5 — 既存被覆 (性質で検索した)

authority 読み込み `_authority_from_bytes` は、**同一 authority blob の中**で
(a) 同じ cell 4-tuple の 2 entry を `duplicate authority cell` で拒否し、
(b) 同じ `cell_key` が別 4-tuple を指す場合を `authority cell digest collision` で拒否し、
(c) 同じ `origin_id` の重複を `duplicate authority origin` で拒否する。
正負例は `orchestrator/tests/test_reflux_origin_ledger.py` の
`test_v03_manifest_identity_and_cell_equivalence_positive_negative` にある。

**訂正 (erratum、段 3 の両レンズが独立に指摘し親が実ファイルで確認した)。** 上の (b)(c) は
既存テストの被覆にも到達可能な枝にも数えてはならない。
`reflux_origin_ledger.py:1848-1849` の `origin_id <= previous_origin` →
`authority origins are not strictly sorted` が、`origin_id` 重複に対して
`:1863-1864` の `duplicate authority origin` より**必ず先に**発火するため、(c) の枝は
現行の検査順では到達不能である。(b) は直前の derived identity 検査を通った後に
実 SHA-256 衝突が要るため同じく到達しない。`test_v03` が固定しているのは (a) の正負例だけで、
(b)(c) の専用入力は持たない。以下 N6 の「既存被覆」も (a) だけを指す。
同 test は `authority_series_id` を変えても `derive_cell_key` が不変であることも固定している
(cell = workload descriptor / axis semantics / verifier policy / environment contract の 4 digest のみ)。

## N6 — 純増検出力

上記 (a)〜(c) はすべて **1 個の authority document の内部**にしか効かない。
「ある authority document が、**それより前の authority document** が発行済みの cell を
再発行する」ことを見る検査は現時点で 0 件である。本 wave が足しうる検出力はここだけで、
意味等価な (byte-different な) 再発行の検出は含まない (裁定どおり人間 gate)。

## N7 — 凍結 bytes の pin 閉包 (DW-O09)

`reflux_origin_authority_v2.json` を読む `*.py` は ledger 本体・
`orchestrator/tests/test_reflux_origin_ledger.py`・過去 wave の使い捨て probe
(`output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py`) の 3 つ。
`FROZEN_MANIFEST` 側 (`orchestrator/tests/test_frozen_artifacts.py`) に
`orchestrator/campaign/` 配下の json entry は無い。role 名を key にする review ledger 型の
pin も、authority / origin ledger を key にするものは見つからなかった。
本 wave は authority の bytes を変えない (不変条件 I1) ので、この閉包は brief の不変条件として
記録するだけで、再発行手続きは発生しない。

## N8 — 受入と実測の環境

受入全走は repo root で `python3 tools/run_tests.py`。Pegasus のログインノードでは
同 runner が gen_S へ同期 dispatch する (ログインノードで pytest 全走をしない)。

## N9 — 裁定の前提に対する差分 (段 4 の入力)

U-3 の裁定文は「successor 世代が意味等価な cell を byte-different に再発行して使用量 0 の
予算を得る」を防ぐ、と書いている。実測 N2 / N3 / N4 により、**その「世代」は現在どの成果物にも
存在しない**。したがって本 wave が作れるのは「世代」ではなく「**同一 series の連続する
authority document**」を単位とする台帳である。これが裁定の射程内かどうかは親の provisional 裁定
(brief の P1) とし、段 3 の攻撃対象にする。
