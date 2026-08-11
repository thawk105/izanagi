# [T-139] land 2 session 1 — 裁定パッケージ

段 3 (2 レンズ) と段 6 (2 レンズ) が独立に real と判定し、親が scope 外と裁定した論点を返す。
いずれも**本 session では実装していない**。実装済みの範囲は `README.md` を参照。

親は各問に推奨を付ける。推奨は親の判断であり、覆してよい。

---

## RP-1. resolver を「呼ぶ側」をどの session で作るか (最重要)

### 事実

- 段 3 lensA・lensB、段 6 revC・revD の 4 レンズすべてが独立に指摘した。
  **`resolve_effective_preregistration` を書いても、それを呼ぶ producer / admission consumer が
  無い限り、§S7 #1 (台帳 → manifest の第 1 矢印) と #2 (Git trust root) は 1 度も発火しない。**
- 承認済み `record-items-v2.md` §6.10 は「**受領証を永続化する関数自体**が `PreregBinding` を
  必須 keyword-only で受け、同じ snapshot の受領証と binding の三つ組・`measurement_head` を
  照合してから publish する。別経路の writer が受領証を publish できてはならない」と定める。
  すなわち**防壁の支配点は writer である。**
- **親が段 4 で確定した順序制約:** 承認 manifest は conformance vectors の digest を pin する
  義務がある (§7)。vectors は §6 / §7.1 の制約に対応する試験資材であり、固定 semantic validator と
  同じ session に属する。**したがって manifest 実体は validator と同じ session でなければ
  承認契約を満たせない。**

### 問い

land 2 の残りをどの単位で組むか。

- **(a) manifest + resolver + 受領証 writer + 固定 semantic validator + conformance vectors を
  1 session にまとめる** (親推奨)。
  順序制約 (manifest は vectors の digest を pin する) と支配点 (writer が binding を要求する) が
  同じ session に入り、その session の終わりに「§S7 #1・#2 が発火する」と初めて言える。
  段 2 見積りでは production 約 1,900 行 + test 約 2,400 行。
- (b) resolver だけ先に別 session で作り、writer は次の session へ回す。
  → 親は反対する。resolver だけの session は本 session と同じく `foundation-only` で終わり、
  「実装したが 1 度も呼ばれないコード」を 2 session 分積むことになる。
- (c) land 2 全体を 1 session でやり直す。
  → 親は反対する。S6 (a) が複数 session を明示的に認めており、15,420 行は 1 session に入らない。

### 同束で決めたいこと

1. **D234 の API 署名を変えてよいか。** 段 2 は resolver へ `approval_manifest_ref` 引数を
   足す案を出したが、段 3 lensB が「これは署名維持ではなく API 契約変更である」と指摘した。
   - **(a) 外部署名を D234 のまま保ち、manifest の解決は内部の固定 path / private helper にする**
     (親推奨。D234 を変えずに済む)
   - (b) `approval_manifest_ref` を足す API 変更を独立の decision として起票する
2. **D282 payload の `alpha_reservation` 節を manifest 側でどう扱うか。**
   本 session の parser は「台帳の証明ではない literal descriptor」として読んでいる。
   manifest がこれを再掲するのか、payload 参照だけで足りるのか。
   - **(a) manifest は再掲せず、resolver が payload から直接読む** (親推奨。二重定義を作らない)
   - (b) manifest にも書き、両者の exact 一致を要求する

---

## RP-2. Git / resolver の trust root policy

### 事実

- 現行 `blobref.py` は `PATH` を Git 環境の allowlist に含め、`"git"` を**名前で**起動する。
  偽 `git` が `rev-parse` / `merge-base` を偽装すれば `F_r` より前の測定が通る (SHA 偽造は不要)。
- 段 3 lensA が環境・設定経路を網羅列挙した (`verbatim/s3-lensA.md` §攻撃所見 3 の表)。
  ELF loader (`LD_PRELOAD` 等)、repo/object 選択 (`GIT_DIR` 等)、config 注入 (`GIT_CONFIG*`,
  `HOME`, `XDG_CONFIG_HOME`)、helper 実行 (`GIT_EXEC_PATH` 等)、repo-local config の
  `include.path` / `includeIf`、alias / `core.fsmonitor` / `core.hooksPath` / filter / textconv、
  commit-graph / alternates / promisor。
- **本環境の `/usr/bin/git` は owner `uid/gid = 65534/65534` (nobody) である** (lensA 実測)。
  「root 所有必須」を採ると**本環境を拒否する**。
- lensA はさらに「resolver source 自身が `F_r` の descendant commit で自己承認できる」と指摘した。
  D282 の `operational_boundary` は「trusted resolver」と書くが、その trusted 性を作る機構を
  定めていない。

### 問い

どこまでを OS の信頼に委ね、どこから digest closure を持つか。

- **(a) 「canonical local main の checkout と、その上で走る Python / Git を信頼する」と
  `operational_boundary` の解釈として明文化し、実装は安価な部分集合だけ入れる**
  (親推奨)。安価な部分集合 = `PATH` 非継承 + 絶対 path 起動 + 全 `GIT_*` 破棄 +
  `GIT_CONFIG_NOSYSTEM` + `core.commitGraph=false` + alternates / promisor 拒否 +
  `--no-pager` + `core.fsmonitor=false`。
  **理由:** 本環境の `git` は nobody 所有で、OS レベルの信頼根を要求すると研究が動かない。
  同一権限の攻撃者を仮定すると Python 実行系まで守る必要があり、研究プロトタイプの
  範囲を超える (memory「研究最優先・プロトタイプ基準」)。
