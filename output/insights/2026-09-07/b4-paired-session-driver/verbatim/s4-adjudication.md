# 段 4 裁定 — B-4 対照対 driver (D1699)

段 3 の 2 レンズが 13 所見を返した。親が現物で裏取りしたうえで裁定する。
以下の「親の実測」は、いずれも親がこの worktree の現物を読んで確かめたものである。

## 裁定表

| id | 判定 | 扱い |
|---|---|---|
| correctness-boundary-1 | real (既存) | scope 外。証明しないことへ 1 行追加 |
| correctness-boundary-2 | **refuted** (残余は real) | 形は採用。rep 交互化は裁定パッケージ |
| correctness-boundary-3 | **real** | **採用。区間の中間 probe を維持する** |
| correctness-boundary-4 | real (既存) | scope 外。持ち越し |
| correctness-boundary-5 | **refuted** | 2 と同一 |
| correctness-boundary-6 | **refuted** | 指示対象の取り違え。記述を明確化 |
| correctness-boundary-7 | 一部 real | 文言を訂正。scope 判断は維持 |
| freeze-surface-01 | **real (実走阻止)** | scope 外。**裁定パッケージの最優先** |
| freeze-surface-02 | **real** | **採用。証明しないことへ明記** |
| freeze-surface-03 | **real** | **採用。reps_per_session を再定義** |
| freeze-surface-04 | **real** | 親の実測事実 6 は誤り。訂正 |
| freeze-surface-05 | 一部 real | scope 維持。依存を記録 |
| freeze-surface-06 | **real** | 親の実測事実 5 は不正確。訂正 |

## refuted の理由

### correctness-boundary-2 / 5 — 「2 呼び出しは 1 低水準 session でない」

**却下する。** 根拠は親が現物で確かめた次の事実である。

`runner.measure_point` は `reps` 回の loop を回し、**各 rep を別 process として spawn する**
(orchestrator/calibrator/runner.py:1122 の `for index in range(reps)`、docstring も
「Each rep is spawned, decoded, parsed, and cleaned before the next rep is started」と明記)。

したがって**この repo で「1 低水準 session」が「1 process」を意味したことは一度も無い。**
現行の 1 role session ですら 5 process の spawn 群である。所見の判定基準を適用すると
「現行 driver には低水準 session が 1 つも存在しない」ことになり、背理となる。
この driver における session の実体は**「admission probe に挟まれた 1 区間」**であり、
その区間へ candidate と reference を入れる形は D1699 の逐語を満たす。

D1699 が却下したのは「**別々の session で測ったもの**を、組だから同一セッションと呼ぶ」
読み替えである。今回は別々の session を作らず、**1 区間 1 record へ統合する**。
これは呼び名の変更ではなく、実行構造の変更である。

**ただし残余は real として認める。** 区間内で candidate の全 rep が reference の全 rep に
先行するため、区間内ドリフトは相殺されない。rep 単位で交互に測ればより強く相殺できる。
これは D1699 が要求していない measurement protocol の変更であり、D1641 §11.1 が
「統計関数」「admission と単独性の条件」の決定主体をユーザーに置いているため、
**実装せず裁定パッケージへ回す。**

### correctness-boundary-6 — 「床値と受理集合の単調性が逆」

**却下する。** 所見は「受理集合」を「tie と判定される block の集合」と読んでいるが、
本件の指示対象は「certified として受理される主張の集合」である。

床値は「これ以下の差は雑音とみなす」帯である。床値 0 は**どんな微差も雑音とみなさない**
ことを意味し、雑音水準の差が実在の勝ちとして certified される。つまり受理集合は広がる。
親 brief の記述は T-2166 の insight の逐語 (「tie 判定が消えて受理集合が最大に広がる」) を
引いたものであり、読みは一貫している。

**ただし記述は改める。** 慎重な読み手が取り違えたのだから、指示対象を明示する。

## 採用する所見

### correctness-boundary-3 — 中間 probe の維持 (必須)

