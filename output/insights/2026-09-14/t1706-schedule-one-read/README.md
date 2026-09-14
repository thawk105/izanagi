# [T-1706] schedule を一度だけ読み、認証した bytes から descriptor SHA と schedule を導く

A/B 装置 `tools/codex_reasoning_ab.py` の 3 入口が schedule file を SHA 用と validation 用に
**別々に読んでいた**ため、同一 UID の書き手が A→B→A と差し替えると、A の SHA を receipt に残したまま
B の内容で検査・集計できた。3 入口を「一度だけ読み、その同じ bytes から導く」形へ直した wave の
一次資料。

- wave branch: `worktree-dev-wave-t1706-schedule-bytes-toctou`
- 実装 commit: `687a7ad076478b336f61ee5ab673335b7a60e2bd` (base `f5423e2fff3adb164731963ca33e82ed08d08c4d`)
- 設計判断は decisions 台帳、near miss は failures 台帳、経緯は worklog を正本とする。

## 変更した 3 入口

| 入口 | 変更前の読み回数 | 変更後 |
|---|---|---|
| `supervise_pair` | source 1 + frozen 2〜3 | source 1 + **frozen ちょうど 1** |
| `_replay_manifest` | schedule 3 (descriptor 照合 / 解析 / SHA 再計算) | **1** |
| `make_packets` | schedule 2 (descriptor 照合 / 解析) | **1** |

`supervise_pair` の authority は **frozen copy のまま**である。段 2 の起草案は source bytes を
authority にしていたが、それは壊れた frozen を拒否する現行の力を失う退行だった。
段 3 の敵対レンズがこれを覆した (verbatim/s3-lens-a.md)。

## 変異台帳

