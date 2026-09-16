## 証拠の復元可能性への所見

以下はすべて**読解**による所見である。保存された実機ログも一次資料として読んだが、今回の実測・テスト実行ではない。

参照の略称：

- **driver** = `orchestrator/campaign/s1_direct_comparison.py`
- **gate** = `orchestrator/campaign/condition_meaning_gate.py`
- **test** = `orchestrator/tests/test_s1_direct_comparison.py`
- **brief** = `output/insights/2026-09-16_t2651-diag-detail-review/verbatim/s1-brief.md`
- **plan** = `/home/SFC/tanab/.claude/jobs/f3824ce9/wave/s2-plan.md`
- **前 wave** = `output/insights/2026-09-15/t1851-c3c-official-floor-run/`

**E1 — 実 rc は残るが、実 stderr・実 argv の全文復元は production 経路ですでに失われている。**

- **file:line:** gate:1563–1576、gate:1610–1615、gate:2597–2605、driver:345–350、前 wave `evidence/999102-floor-driver.stderr:30`。
- **成果物影響:** 材料レポートで「実 stderr・実 argv の全文を復元できた」と認定すると、保存証拠が支える範囲を超える。certified な選択結果・受理集合・試行台帳値の変更は確認していない。
- **根拠の種別:** 読解。
- **反例:** subprocess が `rc=1`、stderr を `b"ROOT_CAUSE\n" + b"x"*500` として返すと、gate は末尾 500 bytes だけを `repr` にする。`ROOT_CAUSE` は driver 到達前に消える。argv も引用整形後 500 bytes を超えると先頭と digest だけになる。

実際の `999102` 保存ログは stderr が `ded from` から始まり、argv には `original=846 bytes` の切り詰め印がある。driver が保持したのは**上流で加工済みの `evidence.detail` 全文**であり、元の subprocess 出力全文ではない。この区別は材料レポート上で必須である。上流実装の変更提案ではない。

**E2 — 外側の digest は照合用であり、消えた中央本文を復元する証拠ではない。**

- **file:line:** driver:273–293、test:289–307。
- **成果物影響:** 材料レポートで「全文 sha256 があるので失われた拒否本文を復元できる」と扱うと、実在しない復元能力を証拠へ加える。受理集合・台帳値への影響はない。
- **根拠の種別:** 読解。
- **反例:** `detail = "A"*5000 + "\n唯一の原因: config.h\n" + "Z"*5000`。中央の原因行は消え、両端・長さ・digest が残るだけになる。

digest の対象は正確には次である。

```python
shlex.join([detail]).encode("utf-8", errors="backslashreplace")
```

元の stderr bytes、元の argv bytes、未引用の `detail` のいずれとも同一とは限らない。人間が別途得た**完全な detail 候補**を同じ変換に通せば照合できるため、候補検証には有用である。しかし、両端からの全文復元、失われた stderr 前半の照合、元 argv の再構成には使えない。

孤立 surrogate を含む入力では `backslashreplace` が非単射になる点もある。例えば実際の孤立 surrogate と、そのエスケープ表記を文字列として含む入力が、変換後に同じ bytes になりうる。したがって digest が保証する同一性は、あくまで**変換後 bytes**についてである。

## byte 予算と切り詰めへの所見

**B1 — 4228 bytes は観測に基づく余裕であり、診断の十分性を保証する上限ではない。**

- **file:line:** driver:54–55、driver:279–293、前 wave `README.md:201–209`。
- **成果物影響:** 材料レポートで「4 倍だから重要行が保持される」と扱う根拠はない。重要行を失った拒否記録から原因を確定できなくなるが、受理集合・台帳値は変わらない。
- **根拠の種別:** 読解。
- **反例:** E2 の中央原因行を持つ長文。

1057 bytes は特定の一走行に由来する。同じ失敗を繰り返した三走行は、コンパイラ・失敗種別・出力文字種・argv 長などの母集合を覆う標本ではない。重要行が中央へ入る確率を算出できる分布資料もない。したがって確率は**評価不能**であり、低いとも言えない。長い後続診断が原因行の後に続く場合は、原因行を中央へ置く具体的反例になる。