- (b) Git binary の digest closure を持ち、承認済み digest と照合する。
  → 親は反対する。承認済み digest をどこに置くかで同じ問題が再帰し、環境更新のたびに
  承認 decision の再発行が要る。
- (c) 何もしない (現状維持)。
  → 親は反対する。`PATH` 差し替えは §S7 #2 として land 2 の必須要件に入っている。

**resolver source 自身の identity 束縛** (lensA の追加指摘) は、(a) を採るなら
`operational_boundary` の内側として扱い、実装しない。これも同じ問いの一部として裁定を求める。

---

## RP-3. raw snapshot consumer の閉包 (§S7 #3)

### 事実

- 段 2 と段 3 lensA が一致して「snapshot API 単体を作っても §S7 #3 を閉じたことにならない」と
  判定した。TOCTOU の対象は `a03` raw、run log、intent、correctness evidence などの
  `fileRecord` であり、それを読むのは固定 semantic validator である。
- 承認済み §6.10 が「読取は単一 fd / snapshot で行い、各 path component を `O_NOFOLLOW` で辿り、
  symlink を拒否する」と定めている。**要件は既に凍結済みで、設計の余地は小さい。**

### 問い

- **(a) RP-1 (a) の session (semantic validator と同じ session) で API と consumer 結線を
  同時に行う** (親推奨)。要件が凍結済みなので、validator を書くときに一緒に書くのが最短で、
  「作ったが結線していない API」を残さない。
- (b) 本 session の後、独立の session で API だけ先に作る。
  → 親は反対する。結線されない API は §S7 #3 を閉じないと 2 レンズが既に判定している。

---

## RP-4. 公表 core `b03` と pilot の解除条件

### 事実

- worklog 407 の次の一手が「**本走投入は段階 2 の再提出後まで依然不可**」と記録している。
- 2026-08-11、peer (`t139 core phase 2`) が公表 core 段階 2 を land した (main `d6f2c836`)。
  ただし **3 文書 (新 core v2 / 追補 B 再発行版 / 追補 P 草案) はいずれも `authority: none` で
  未発効**であり、凍結承認はユーザー手番として返されている。
- peer は **`b03` の縮小が確定**したと通知した。`b03` から次の 5 つが落ちる —
  (i) `current_study.ordinal` と `reservation` / `separate_ledger` の yaml、
  (ii)「producer が選べない canonical な台帳で原子的に」、
  (iii)「`(publication_family_root, ordinal)` は一意」、
  (iv)「失敗・中断・未公表でも ordinal を解放・再利用しない」、
  (v)「この一意性が成立しないまま本走を投入してはならない」。
  読み先は新 core v2 §8.2 と追補 P `p03`。
- peer は **新規 [T-793]** を「land 2 の必須要件 §S7 #7 (`b03` 個別公表系列台帳) を具体化して
  同じ producer 系列へ結線するもの」として起票した。別 ownership の並行実装ではない。
- **(v) の消失は本走の投入 gate を 1 つ減らす。** peer はこの帰結を Q1 としてユーザー裁定へ
  返しており、親推奨は「裁定どおり外して受け入れる」だった。

### 問い

pilot 投入の解禁条件を何にするか。

- **(a) 「3 文書の凍結承認 + その fold」を解禁条件とし、land 2 側は §S7 #7 を [T-793] へ委譲する**
  (親推奨)。[T-793] が同じ producer 系列へ結線する起票として立っているので、land 2 が
  `b03` consumer を二重に書く理由がない。land 2 は消費側として新 core v2 §8.2 と `p03` を読む。
- (b) land 2 側でも `b03` consumer を書く。
  → 親は反対する。C-2b (a) が「`b03` の正本は公表 core 側」と定めており、二重定義になる。

**本 session はこの論点に一切触れていない** (`b03` consumer を 1 行も書いていない)。
裁定を待って後続 session の scope を決める。

---

## 付録. 本 session が撤回した親の provisional 裁定

| ID | 内容 | 撤回理由 |
|---|---|---|
| (P1) | A/B の 2 lane 並列で足りる | 段 2 が所有面不足を実測。実質 3 lane 並列 → 1 lane 直列 |
| (P2) | Git を絶対 path で解決し実体 digest を受領証へ記録すれば足りる | 順序が逆 (ambient PATH で解決してから digest を取っても偽物の digest を記録するだけ)。かつ記録先 field が承認済み schema に無い |
| (P3) | leaf の fd 再利用で足りる | component walk・regular 検査・bounded read・read 前後 metadata が必要。かつ consumer 不在で閉じない |
| — | 「D282 の承認 blob は 6」 | 正は target core 1 + approved blobs 6 = **7 三つ組** |
| — | 「承認 blob path を pin する `*.py` は 2 箇所」 | 当該 2 箇所は**草案** path の pin。承認 v2 path の pin は **0 箇所**だった |
