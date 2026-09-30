# check_docs.py を判定を変えずに約 2.4 倍速くした (md_5)

wave: `dev-wave-check-docs-speed` (2026-09-30、branch `worktree-dev-wave-check-docs-speed`)
基準 commit: `4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037` (main)。実装 commit: `41b678391a71491127e9d78205250cdf549fb01e` → `535790d49c867c55fb033cab8b1c51a5abdd340f` (最終)。
依頼: `/work/1/SFC/tanab/tmp/speedup-2026-09-29/md_5.txt` (共通指示 `common.txt`)。「判定 (どの入力を緑・赤にするか) を 1 つも変えずに速くする」。

## 結論

- 計算ノードの同じノードで旧版と新版を交互に 5 回ずつ走らせた (同時刻対照)。wall の中央値は **旧 37.49 秒 → 新 15.52 秒 (比 0.414)**。
  旧 5 走は 37.29〜37.60 秒、新 5 走は 15.51〜15.91 秒で、分布は重ならない。全 12 走 (予備走を含む) の stdout は同じ sha256 だった。
- 判定は変わっていない。確かめた範囲は「確かめたこと」の節のとおり (main の現物、故障を入れた 6 種の木、test_check_docs.py の全 fixture、旧実装との網羅対照、変異 8 件)。
- 最大常駐メモリは 309,044 KiB → 318,288 KiB (+9,244 KiB、+3.0%)。途中の版では +61 MiB あったので、原因を突き止めて直した (後述)。
- 残る時間の大半は carry 参照 (95.9 万件) の走査で、worklog の entry が増えるほど伸びる。次の一手に書いた。

## 変更前の律速 (計算ノード、cProfile、1 走)

request 37675.nqsv (Elapse 78 秒、cProfile 下 72.1 秒)。要約は `raw/profile-before-4f412c67.txt`。
`_check_backlog_guard` が 65.5 秒 (91%) を占め、その中身は CPU 処理だった。stat は計算ノードでは 2.9 万回で 1.4 秒しかない
(依頼文の「stat で約 25 秒」は login での観測。login では I/O 待ちが大きく、後述の参考値を参照)。

| 関数 (tools/check_docs.py) | 呼出し回数 | 累積 秒 (変更前) | 累積 秒 (最終版) | 何が重かったか |
|---|---|---|---|---|
| `_line_number` | 1,933,522 | 16.2 | 3.5 | 行番号を毎回ファイル先頭から数え直していた (`str.count`) |
| `_visible_markdown_lines` | 10,382 → 8,374 | 17.1 | 6.8 | 同じ entry 本文を何度も解析していた |
| `_top_level_ids` | 6,394 → 4,386 | 15.7 | 6.9 | 同上 (遷移先 entry の本文を 2 回目に解析) |
| `_top_level_item_raw_slice` | 958,893 | 6.8 | 2.7 | 1 文字ずつの走査 |
| `_archive_is_before` | 1,352,190 → 0 | 4.8 | — | archive 1,645 本の全ペアで毎回タイトルを正規表現で解析 |
| `_validate_entry_universe` | 1 | 28.6 | 15.9 | 上記の積み重ね (carry 95.9 万件) |
| `_check_backlog_guard` | 1 | 65.5 | 30.9 | 全体 |

最終版の値は計算ノード bnode007 の cProfile 1 走 (`raw/profile-after-535790d4.txt`、cProfile 下 34.7 秒)。cProfile は細かい関数を多く呼ぶ処理を重く見せるので、
表は「どこが減ったか」の帰属にだけ使い、速さの主張は下の同時刻対照だけで行う。

## 何を変えたか (tools/check_docs.py、Codex author)

1. `_line_number`: 改行位置の索引 (上限 4 件の LRU、`main()` の終了時に消去) を二分探索する。負の offset・範囲外も `str.count` と同じ規則に正規化する。
2. entry 本文の ID を entry ごとに 1 回だけ求め、「ID を持つ entry か」の判定と遷移先 (sink) の照合に共用する。archive 間の境界に使う先頭 entry の ID だけを archive と一緒に保持する。
3. `_top_level_item_raw_slice`: 1 文字ずつの走査を正規表現 `[\r\n]` の検索に置き換える (CR 単独・LF・CRLF の扱いは同じ)。
4. archive の順序検査: 全ペアの比較は残し (異常時の所見と順序を変えないため)、各 archive の先頭・末尾の entry 日付と番号を 1 回だけ求めて比べる。
5. `_visible_markdown_lines`: HTML comment の外で `<!--` を含まない行は comment 処理を呼ばない (呼んでも同じ行がそのまま返る)。
6. `_is_carry_candidate` の正規表現を事前に compile する (パターンは同じ文字列)。
7. (fix 第 2 巡) 2. で保持する ID 文字列を `sys.intern` で共有する。

