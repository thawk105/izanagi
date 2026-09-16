# [T-2464] B-4 事前登録の開始時刻欄を発効条件から外した (D1871)

- wave branch: `worktree-dev-wave-t2464-b4-start-time`
- 基準 commit: `d97c423bdd14e0b416cb4f585d350e6c2b251287` (local main)
- 実装 + 追補 commit: `fefbec1ab86a7998033a5033babfe5c8f676a8f1`
- 裁定: `docs/decisions.md` の D1871 (2026-09-09)。台帳 [T-2464] (P1・実装 + 追補手番)

## 何をしたか

D1649 決定 2 (2026-09-05) が「開始時刻は `未記入` のままでよく、実際の開始時刻は実走成果物側の
記録だけを正本とする」と拘束を撤廃してから、受理側がその裁定を実施していなかった。
`assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel` は §5 表の
全 10 行へ一律に予約 sentinel 禁止を掛けており、対象欄の `未記入` も拒否していた。

本 wave は D1871 に従い、**「実行責任者・開始時刻」欄 1 行だけ**を緩めた。行 label 集合
(`_SECTION5_LABELS`) は変えていない。事前登録本文は同文書の改訂契約に従い、§5.1 の「開始時刻」節へ
追補 (erratum) を末尾追加した。既存行は 1 文字も書き換えていない。

## 受理する形 (実装の逐語)

値へ既存の正規化 (セル外周の空白除去と NFKC 正規化) を施した結果が

```
実行責任者 = (?P<owner>[^、=\r\n]+)、開始時刻 = 未記入
```

へ `re.fullmatch` で全体一致し、`owner.strip()` が非空・`_RESERVED_SENTINEL_RE` 不一致・
`_RESERVED_SENTINEL_WHOLE_VALUES` 非該当をすべて満たすときだけ受理する。1 つでも欠ければ
既存判定へ落ちて従来どおり拒否される。この構文は D1871 が定めたものではなく、同裁定を実装する
ために本 wave が定めた形である (decisions 参照)。

## 実測した事実

### 変更前後の受理行列 (親の反実仮想)

一次資料は `verbatim/parent-probe-counterfactual-before.txt` と
`verbatim/parent-probe-matrix-after.txt`。現行コード (変更前) では、開始時刻に**非 sentinel の
実値**を入れれば次の owner はすべて受理された。同じ文字列を `env_tag (実測環境)` 欄へ入れても
受理された。

|owner|開始時刻 = 実値 (変更前)|開始時刻 = 未記入 (変更前)|開始時刻 = 未記入 (変更後)|
|---|---|---|---|
|`thawk105`|ACCEPT|REJECT|ACCEPT|
|説明文 (`担当者が決まり次第指名する`)|ACCEPT|REJECT|ACCEPT|
|`thawk105（計測完了後に確定）`|ACCEPT|REJECT|ACCEPT|
|NUL 1 文字|ACCEPT|REJECT|ACCEPT|
|BEL 1 文字|ACCEPT|REJECT|ACCEPT|
|`---` + NUL|ACCEPT|REJECT|ACCEPT|
|`TBD`|REJECT|REJECT|REJECT|
|`未記入`|REJECT|REJECT|REJECT|

**この表が段 3 レンズ A の最重大所見を反証した根拠である。** レンズ A は「追加受理経路が責任者
未指名の説明文と NUL 1 文字の責任者を受理する」ことをメモリ上の probe で実測し、高重大度の
must-fix とした。所見の現象は正しいが、同じ文字列は**変更前から受理されていた** — 開始時刻が
非 sentinel の実値であれば対象行でも、また expectation 行を除く他の欄でも受理される。
受理側の関数は `types, meanings, and rendered non-emptiness are not checked` と非保証を宣言している。
案 B の owner 側検査 (非空・非 sentinel) は既存 regime を owner 部分文字列へ写したものであり、
狭めも広げもしない。

