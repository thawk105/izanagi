結論は **NO-GO** です。修正で多くの所見は閉じましたが、差分実測値、README、roadmap 継承条件、worklog の時制に承認前 blocker が残っています。

以下の表はレンズ D 内の重複再掲も省略せず、全 46 項目を判定しています。パスは repo root からの相対です。

## 1. 所見対応表

### レンズ C

| 所見 (レンズ・重み・要旨) | 親の処置 | 判定 | 根拠 (file:line) |
|---|---|---|---|
| C blocker 1 — 追補 B の exact diff 説明が偽 | 3 文書へ「7 hunk、39追加/33削除」と追記 | **regressed** — 新しい数値も偽。標準 Myers の `--numstat` は 46追加/31削除。旧版235行→v2 250行なので、39−33=6とも両立しない | `addendum-b-v2.md:8-16`; `package.md:194-199`; `README.md:35-38`; `worklog fragment:48-50` |
| C blocker 2 — source `submit_main` の投入前一意性 gate が孤児化 | gate 喪失を明記し、Q1(a)で受容する選択としてユーザーへ返した | **closed** — 復元ではないが、レンズ C 自身が推奨した「喪失を明示して裁定」を満たす | `package.md:97-125`; `addendum-b-v2.md:221-228`; `worklog fragment:29-33` |
| C blocker 3 — `p03` が同じ根での台帳取り替えを閉じない | P本文・Q3で反例を明記し、推奨を「台帳実体決定後に凍結」へ変更 | **closed** — Pは凍結対象外で、閉じたとは主張していない | `addendum-p-draft.md:163-188`; `package.md:146-169`; `README.md:43-45` |
| C must-fix 1 — unresolved marker が機械防壁でない | 機械防壁でないと明記し、将来実装Tへ送った | **closed** — 実装追加は別waveという裁定範囲に従う | `addendum-p-draft.md:42-49`; `package.md:246-250`; `worklog fragment:106-109` |
| C must-fix 2 — README が旧追補A blobを指す | reissue path・digestへ修正し、旧版との違いも明記 | **closed** | `README.md:20-25`; `publication-core-v2.md:38-40` |
| C nit — envelope説明とparserのfence規則が逆 | packageに記録しただけでB本文は維持 | **not-addressed** — 現bytesへの影響はないが、記述の逆転自体は残る | `addendum-b-v2.md:51-64`; `package.md:259-261` |

### レンズ D — 段3所見19行の処理監査

| 所見 (レンズ・重み・要旨) | 親の処置 | 判定 | 根拠 (file:line) |
|---|---|---|---|
| D/A1 nit→must-fix — 現行bytesのSHAが無い | worklogへ4 SHAを追加 | **closed** — 全4値とも実ファイルと一致 | `worklog fragment:65-73` |
| D/A2 blocker — 台帳取り替え攻撃の影響 | Q1へ攻撃系列と成果物影響を明記 | **closed** | `package.md:93-125` |
| D/A3 blocker — coreの予約正本宣言とB `b01` が競合 | coreを「公表台帳への予約手続き」に限定し、source候補数会計を分離 | **closed** | `publication-core-v2.md:569-574`; `addendum-b-v2.md:182-186`; `package.md:104-107` |
| D/A4 blocker — Pの未解決core参照 | Pを草案・非凍結に限定 | **closed** | `addendum-p-draft.md:20-49`; `package.md:12-14` |
| D/A5 nit — fence規則の相違 | nitとして記録のみ | **not-addressed** | `addendum-b-v2.md:51-64`; `package.md:259-261` |
| D/A6 must-fix — 近似値をexactと呼ぶ | 「高精度近似」と修正し、論理境界に使わないと明記 | **closed** | `package.md:41-51`; `worklog fragment:55-63` |
| D/A7 nit — `>` と `≥` の差 | 保守側の`>`を維持する理由を記録 | **closed** | `package.md:262-263` |
| D/B1 blocker — 最新指示をQ3で再質問 | supersedeとして記録し、問いを削除 | **closed** | `package.md:68-74`; `worklog fragment:18-20` |
| D/B2 blocker→must-fix — `p01`/`p02`を一括質問 | Q6/Q7へ分離 | **closed** | `package.md:209-242` |
| D/B3 blocker — 台帳実体未定のまま`p03`確定可能 | 推奨をQ3(b)へ変更し、Pを凍結対象外に維持 | **closed** | `package.md:146-169`; `addendum-p-draft.md:178-188` |
| D/B4 blocker→must-fix — B未承認と「C-1〜C-5実行済み」が矛盾 | package/worklogはC-1/C-3/C-5だけ実施へ修正 | **partial** — READMEはなお「C-1〜C-5を実行」と書く | `package.md:3-6`; `worklog fragment:12-16`; `README.md:3-4` |
| D/B5 must-fix — primary参照禁止のpin | Bとdecisionへ明記 | **closed** | `addendum-b-v2.md:177-180`; `decisions fragment:70-79` |
| D/B6 blocker — roadmap継承条件が不足 | decisionsの条件列挙を大幅拡充 | **partial** — source追補B、fold時core bytes同一性、事前seed・runtime乱数禁止がまだ明示されない | `decisions fragment:18-44`; `docs/roadmap.md:230-240` |
| D/B7 blocker→must-fix — land 2との所有関係 | 新規Tを§S7 #7と同じproducer系列へ結線 | **closed** | `worklog fragment:100-109`; `package.md:60-66` |
| D/B8 blocker — Pを同一landで凍結 | Pを明示的に除外 | **closed** | `package.md:12-14,127-144`; `addendum-p-draft.md:20-49` |
| D/B9 blocker — coreの「二者だけ」とB予約規範の競合 | authorityを「公表台帳への予約手続き」に限定 | **closed** | `publication-core-v2.md:569-574`; `addendum-b-v2.md:182-186` |
| D/B10 must-fix — B変更説明がexact diffでない | 変更分類と数値を追加 | **regressed** — 分類は改善したが数値が新たに偽 | `addendum-b-v2.md:8-16,221-228` |
| D/B11 must-fix — B v2には別承認が必要 | preambleとQ5へ明記 | **closed** | `addendum-b-v2.md:3-16`; `package.md:190-207` |
| D/B12 must-fix→blocker — landの効果を過小申告 | runtime不変とcanonical変更を分離して列挙 | **closed** | `package.md:16-32` |