検査項目の削除・閾値の緩和・対象の除外・早期打ち切りはしていない。`_safe_read_text` が毎回行う symlink / lstat の安全判定と読取 cache (T-1222) には触れていない。

### メモリ増の原因と修正

最初の版 (commit `41b67839`) は同時刻対照で最大常駐メモリを 309,024 → 371,380 KiB (+62,356 KiB ≈ +61 MiB) に増やしていた (`raw/e3-r2.json`)。
2. で保持する先頭 entry の ID は、全 1,645 archive で計 839,548 件 (平均 510 件) ある。種類は数百しかないのに、文字列が別々の実体として並んでいた
(短い文字列 1 件 ≈ 57 バイト + リストの枠 8 バイトで約 55 MB と見積もり、+61 MiB とほぼ合う。この帰属は算術による推定で、メモリ計測器で個別に確かめてはいない)。
`sys.intern` で共有した最終版は +9,244 KiB (+3.0%) で、wall は変わらなかった (`raw/e3-r3.json`)。

## 確かめたこと

### 1. 速さ (同時刻対照、計算ノード)

`bench_abab.py` (repo 外 probe、逐語は `verbatim/probe-scripts.md`) が同じ clone 木で旧/新を交互に走らせ、各走の wall と子プロセスの最大常駐メモリ (`wait4` の ru_maxrss) を記録した。予備走 1 往復は集計に入れていない。

| 版 | node | 旧 wall 中央値 (最小〜最大) | 新 wall 中央値 (最小〜最大) | 比 | 旧 RSS 中央値 | 新 RSS 中央値 |
|---|---|---|---|---|---|---|
| r1 (fix 前の途中版) | bnode010 | 38.29 (38.12〜38.48) | 16.35 (16.25〜17.00) | 0.427 | 309,144 KiB | 381,244 KiB |
| r2 (`41b67839`) | bnode006 | 37.52 (37.23〜37.70) | 15.51 (15.40〜15.59) | 0.413 | 309,024 KiB | 371,380 KiB |
| **r3 (`535790d4`、最終)** | bnode007 | **37.49 (37.29〜37.60)** | **15.52 (15.51〜15.91)** | **0.414** | 309,044 KiB | 318,288 KiB |

各行 n = 旧 5 走・新 5 走。3 回とも別の node で、旧の中央値は 37.49〜38.29 秒、新は 15.51〜16.35 秒だった。

### 2. 判定不変: main の現物と故障を入れた木 (E1、`equiv_real.py`)

main (`4f412c67`) の独立 clone 1 本で、7 つの状態それぞれについて旧→新の順に checker を走らせ、rc・stdout・stderr を bytes で比べた (`raw/e1-r3.json`、bnode013)。

| 状態 | 故障が検査に届いたか | 旧 rc | 所見数 | 新旧 bytes 一致 |
|---|---|---|---|---|
| 無改変 | — | 0 | 0 | 一致 |
| 宙吊り carry (末尾 entry に参照先の無い carry) | 届いた | 1 | 3 | 一致 |
| entry 番号の重複 (番号付き archive 2 本) | 届いた | 1 | 4 | 一致 |
| archive 順序の曖昧化 | 届いた | 1 | 4 | 一致 |
| 改行混在 (CRLF の archive と CR 単独の archive に宙吊り carry) | 届いた | 1 | 6 | 一致 |
| 可視性 (comment 内・fence 内の項目と可視の宙吊り carry) | 届いた | 1 | 3 | 一致 |
| carry 文法崩れ | 届いた | 1 | 1 | 一致 |

「届いた」は旧 checker の rc と stdout が無改変と変わったことを指す。最初の probe (r1、`raw/e1-r1.json`) では 3 種 (番号重複・改行混在・可視性) が届いておらず
(無改変と同じ出力)、判定不変の証拠にならなかったので、故障の入れ方を直して取り直した (`verbatim/s6-probe-fix1-ruling.md`)。
可視性の状態では、comment 内 (`[T-9996]`) と fence 内 (`[T-9995]`) の項目は所見にならず、可視の `[T-9993]` だけが所見になった (新旧とも)。

### 3. 判定不変: test_check_docs.py の全 fixture (E2、`equiv_fixtures.py` + `equiv_plugin.py`)

同じ旧 commit の test file を、旧 checker の clone 木と新 checker に差し替えた clone 木で直列に走らせた。pytest plugin が、checker を起動する subprocess 呼出しごとに
(node、呼出し順、引数、rc、stdout、stderr) を記録した (`raw/e2-r3.json.gz`、bnode007)。