ただし前 wave 自身は `README.md:202` で切り詰め不発を保証していない。予算の採用そのものを、この読解だけで実装 must-fix とはしない。

**B2 — 全拒否本文に 4228-byte 制限はない。ただし現行経路の record 数は最大 8 件に限定される。**

- **file:line:** driver:180–185、driver:198–215、driver:313–350、gate:74、gate:139–158、gate:4090–4103。
- **成果物影響:** 拒否本文全体を 4228 bytes 以下とする材料レポートの説明は誤りになる。選択結果・台帳値を変える欠陥は確認していない。
- **根拠の種別:** 読解。
- **具体的状態:** 対応する四つの macro を flags に含め、各 request の supply と meaning が non-green になる状態。

driver の defaults は四つだけで、それ以外の既知 macro は request 発行前に拒否される。各 request は supply・meaning を一件ずつ append する。gate の family 検査も各 request の二 arm の対応を要求し、record を追加しない。

したがって構造上の上限は **4 requests × 2 arms = 8 records**。detail 部分の合計は最大 **33,824 bytes**、さらに理由一覧・record prefix・改行が加わる。全体への共通切り詰めはない。これは実機で八件を観測したという意味ではない。

また、掲載対象は red だけでなく `unestablished` も含む。gate:3335–3340 のように detail 自体が存在しない record には、driver:346 の代替文字列が出る。

**B3 — 現行定数では、重複 slice・`[-0:]`・非正の available は到達不能と判断する。**

- **file:line:** driver:275–293。
- **成果物影響:** この境界について誤った診断 bytes や成果物値へ至る反例は確認していない。
- **根拠の種別:** 読解。実測ではない。
- **境界入力と帰結:**

| 条件 | 読解上の帰結 |
|---|---|
| 引用整形後 4228 bytes | そのまま返す |
| 引用整形後 4229 bytes | marker を確保して中央を省略する。省略量は 1 byte ではない |
| 現行定数・通常の実行可能な bytes 長 | marker は予算より十分小さく、`available > 0`、`tail_bytes > 0` |
| `available == 0` | 仮に成立すれば `[-0:]` が全文を返すが、現行設定では到達不能 |
| `available < 0` | 仮に成立すれば分割の前提が崩れるが、現行設定では到達不能 |

到達不能の根拠は、marker の増加要因が長さの十進桁数二つだけで、digest が固定長であること。64-bit の Python で表現可能な bytes 長でも各桁数は最大 19 桁であり、marker は 4228 bytes に遠く及ばない。

長文枝では `head_bytes + tail_bytes = available < len(encoded)`。したがって head と tail の元 bytes は重複しない。短文枝では分割自体を行わない。

**B4 — omitted の会計は変換後 bytes に対して整合する。raw stderr の会計ではない。**

- **file:line:** driver:274、driver:286–293、test:296–305。
- **成果物影響:** `original` と `omitted` を raw stderr の長さとして転記すれば、材料レポートの数量が誤る。変換後 bytes としての計数矛盾は確認していない。
- **根拠の種別:** 読解。
- **具体的状態:** head・tail 境界が日本語の UTF-8 文字途中へ入る入力。

`errors="ignore"` が落とした不完全な文字は、保持部分を再 encode して長さを引くため省略数へ含まれる。`backslashreplace` で展開された ASCII bytes も `original` に含まれる。これは一貫している。

一方、エスケープ表記の途中で切れる可能性はあり、計数の正しさは文字列の意味の復元を保証しない。また、短文枝は `encoded.decode()` ではなく元の `rendered` を返すため、孤立 surrogate の出力先での扱いまでは統一されていない。

## 親 brief と plan への所見

**P1 — この wave の成果は診断保持の検証であり、official 床値取得そのものではない。**

- **file:line:** brief:8–16、brief:64–67、前 wave `README.md:315–319`。
- **成果物影響:** 完了報告で床値 campaign の blocker 解消や床値取得を成果に数えると、材料レポートの到達段階が実態より進む。
- **根拠の種別:** 読解。
- **具体的状態:** 六変異の期待 node が一致し受入検査も成功しても、isolate worktree に `config.h` が供給されなければ元の build blocker は残る。campaign 再投入も今回の scope 外である。

