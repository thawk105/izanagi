# [T-902] holdout live scan の係数削減 — 「ファイル数比例を外す」は契約上できなかった

2026-08-18 / wave `dev-wave-t902-holdout-scan-cost` / base main = a160f4aa

## 何をしたか

`orchestrator/campaign/s8b_holdout_freeze.search_repository` の regex 係数を削った。
出力は canonical bytes まで完全不変。受理集合 (`_assert_search_pass` の
conjunction = 0 かつ positive_control > 0) は 1 bit も変えていない。

- **B'** 軸ごとの prefilter。既存 `_derive_required_literal` を 1 要素 mapping
  `{axis: expression}` で呼び直すだけで、新しい regex parser を書かない。
- **C** 同一 `search_repository` 呼出し内で expression 単位に hit 集合を memo 化する。
  production 3 候補 × 3 軸 = 9 走査のうち相異なるのは 5 本。

## 一番の発見 — 裁定文が求めた「ファイル数比例をやめる」は達成できない

[T-915] (2026-08-12 第 6 束) は「ファイル数比例をやめる最適化として T-902 が扱う」と裁定した。
**これは出力契約と両立しない。**

- `search.skipped_binary_count` は「全 file について binary/UTF-8 判定した結果」であり、
  全 file を読まないと出せない。
- regex hit は file の任意位置にありうるので、先頭だけ読む短絡もできない。
- `exempt_exact` の免除判定は全 bytes の SHA-256 を要する。

よって 13,548 file の列挙・open・read・decode は削れない。段 2 プランと段 3 の 2 レンズが
独立に同じ結論へ達し、親の実測もこれを支持した。**本 wave の到達点は係数削減である。**

## 律速は Python ではなく lustre のメタデータ遅延だった

`/work` は lustre。cProfile (end-to-end 16.783s) の内訳:

| 項目 | 秒 | 性質 |
|---|---|---|
| `io.open` × 13,548 | 3.40 | file 数比例 |
| `posix.stat` (`is_file`) × 13,548 | 2.70 | file 数比例 |
| close × 13,548 | 1.78 | file 数比例 |
| `_normalise_files` | 0.82 | file 数比例 |
| `re.Pattern.search` × 8,595 | 4.70 | prefilter 通過 file 比例 |
| `enumerate_repository_files` (git × 3) | 1.25 | ほぼ定数 |

syscall あたり: `os.stat` 163.0 us/file、open+read+close 345.6 us/file。
`pathlib` と raw `os.open` の差は 10 us 未満で、**Python overhead ではない**。
`is_file()` は warm 状態でも 171.6 us/file (合計 2.324s) で、ページキャッシュでも消えない。

## 却下した案とその理由

### A — `is_file()` を open 後の `os.fstat` へ畳む (実測 2.3 秒 = 18% の価値)

**性能はあるが厳密等価にならないので却下した。** 段 2 と段 3 レンズ A が独立に境界表で反証。
directory / symlink 先の特殊 file / FIFO / Unix socket / char・block device /
dangling symlink / 列挙後の削除 race / stat 権限不足 / NUL を含む path の 9 系統で、
例外の型・文言・**「そもそも open しない」という現行挙動**を保存できない。
特に FIFO と device は現行が一度も開かないものを開くことになる。

性能を理由に厳密等価性を緩めない (規律 2 の対称)。

### B の当初案 — 新しい regex parser で value literal prefix まで導出する

**追加で買えるのは 0.71 秒 (end-to-end の約 5%) だけだったので却下した。**

scan 部のみの実測 (read 経路は共通、各 3 試行の最小値):

| 形 | scan 部 |
|---|---|
| 現行 + memo | 3.221s |
| **B' 既存 helper を軸ごと再利用** | **1.928s** |
| B 新 parser で value prefix | 1.214s |

その 5% のために「量指定子・escape・文字クラス・inline flag・空 alternative・
nested group・非 ASCII」を自前で正しく扱う新文法を背負う取引はしない。