- node 集合と各 node の結果は新旧で一致した (583 node: passed 580、skipped 3)。
- checker 呼出しは 455 node で計 727 回。rc・stdout・stderr はすべて一致した。
- 呼出し記録の差分は 3 件で、3 件とも **テスト側が渡す引数 `--expect-active-transaction` の値だけ**が違った (rc・stdout・stderr は一致)。
  この値は走るたびに変わる。同じ旧 checker 同士でも r1・r2・r3 で値が異なる (例: `test_spool_fold_rotation_ordinal_1001_is_numbered_archive` の旧側は
  r1 `8995460229cf…`、r2 `093c72ceb6c5…`、r3 `3f1f750f98cc…`)。したがって新旧の差ではない。

### 4. 旧実装との網羅対照と正例・負例 (test_check_docs.py に追加した 10 node)

- `test_speed_line_number_matches_count_boundaries`: 文字 `a`・`\n`・`\r` の長さ 0〜7 の全文字列と offset −(長さ+2)〜長さ+2 で、`str.count` による旧定義と一致。
- `test_speed_raw_slice_matches_reference_exhaustively`: 文字 `-`・`x`・空白・タブ・`\r`・`\n` の長さ 1〜6 の全文字列と全 offset で、テスト内に逐語複製した旧実装と一致 (assert 経路も一致)。所要 4.83 秒。
- `test_speed_visible_lines_matches_reference`: comment の開始・継続・終了、fence 内の `<!--`、CR/CRLF を含む 11 入力で旧実装と一致。
- `test_speed_transition_sink_uses_whole_entry_body` (6 通り): worklog 内・archive 間・最終 archive→worklog の 3 境界で、遷移先 entry の「次の一手」節の外にだけ ID がある正例は所見なし、無い負例は所見あり。
- `test_speed_archive_order_uses_last_entry_of_left_archive`: 左の archive の末尾 entry を使わないと検出できない順序の曖昧さ。

いずれも合成文字列と一時 repo だけを使い、実 repo の docs には到達しない。T2 以外の 9 node はそれぞれ 3.79 秒未満 (焦点走の durations 上位 40 に入らない)。

### 5. 変異 (事前登録 8 件、`tools/mutation_worktree.py` の束ね経路、独立 clone)

段 4 で登録した変異を、最終 commit `535790d4` で走らせた。**8/8 が登録どおり** (KILLED 7、等価変異 m0 は SURVIVED、MISMATCH 0、baseline PASSED)。
request 37940.nqsv、Elapse 404 秒。台帳は `mutation/ledger-final2-535790d4.json.gz`、spec は `mutation/spec-final.json`。
期待 node は probe 走 (全件 SURVIVED 期待で観測 node を集める、`mutation/ledger-probe-41b67839.json.gz`) で完全集合を確定し、`41b67839` でも同じ 8/8 を得ている。

| 変異 | 何を壊すか | 赤になった node 数 | 既存 test だけで捕まるか |
|---|---|---|---|
| m1 | 行番号の境界を 1 つずらす | 1 | 捕まらない (追加 test だけ) |
| m2 | 負の offset の正規化を外す | 1 | 捕まらない (本番では負の offset は出ない) |
| m3 | 遷移先に entry 本文でなく「次の一手」節の ID を使う | 321 | 捕まる |
| m4 | archive 境界の遷移先に左の archive を使う | 2 | 捕まる (既存 1 + 追加 1) |
| m5 | 行の終わりに `\r` を数えない | 1 | 捕まらない (追加 test だけ) |
| m6 | comment 継続中でも近道する | 6 | 捕まる |
| m7 | 順序検査で左の archive の先頭 entry を使う | 1 | 捕まらない (追加 test だけ) |

### 6. 焦点走・監査

- 焦点走 (計算ノード、`41b67839` の内容を未 commit で適用した木): test_check_docs・hold 契約・hold 台帳・spool_fold・scoped acceptance・dev_wave_land・checker と、
  production 変更時に必須の inventory 4 群 (test_campaign・test_official_perf_closure・test_p3_exploration_namespace・test_p3_b4_wiring_probe) で 1,872 passed / 7 skipped / 1 failed。
  赤は `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` で、作業ツリーに未 commit の変更があることを検出する test だった (commit で消える種類、実装差分への帰属なし)。
  1 巡目は追加 test を hold 呼出しの後ろに置いていたため `test_growth_test_holds_contract.py::test_every_held_module_has_exact_top_level_guard_binding` が赤で、fix 第 1 巡で移した。
