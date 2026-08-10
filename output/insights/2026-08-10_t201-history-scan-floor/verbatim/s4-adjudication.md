# 段 4 v2 裁定 — dev-wave-suite-floor-recheck

段 3 v2 の 2 レンズ (sol = 正しさ境界、luna = 実効性・計測) はいずれも **NO-GO** を返した。
親は下記を裁定し、プラン v2 を確定する。base main `34957a24`。

## ユーザー裁定 (2026-08-09、本セッションで直接得た)

**「copy 元節を意図的に外す」を採用。** すなわち `_history_touches_path` の argv から
`--find-copies-harder` を除去し、**「receipt を未変更のままコピー元にした commit」だけを
検出しなくなる**ことを明示的な受理集合の縮小として受け入れる。
receipt 自体の M / D / T / R は従来どおり検出する。

この裁定は 2026-07-31 の受理条件「受理集合不変を positive control で固定してから入れる」を
**ユーザー自身が更新したもの**である。したがって本 wave の positive control の役割は
「不変であることの証明」ではなく、**「変わるのはこの 1 ケースだけであることの固定」**に変わる。

## 親が段 3/段 4 で直接実測した事実

**測定環境: ログインノード pegasus02 (共有・単独走行 1 回)。一次証拠にはせず、計算ノードで測り直す。**

| 対象 | 現行 (`--find-copies-harder` 付き) | 除去後 (`-M -C` のみ) |
|---|---|---|
| HEAD 1 commit | 4.208 秒 / 再走 7.609 秒 (CPU 約 1.0 秒) | 0.019 秒 |
| descendant 20 commit (`--stdin`) | **45.31 秒 (CPU 13.2 秒)** | **0.180 秒** |
| 出力行数 (20 commit) | 238 行 | 238 行 (**一致**) |

- 1 commit あたり **2.27 秒 wall / 0.66 秒 CPU**。descendant 1529 件へ外挿すると
  **単走 3470 秒、production の 8-thread pool でも約 434 秒**。受入全走 1055〜1210 秒の
  **約 4 割**を、この 1 機構が占める。**D104 決定 (2) は現規模でも成立し、当時より強く効いている。**
- 費用の主因は CPU ではなく I/O である (wall 4〜7 秒に対し CPU 1.0 秒)。
  `--find-copies-harder` は未変更ファイルまで copy 元候補として読むため、
  `output/` の 9435 ファイル / 284 MB を commit ごとに共有 FS から読む。
- **全 2183 commit のうち receipt path を触った commit は導入 commit 1 個だけ**
  (`git log --format=%H -- <RECEIPT_REL>` = 1 行)。現行は毎回 1529 commit を全走査して
  「何も見つからない」ことを確認している。
- `--stdin` batching の節約は process 起動分だけで **1% 未満**。段 2 v2 の推奨候補は
  D104 決定 (3) により**不採用**とする。

## 所見の裁定

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| A-1 | 全史 equivalence は positive control になっていない (新旧とも全件 False で通る) | **real (blocker)** | ユーザー裁定で目的が変わったため、全史 differential は「実履歴では挙動が変わらないことの確認」に格下げ。**恒久 control は合成 matrix**とする。`true_count` を必須出力にし、0 なら vacuous と明記する |
| A-2 | fallback が equivalence を恒真化できる | **real (blocker)** | **fallback を実装しない**。argv から token を除くだけの変更なので fallback 経路自体を作らない |
| A-3 | 全史の head 集合が production consumer を閉じていない (`s8b_oracle_report.py:209` が WAL の任意 `validation_head` で `inspect_receipt_history` を呼ぶ) | **real (blocker)** | brief v2 の M3 を訂正する。**直接 callsite 1 箇所 ≠ production entrypoint 1 箇所**。全史 differential の head 集合は `{HEAD, --all refs}` の reachable union とする |
| A-4 | 集約・error precedence の control 不足 | **real (must-fix)** | 既存の空・単一・逆順テストを残し、`{error,false,true}` → True、`{false,error}` → `receipt.git_error` を追加登録する |
| A-5 | merge matrix が二親 1 例に縮んでいる | **real (must-fix)** | 三親 merge の第三親 `M`/`T`、symlink・submodule の typechange、外部親に receipt 不在の `A=False` を control に含める |
| A-6 | `DW-O09` pin 閉包が不完全 (`test_s8b_oracle_driver.py:200/1717/1771`、D78 の byte 不変) | **real (must-fix)** | 追加 pin を no-touch として brief へ記録。**receipt 本体と既存 golden は一切触らない** (本変更は argv のみ) |
| A-7 | reverse query の比較 command 固定不足 | **real (nit)** | reverse 候補は**不採用**なので措置不要 |
| B (総括) | `--stdin` batching は効果 0.73% | **real (blocker)** | **不採用** (上記) |
| B | probe の 19 所見が閉じていない | **real** | **probe 機構そのものを破棄する** (下記) |
| B | before/after の SHA・allocation・順序・必要走数が未固定 | **real (blocker)** | 下記の計測設計で固定する |

**refuted はゼロ。**

## 規律 5 に基づく破棄 — probe 機構を捨てる