### 追補の文面と実装の差 (段 6 レビュー B の must-fix)

一次資料は `verbatim/parent-probe-owner-grammar-after.txt`。追補の初稿は「`<値>` が非空で既存の
予約 sentinel に該当しない場合」としか書いておらず、実装より広かった。

|対象行の値|変更後の判定|
|---|---|
|`実行責任者 = thawk105、開始時刻 = 未記入`|ACCEPT|
|`実行責任者 = uid=alice、開始時刻 = 未記入`|**REJECT** (owner に等号)|
|`実行責任者 = alice、bob、開始時刻 = 未記入`|**REJECT** (owner に読点)|
|`実行責任者 ＝ ｔｈａｗｋ１０５、開始時刻 ＝ 未記入`|ACCEPT (NFKC 後に一致)|
|`実行責任者 =   thawk105  、開始時刻 = 未記入`|ACCEPT (owner の前後空白を除去)|
|`実行責任者 =    、開始時刻 = 未記入`|REJECT (strip 後が空)|
|`実行責任者 = TBD123、開始時刻 = 未記入`|ACCEPT (既存 sentinel の単語境界の外)|

追補に「正規化後の全体一致」「owner は読点・等号・改行を含まない」「前後空白を除いて非空」を
明記して閉じた。同じ probe で、expectation 行へ説明文を置くと別の exact grammar 検査で拒否される
ことも確認した (段 4 裁定の「全 10 欄に共通」は広すぎ、正しくは expectation 行を除く 9 欄)。

### 本変更後も実文書は受理されない

§5 表には対象行以外に **6 つ**の `未記入` が残る。変更後も同じ拒否 reason で止まることを実測した
(`verbatim/parent-probe-after.txt`)。**本 wave は事前登録を発効させない。**

### 凍結 pin の不変

追補の挿入位置は §5.1 の開始時刻節末尾 (§5.1.0 見出しの前) なので、
`PREREGISTRATION_SECTION_5_1_1_SHA256` / `..._SEMANTIC_SHA256` が pin する §5.1.1 の bytes は
動かない。実測で節長 21,833 bytes・raw `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`・
semantic `5d0b189bd68391b4a6876bd24400230e7186f6bc1fe374ea298d44edebcfd1a7` が pin と一致し、
`extract_preregistered_analysis_contract` も通った (`verbatim/parent-probe-section511-after.txt`)。
文書全体の sha だけが `09109bf472980fcceaa99b9aeab95f088b6d122d027aa62cd70d7031c4a4f47a` から変わった。
発行済み admission record は repo に 0 件なので失効対象はない — 親と段 3・段 6 の 2 レンズが
独立に現物で確認した (必須 3 path の不在、hidden / ignored を含む schema 検索)。
ただしこれは「この worktree と HEAD で 0 件」であり、外部 checkout まで含む主張ではない。

## 変異 matrix

**baseline PASSED (2 走とも)・9/9 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致。**
両走の `repo_head` はいずれも `fefbec1ab86a7998033a5033babfe5c8f676a8f1`。

|#|変異|期待赤 node 数|status|
|---|---|---|---|
|m1|追加受理分岐を削除し一律 sentinel 検査に戻す|1 (正例)|KILLED|
|m2|対象 label 分岐を無条件 `continue` にする|8|KILLED|
|m3|例外適用から label 一致条件を外す|1|KILLED|
|m4|owner の非空条件を削除|1|KILLED|
|m5|owner の `_RESERVED_SENTINEL_RE` 条件を削除|2|KILLED|
|m6|owner の whole-value sentinel 条件を削除|1|KILLED|
|m7|開始時刻の `未記入` を `(?:未記入|TODO)` へ広げる|1|KILLED|
|m8|`re.fullmatch` を `re.match` へ替える|1|KILLED|
|m9|owner capture を `[^、=\r\n]+` から `.+` へ替える|1|KILLED|

