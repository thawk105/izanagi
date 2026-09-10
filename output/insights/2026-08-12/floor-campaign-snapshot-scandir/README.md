# 2026-08-12 — test_s8b_floor_campaign の実 output 走査を os.scandir へ置換した

wave = `dev-wave-floor-campaign-speed` / branch = `worktree-dev-wave-floor-campaign-speed`
依頼 (ユーザー逐語) = 「test_s8b_floor_campaign の高速化をしてください」

## 1. 遅さの所在 (受入 base arm の junit が一次資料)

一次資料 = `dev-wave-jobs/dev-wave-t813-shard-eval/junit-base-0.xml` (48 worker、bnode014)。

- file 直列和 **900.83s / n=212** (file 別 3 位)。
- **上位 12 テストで 887s = 98.5%。残り 200 実行は約 13s。**
  → 高速化の対象は 12 テストであって file 全体ではない。
- 92s 級 7 本 / 82s 1 本 / 39s 級 4 本。**同一 body の parametrize が 39.35s と 91.79s に割れる。**

主因は `_real_output_snapshot` (`orchestrator/tests/test_s8b_floor_campaign.py:432`)。
実 repo `output/` (**11,033 entry / 337MB / 10,367 file**) を `Path.rglob` で走査し
全 file を `read_bytes()` して SHA-256 する。**11 テストが前後 2 回ずつ = 22 回、約 7.4GB。**

cProfile (solo、焦点 11 実行): 全体 161.34s のうち
**`_real_output_snapshot` = 22 call / cum 128.95s = 79.9%**、`read_bytes` = 228,263 call、
検査対象本体の `_run_campaign` = 19 call / 31.74s。

## 2. この関数は正しさ防壁である

「統合テストが実 repo の `output/` を 1 bit も変えない」ことを bytes まで固定する。
`output/` には凍結成果物 (s1-freeze / s8b-freeze / campaign output) が入っており、
ここが黙って変われば certified 選択の入力 bytes が変わる = 受理集合が変わる。
**したがって要件は「速くすること」ではなく「検出集合を変えずに速くすること」だった。**

## 3. 却下した 2 設計 (敵対 2 本が独立に NO-GO)

### (a) 連鎖 cache — テスト i の事後 snapshot を i+1 の事前へ再利用する

22 → 12 回に減るが、成立に**直列化 (xdist group への収容)** を要する。

- **node id が変わる。** group に入れた node は実行時 id に `@group` 接尾辞が付く
  (受入 junit の `..._returns_rc_2_on_gate_refused@real-repo` で実在確認)。
  **F95** に、同じ接尾辞が変異 harness の consumer 2 つを壊した既往がある。
- `conftest.py:199-200` に「実 output / snapshot 系もこの reader/writer 競合面には含めない」
  という**明文の除外**があり、`REAL_REPO_SERIAL_NODES` は性能グループではなく
  排他不変条件の正本である ([T-826] M0 の対象そのもの)。
- **ordinal の連続は状態静穏性を証明しない。** fixture setup/teardown 中の変更、
  setup skip/error が ordinal を消費しない経路、rerun が失敗 post を pre に使う経路の 3 つで、
  現行なら赤になるものが緑になる。

### (b) 親の対案 — `real-repo` とは別の専用 group

**(a) と同じ理由 (node id 接尾辞) で同時に死んだ。** 親の誤りとして撤回した。

### (c) 親の第 2 案 — 事前を旧実装、事後を新実装で取って比較する

**検出力が等価でない。** 壊れた新実装が事前値をそのまま返すと
`reference_pre(X) == optimized_post(X)` が成立し、**殺したい「実測値を捨てる」変異を
比較構造そのものが隠す。** 敵対レビューの指摘により撤回した。

## 4. 採用した設計と、そこから出た最重要の知見

出力 tuple を 1 bit も変えず、`Path.rglob` + `read_bytes` を `os.scandir` へ置換した。
検出集合を変えないので、上記の穴すべてに構造的な免疫を持つ。

### 素材: 並列化は単独計測では 4 倍、並列環境では有害だった

