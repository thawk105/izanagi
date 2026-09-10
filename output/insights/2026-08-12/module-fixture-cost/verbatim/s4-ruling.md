# 段 4 裁定 — dev-wave-module-fixture-cost

親が段 1〜3 の全証拠を突き合わせて確定させた裁定。real/refuted、採否、scope、plan v2、
変異事前登録を含む。

---

## 1. real / refuted

| # | 出所 | 所見 | 判定 |
|---|---|---|---|
| B1 | 段 2 plan | raw literal だけでは escape/UTF-16,32 経路で漏れる | **real** — 保守的述語を必須にする |
| B2 | 段 2 plan + 両レンズ | path 一覧 signature の memo は同一 path 書換で stale | **real** — P1b を落とす |
| B3 | 段 2 plan | brief の「production 0 byte」が主案と矛盾 | **real** — 撤回済み |
| B4 | レンズ A | 候補外行の**非捕捉例外**が消え、受理集合が変わる | **real** — 下記 §2 で明示裁定 |
| B5 | レンズ A | brief に P1b が残り plan と割れている | **real** — §3 で明示的に落とす |
| B6 | レンズ B | wall 削減の上界は `539.83−303.96 = 235.87s`、0 もありうる | **real** — 効果主張を work に限定する |
| B7 | レンズ B | 純 CPU 削減は CPU 稼働率 9% では wall へ写らないかもしれない | **real** — 段 6 で実測して確定させる |
| B8 | レンズ B | P2 の直列鎖見積り「41s+50s=91s」は P1b 込みの前提で成立しない | **real** — 親の誤り。P2 を不採用にする理由の 1 つ |
| B9 | レンズ B | P1a は係数を下げるだけで比例を消さない (約 26 日で倍) | **real** — §5 の裁定パッケージへ |
| B10 | レンズ B | 「P1a 単独では land 不可」 | **partially refuted** — §3 で理由を述べる |
| B11 | レンズ A | 親の「fixture 14 回」は直接観測でなく推論 | **real** — 表現を是正する (§4) |

**親自身の誤り 4 件を撤回する:** (i) 「P1a は完全同値」(B4 により不成立)、
(ii) 「memo の入力は不変」(B2)、(iii) 「production 0 byte」(B3)、
(iv) 「P2 の鎖長 91s」(B8)。

---

## 2. B4 の明示裁定 — 受理入力域を狭めることを認める

**事実:** 現行 `_json_lines` は全物理行を `json.loads` し、握り潰すのは `JSONDecodeError` と
`UnicodeDecodeError` **だけ**である。よって `payload` に 5000 桁整数を含む**非対象行**は
`ValueError` (int 変換上限) を伝播させ、`_find_rollout` 全体を停止させる。
事前フィルタ版はこの行を候補外として読み飛ばすので、**従来停止した入力が成功する**。

**裁定: 認める。** 理由は 3 つ。

1. **これは正しさゲートではない。** 停止していたのは「無関係な行の病的な bytes によって
   interpreter が偶発的に投げる例外」であって、設計された検査ではない。
   `_find_rollout` が守るべき性質 (どの rollout を返すか) は 1 bit も変わらない。
2. **同一性の錨は SHA pin である。** `_find_rollout` の 5 呼出はいずれも直後に
   `_verify_rollout_sha` を走らせる (`tools/codex_reasoning_ab.py:568`、`:1544`、既定有効)。
   返す path が正しいことは `ROLLOUT_SHA256` が保証しており、本変更はそこに触れない。
3. **対象行の抽出が同一であることは独立 2 経路で実証済み。** 親の全 corpus 実測
   (2799 ファイル / 606,027 行、不一致 0) と、レンズ A の網羅的 encoding 解析
   (literal / `_` / BOM / CR / UTF-16LE,BE / UTF-32LE,BE / surrogate / `\/` / 大文字 `\U`)
   が独立に「正常 decode される対象行の false negative は構成不能」と結論した (DW-G03 成立)。

**ただし記録義務を課す:** 受理入力域が
「正常 decode される行、または現行が握り潰す 2 例外を出す行」へ狭まったことを
decisions へ明記し、**§5 の裁定パッケージでユーザーが覆せる形で提示する。**