**親が実際に踏んだ罠がこれを裏づける。** 親が最初に書いた「metachar 直前までを literal prefix と
する」規則は、量指定子が literal 末尾に掛かる場合に false negative を出す
(`(?:ycsb_rmw=0*)` の prefix を `ycsb_rmw=0` とすると、regex に一致する `ycsb_rmw=` を落とす)。
無作為生成 40 万試行の fuzz で、素朴版は **prefilter 適用 78 件のうち 5 件で反例**、
末尾 1 文字を落とす修正版は 136,142 件で反例 0 だった。B' はこの規則を導入しないので、
**この攻撃面ごと消える。**

### `git grep` / `--cached` / 結果 cache への読取経路置換

集合が**既に一致していない**。in-memory 524 件に対し worktree grep 519 件、
`ycsb_` は 955 件に対し 944 件。untracked / submodule / worktree bytes の扱いが異なり、
binary・UTF-8・免除の意味論を別途証明しないと受理集合を静かに変える。別 wave の裁定事項。

## 検出力の設計 — 出力等価な変異をどう殺すか

軸 prefilter を wave 前の形 (共通 `ycsb_` のみ) へ戻す変異は**出力が変わらない**。
report の比較では殺せない。**唯一の番人は regex の発火回数**である。

等価性 fixture の無関係 text を `irrelevant\n` から `ycsb_unrelated\n` へ変えることで、
同じ入力に対する `re.Pattern.search` の発火回数が三段に分離する。

| 状態 | `ycsb_unrelated\n` への発火回数 |
|---|---|
| 最適化 (軸 prefilter + memo) | 0 |
| 共通 prefilter のみ無効化 (memo だけ生存) | 5 |
| 完全 slow path (`_scan_one` 自体を差し替え) | 9 |

段 3 レンズ A が指摘したとおり、`_derive_required_literal` を `None` にするだけの
従来の「slow path」比較では、新しい層が slow 側にも残って **assert が恒真**になりうる。
`M._scan_one` **自体**を prefilter も memo も持たない reference へ差し替え、
その reference が rr80 / rr20 / positive の 3 回呼ばれたことまで assert して塞いだ。

## 段 6 で両レンズが独立に指摘し、親が採った訂正

**出力に存在しない順序を守るための全走査を、テストが設計契約として固定していた。**

初版実装は `per_axis_paths` を `texts` の挿入順で再構築し、conjunction 用に再度 `texts` を
全走査していた。しかし report に出るのは `per_axis_counts` の件数だけで、path 順序は出ない。
`conjunction_hits` は直後に独立して sort される。つまり「cache の集合順で組む」変異は
**等価変異**であり、それを守るための走査は不要だった。

実費は 18.23 ms (全体の 0.18%) と些少だが、**ファイル数比例の走査をテスト契約として凍結する形**
そのものが test-time regression の既裁定に反する。集合演算 (`len(hits)` と
`sorted(first.intersection(*rest))`) へ単純化し、当該変異を登録から外した。

## 親自身の所見 2 件は、どちらも実測で自壊した

記録として残す。**測らずに裁定していれば無意味な変更を実装子へ投げていた。**

1. 「等価性 fixture の text 変更で検出力が消えた」→ **取り下げ**。元の性質は
   `test_empty_prefilter_is_distinct_from_disabled_prefilter` が維持している。さらに親自身の
   実測で、共通 literal は軸 literal に部分文字列として包含され (実 expression 9 本すべてで
   包含 = True)、除去しても観測可能な差が出ない**等価変異**だと判明した。
2. 「共通 literal 走査は冗長だから除去すれば約 0.6 秒浮く」→ **不採用**。実測は **0.030 秒**
   (共通+軸 0.755s vs 軸のみ 0.725s)。見積もりが 20 倍外れていた。

## 凍結側の状態 — 記述を 1 件訂正した

親は段 1 brief で「live bytes を束縛する pin は無い」と書いたが**不正確**だった。正しくは:

- **generator source** (`orchestrator/campaign/s8b_holdout_freeze.py`) の bytes pin は
  `freeze_verification_hold.HELD = True` により**評価されない**。現行 hash
  `4bd0bc638e30f183b0c119e2be38bd3cd852f51df8bea5494497a3033a487033` は凍結記録
  `1910fff38edf0e58f5bff221c29660a8f85dd0ed1b5c980234ec1af098584e5f` と**既に不一致のまま
  全検査が緑**である。→ 編集してよい。**[T-902] を阻んでいた「1 byte 変えると freeze 再発行」
  の閂は実在しない。**