| 構成 | file wall | `test_real_seal` (この file の critical path) | guard 11 本 (個々) |
|---|---|---|---|
| base (wave 前) | 42.19s | 39.34s | 23.7s |
| `os.scandir` + 4 thread | 51.57s | **48.9s** | 15.3s |
| **`os.scandir` のみ (最終形)** | **41.78s** | **39.19s** | **15.4s** |

- login node 単独では `os.scandir` + 8 thread が **5.79s → 1.43s (4.05 倍)**、
  競合の無い直列走行では焦点 11 実行が **128.39s → 35.46s (3.6 倍)** だった。
- しかし **32 worker の並列走行では thread は guard を 1 秒も速くしない** (15.3 vs 15.4s)。
  **disk が律速**なので thread を増やしても bytes の到着は速くならず、待ち行列を長くするだけ。
- その結果 thread は**同時走行の critical path を 9.7s 飢えさせた**。
  害は「隣人を飢えさせる」形で**非対称に大きい**。
- **効いていたのは `Path.rglob` → `os.scandir` の置換だけ**であり、それは
  並列環境でも guard を 23.7 → 15.4s (**-35%**) にした。

**D104 決定 (4)「性能施策の一次証拠を duration にしてはならない」の再確認である。**
単独計測の高速化率を並列環境へ一般化してはならない。実測値をコードのコメントへ残した。

## 5. 等価性の主張 (敵対レビューにより狭めた)

**「出力が常に完全一致する」は偽である。** 次の 3 つで新旧の挙動が違う (いずれも fail-open ではない)。

- 親からは列挙できるが**中を読めない directory**: 旧 `rglob` は再帰時の `PermissionError` を
  抑制して `("dir", ...)` 行を含む tuple を作るが、新実装は `os.scandir` の例外を伝播する。
- **root 自体が通常 file**: 旧は空列挙、新は `NotADirectoryError`。
- **走査中の tree 変化**: 新は全 entry を分類してから hash、旧は path ごとに分類と hash をする。

主張は **「安定しており root と全 directory が読める通常 POSIX tree を定義域として、
実 `output/` (11,033 entry、3 走) と synthetic fixture で出力 tuple が一致し、
登録変異 12/12 を kill した」** に限定する。定義域を docstring に明記した。

## 6. 検出力を守った 4 つの正例

- `..._matches_reference_and_is_deterministic` — tmp tree で旧実装 (独立 oracle として保持) と
  完全一致。file / 空 file / **同 size 異内容** / 空 dir / 深い入れ子 / **file symlink・dir symlink**
  を含む。**実 `output/` に symlink は 0 件なので、symlink 枝はここでしか検証されない。**
- `..._default_root_reobserves_dependencies` — `_walk_entries` と `_digest` を合成値へ差し替え、
  **引数なしで 2 回呼ぶ**。1 回目で「実 root を特別扱いする / 実測値を捨てる」変異を、
  2 回目 (合成値を差し替えて再観測を要求) で「**初回だけ実測し以後 cache を返す**」変異を殺す。
  **実 `output/` を 1 度も走査しない。**
- `..._propagates_digest_failure` — `_walk_entries` に存在しない path を返させ、
  **実物の `_digest` の `open`/`read`** を通して例外伝播を検査する。
  `_digest` 自体を差し替えると、内部で `OSError` を握り潰す退行を検査できない。
- `..._reference_is_independent` — 依存を poison しても reference が旧経路の期待を返す。
  reference が新実装へ委譲する 1 行変異で等価性テストが恒真になるのを防ぐ。

## 7. 変異 12 件の結果 (baseline PASSED / rc=0)

**全 12 件が検出された (SURVIVED 0)。** 内訳は M01〜M08・M11 が期待どおりの
完全一致 KILLED、M10 のみ初回が MISMATCH で、実測から導いた完全集合で再登録・再走した。