**候補行側の例外境界は完全一致させる。** 候補判定を通った行の parse では、
現行と同じく `JSONDecodeError` と `UnicodeDecodeError` **だけ**を握り潰す。
`except ValueError` のような広い捕捉にしてはならない (現行が伝播させる巨大整数を握り潰すため)。

---

## 3. 採否

| 案 | 裁定 | 根拠 |
|---|---|---|
| **P1a 事前フィルタ (専用 scanner)** | **採用** | 削減 39.1〜39.8% を 4 走で実証、同一性を独立 2 経路で実証 |
| **P1b memo** | **不採用** | B2/B5。追加寄与 17% のために stale の穴を開ける取引は割に合わない |
| **P2 xdist group** | **不採用 (本 wave では)** | [T-201] (d) と衝突。N1 の再裁定が要る。B8 で親の見積りも崩れた |
| **P3 POS/NEG 遅延分割** | **不採用** | 片側のみ利用は 17 中 5 本。効果小 |
| **名前 glob による O(1) 参照** | **不採用 (本 wave では) → 裁定パッケージ** | §5。受理集合を広げるため一存で採らない |

### B10 (「P1a 単独では land 不可」) を部分的に refute する

レンズ B は「P1a は比例を消さないので恒久ルールに不適合、よって land 不可」とした。
**恒久ルールの文言は「repo 履歴に比例するコストをテスト経路に *入れない*」であり、
既存の比例コストを 39% 削る変更を禁じてはいない。** 本 wave は比例を新規に入れていない。

ただしレンズ B の実質は正しい: **P1a は約 26 日で効果を失う。**
よって本 wave は P1a を land しつつ、**比例除去を §5 の最優先裁定項目として起票する。**
「39% の改善を、100% の解決でないという理由で見送る」ことはしない。

---

## 4. B11 の是正 — 「14 回構築」の証拠の格付け

**旧表現 (誤り):** 「fixture が 14 回構築されていることを直接観測した」。
**是正後:** 一次資料 junit から**直接観測できるのは**、`benchmark_snapshots` を引数に取る
17 test のうち **14 本が 155〜230 秒を要し、3 本が 1.5〜3 秒で済んでいる**ことである。
構築回数 14 は、`scope="module"` が worker process 内共有であることと合わせた**強い推論**であって
直接計数ではない。

**段 6 で直接計数に格上げする:** 受入形実測で、fixture 構築の実発火回数を
**scanner の呼出回数として直接数える** (D104 決定 (4) が要求する「機構の実発火回数の直接観測」)。

---

## 5. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

### Q1 (最優先) — 全履歴走査そのものを消すか

**事実:** `_find_rollout` は、**中身が `ROLLOUT_SHA256` で pin されている 5 本**を探すために、
`~/.codex/sessions` の全 rollout を線形走査している。この archive は codex を使うほど増え、
本 wave の作業中だけで **2799 → 2806 → 2813** と増えた。実測増加率 **約 106 files/day、
約 26 日で倍**。**「開発を進めるほどテストが遅くなる」構造そのものである。**

**実証済みの代替:** ファイル名は `rollout-<timestamp>-<session_id>.jsonl` で session id を含む。
pin 済み 5 session すべてで、**名前 glob の結果が全走査の結果と完全一致し、SHA pin とも一致した**
(0.020s 対 2.66〜7.12s = **131〜363 倍**)。

**採らなかった理由:** 現行は「全ファイル中で一致がちょうど 1 件」を要求する
(`len(matches) != 1` → `RC_SESSION`)。名前 glob は他所の重複を見ないため、
**「重複があるが名前一致の SHA は正しい」入力を、現行は拒否し fast path は受理する。**
受理集合を広げる形なので規律 2 に従い親の一存では採らない。

**親の推奨: (a) を採る。**
- (a) **SHA pin を持つ label に限り fast path** (名前 glob → 内容照合 → SHA 照合)、
  pin の無い呼出元 (`:2856` の `thread_id`) は現行の全走査を維持する。
  pin 照合は件数検査より強い identity 保証を与えるので、実質的な弱体化はない。