harness = `tools/mutation_harness.py`、`--runner-mode dispatch --detached`。
runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_codex_reasoning_ab.py
orchestrator/tests/test_t189_oracle_wiring_slice.py -rf`、
runner_sha256 = `efaba8592b70c0c3baebae5bb1aa8613bb9b370d194159ac522ccf40a73b5b7c`。
両走とも repo_head = `687a7ad076478b336f61ee5ab673335b7a60e2bd`。

### probe 走 (観測 node を集める。全件 SURVIVED で登録)

spec = `verbatim/mutation-spec-probe.json`、
sha256 = `f90cb99355e024e0fbcdfcf7b5fee31dc0e9576b668c9834e4e561bfeb806f57`。
baseline PASSED (rc=0)。6 件すべて MISMATCH (= 登録した SURVIVED と食い違い、実際には赤)。
**巻き添えはゼロで、各変異が落とした node は下表の集合ちょうどだった。**

### 本走 (KILLED 期待・完全集合)

spec = `verbatim/mutation-spec-final.json`、
sha256 = `3e41d686aa0b0f21d7bba256aae1657febfd27843ed98a5e61111e9db87e8bdc`。
baseline PASSED (rc=0)。**KILLED 6 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0。**

| ID | 変異 | 落ちた node (完全集合) |
|---|---|---|
| M1 | supervisor の loader から `data=` を外す | `test_schedule_authenticated_bytes_{accept_static,reject_swap_restore}[supervisor]` |
| M2 | replay の loader から `data=` を外す | 同 `[replay]` |
| M3 | packets の loader から `data=` を外す | 同 `[packets]` |
| M4 | 姉妹 helper の `return path, data` を `return path, path.read_bytes()` にする | 同 `[replay]` と `[packets]` の計 4 件 |
| M5 | replay の SHA 入力を `schedule_path.read_bytes()` に戻す | 同 `[replay]` |
| M6 | supervisor の SHA 入力を `frozen_schedule.read_bytes()` に戻す | 同 `[supervisor]` |

**M4 が supervisor を落とさないのは、supervisor が姉妹 helper を通らないからである** —
段 6 の焦点再レビューがこの制約を先に指摘し、登録先を replay / packets に限った
(verbatim/s6-focus-rereview.md)。

### 単一理由性 (F820) の扱い

**単一理由の gate は正例 `test_schedule_authenticated_bytes_accept_static` に置いた。**

- 正例では入力 file が呼び出し中に一切変化しないので、2 回目の読みが起きても返る bytes は
  1 回目と同一である。解析結果・SHA・受理結果は何も変わらず、**観測できる差は read 回数だけ**になる。
  したがって同じ入力を拒否する層が前後にも内側にも無い。
- 負例 `test_schedule_authenticated_bytes_reject_swap_restore` は拒否理由が過剰決定である
  (duplicate slot_id に加えて manifest SHA 不一致・launch SHA 不一致・unknown slot が重なる)。
  suite には残すが、**単一理由の変異証拠としては数えない。**
- この切り分けは段 6 レビュー A・B が独立に指摘し (verbatim/s6-review-a.md, s6-review-b.md)、
  焦点再レビューが 6 経路すべてについて静的に確認した。

## 受理集合について公開する事実

- **呼び出し中に変化しない input に対する受理集合は不変である。** 受理・拒否・rc・reason が
  すべて従来と一致する。非 canonical な空白・末尾改行・BOM・非 UTF-8 byte 列・重複 key・空 file を
  含めて、段 3 と段 6 の 4 レンズがいずれも差の出る入力を構成できなかった。
- **呼び出し中に変化する input に対しては挙動が変わる。それが本修正の目的である。**
  例えば descriptor 照合の後に file が消えると、従来は再読が失敗して
  `cannot read JSON object` で拒否したが、以後は最初の読みで得た bytes で続行する。
  これは弱化ではなく、**認証した bytes をその後の file の状態から切り離す**という契約そのものである。

## 不在の主張 (成り立つ範囲つき)

- **現行 bytes を pin する live consumer は 0 件。** 旧装置 bytes (`58f1176e...`) の歴史 pin が
  `output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` に 1 件存在し、
  D1285 により更新対象外。範囲 = tracked 全体の path 検索、`tool_sha256` / `apparatus-pin` の key 検索、
  実装 commit 前の現行 sha 値検索 (hit 0)、事前登録 §8.3 wiring slice の全 field 走査。
  ignored file・別 worktree・文字列 literal 以外で構成される pin はこの母集合の外である。
- **`_validate_schedule` を呼ぶ schedule 取込み経路は本 production 内で 3 箇所が全数。**
  段 2 の子が AST で、段 3 レンズ A が I/O・JSON loader・artifact resolver の呼出引数から、
  段 3 レンズ B が token 検索から、それぞれ独立に数えて一致した。
  **この一致は、validator を通らない動的参照や外部 consumer の不在までは保証しない。**

## 未実測として残すもの

静的・実測で確定したのは「hash と解析の入力が食い違いうる構造が 3 入口にあり、
修正後は 1 回読みになる」ことと、上記の変異 6 件が新テストで死ぬことである。
**model・price・slot 集合を任意に変えた schedule が、launch receipt・attempt ledger・adjudication の
後続照合まで通って certified な集計を成立させることは、本 wave では実証していない。**
負例が実証したのは各入口の validator 通過までである。

## 一次資料

`verbatim/` に段ごとの逐語を置く。

| file | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief (scope・不変条件・provisional 裁定) |
| `s2-plan.md` | 段 2 の実装プラン起草 (supervisor の退行案を含む) |
| `s3-lens-a.md` | 段 3 敵対相談 レンズ A (受理集合・SHA 帰属) |
| `s3-lens-b.md` | 段 3 敵対相談 レンズ B (検査の実効性・変異の帰属) |
| `s4-ruling.md` | 段 4 裁定・プラン v2・変異事前登録 |
| `s5-author.md` | 段 5 実装子の完了報告 |
| `s6-review-a.md` / `s6-review-b.md` | 段 6 敵対レビュー 2 本 |
| `s6-fix.md` | 段 6 fix (共有 fixture consumer 登録) |
| `s6-focus-rereview.md` | 段 6 焦点再レビュー (所見対応表) |
| `mutation-spec-probe.json` / `mutation-spec-final.json` | 変異 spec 2 版 |

変異 report の全文は repo 外の
`/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1706-schedule-bytes-toctou/dev-wave-job-t1706/`
に `mutation-probe-report.json` (324,346 bytes) と `mutation-final-report.json` (287,758 bytes) として残す。

### 逐語の正規化 (可逆・可視文字不変)

Codex の出力は markdown の hard line break として**行末に ASCII 空白 2 個**を持つ行があり、
`git diff --check` に抵触した。5 file について**行末 ASCII 空白の除去だけ**を行った。
可視文字は 1 文字も変えていない。原文は各 codex receipt の `output_sha256` に封じてあり、
`sed -i 's/[ \t][ \t]*$//'` がここで適用した正規化の全部である。

| file | 原文 sha256 / bytes | 収録 sha256 / bytes |
|---|---|---|
| `s3-lens-a.md` | `84da3ee6aaa0f5ebb26eb6a6c88696fb9c5694ead973a4b05467ed92d3f5ce73` / 7247 | `2167852a7efa29d358523c0f5fb520cd1f7a48de7b6fa751ea3ac18f7acb3976` / 7227 |
| `s3-lens-b.md` | `09cef1184ca9ff759b11f3bde4d10cc5ac810206c368967e65decd4d73869f12` / 8809 | `7af11a3bc300e72c37deb9334ef5ffda59d9d6788504e125e725d98cbfdc277b` / 8785 |
| `s6-fix.md` | `a013827eef518e0c8e596a9e3f0104f2cdc2b39f5fd0a7226cceb52b54a6c3b5` / 2552 | `fd5c9be99ff2b5f575d435c81cd801513ee604533ff71af55153151f54c3012a` / 2546 |
| `s6-review-a.md` | `fee138865e6f1cc23739ece934ed87ea8c46ae895d4bbc90758894a4f1e494fd` / 6048 | `71bac66d92e0a1e4bb47a5fc529a4f7a2c7a076a703a27071f9f26ae40621195` / 6034 |
| `s6-review-b.md` | `24f58ab84f841a8d1a58135b8672e8499546d1575d0e18dc736935023258f364` / 9361 | `7852f543bfb60a520847ec8d5d278fb987f2bddcdec1cb9b5c85c783bf59b16c` / 9349 |

残る 5 file (`s1-brief.md`、`s2-plan.md`、`s4-ruling.md`、`s5-author.md`、`s6-focus-rereview.md`) は
無変更である。