| # | 変異 | 結果 |
|---|---|---|
| M01 | `_digest` の SHA-256 を長さへ置換 | KILLED (tmp 等価性) |
| M02 | symlink 行を落とす | KILLED (tmp 等価性) |
| M03 | 空 dir 行を落とす | KILLED (tmp 等価性 + canary) |
| M04 | 入れ子再帰を 1 段で打ち切る | KILLED (tmp 等価性) |
| M05 | 出力の sort を外す | KILLED (tmp 等価性 + canary) |
| **M06a** | 実 root で固定値を返す | **KILLED (canary 1 回目)** |
| **M06b** | 実 root で初回実測・以後 cache | **KILLED (canary 2 回目 = 再観測)** |
| **M07a** | digest ループで例外を握り潰す | **KILLED (fail-closed)** |
| **M07b** | `_digest` 内部で `OSError` を固定値へ | **KILLED (fail-closed)** |
| M08 | 相対 path の基準を取り違える | KILLED (tmp 等価性) |
| M10 | 引数なしの既定 root を `ROOT` にする | 初回 MISMATCH → 完全集合で再走 |
| **M11** | reference が新実装へ委譲する | **KILLED (reference 独立性)** |

**M06a / M06b / M07a / M07b / M11 は、段 6 の敵対レビューが「段 5 の実装では殺せない」と
指摘した型そのものである。** fix 後にそれらが実際に KILLED されたことで、
指摘が real であったことと fix が効いたことの両方が実測で確かめられた。

### erratum — M10 は過剰決定的で失敗 node 集合が非決定だった (DW-M03 / DW-M08)

**3 走ぶんの実測を残す。**

1. **初回 (`mutation-ledger.json`)**: 期待 = canary 1 本。実際 = **canary + guard 10 本の 11 node**。
   機序は「既定 root を `ROOT/"output"` から `ROOT` へ変えると guard が repo 全体
   (`.git` や dispatch receipt を含む) を走査し、走行中に中身が変わって事前 ≠ 事後になる」。
   変異は殺されているが完全一致ではないので契約上 MISMATCH。
2. **再走 (`mutation-ledger-m10.json`)**: 実測から導いた 11 node の完全集合で再登録したが、
   **また MISMATCH**。突き合わせると **10 node 共通・1 node 入れ替わり**
   (`..._contamination[launch-start]` ⇄ `..._resume_rejects_renamed_run_dir`)。
   → **この変異の失敗 node 集合は非決定である。** どの guard が落ちるかは
   「その guard の実行窓の間に repo が変わったか」というレースで決まる。
3. **単一理由へ分割 (`mutation-ledger-m10b.json`)**: 原因は変異が**過剰決定的**だったこと —
   「どの root を既定にするか」と「揺れる木を走査するか」の 2 つを同時に変えていた。
   **安定した誤 root (`ROOT / "docs"`) へ差し替える M10b** に置き換えた。これなら guard は
   事前・事後とも同じ安定 tree を見るので通り、**canary だけが落ちる決定的な集合**になる。

**教訓 (2 つ)。** (a) 既定値を変える変異は、その既定値に依存する全 consumer を期待集合に数える。
(b) **走査対象を「揺れる木」へ広げる変異は失敗 node が非決定になり、DW-M08 の完全一致を
原理的に満たせない。** 変異は「検査したい 1 つの束縛」だけを変える形に分割する (DW-M03 の単一理由性)。

## 8. 一次資料

すべて `dev-wave-jobs/dev-wave-floor-campaign-speed/` に置く (repo 外)。

- `s2-plan.md` / `s3-sol-out.md` / `s3-luna-out.md` — 段 2 プランと段 3 敵対 2 本
- `s4-ruling.md` / `s6-ruling.md` — 段 4・段 6 の裁定 (所見の real/refuted 表を含む)
- `s6-sol-out.md` / `s6-luna-out.md` — 段 6 敵対レビュー 2 本
- `focal-base.log` / `prof-base.out` — 基線の cProfile (ncalls が一次証拠)
- `serial.log` / `final.log` / `threads.log` — paired A-B-A の実測
- `mutation-spec.json` / `mutation-ledger.json` — 変異 12 件
- `ruling-package.md` — C2 の裁定パッケージ