- (b) 走査 root を pin 済み session だけの snapshot に限定する契約を producer 側に設ける。
- (c) producer が ID → immutable path/generation を発行する (最も重いが最も原理的)。
- (d) 何もしない (約 26 日で P1a の効果は消える)。

### Q2 — [T-201] (d) の再裁定 (新事実 N1)

[T-201] の選択肢文は (d) xdist grouping を「[T-120] が同型を実測で棄却済み」として退けたが、
**D91 決定 (2) の逐語は「1 file 1 xdist group を*維持*する」であり、group を*外す*案の棄却**である。
機序も「**分割は総 work を増やす — 全 worker へ散らすと fork/exec と I/O が競合する**」で、
本 wave の観測そのもの。**親の推奨: 「特定 fixture の利用者に限定した group」を (d) とは別案として
再提示可能とする。ただし本 wave では実装しない** (B8 により鎖長の見積りが未確立のため)。

### Q3 — §2 の受理入力域の狭まりを認めるか

§2 の裁定 (病的な非対象行での偶発停止を失うことを認める) をユーザーが覆す場合、
P1a は実装できない。**親の推奨: 認める** (§2 の 3 理由)。

---

## 6. scope (確定)

- **編集する:** `tools/codex_reasoning_ab.py` — `_json_lines` の直後に専用 scanner を追加し、
  `_find_rollout` の行供給元だけを差し替える。`orchestrator/tests/test_codex_reasoning_ab.py` —
  同値性の回帰テストを追加。
- **触らない:** `_json_lines` 本体 (他 11 呼出元)、`len(matches) != 1` の 5 行 (byte 単位で不変)、
  `payload.id` / `payload.session_id` の OR 条件、`sorted(rglob(...))`、`path.resolve()`、
  ファイルごとの `break`、全ファイル走査。
- **触らない (並行 wave の領域):** `t080_freeze_migration.py`、`s8b_oracle_driver.py`、
  `test_s8b_oracle_driver.py` の T-080 E2E fixture、gate 判定、receipt 機構。
- **触らない (production の安全性質):** `build_snapshot` の `--no-hardlinks` clone、
  `_seal_git_object_closure`、`verify_snapshot`、`ROLLOUT_SHA256` と `_verify_rollout_sha`。

---

## 7. 変異事前登録 (DW-M01。単一理由性を満たす形で 6 件)

新設する検査が本当に発火することを、**wave 前の実コードの形を含む**変異で確かめる
(memory: 変異は wave 前の実コードの形を必ず含める)。

| # | 変異 | 期待 | 単一理由 |
|---|---|---|---|
| V1 | 述語から `b"\\u00"` 分岐を削る | KILLED | escape 表記の対象行を漏らす |
| V2 | 述語から `b"\x00"` 分岐を削る | KILLED | UTF-16/32 の対象行を漏らす |
| V3 | 述語を `b'"session_meta"' in line` だけにする (= **wave 前の親案の形**) | KILLED | V1+V2 の複合。親が最初に書いた形が捕まることを示す |
| V4 | 候補行の例外捕捉を `except Exception` へ広げる | KILLED | 現行が伝播させる例外まで握り潰す |
| V5 | `payload.get("id") or payload.get("session_id")` へ縮約する | KILLED | 両 field が異なる実データで誤判定 |
| V6 | ファイルごとの `break` を最初の `session_meta` で無条件停止に変える | KILLED | 4 ファイルは `session_meta` を 2 行以上持つ |

**期待 node は fix 後に完全集合を再導出する** (memory: expected-nodes-rederived-after-fix-commit)。

---

## 8. 成功判定

1. 新規 scanner の同値性テストが緑 (V1〜V6 が全件 KILLED)。
2. 受入全走 8832 passed 相当 / 0 failed。
3. **効果は work で主張する** (B6/B7)。受入形 paired 実測で
   `test_codex_reasoning_ab` の直列総和と scanner 呼出回数を before/after で併記する。
   **wall が縮まなくても失敗とはしない** — その場合は「work は減ったが wall は動かない」と
   正直に記録し、律速が `test_s8b_oracle_driver` と `real-repo` にあることを再確認する。