- **凍結 artifact** (`output/s8b-freeze/holdout_freeze.json`) の raw bytes は
  `s8b_ratified_freeze.load_legacy_freeze` が **hold と無関係に無条件で** pin している
  (`V1_FREEZE_SHA256`)。`test_frozen_artifacts.FROZEN_MANIFEST` も同 file を持つが
  `HELD_FROZEN_MANIFEST_KEYS` 側なので現在は未検査。→ 1 byte も変えてはならない。

また `verify_document` は `search.file_count` / `skipped_binary_count` を「非負整数か」しか
見ない。記録値 1197 / 11 に対し実測は 13,548 / 21 で、それでも verify は通る。
scope 件数は bytes 束縛されていない。

## 受入経路に残るもの (ユーザー裁定へ返す)

実 repo 全走は 2 か所だけ。

- `test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`
  → 既に `tracked_files` 軸で**恒久保留済み** (`growth_test_holds.py:145`)。
  保留理由文「Scans the real checkout, so cost grows with tracked files.」は本 wave 後も正しい。
- `test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan`
  → **未保留**、call 14.57 秒、tracked file 数比例。本 wave の係数削減は受けるが比例は残る。

後者の扱いは (a) 恒久保留 / (b) synthetic fixture へ分解 / (c) 現状維持 の 3 択で、
保留の新設は**ユーザー明示命令のみ**で可能なため親は提案に留める。

## 変異 matrix

`mutation-ledger.json` が正本。repo_head = 4ef5ba65c9a39d8b0fbc2234efcc0f36aa82b8a2、
runner = `tools/run_tests.py orchestrator/tests/test_s8b_holdout_freeze.py --force-dispatch`、
dispatch 経路。

**baseline PASSED / KILLED 9 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0。**

| 変異 | 期待 node 数 | 結果 |
|---|---|---|
| m1 軸 prefilter を wave 前の共通 literal のみへ戻す | 7 | KILLED |
| m2 共通 literal 判定を `text[:8192]` へ狭める | 1 | KILLED |
| m3 軸 literal 判定を `text[:8192]` へ狭める | 1 | KILLED |
| m4 memo key を expression でなく axis にする | 25 | KILLED |
| m5 `memo.texts is texts` の identity 束縛を外す | 1 | KILLED |
| m6 memo の内容変化 fail-closed を削除する | 1 | KILLED |
| m7 共通 literal が None でも軸 literal を導出する | 2 | KILLED |
| m8 `MappingProxyType` を外す | 1 | KILLED |
| m9 conjunction を intersection から union にする | 26 | KILLED |

**m1 は出力等価な変異である。** 唯一の番人は `re.Pattern.search` の発火回数であり、
`test_axis_prefilter_skips_common_only_text_and_memo_searches_unique_expressions` を含む
7 node で赤になった。等価性テストの report 比較だけでは殺せない。

**m2 / m3 はそれぞれ `test_prefilter_scans_common_and_axis_literals_after_8192_bytes`
ただ 1 node で赤になった。** この fixture は段 6 レンズ C が要求したもので、
それ以前の全 fixture は hit が短文だったため、判定を先頭 8KB へ狭める変異を 1 件も検出できなかった。

### 登録から外した等価変異

`type(expression) is str` を `isinstance(expression, str)` へ緩める変異は probe で SURVIVED
(注入実在は `anchor_counts` = 1 で確認、120 passed)。str subclass のとき
`_derive_required_literal` の `all(type(e) is str ...)` gate により `required_literal` が None となり
prefilter が全面無効になるため、memo に載るのは純粋な regex 結果である。subclass key で
再利用しても挙動が変わらない**等価変異**と判定し、本走の登録から外した (DW-M01)。

## 実測 (2026-08-18、Pegasus login、lustre、load avg 21〜24 / 96 core)

計測 checkout = worktree `dev-wave-t902-holdout-scan-cost`。login ノードは負荷変動が大きく
単発値の分散が大きいため、複数試行の最小値と中央値を併記する。

### 本 wave の削減 (B'+C、read 経路は据え置き)