`_RESERVED_SENTINEL_RE` の定義そのものを変える変異は、対象欄以外の全行へ波及して赤の理由が
一つに絞れないため DW-M01 の単一理由性を満たさず登録しなかった。

### erratum — 初回走は m5 の timeout で中断した

初回 spec (`mutation-spec.json`、sha256
`eed4f890dd4478f52748eda7f012f11bfc127bbd2996f3586191e6c908c3b3fa`) は
`timeout_seconds` を 600 に置いた。m1〜m4 は KILLED (期待 node 完全一致) で通ったが、**m5 が
600 秒で timeout し、`hang_risk=false` の変異なので kill に数えられない** (DW-M06 は timeout を
fail-open の証拠とする)。harness はそこで orphan-hold を立てて中断し、m5 の変異が作業ツリーに
残った。初回結果は `mutation-out.json` にそのまま残してある (summary: registered 9・recorded 4)。

原因は hang ではなく **600 秒の枠に Pegasus の queue 待ちが収まらなかったこと**である。計測時の
scheduler には他 session の job が 14 本あり、うち複数が変異走だった。baseline 1 走の実測は
07:27:05→07:31:27 の 262 秒で、queue 待ちが支配的である。dispatch の既定 envelope
(queue-wait 900 秒 + overall grace 300 秒) より spec の 600 秒が先に切れていた。

復旧は orphan-hold の手順どおり行った。(i) `qstat` の行頭 RequestID で 1313.nqsv の不在
(= 終端) を確認、(ii) dirty path を `git checkout --` で復元、(iii) 復元 bytes を
`git diff --exit-code HEAD` で commit と照合し clean を確認、(iv) hold と sidecar
(`orphan-holds/1313.nqsv.json`) を削除。手動 `qdel` は F47 ラッチを武装させるので使っていない。

再走は残り 5 変異だけの spec (`mutation-spec-2.json`、sha256
`fbe77129f036e127467a70cedb3200addf298c9a8fa0bbe61f1cfdc058da96a3`) を新しい
`--out` / `--attempt-out` / `--wrapper-attempt 2` で起動し、`timeout_seconds` を 2700 (job walltime
3600 未満) へ、D612 の `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=1800` /
`IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600` を併せて上げた。5/5 KILLED・期待 node 完全一致で
完走した。

## 段 3・段 6 の所見の裁定

|#|所見|判定|
|---|---|---|
|A-1|追加受理経路が責任者未指名・制御文字を通す|real (記述)・refuted (本変更への帰属)。scope 外|
|A-2|負例の一部が追加分岐を通らず恒真。expectation 行のケースは別検査で落ちる|real・採用 (変異表と test 設計へ反映)|
|A-3|変異の期待失敗 node が一意でない|real・採用 (期待 node を完全集合で登録)|
|A-4|expectation / projection の到達性は増えるが検査は残る|refuted (blocker として)|
|A-5 / B-4|親 brief の欄数・anchor・pin 一般化の誤り|real・採用 (段 4 と本書で訂正)|
|A-6|floor セル読取経路が admission 検査を通らない|real だが scope 外|
|B-1|追補が実装より広い|real・**must-fix。追補を正確化して閉じた**|
|B-2|「6 つの未記入」は将来陳腐化する自己言及|nit。「本追補の時点で」で歴史的記述に限定済み|
|B-3|親 brief / 段 4 に残る誤記|real・採用 (下記で訂正)|
|B-5|§0 の射程を追補で明示すべき|real・採用 (追補へ 1 文追加)|

レビュー A の must-fix は 0 件、レビュー B の must-fix は B-1 の 1 件だった。

## 親の記録の訂正 (段 2 plan と段 6 レビューが指摘)

1. **未記入の欄数**: 段 1 brief は「残り 5 欄」と書いたが、正しくは**対象行以外に 6 欄**
   (対象行を含めて 7 行)。段 2 plan が先に訂正し、親が数え直して確定した。