### レンズ D — Q1〜Q7

| 所見 (レンズ・重み・要旨) | 親の処置 | 判定 | 根拠 (file:line) |
|---|---|---|---|
| D/Q1 must-fix — 推奨理由が失われたsource gateを復元しない | 復元しないことを明記し、選択肢と影響を提示 | **closed** | `package.md:109-125` |
| D/Q2 nit — 各選択肢の時期・成果物影響 | 3選択肢の影響を追記 | **closed** | `package.md:127-144` |
| D/Q3 blocker — 既決の直接指示を再質問 | 質問を削除しsupersedeとして記録 | **closed** | `package.md:68-74` |
| D/Q4 blocker — 実体未定の`p03`凍結 | 新Q3で(b)を推奨、Pは承認対象外 | **closed** | `package.md:146-169` |
| D/Q5 must-fix — core差分・内部矛盾・成果物影響 | packageでは構造差分と影響を正しく記述 | **partial** — READMEに「5行だけ／698行不変」が残る | `package.md:171-188`; `README.md:11,52` |
| D/Q6 must-fix — B差分説明・成果物影響 | 影響を追加し数値化 | **regressed** — 「7 hunk、39/33」が偽 | `package.md:190-207` |
| D/Q7 must-fix — `p01`/`p02`を分離 | Q6/Q7へ分割し別値入力も可能にした | **closed** | `package.md:209-242` |

### レンズ D — worklog fragment

| 所見 (レンズ・重み・要旨) | 親の処置 | 判定 | 根拠 (file:line) |
|---|---|---|---|
| D blocker — 未実行C-2/C-4を実行済みと記録 | 実施3件・未実施3件へ修正 | **closed** — worklog自体は修正済み | `worklog fragment:7,12-16` |
| D must-fix — 「ユーザーへ返した」の時制違反 | 元の文は削除 | **partial** — titleの「承認へ返した」、本文の「再裁定へ戻した」がなお完了形 | `worklog fragment:7,27-28` |
| D nit — P6攻撃系列の記録は正確 | 維持 | **closed** | `worklog fragment:46-47` |
| D must-fix — 近似値の呼称 | 高精度近似へ修正 | **closed** | `worklog fragment:55-63` |
| D nit — 実装差分ゼロ | 維持し範囲を明記 | **closed** | `worklog fragment:75-78` |
| D nit — セッション事象 | 維持 | **closed** | `worklog fragment:80-82` |

### レンズ D — decisions / spool

| 所見 (レンズ・重み・要旨) | 親の処置 | 判定 | 根拠 (file:line) |
|---|---|---|---|
| D blocker — roadmap条件の列挙不足 | 8群へ拡充 | **partial** — roadmapの全条件をまだ覆わない | `decisions fragment:18-44`; `docs/roadmap.md:232-240` |
| D must-fix — 「B5」と「第5案」の混同 | 両者を別裁定と明記 | **closed** | `decisions fragment:76-79` |
| D nit — decisions構造文法 | 構造を維持 | **closed** | `decisions fragment:1-13,50-70,81-93` |
| D 形式確認 — spool形式はGO | frontmatter・H2構造を維持 | **closed** | `worklog fragment:1-10,84-99`; `decisions fragment:1-9,70` |

### レンズ D — 取りこぼし・越権・実効性

| 所見 (レンズ・重み・要旨) | 親の処置 | 判定 | 根拠 (file:line) |
|---|---|---|---|
| D must-fix — land 2との所有関係 | §S7 #7を具体化する同一producer系列と明記 | **closed** | `worklog fragment:100-109`; `package.md:60-66` |
| D must-fix — Pの越権境界 | Pを非凍結にし、実体決定後の凍結を推奨 | **closed** | `addendum-p-draft.md:20-49`; `package.md:146-169` |
| D must-fix — B v2変更説明 | 分類と数値を追記 | **regressed** — 新しいexact数値が実測と不一致 | `addendum-b-v2.md:8-16`; `package.md:194-199` |
| D blocker — land効果の過小申告 | canonical変更とruntime不変を分離列挙 | **closed** | `package.md:16-32` |