`probe_bc_only.py` 6 試行 (production 12.791〜21.363s / B+C 9.086〜12.112s):
**最小同士 12.791s → 9.086s (29.0%)、中央同士 14.31s → 11.18s (21.9%)。**
正直な値は **2〜4 秒・20〜30% の削減**である。

### 出力不変の検証

`probe_verify_impl.py` 4 試行 (fix 後)。着地実装と、prefilter も memo も持たない
参照 scanner の report を canonical bytes で比較し、**4/4 で等値**。
report の sha256 `63c482d2fc63a8edadcd2a944f9fa81f903ff85a8bff1922a3e3a5e2dfef153a` は
**wave 前の production が出していた値と同一**である。

なお同 probe が出す「完全 slow 29.4s → 着地 10.0s (66%)」は、
**wave 前から存在した共通 prefilter の効果を含む**ため本 wave の成果ではない。

### 受入経路

`test_s8c_preregistration_invariant.py` baseline = 13 passed / 42.87s、
うち `test_wave_files_do_not_contaminate_production_holdout_scan` が call 14.57 秒。

## エージェント工数

codex 子 8 本 (plan 1・consult 3 (うち 1 本は認証失効で不受理・再投入)・author 1・review 2・fix 1)。
plan / consult は `reasoning=max`、author / review / fix は `high`。
段 5 author は 32 model call / 600 秒、段 6 fix は 32 call / 504 秒。

**codex 認証が wave 中に失効した (13:01 JST、`401 Unauthorized ... auth error code: token_revoked`)。**
consult luna は 371 秒・34 model call・出力 13,874 token を消費した後に websocket 再接続で
401 を踏んで rc=1・出力 0 bytes で死んだ。consult sol は同じ 401 を 3 回受けながら既存 session で
耐え、認証回復後の 13:09 に完走した。並行 wave からは「枠切れ (数秒・token ゼロの即死)」と
周知されたが、**本 wave の失敗はその型ではなく認証失効である**。再投入は別 artifact-root で行った
(同一 prompt は job-id が同じになり receipt 上書き拒否で rc=2 になる)。

## erratum E1 — 変異台帳が production holdout scan を汚染したので可逆 defang した

**事象。** 段 7 の記録 commit `54f747c2` が変異台帳を raw のまま入れた結果、
実 repo の holdout scan が rr80 / rr20 とも conjunction hit 1 件
(`output/insights/2026-08-18_t902-holdout-scan-coefficient/mutation-ledger.json`) を返し、
`test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan`
が赤になった。台帳は変異走行の pytest stdout を保持しており、その中に等価性 fixture が書く
三軸文字列がそのまま入っていたためである。

**これは commit 2473483f が test fixture について直したのと同じ型を、記録側から再発させたものである。**
`DW-S07` の「凍結前に全 gate の検出語 (三軸語・placeholder) を機械走査し、hit は
原文 hash 付きの可逆 defang + erratum とする (D88)」を、親が段 7 で適用し損ねた。
他の insight にも単一軸の語は多数あるが、**同一 file 内で三軸が揃うのは本台帳だけ**だったため、
conjunction 検査はそこだけを指した。

**対応。** 台帳の JSON string 内に現れる軸 key 接頭辞の下線 1 文字を、
JSON の 6 文字 unicode escape 表記 (backslash + `u005f`) へ置き換えた (325 箇所)。
JSON parser はこの表記を下線として読むため、**`json.load` の結果は原文と完全に一致する**
(実測で等値を確認済み)。raw bytes からのみ三軸 literal が消える。

- 原文 sha256   = `bcef5f3c38436fab529e1f3b208b291ff8afe6d67232b19c117b8383f34a9631`
- defang sha256 = `c02e3911ddfe85a43c381f92d0d9b87e5472003ca5b5300401a396fd0b6f6fbc`
- 復元法: `json.load` するか、raw text の当該 escape 表記を下線へ戻す。
- defang 後の実測: rr80 / rr20 とも conjunction 0 件、陽性対照 83 件 (> 0)。

**教訓。** 変異台帳は runner の stdout を丸ごと保持するため、**gate の検出語を持つ fixture を
使う wave では台帳自身が gate を破る**。台帳を insights へ入れる前に、その wave が関わる
gate の検出語で raw 走査するのが要る。今回は holdout の三軸だったが、placeholder gate や
他の literal gate でも同型が起こる。
