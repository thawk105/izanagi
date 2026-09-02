# [T-2166] B-4 床値の対照対 driver — wave の逐語と変異台帳

事前登録 §11.2 が要求する測定計画を起動できる経路 (`orchestrator/campaign/floor_pair_driver.py`)
を新設した wave の一次資料。裁定は D1453、境界は D1437、役割は D1383 / D1266。

**この wave は bench を 1 度も実走していない。** 性能値を新規取得していない。
実走は床値発効の凍結項目確定と測定認可の後に限る (D1453)。

## 何を作ったか

凍結した測定手順 spec (校正済み `PerfConfig`、閉じたセル集合、対照対と共通参照点、標本数、
時間窓、統計関数、出力先) を読み、対照対ごとに `D = |gain_1 - gain_2|` を測り、
raw から再計算できる create-only 成果物へ出す driver。`gain = throughput / reference_tps - 1`。

## 敵対レビューが暴いた、緑のテストが守っていなかった穴

初版は焦点走 110 件が緑だったが、レビュー 2 本が独立に次を指した。いずれも成果物の値と
受理集合を動かす経路であり、仮想リスクではない。

1. **測定実体の身元が自己申告で偽装できた。** 実装は測定関数の `__module__` と `__qualname__` を
   本番の名前と比較していた。Python ではこの 2 属性は書き換えられるので、偽関数に本番と同じ
   名前を付ければ通る。偽関数が対の両側へ同じ値を返せば `D = 0`、すなわち**床値 0** が生成でき、
   tie 判定が消えて受理集合が最大に広がる。差し込み口自体を権威経路から除いて閉じた。
2. **校正の意味照合が半分だった。** schema が正規値として許す `quality.status="rejected"` の
   成果物を受理し、校正の `saturation.records` と実際に測る `records` を比べていなかった。
   棄却された動作点や別のレコード数で測れる状態だった。
3. **競合検査を常時無効化できた。** 競合検知の argv が spec の自由 field だったため、
   常に rc=1 を返す command を指定すると分類器が「競合なし」と読む。競合中の汚染された測定値が
   正常標本として床値に入る。argv を driver 側の定数へ固定した。
4. **site 判定が証拠必須でなかった。** NQSV 証拠を欠く Pegasus login node を OTHER と誤認しえた。
5. **finalizer が実行順と terminal を再検証していなかった。** 無作為化した順で実行したという
   参照が、後から並べ替えた成果物と区別できなかった。

## 親が「保証」と書かないことで閉じた 3 件

新しい受領証・台帳・attestation を建てず、**証明していないことを明記する**方向で閉じた。
これは仮想リスク向けの機構を足さないという scope 判断であり、§11.1 が凍結項目の決定主体を
ユーザーに置いていることにも従う。

- 測定手順 spec が結果を見る前に凍結されたことを証明しない (freeze receipt は無い)。
- 測定が人間の認可後に行われたことを証明しない。
- 成果物の削除・改名・改変を防がない。防ぐのは「同じ path が残っている間の再作成」だけ。
- 標本の統計的独立性を判定しない。window / campaign を記録するだけ。
- strip 済み binary の trace 混入を検出しない。`nm` の PATH 解決先も束縛しない。

## 変異走行 — probe で 3 件が生存し、うち 1 件が実欠陥だった

期待ノードを推測で書くと帰属が崩れるため、**probe (全件 SURVIVED 期待で観測ノードを集める)
→ 期待確定 → 本走**の順で回した。

- `mutation-spec-probe.json` / `mutation-probe-ledger.json`: 24 件登録、24 件完走。
  21 件が赤 (登録は SURVIVED 期待なので MISMATCH と記録される)、**3 件が生存**。
- 生存 3 件の決着:
  - **参照成果物の宣言 sha256 の一致検査は実欠陥だった。** 取り除いても 139 件のテストが 1 件も
    落ちなかった。実 bytes は HEAD tracked blob と一致させたまま宣言値だけを誤らせる負例を足した。
  - **build receipt の `trace=false` と binary SHA の 2 件は冗長 gate だった。** driver が呼ぶ前に
    sanctioned な `s8b_binary_admission.validate_portable_binary_record` が同じ入力を先に拒否する
    (`orchestrator/campaign/s8b_binary_admission.py:351` と `:397`、親が現物で確認)。
    driver 側の同名検査だけで赤になる入力は構造的に存在しない。実装は防御として残すが、
    **実効 gate は validator 側**であり、単独変異の証拠からは外す (DW-M03)。
    子は偽装テストを作らず file:line の根拠付きで「到達不能」と報告した。
- `mutation-spec-final.json` / `mutation-final-ledger.json`: 22 件登録、
  **22 件 KILLED、期待ノード完全一致、MISMATCH と SURVIVED ともに 0**。

### 変異 harness の wrapper について正直に書く

本走・probe とも、使い捨て worktree の wrapper が走行後に
「共有木の観測 bytes が変化した」として rc=125 を返した。**変異自体は固定 commit の
使い捨て worktree で 24/24・22/22 完走しており、台帳は完全である。**
親は自分の wave worktree が走行前後で変更ゼロであることを独立に確認した。
走行中に他の稼働 wave が共有木を動かしたためと見ており、wrapper が主張できなかったのは
「全窓にわたって共有木が不変だった」ことだけである。**この限界は主張せず明記する。**

## 収録物

- `verbatim/s2-plan.md` — 段 2 プラン (codex plan / read-only / xhigh)
- `verbatim/s3-consult-lensA.md` — 段 3 敵対相談 A (正しさ境界)
- `verbatim/s3-consult-lensB.md` — 段 3 敵対相談 B (整合と実効性)
- `verbatim/s5s6-author.md` — 段 5 実装
- `verbatim/s5s6-review-A.md` / `verbatim/s5s6-review-B.md` — 段 6 敵対レビュー 2 本
- `verbatim/s5s6-fix.md` — fix 1 巡目 (M1〜M10)
- `verbatim/s5s6-fix-round2.md` — fix 2 巡目 (親の実走で出た赤 2 件)
- `verbatim/s5s6-fix-round3.md` — fix 3 巡目 (変異で生存した 3 件)
- `verbatim/s5s6-fix-round4.md` — fix 4 巡目 (在庫登録)
- `mutation-spec-probe.json` / `mutation-probe-ledger.json` — probe 段
- `mutation-spec-final.json` / `mutation-final-ledger.json` — 本走

逐語はいずれも子の出力そのままで、親は編集していない。子の主張がそのまま正しいことを
意味しない — 親が real / refuted を裁定した結果は worklog と各 commit message にある。

## 逐語の可逆最小正規化

4 file が markdown の強制改行 (行末の連続空白) を含み、`git diff --check` に抵触した。
**可視文字を 1 つも変えず、行末の空白だけを除いた。** 原文の sha256 と byte 数、および
除いた行番号とその接尾辞を `verbatim-normalization.json` に記録してある。同 file を使えば
原文 bytes を厳密に復元できる。

|file|原文 bytes|正規化後|除いた行数|
|---|---:|---:|---:|
|`verbatim/s2-plan.md`|22,725|22,715|5|
|`verbatim/s3-consult-lensA.md`|19,357|19,349|4|
|`verbatim/s3-consult-lensB.md`|18,992|18,984|4|
|`verbatim/s5s6-review-B.md`|15,889|15,833|28|