## 2. 独立再計算

### 追補 B v2

標準の `git diff --no-index` で再計算した結果は次です。

- 初版: 235行
- v2: 250行
- `--numstat`: **46行追加 / 31行削除**
- `--unified=0` の `@@` 数: **8 hunk**
- 通常のcontext 3では近接差分が結合され5 hunkになるため、hunk数はオプション依存

したがって「7 hunk、39行追加/33行削除」は偽です。特に `39−33=6` は実ファイルの純増 `250−235=15` と両立しません。偽の値は `addendum-b-v2.md:8`、`package.md:194`、`README.md:35`、`worklog fragment:49` に重複しています。

`b01`・`b02` の slice は確認できました。

- 初版 `addendum-b.md:63-147`
- v2 `addendum-b-v2.md:78-162`
- 双方 **5186 bytes**
- 双方のSHA-256: `98ba244e857a3707cab3a350796042160e43c81bf3c405a4e394706e2d5d6f6c`
- byte比較: 一致

### 新 core v2

初版との差分は構造上、次の2箇所だけです。

- §0の段階表2行: `publication-core-v2.md:104-105`
- §8.1のblockquote: `publication-core-v2.md:569-574`

ただし統計は **8行追加 / 5行削除、698行→701行** です。したがって「対象箇所が2箇所だけ」は正しい一方、「5行だけ」「総行数698で不変」は誤りです。

packageは旧主張を削除済みです (`package.md:171-181`)。READMEは削除できておらず、明示された blocker 条件に該当します (`README.md:11,52`)。

### worklogの4 SHA-256

4件すべて実ファイルと一致しました。

| 対象 | 実測 | worklog |
|---|---|---|
| source core | `ac939af4de87…60e9` | 一致 |
| 追補A reissue | `f7db96ce8ecb…cfec` | 一致 |
| 新core初版 | `9b7bc1932dd7…6a64` | 一致 |
| 追補B初版 | `5071acbd9db1…4384` | 一致 |

記載箇所は `worklog fragment:65-73` です。

### roadmap継承条件

**完全一致ではありません。**

decisions fragmentはcluster-level、順序均衡、trace分離、fail-closed、独立validator、流用禁止を追加しました。しかし少なくとも次が落ちています。

- roadmapは本走入力について、source core・追補A・追補B、各commit/path/digest、測定checkout祖先性、fold時点core bytesとの同一性を要求する (`docs/roadmap.md:232-234`)。fragmentは下流coreと追補を一般化して書く一方、source追補Bとfold時点bytes同一性を明記していない (`decisions fragment:24-27`)。
- roadmapはblock順を事前seedと許容集合から選び、runtime乱数を使わないことを要求する (`docs/roadmap.md:235`)。fragmentは6順列・均衡・結果後変更禁止までで、この条件を落としている (`decisions fragment:31-33`)。

冒頭の「すべて引き継ぐ」という包括文だけでは、直後の不完全な具体列挙を補えません。

## 3. 新しい穴

- READMEがfix前状態のまま残っています。

  - 全C-1〜C-5実行済み: `README.md:3`
  - 旧Q番号: `README.md:10`
  - coreは5行だけ: `README.md:11,52`
  - Bは`b03`縮小1点のみ: `README.md:12`

- packageとworklogのQ番号自体は一致しています (`package.md:88-242`; `worklog fragment:88-95`)。ずれているのはREADMEです。
- worklogのtitle・本文・次の一手は「実施はC-1/C-3/C-5」で概ね一致しました。ただし `worklog fragment:27-28` はQ4〜Q7をまとめて「凍結承認」と呼びます。実際にはQ4/Q5が文書の凍結承認、Q6/Q7はPの候補値裁定です。
- `p03`の要件1の構成は、新しい誤認源とは判定しません。「呼び手が選べない」は必要条件として正しく、その直後に「これだけでは閉じない」反例、唯一台帳への束縛、scope外であることが明記されています (`addendum-p-draft.md:165-182`)。packageも(a)を非推奨、(b)を推奨しています (`package.md:152-169`)。

## 4. 承認前の必須修正

**NO-GO** です。承認前に必要なのは次の4点です。

1. 追補Bの偽の差分値を全箇所で訂正する。hunk数はcontext依存なので、使用コマンドを固定しないなら記載しない。
2. READMEを現packageへ全面同期する。特に実施状態、Q番号、core差分、B差分を直す。
3. decisions fragmentへroadmapの欠落条件を補う。最低でもsource追補B、fold時点core bytes同一性、事前seed・許容順序集合・runtime乱数禁止が必要。
4. worklogの返却完了形とQ4〜Q7の一括「凍結承認」を、実際の時点・問いの種類に合わせる。

fence規則の逆転は未解消ですが、現bytesの受理集合を変えないnitなので上の必須修正には含めません。

## 総括

closed: **35**
partial: **5**
regressed: **4**
not-addressed: **2**
判定: **NO-GO**