# 裁定パッケージ — dev-wave-module-fixture-cost (3 問)

親は段 4 で「実装するもの」を決め切ったうえで、**一存で決めてはいけない 3 点**を返す。
いずれも証拠は本 wave の実測で揃っている。

---

## Q1 (最優先) — 全履歴走査そのものを消すか

### 事実

`tools/codex_reasoning_ab.py` の `_find_rollout` は、**中身が `ROLLOUT_SHA256` で pin されている
5 本の rollout** を見つけるために、`~/.codex/sessions` の全ファイルを線形走査している。

- この archive は **codex を使うほど増える**。本 wave の作業中だけで
  **2799 → 2806 → 2813** と増えた。実測増加率 **約 106 files/day、約 26 日で倍**。
- よって本 wave の 39% 改善は **約 1 ヶ月で失われる**。
- これはユーザーが 2026-08-11 に定めた恒久ルール
  **「repo 履歴に比例するコストをテスト経路に入れない」**が禁じる構造そのものである。

### 実証済みの代替 (親が実データで確認)

rollout のファイル名は `rollout-<timestamp>-<session_id>.jsonl` で session id を含む。
**pin 済み 5 session すべてで、名前 glob の結果が全走査の結果と完全一致し、SHA pin とも一致した。**

| session | 名前 glob | 内容走査 | 一致 | SHA pin | 速度比 |
|---|---|---|---|---|---|
| NEG | 1 件 / 0.020s | 1 件 / 7.12s | True | True | **363x** |
| POS | 1 件 / 0.020s | 1 件 / 2.89s | True | True | 147x |
| author | 1 件 / 0.020s | 1 件 / 2.90s | True | True | 143x |
| fix1 | 1 件 / 0.020s | 1 件 / 2.71s | True | True | 134x |
| fix2 | 1 件 / 0.020s | 1 件 / 2.66s | True | True | 131x |

さらに `_find_rollout` の 5 呼出は**いずれも直後に `_verify_rollout_sha` を走らせる**
(`:568` の `derive_independent_golden`、`:1544` の `render_prompt`、既定で有効)。
**同一性の錨は既に SHA pin である。**

### なぜ親の一存で採らなかったか

現行は「全ファイル中で一致がちょうど 1 件」を要求する (`len(matches) != 1` → `RC_SESSION`)。
名前 glob は他所の重複を見ないため、**「重複があるが名前一致の SHA は正しい」入力を、
現行は拒否し fast path は受理する**。**受理集合を広げる形であり、規律 2 に抵触しうる。**

### 選択肢

- **(a) 親の推奨 — SHA pin を持つ label に限り fast path。**
  名前 glob → 内容照合 → SHA 照合の 3 段。pin の無い呼出元 (`:2856` の `thread_id`) は
  現行の全走査を維持する。pin 照合は件数検査より強い identity 保証を与えるので、
  **pin 付き label に関しては実質的な弱体化がない。**
- (b) 走査 root を pin 済み session だけの snapshot に限定する契約を producer 側に設ける。
- (c) producer が ID → immutable path / generation を発行する (最も重いが最も原理的)。
- (d) 何もしない。**約 26 日で本 wave の効果は消える。**

---

## Q2 — [T-201] (d) の再裁定 (新事実あり)

### 新事実 N1

[T-201] (2026-07-31 ユーザー裁定) の選択肢文は (d) xdist grouping を
**「[T-120] が同型を実測で棄却済み」**として退けた。しかし **D91 決定 (2) の逐語は
「`test_dev_waves_integration.py` は 1 file 1 xdist group を*維持*する」**であり、
group を***外す***案を棄却したものである。

しかも D91 の機序は
**「分割は総 work を増やす向きに働く — 各 node が temp git repo の構築に subprocess を多用するため、
全 worker へ散らすと fork/exec と I/O が競合する」**であり、
これは本 wave が観測した現象そのもの (同一 fixture が 14 worker で 14 回構築) で、
**むしろ grouping を支持する。**

### 選択肢

- **(a) 親の推奨 — 「特定 fixture の利用者に限定した group」を (d) とは別案として再提示可能とする。**
  ただし**本 wave では実装しない**。段 3 レンズ B が親の鎖長見積り
  (「41s + 50s = 91s」) を「P1b 込みの前提で成立しない」と正しく崩したため、
  効果見積りが未確立である。
- (b) [T-201] (d) の不採用を維持する (grouping は今後も採らない)。

---

## Q3 — 受理入力域が狭まることを認めるか

### 事実

現行 `_json_lines` は全物理行を `json.loads` し、握り潰すのは `JSONDecodeError` と
`UnicodeDecodeError` **だけ**である。よって `payload` に 5000 桁整数を含むような
**非対象行**は `ValueError` (int 変換上限) を伝播させ、`_find_rollout` 全体を停止させる。
候補行だけを parse する新 scanner は、この行を読み飛ばすので **従来停止した入力が成功する**。

### 親は段 4 §2 でこれを認めた。理由

1. **正しさゲートではない。** 停止していたのは無関係な行の病的 bytes による偶発例外であり、
   設計された検査ではない。`_find_rollout` が返す path は 1 bit も変わらない。
2. **同一性の錨は SHA pin。** 5 呼出とも直後に `_verify_rollout_sha` が走る。
3. **対象行抽出の同一性は独立 2 経路で実証。** 親の全 corpus 突き合わせ
   (2,799 ファイル / 606,027 行、不一致 0) と、敵対レンズの符号化網羅解析
   (literal / `\u00XX` / BOM / CR / UTF-16LE,BE / UTF-32LE,BE / surrogate / `\/` / 大文字 `\U`)
   が独立に「正常 decode される対象行の false negative は構成不能」と結論した (DW-G03 成立)。

候補行側の例外境界は現行と同一に保った (`except (json.JSONDecodeError, UnicodeDecodeError)`)。
`except Exception` への拡大は変異 V4 で機械的に禁止した。

### 選択肢

- **(a) 親の推奨 — 認める。** 上記 3 理由。
- (b) 認めない。この場合 **P1a は実装できない**ので本 wave の改善を revert する。

---

## 付記 — 本 wave で実装したものと、しなかったもの

| | 判断 | 根拠 |
|---|---|---|
| P1a 候補行だけの専用 scanner | **実装した** | 39.1〜39.8% を 4 走 paired で実証、同一性を独立 3 経路で実証 |
| P1b root 単位 memo | 実装しない | 同一 path 書換で stale。作業中に root が 3 度増えた |
| P2 xdist group | 実装しない | Q2 の再裁定待ち + 鎖長見積り未確立 |
| P3 POS/NEG 遅延分割 | 実装しない | 片側のみ利用は 17 中 5 本で効果小 |
| 名前 glob fast path | 実装しない | Q1 の裁定待ち (受理集合を広げるため) |