- 全史 provenance 監査: 実装 commit・fix commit の後ともに rc=0 (13,671 件、新規違反なし)。

### 7. login での参考値 (同時刻対照ではない)

| | wall | ユーザー CPU | 最大常駐メモリ | CPU 使用率 | 1 分 load |
|---|---|---|---|---|---|
| 変更前 (12:15 JST) | 85.2 秒 | 30.9 秒 | 302 MiB | 38% | 42 |
| 変更後 (`41b67839`、13:42 JST) | 38.6 秒 | 14.9 秒 | 363 MiB | 42% | 11 |

時刻と load が違うので wall の比較には使わない。どちらも wall の半分以上が CPU 以外の待ち (login の Lustre 読取と stat) で、この部分は今回の変更では縮めていない。
変更後の 363 MiB は fix 第 2 巡の前の版の値である。

## 確かめていないこと

- 判定不変は、上の入力 (main の現物、故障 6 種、test_check_docs.py の fixture、網羅対照の小さい文字集合) について示したもので、あらゆる入力木での一致を証明したものではない。
- login での同時刻対照は取っていない。login の wall を支配する I/O 待ち (Lustre の stat・読取) は減らしていない。
- メモリ増の原因は算術で帰属しただけで、メモリ計測器で内訳を測ってはいない (修正後に +3.0% へ下がったことは実測)。
- 受入全走の結果はこの文書には書いていない。受入はこの記録を含む tip で走らせるため、その後に記録 commit を足せない (結果は repo 外の job 記録と最終報告に残す)。

## 残る成長比例の項と次の一手

最終版でも `_check_backlog_guard` が cProfile 下 30.9 / 34.7 秒を占める。内訳は carry 参照 958,894 件の走査 (`_iter_carry_references` 累積 15.3 秒)、
「次の一手」節の解析 (`_validate_next_action_items` 5.0 秒) など。carry は各 entry の「次の一手」に active な T の数だけ並ぶ (直近 5 entry は 139〜142 件)ため、
**総量は entry 数 × active な T の数に比例して伸びる** (いまの全域 entry は archive 2,193 + worklog 11)。候補:

1. 同じ「次の一手」節を 3 回 (ID 集合・項目検査・carry 走査) 解析しているのを 1 回にする (最終版 profile で `_visible_markdown_lines` 6.8 秒、`_top_level_items` 10.1 秒の一部)。
   `_iter_carry_references` の逐次性 (test が `_top_level_items` を差し替えて観測している) を保つ設計が要る。
2. carry ごとの raw slice と sha256 (`_top_level_item_raw_slice` 2.7 秒 + `_placeholder_line_digest` 1.5 秒) を、既知不一致の照合が必要な場合だけ求める。
   `_CarryReference` の形と既存 test の期待を保つ設計が要る。
3. 凍結済み archive の走査結果を内容の hash で再利用すれば伸びそのものを止められるが、実行をまたぐ cache は判定の束縛の設計 (何が変われば無効化するか) が要るので、別 wave で設計から始める。

## 計算資源

計算ノードの job Elapse の合計は 5,782 秒 (約 1.61 node 時間): 変更前 profile 78、E1〜E3 を 3 版 (1,519 + 1,596 + 1,447)、焦点走 2 回 (20 + 49)、変異 3 走 (259 + 410 + 404)。
受入全走はこれに含まれない。

## 資料

- `raw/`: E1 (`e1-r{1,2,3}.json`)、E2 (`e2-r{1,2,3}.json.gz`)、E3 (`e3-r{1,2,3}.json`)、profile 要約 (`profile-before-4f412c67.txt`、`profile-after-535790d4.txt`)。
- `mutation/`: spec と台帳。
- `verbatim/`: 段 1 brief、段 3 相談 2 本、段 4 裁定、段 5 実装子 2 本、段 6 レビュー 2 本・fix 裁定と fix 子・焦点再レビュー、probe の逐語。
  `s3-consult-a-correctness.md` (原文 sha256 `65ceab64e9dd94ca64d83113a34a035bcc0a4964aa6dcbd76ffaaee90b77845a`、8,540 bytes) と
  `s6-review-a-correctness.md` (原文 sha256 `eced19a04c7bc607ca3d03a204a62e6d0122fc60a9179ee7f16c173f8f63e696`、3,338 bytes) は、
  行末の 2 空白 (Markdown の改行指定) を除いた。対象は前者の 1,2,5,6,9,10,13,14,17,18,21,22,25,26,29,30,33,34 行、後者の 1,4,7 行で、
  すべて空白ちょうど 2 個だった。復元はこれらの行末へ空白 2 個を足す。
