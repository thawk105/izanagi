# 段 4 裁定 — [T-2464] / D1871

## 0. 親 brief の訂正 (両レンズが指摘、親が現物で確認)

- **未記入の欄数は 5 ではなく 6** (対象行を含めると 7 行)。現物 `docs/phase3-b4-reflux-ablation-preregistration.md:159,162,163,164,165,166` + 対象行 `:167`。親が `awk` で数え直して確定した。
- **「whole-file sha pin は無い」は言い過ぎ。** literal の pin は無いが、**動的な whole-file 束縛はある** —
  `orchestrator/campaign/p3_b4_admission_record.py:775-783` が record 宣言の sha と HEAD 文書 bytes の
  一致を要求する。発行済み record が 1 件でもあれば本 wave の追補はそれを失効させる。
  両レンズが独立に「発行済み record 0 件」を現物で確認したので、本 wave は進めてよい。
- **D1789 の要約が不正確だった。** D1789 は「発効し、その規則で解析を回した後」に bytes を変えないと
  定めるもので、訂正先は insight の erratum である。本 wave が本文へ追補を書ける根拠は D1789 ではなく、
  (i) 本書がまだ**発効前 draft** であること (`:34`)、(ii) §1 の改訂契約、(iii) D1871 が
  「事前登録本文の改訂は同文書の改訂契約 (追補) に従って別 wave が行う」と明示したこと、の 3 点である。
- anchor の訂正: 検査関数は `602-688` (返却まで)、fixture は `orchestrator/tests/test_p3_b4_admission_record.py:81-112`、
  label 定義の開始は `:77`、§0 の対象例外は `:38-41`。

## 1. 所見の裁定

|#|所見|判定|scope|
|---|---|---|---|
|A-1|追加受理経路が責任者未指名 (説明文) と制御文字 (NUL/BEL) を通す|**real (記述として)・refuted (本変更への帰属として)**|scope 外。裁定パッケージ候補|
|A-2|負例の一部が追加分岐を通らず恒真 / expectation 行のケースは別検査で落ちる|real|scope 内・must-fix|
|A-3|変異の期待失敗 node が一意でない (指定 1 node と実際の集合が食い違う)|real|scope 内・must-fix|
|A-4|expectation / projection の到達性は増えるが検査は残る。closure hash は変わる|refuted (blocker として)|—|
|A-5|親 brief の欄数・anchor・pin 一般化の誤り|real|scope 内・§0 で訂正済み|
|A-6|floor セル読取経路が admission 検査を通らない|real|scope 外。参照一覧の補完として記録|
|B-1|D1789 の要約が不正確|real|scope 内・§0 で訂正済み|
|B-2|consumer 列挙に prerun issuer / floor resolver / material report が欠落|real|scope 内・焦点走へ 4 file 追加|
|B-3|「pin なし」「living だけ」の一般化が広い|real|scope 内・§0 で訂正済み|
|B-4|未記入数・anchor|A-5 と同一|—|
|B-5|追補に §0 の射程を 1 文で明示すべき|real|scope 内・採用|

### A-1 を不採用にする理由 (親の反実仮想実測)

親が現行 (未変更) コードで測った結果 (`verbatim/parent-probe-counterfactual.txt`):

- `実行責任者 = 担当者が決まり次第指名する、開始時刻 = 2026-01-01T00:00:00+09:00` → **ACCEPT**
- `実行責任者 = <NUL>、開始時刻 = 2026-01-01T00:00:00+09:00` → **ACCEPT**
- 同じ文字列を `env_tag (実測環境)` 欄へ入れても → **ACCEPT**

つまり「説明文・制御文字を値として受理する」のは**全 10 欄に共通する現行関数の既存性質**であり、
本変更が持ち込むものではない。関数の docstring 自身が
`types, meanings, and rendered non-emptiness are not checked` と非保証を宣言している
(`p3_b4_admission_record.py:27-30`)。案 B の owner 側検査 (非空・非 sentinel) は、
**既存 regime を owner 部分文字列へそのまま写したもの**であり、狭めも広げもしない。

owner の意味検証を足すことは、(i) ユーザーが名指しで scope 外とした
「仮想リスク向けの gate・検査・台帳・一般化の追加」に当たり、(ii) 対象行だけを他 9 欄より
**厳しく**して、D1871 の「§0 の原子性・sentinel 規則は他の欄についてはそのまま維持する」が
前提とする欄間の対称性を壊す。よって**実装しない。** 裁定パッケージ候補として返す。

## 2. プラン v2 (確定)

### 2.1 受理側 (`orchestrator/campaign/p3_b4_admission_record.py`)

段 2 plan §1 の**案 B をそのまま採用**する。`:667-673` の走査を `values.items()` にし、
label 文字列 `"実行責任者・開始時刻"` の一致でのみ追加受理する。追加受理する形は

```
^実行責任者 = (?P<owner>[^、=\r\n]+)、開始時刻 = 未記入$   (re.fullmatch)
```

で、`owner.strip()` に対し既存の 3 条件 (非空 / `_RESERVED_SENTINEL_RE` 不一致 /
`_RESERVED_SENTINEL_WHOLE_VALUES` 非該当) を課す。満たせば `continue`、満たさなければ既存判定へ落ちる。
`_SECTION5_LABELS`、sentinel 定義、正規化、表構造検査、`:674` 以降の expectation / projection 経路は
一切変えない。

### 2.2 テスト (`orchestrator/tests/test_p3_b4_admission_record.py`)

段 2 plan §2 を A-2 の裁定で次のように修正して採用する。

- **正例 1 件**: 対象行 = `実行責任者 = thawk105、開始時刻 = 未記入`、他 9 行は fixture の既定値。受理され、
  projection の返却が `_PROJECTIONS` と一致すること。