brief の「研究前進」は、診断の信頼性について残っていたレビュー・変異検証を埋めるという**間接的価値**なら妥当である。床値取得を直接前進させる実装、と読むなら過大である。brief が明示的に床値取得完了を約束している、とまでは認定しない。

**P2 — 六変異の検出は、証拠復元可能性の十分条件ではない。**

- **file:line:** brief:48–49、test:235–260、test:276–309、plan:93。
- **成果物影響:** 六件の KILLED を「production で実 rc・実 stderr・実 argv を復元できる」証明へ拡張すると、材料レポートに未検証の保証が混入する。
- **根拠の種別:** 読解。
- **反例:** 上流が stderr の前半を捨てても、test:259 の「加工済み detail と拒否本文が一致する」は成立する。中央に原因行が消える E2 の入力も、両端・省略数・digest・予算という既存性質とは両立する。

登録の追加・削除は提案しない。P2 は今回の検証対象を固定する方針として成立するが、十分性の主張には使えない。

**P3 — 単一理由性は、M1 の挙動と M7 の検査依存を区別して記録する必要がある。**

- **file:line:** plan:9–14、plan:21–27、plan:60–64、test:209–232、test:296–307。
- **成果物影響:** mutation matrix の失敗 node をすべて同じ性質の独立検出として数えると、材料レポート上の検出力が過大になる。
- **根拠の種別:** 読解。
- **反例・判定:**

| 変異 | `new` の実際の効果 |
|---|---|
| M1 | detail を消すと同時に formatter 呼出し自体を消す。注入された `KeyboardInterrupt`・`SystemExit`・`GeneratorExit` が発生しなくなり、通常の `DriverError` になる。本文保持に加えて割込み伝播の検査も壊す |
| M2 | non-green の先頭一件だけ処理する。二件分の fallback を失うのも同じ record 網羅性の欠落であり、別の admission 性質を壊すとは認めない |
| M3 | 外側の `Exception` 捕捉を無効化する。指定テストは helper 全体を差し替えるので、その境界を直接攻撃している |
| M5 / M6 | 一方の端を空にする。omitted は再計算されるため、計数・digest・予算まで独立に壊すとは認めない |
| M7 | sha256 欄を消すと marker が短くなり、保持境界と omitted 値も変わる。ただし omitted の算術は維持される。omitted テストが失敗するのは正規表現が sha256 欄も要求するため |

M1 は「本文保持だけを壊す」という厳密な説明には収まらない。M7 は二種類の node が失敗しても、**省略数の正しさと digest 保持を独立に二つ破った証拠ではない**。plan はこれらの失敗集合を概ね明示しており、隠しているわけではない。

## 前 wave の主張の裏取り

**W1 — §7 の「M1〜M3 と M5〜M7 が守る性質を直接観測」は、保存ログが示す範囲より広い。**

- **file:line:** 前 wave `README.md:257–260`、`evidence/998882-floor-driver.stderr:29`、`evidence/999039-floor-driver.stderr:30`、`evidence/999102-floor-driver.stderr:29–30`。
- **成果物影響:** §7 を六性質の production 証明として材料レポートから参照すると、未発火の枝まで証明済みとして継承される。
- **根拠の種別:** 読解。過去実機ログとの照合であり、今回の実測ではない。
- **反例:** 三回とも掲載された拒否 record は `BACKOFF_FIXED:supply-effectuation:preprocess-failed` 一件で、formatter 例外の記録はない。

保存資料が支える範囲は次のとおり。

| 性質 | 裏取りできる範囲 |
|---|---|
| M1：detail 掲載 | 一回目は reason のみ、後続二回では detail 掲載を確認できる |
| M2：複数 non-green 全件掲載 | 複数件の掲載状態を示していない |
| M3：整形例外時も拒否保持 | 例外枝の発火を示していない |
| M5 / M6：外側の長文切り詰めで両端保持 | 三回目は外側予算内の全文掲載であり、現行の両端切り詰め枝の実証ではない |
| M7：外側の omitted 数・全文 digest | 三回目の digest は内側の argv 用。現行外側 marker の観測ではない |