3 session を 2 session にすると、probe 対が pair-sample あたり 3 対から 2 対へ減り、
**検出できない競合の窓が広がる**。現行なら candidate と reference の境界で検出できた競合を
新設計は取り逃す。**これは既存の正しさゲートの弱体化であり、規律 2 が禁じる。**

**採用する形:** 1 side session を `pre → 測定1 → mid → 測定2 → post` とする。
session は 1 つのままで、**3 probe すべてが clear のときだけ complete** とする。

- pair-sample あたりの probe 対の数は 3 対のまま変わらない (2 session x 3 probe = 6 probe、
  現行は 3 session x 2 probe = 6 probe)。**検出力を維持するだけで、新しい gate を足さない。**
- 既存の `_run_probe` 呼び出し点を使うので、subprocess 起動点の固定台帳は影響を受けない。

### freeze-surface-02 — 凍結が束縛する範囲の明記

凍結検査が束縛するのは**同一 revision 内の自己整合** (module 定数、spec、plan、raw、summary)
であって、**定数が D1699 の裁定値であること**ではない。定数と spec と実装とテストを
同じ commit で同期して変えれば赤にならない。

**採用:** 「証明していないこと」へ次を明記する。これは gate の追加ではなく、
**謳っていない保証を謳わないための記述**である (T-2166 が採った形と同じ)。

### freeze-surface-03 — `reps_per_session` の再定義

新しい side session は `measure_point` を 2 回呼ぶので、既存 header の `reps_per_session` は
実体と食い違う。**採用:** v3 header で `reps_per_measurement` へ改名する。

### correctness-boundary-1 — 測定実体の module 属性

**real だが本 wave が新設するものではない。** 親が確認したとおり、driver に `measure_fn`
引数は 1 箇所も存在しない (検索結果 0 件)。T-2166 が閉じた欠陥は
**caller が渡す callable の身元を書き換え可能な属性で照合していた**ことであり、それは既に無い。
module 属性の差し替えは同一 process 内でのコード実行を要し、in-process の gate では防げない。

**採用するのは「証明していないこと」への 1 行追加だけ。** 引数 seam を作らない方針は維持する。

## scope 外の real 所見 (裁定パッケージとしてユーザーへ返す)

### [最優先] freeze-surface-01 — 凍結 spec は実 Git 上で作成できない

**親が現物で確認した。** `load_frozen_spec` は次の 2 つを同時に要求する。

- spec の bytes が HEAD の tracked blob と一致すること (floor_pair_driver.py:1137-1139)
- spec 内の `provenance.source_commit` が load 時の HEAD と一致すること (同 :1182-1186)

spec は tracked file なので、**spec は自分自身を含む commit の hash を自分の中に書く**
ことになる。source_commit を書き換えれば blob が変わり tree が変わり commit hash が変わる。
これは hash の不動点であり、実用上構成できない。

テストが緑なのは、偽 Git が常に同じ定数を返すからである
(test_floor_pair_driver.py:320 付近の fake、spec の `source_commit` は固定値)。

**影響:** 現状 driver は production で spec を 1 度も load できない。window も summary も
`candidate_floor` も 1 件も生成されない。**B-4 床値の実走はこの欠陥を閉じるまで開始できない。**

**本 wave の scope 外である。** 依頼は「driver の形の修正と凍結だけ」であり、これは
provenance 束縛の設計 (spec をどの commit へどう束ねるか) の択一で、別の裁定が要る。
選択肢の例: source_commit を spec commit の親へ束ねる / blob hash だけで束ねる /
HEAD が source_commit の子孫であることを要求する。**どれを採るかはユーザー手番。**

### correctness-boundary-2 の残余 — rep 単位の交互測定

区間内ドリフトをさらに相殺するには、candidate と reference を rep 単位で交互に測る形がある。
D1699 は要求しておらず、D1641 §11.1 が測定手順の決定主体をユーザーに置いている。

### correctness-boundary-4 — `probe_fn` の差し込み口

`run_window` は competing-probe の callable を caller から受ける。CLI は固定の `_run_probe` を
渡すが、API 面としては差し替え可能である。**既存の形であり本 wave は変えない。**