- **負例 (採用)**: セル全体 `未記入` / owner が `未記入` / owner が**空白のみ** / owner が
  `TBD`・`ＴＢＤ`・`N/A`・`要記入`・`x`・`---` / 開始時刻が `TODO`・`要記入` / 開始時刻に後続説明
  (`未記入（後日記入）`) / 順序逆転 / `、代理 = other` の挿入。
- **負例 (恒真なので変異の証拠に使わない)**: owner が**空文字**のケース。capture の `+` が先に落ちるため
  `bool(owner)` 削除に対して恒真である。テストとして置くこと自体は許すが、**変異表の期待 node に使わない**。
- **負例 (別検査で落ちるので使わない)**: expectation 行を `未記入` にするケース。`:674` の構文検査が
  先に落ちるため、その行の sentinel 保持を証明しない。
- **label 条件の正例・負例 (必須)**: 対象行を正例の値にしたうえで、`env_tag (実測環境)` 欄へ
  **正例と同一の文字列** `実行責任者 = thawk105、開始時刻 = 未記入` を置いたケースが**拒否される**こと。
  これが無いと「label 条件を外して構文だけで全行へ免除を広げる」変異が SURVIVE する。
- 既存テスト・既存 fixture の期待値を 1 つも変えない。

### 2.3 追補 (親が書く。実装面ではない)

挿入位置は `docs/phase3-b4-reflux-ablation-preregistration.md:357` の直後 (空行 `:358` の前、
§5.1.0 見出し `:359` の前)。両レンズが現物で一致を確認済み。
段 2 plan §3 の文面に、B-5 の 1 文 (§0 の「placeholder 語が 1 つでも残る限り」の射程が
本欄の開始時刻 `未記入` には及ばないこと) を足す。既存行を 1 文字も書き換えない。

### 2.4 焦点走の対象集合 (B-2 で補完)

```
orchestrator/tests/test_p3_b4_admission_record.py
orchestrator/tests/test_p3_b4_closed_critic.py
orchestrator/tests/test_p3_b4_launcher.py
orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py
orchestrator/tests/test_p3_b4_analysis_path.py
orchestrator/tests/test_p3_b4_prerun_issuer.py
orchestrator/tests/test_p3_b4_raw_record_producer.py
orchestrator/tests/test_p3_b4_material_report.py
orchestrator/tests/test_p3_b4_floor_artifact_issuer.py
```

`test_ccbench_spawn_sites.py` / `test_t671_source_binding.py` / `test_artifact_admission.py` は
本差分の焦点走からは外す (変更しない symbol の列挙であるため)。受入全走からは外さない。

## 3. 変異事前登録

A-3 の裁定により、**期待失敗 node の集合が事前に一意に確定しない**。DW-M07 / DW-M08 に従い、
**初回は probe 走とし全件 SURVIVED 期待で登録して観測 node を集め**、その結果で本登録し直す。

登録する変異 (位置はすべて 2.1 の追加分岐):

|#|変異|狙う条件|
|---|---|---|
|M1|追加受理分岐を削除し一律 sentinel 検査に戻す|機構そのもの|
|M2|対象 label 分岐を無条件 `continue` にする|対象行の他 sentinel 拒否|
|M3|例外適用から label 一致条件を外す|対象行限定 (env_tag 負例が殺す)|
|M4|owner の非空条件 (`owner and`) を削除|owner 空白拒否|
|M5|owner の `_RESERVED_SENTINEL_RE` 条件を削除|owner sentinel 拒否|
|M6|owner の whole-value sentinel 条件を削除|owner の `x` / `---` 拒否|
|M7|開始時刻の `未記入` を `(?:未記入|TODO)` へ広げる|開始時刻の語の厳密さ|
|M8|`re.fullmatch` を `re.match` へ替える|後続説明の拒否|
|M9|owner capture を `[^、=\r\n]+` から `.+` へ替える|追加 field の拒否|

M4 の期待 node には**空白 owner** のケースだけを使う (空文字ケースは恒真、A-2)。
`_RESERVED_SENTINEL_RE` の定義そのものを変える変異は、対象欄以外の全行へ波及して赤の理由が
一つに絞れないため **DW-M01 の単一理由性を満たさず登録しない**。

## 4. 段 5 の分割

編集面は `orchestrator/campaign/p3_b4_admission_record.py` と
`orchestrator/tests/test_p3_b4_admission_record.py` の 2 file、所有は素集合にならない
(同一機構の実装と検査) ため **Codex `role=author` 1 本**に寄せる。docs 追補は親が書く。

## 5. 裁定パッケージ候補 (real だが scope 外 — ユーザーへ返す)

1. **§5 の値セルは意味・表示上の非空を検査しない** (`p3_b4_admission_record.py:27-30` の自己申告どおり)。
   説明文・制御文字 (NUL/BEL) を値として受理する。全 10 欄に共通する既存性質であり、
   責任者の「不変の識別子による指名」義務 (§5.1、D1812 (b)) は機械的に強制されていない。
2. **floor セルの読取経路が admission 検査を通らない。**
   `p3_b4_material_report.py:215` → `p3_b4_floor_artifact_issuer.py:1470-1516` は文書全体から
   floor 行を exact prefix で探し、§5 の見出し境界・他の欄・責任者・開始時刻を検査しない。
   本 wave では挙動は変わらない。
3. **admission validator のコード bytes が projection closure の入力である**
   (`p3_b4_closed_critic.py:646-647`、`p3_b4_raw_record_producer.py:987-995`)。
   本 wave のコード変更で live closure hash は変わる。literal pin は無いので現状は赤にならないが、
   「開始時刻だけの変更なので成果物参照も不変」とは言えない。