2. **D1789 の要約**: D1789 は「発効し、その規則で解析を回した後」に bytes を変えず
   **insight の erratum** へ記録する裁定である。本 wave が本文へ追補を書ける根拠は D1789 ではなく、
   (i) 本書がまだ発効前 draft であること、(ii) §1 の改訂契約、(iii) D1871 が
   「事前登録本文の改訂は同文書の改訂契約 (追補) に従って別 wave が行う」と明示したこと。
3. **whole-file sha の pin**: literal の pin は無いが、record 検証が**動的に** whole-file sha と
   HEAD bytes の一致を要求する。「pin は無い」と一般化してはいけない。
4. **admission record JSON の field 名**: JSON 側は `preregistration_binding.content_sha256` で、
   `preregistration_content_sha256` は dataclass 側の名前である。
5. **「全 10 欄に共通」は広すぎる**: expectation 行には別の exact grammar 検査があり、説明文を置くと
   拒否される (実測)。正しくは expectation 行を除く 9 欄。
6. **検査順序**: sentinel 走査が先、expectation の構文検査が後。段 4 裁定は逆に書いていた。
   「expectation 行の負例だけでは sentinel 保持を証明できない」という結論は変わらない。
7. **anchor**: 適用後は検査関数の返却と文書束縛の行が下へずれた。段 1 brief の行番号は変更前の位置である。

## scope 外として残した real 所見 (裁定パッケージ候補)

1. **§5 の値セルは意味・表示上の非空を検査しない。** 説明文・制御文字 (NUL/BEL) を値として受理する。
   expectation 行を除く 9 欄に共通する既存性質であり、責任者の「不変の識別子による指名」義務
   (§5.1、D1812 (b)) は機械的に強制されていない。
2. **floor セルの読取経路が admission 検査を通らない。** material report → floor artifact issuer は
   文書全体から floor 行を exact prefix で探し、§5 の見出し境界・他の欄・責任者・開始時刻を検査しない。
   本 wave では挙動は変わらない (floor セルは `未記入` のままなので `None`)。
3. **admission validator のコード bytes が projection closure の入力である。** 本 wave のコード変更で
   live closure hash は変わる。literal pin が無いので現状は赤にならないが、
   「開始時刻だけの変更なので成果物参照も不変」とは言えない。

## 工数

- codex 子 6 本: plan 1 (read-only)、consult 2 (sol / luna)、author 1、review 2。
  luna は 1 回目が `Selected model is at capacity. Please try a different model.` で
  8 model call・220 秒・出力 0 byte (`f45_missing_output`) になり、`--job-id` を変えた再投入で成功した。
- 親の実測: probe 4 本、焦点走 2 本 (29 passed / 385 passed)、provenance full 監査 1 本
  (10466 件・新規違反なし)、変異走 2 本 (初回 4 変異 + baseline、再走 5 変異 + baseline)。
- 段 5 実装子は `run_tests.py` の dispatch preflight が rc=16 で落ち、自分ではテストを走らせて
  いない。「実装済み・未実走」と正直に申告した。実走は親が行った。

## 一次資料

- `verbatim/s1-brief.md`、`verbatim/s2-plan.md`、`verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`、
  `verbatim/s4-adjudication.md`、`verbatim/s5-author.md`、`verbatim/s6-reviewA.md`、
  `verbatim/s6-reviewB.md`
- 親の実測: `verbatim/parent-probe-before.txt`、`verbatim/parent-probe-counterfactual-before.txt`、
  `verbatim/parent-probe-after.txt`、`verbatim/parent-probe-matrix-after.txt`、
  `verbatim/parent-probe-owner-grammar-after.txt`、`verbatim/parent-probe-section511-after.txt`
- 変異: `mutation-spec.json`、`mutation-out.json` (初回・中断)、`mutation-spec-2.json`、
  `mutation-out-2.json` (再走)