### freeze-surface-05 — 事前登録文書の追随

新設計では reference が pair-sample あたり 2 件になるため、事前登録 §11.2 の
費用の目安 (参照 118 session) と、単一 `reference_tps` を使う式の記述が実体と食い違う。
**正式標本の実走前に更新が必要。** 別 wave [d2dd9f] が §11.2 の数値を触っており、
構成に関する記述は本件の裁定範囲として当方へ残すと通知してきた。依存として記録する。

## 親の実測事実の訂正 (段 3 が正しく暴いた)

- **事実 6 は誤りだった。** summary の consumer は現時点で**存在しない**。
  `p3_b4_material_report.py:242` は `floor=None` を無条件に渡す。別 session が今まさに
  その consumer を作っている段階であり、「唯一の consumer」は将来の consumer である。
  設計判断 (schema を上げる) は変わらない。
- **事実 5 は不正確だった。** `test_floor_pair_driver.py:1977` が
  `"floor-pair-summary/v2"` を literal で pin している。変更対象 file の内側なので実害は無く、
  プランも更新を拾っているが、「main 全体で 2 台帳だけ」という言い方は誤りだった。
- **事実 1 の言い方を訂正する。** 正しくは「既存の 2 つの API はいずれも binary を 1 個しか
  取らない」であり、「低水準で 2 binary を 1 session に収めることが原理的に不可能」ではない。
  runner へ対測定 API を足すことは可能である。ただし runner は全 campaign が使う共有の
  測定権威であり、2 file の scope 外なので採らない。上の背理により、必要でもない。

## プラン v2 (実装子へ渡す確定形)

段 2 プランを基礎とし、次の 4 点を変更する。

1. side session を `pre → 測定1 → mid → 測定2 → post` とし、**3 probe すべて clear** を
   complete の条件に加える。probe record は session 内に 3 件持つ。
2. window header の `reps_per_session` を `reps_per_measurement` へ改名する。
3. 「証明していないこと」へ次の 2 行を追加する。
   - 凍結項目の一致検査は同一 revision 内の自己整合を示すだけであり、定数が D1699 の
     裁定値であることを証明しない。独立な pin も freeze receipt も無い。
   - 測定実体は module 属性であり、同一 process 内でこれを差し替える経路は防がない。
4. (P1-d) はプランの対案どおり、spec / plan / window / summary の 4 schema を上げる。

それ以外はプランのとおり。**測定 callable の引数 seam は追加しない。**
**rep 単位の交互測定は実装しない** (裁定パッケージ)。
**freeze-surface-01 は本 wave では直さない** (裁定パッケージ)。

## 変異事前登録 (DW-M01)

実装後、各変異が**ただ 1 つの理由で赤になる**ことを確認する。
確認できない変異は登録から外し、実効 gate へ再照準する。

| # | 位置 | 変異 | 期待する唯一の赤 |
|---|---|---|---|
| M1 | `compute_gain_difference` | 分母を 1 つに戻す (r1 のみ使う) | r1 != r2 の四入力テスト |
| M2 | `_run_planned_session` | 中間 probe を削除する | probe 順序テスト |
| M3 | `_run_planned_session` | 中間 probe の結果を complete 判定から外す | 中間 probe 汚染テスト |
| M4 | `_parse_statistics` | reference 数の exact 一致検査を外す | spec 側だけ 1 にした負例 |
| M5 | `_parse_statistics` | D 式の exact 一致検査を外す | spec 側だけ改変した負例 |
| M6 | session complete 判定 | measurement 1 件でも complete にする | exact 2 件完備テスト |
| M7 | plan 束縛 | raw の自己申告 role を権威にする | candidate/reference 交換の負例 |
| M8 | window header | `reps_per_measurement` を旧定義のままにする | header と実測定数の照合 |

受理集合を縮小する変更ではないため過剰拒否の正例は登録しない。
テスト強化だけの wave でもないため `DW-M08` の新旧両走は登録しない。