段 5 で作った probe 6 ファイル (pytest plugin / cgroup sampler / analyzer / PBS driver /
microbench / static inventory) は、**旧 scope (内訳の帰属推定) のための機構**であり、
レビュー 2 本で所見 19 件・NO-GO を受けている。裁定が「argv から 1 token を除く」に確定した今、
必要な証拠は **before/after の受入全走 wall** と **全史 differential** だけになった。
規律 5 (段階導入 / 盛らない) と D104 決定 (3) に従い、**probe 6 ファイルは採用しない**。
job dir に残すが repo へは入れず、成果物としても数えない。

## プラン v2 (確定)

### 実装 (repo 内、3 単位・所有素集合)

- **単位 A (Codex author 1)**: `orchestrator/campaign/t080_freeze_migration.py`
  — `_history_touches_path` の argv から `"--find-copies-harder"` を除く。
  docstring に「この述語は receipt を未変更のままコピー元にした commit を検出しない
  (2026-08-09 ユーザー裁定)」を明記する。**それ以外の挙動を変えない。**
- **単位 B (Codex author 2)**: `orchestrator/tests/test_t080_freeze_migration.py`
  — positive control。**実装を見ずに、下記の期待表から書く**。
- 単位 A と B は同時に投入し、B は「単位 A が入るまで赤になる」ことを事前に申告してよい。

### positive control の期待表 (単位 B はこの表を仕様として使う)

合成 repo (repo 外の tmp) に次の commit を作り、`_history_touches_path(commit, RECEIPT_REL, root)` の
期待値を固定する。**すべて非 vacuous であること** (`True` を返すケースが 1 件以上あること) を
テスト自身が assert する。

| ケース | 期待 |
|---|---|
| receipt を変更した commit (M) | **True** |
| receipt を削除した commit (D) | **True** |
| receipt を別名へ rename した commit (R、receipt が source) | **True** |
| 別ファイルを receipt へ rename した commit (R、receipt が destination) | **True** |
| receipt を regular file → symlink にした commit (T) | **True** |
| receipt を regular file → submodule entry にした commit (T) | **True** |
| receipt を**追加**しただけの commit (A) | **False** (現行も False) |
| 無関係なファイルだけを変更した commit | **False** |
| root commit で receipt を追加 | **False** |
| 2 親 merge で第二親だけ receipt が別 blob (M) | **True** |
| **3 親 merge で第三親だけ receipt が別 blob (M)** | **True** (A-5) |
| **receipt を未変更のまま同内容の別ファイルを追加 (旧 C)** | **False** ← **本裁定で変わる唯一のケース。この行が変わったら裁定のやり直しである旨をテストに書く** |
| 存在しない commit | `MigrationError` |
| `_any_history_touches_path({error, false, true})` | **True** (error より True が勝つ) |
| `_any_history_touches_path({false, error})` | `receipt.git_error` を送出 |
| `_any_history_touches_path(空集合)` | **False** |

### 計測 (計算ノード 1 allocation、単位 C = Codex author 3 が driver を書く)

- arm 順: **BEFORE → AFTER → BEFORE** (同一ノード・同一 allocation・順序 counterbalance)。
  BEFORE = 変更前 commit、AFTER = 変更後 commit。受入 shape のまま走らせる (flag を足さない)。
- **判定閾値を事前登録**: 走行間 range は D104 実測で 6.56%。現規模 1200 秒で **84 秒**。
  2 本の BEFORE の差が 84 秒を超えたら「ノード外乱」として判定不能にする。
  効果の主張は `mean(BEFORE) − AFTER` が 84 秒を**超えた場合だけ**行う。
- **全史 differential**: `{HEAD, --all refs}` の reachable union の全 commit に対し、
  現行 argv と新 argv の判定値を比較する。48 並列。**`true_count` を必ず出力**し、
  0 なら「vacuous な確認であり positive control ではない」と結果に明記する。
- repo の worktree を破壊的に変更しない。BEFORE/AFTER は別 worktree か、
  終了時に元 HEAD へ戻すことを job 自身が検証する。

## 変異事前登録 (DW-M01)

実装差分があるため免除されない。単一理由で落ちる node を事前に指定する。

| ID | 位置 | 変異 | 単一理由で落ちるテスト |
|---|---|---|---|
| M1 | `_history_touches_path` argv | `-M` を落とす | rename (source / destination) の 2 ケース |
| M2 | `_history_touches_path` argv | `-m` を落とす | 2 親 merge / 3 親 merge のケース |
| M3 | `_history_touches_path` argv | `--root` を落とす | root commit のケース |
| M4 | 述語 | `status_code in {"M","D","R","C","T"}` へ `"A"` を足す | receipt を追加しただけの commit = False のケース |
| M5 | 述語 | `path in fields[1:]` を `path == fields[1]` にする | rename source のケース |
| M6 | `_any_history_touches_path` | error より True を優先する規則を反転する | `{false, error}` / `{error,false,true}` のケース |
| M7 | argv | `--find-copies-harder` を**戻す** | 「旧 C ケースが False であること」を固定したテスト (裁定の逆行検出) |

各変異は他層に同じ入力を拒否する gate が無いことを実装時に確認する。

## 本 wave が出さない結論

- 内訳の帰属推定 (どの成分が何秒か) は出さない。probe を破棄したため測っていない。
  出すのは **before/after の受入全走 wall** と **機構単体の単価**だけである。
- (b)(c)(d) は実装しない。(b) は本 wave の実測 (費用は tracked bytes への I/O に比例) が
  直接支持するので、裁定材料として返す。