特に「いずれも全文 sha256 の印つき」という表現は不正確である。一回目の保存拒否本文には digest がなく、三回目の digest は **argv の引用整形後全文**に対するもの。detail 全文の digest と混同できない。

§7 が harness の代替ではないと明記する点は正しい。親 brief:11–16 も harness 未実施を残件とし本走を求めており、**代替扱いしていない点では整合する**。ただし、この整合性は §7 の「六性質を直接観測」という過大な部分を正当化しない。

## 未被覆の性質 (提案ではなく観察)

以下は登録追加の提案ではない。根拠はすべて読解であり、未被覆だけを理由に実装 must-fix とはしない。

| 未被覆の性質 | file:line・具体的反例 | 成果物影響 |
|---|---|---|
| raw process 証拠から掲載本文までの全文保存 | gate:1614、test:255–259。先頭に原因があり末尾 500 bytes が別内容の stderr | 加工済み detail の一致だけでは raw stderr 全文保存を認定できない |
| 中央の重要行の復元 | driver:290–293、test:282–307。E2 の中央原因行 | 六変異検出後も原因不明の拒否資料が残りうる |
| 4228 / 4229 bytes の厳密な境界 | driver:275、test:258、test:290、test:316–317。`"a"*4228` と `"a"*4229` | 境界の検出力を六件の結果から認定できない |
| 長文を複数 record の拒否本文へ接続する経路 | test:193 は同じ短文、test:291 は helper 直接呼出し。異なる長文を複数 arm に持つ状態 | helper の性質だけでは掲載時の対応・網羅性まで保証できない |
| digest 値の改変検出力の変異実証 | plan:14 は欄の削除のみ、test:307 は値一致も検査。64 桁の形式を保った誤 digest | M7 の結果だけでは値改変変異を殺した実績にはならない |
| surrogate・引用境界・出力先 encoding | driver:273–276、driver:290–293。孤立 surrogate や引用の途中での切断 | byte 会計の正しさから保存先での完全な文字列保持を認定できない |

## nit

**N1 — 切り詰め結果は shell token としての可逆性を持たない。**

- **file:line:** driver:273、driver:281–293。
- **根拠の種別:** 読解。
- **反例:** `detail = "a"*5000` は引用不要の一 token だが、切り詰め後は空白や `<`・`>` を含む marker が挿入されるため、元の一 token として扱えない。引用エスケープ列の途中で切れば、引用構文自体も壊れうる。
- **成果物影響:** この文字列を shell token として解析する production consumer は今回確認しておらず、選択結果・材料レポート・台帳への具体的変更を確定できないため nit。

「引用整形した全文の一部を表示した文字列」と読むべきであり、再実行用の shell 表現とは認定できない。

**N2 — 短文に digest がないことは、現行実装の仕様と一致する。**

- **file:line:** driver:275–277。
- **根拠の種別:** 読解。
- **具体的入力:** `detail = "error: short diagnostic"` は引用本文だけを返す。
- **成果物影響:** 実装欠陥による成果物変更は確認していない。すべての掲載 detail に digest があるという説明だけが不正確になる。

## scope 外の観察

gate:1563–1621 の上流情報損失と、前 wave `README.md:317–319` の `config.h` 供給 blocker は確認したが、本 wave での上流変更・新規 gate・兄弟 driver 横展開・campaign 再投入は提案しない。

## 読めなかった射影 file

なし。

## 総括

現行機構は、**gate が生成した detail を予算内なら全文、長文なら両端と照合情報として拒否本文へ運ぶ**。実 rc・実 stderr・実 argv の全文復元を保証する機構ではない。

材料レポート上で裁定が必要なのは、全文復元の対象、前 wave §7 の観測範囲、六変異の KILLED が証明する性質である。現行定数での byte 会計・slice 重複・`[-0:]` に実装 must-fix は確認していない。ファイル変更・テスト・変異実行は行っていない。