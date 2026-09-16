単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate

## 必読事項の射影

次の絶対パスだけを読む。**この節が列挙した file を読めなければ即停止する** (停止規則の射程は
この射影 file に限る。ここに無い path の不在は停止理由にしない)。

- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/applied.patch — **今回の実装差分 (レビュー対象)**
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/ruling-stage4.md — 親の裁定 (仕様の正本)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D191.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D218.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D155.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-F108.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/cli.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/effective_clock_policy.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/report.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/schema_v2.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/campaign/execution_guard.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/tests/test_calibrator_certify.py

## 役割

**レンズ A = 実装の正しさ。** 実装を守らない。壊しに行く。
「この gate が効かない入力」「この gate が誤って落とす入力」を具体的に作れ。

## 攻撃してほしい点

1. **単一理由性 (変異の帰属)。** 親は下記 9 変異を事前登録した。各変異について、
   **その変異を入れたとき赤になる test が本当にその変異だけを理由にしているか**、
   手前・内側・後段の別の層が同じ入力を先に拒否していないかを実コードで確かめよ。
   帰属が成立しない変異があれば名指しで報告せよ。

   - M01 gate ブロック削除 / M02 expected と observed を入れ替え /
     M03 observed を `static_post` から `profile` へ / M04 expected を `profile` から `static_pre` へ /
     M05 canonical 戻り値を捨て `diagnostics["band_pass"]` で判定 / M06 `reasons.append` を消す /
     M07 `tolerance_pct` を凍結値でなく現行 policy から取る / M08 gate を `status` 決定の後ろへ移す /
     M09 条件を恒真拒否 (`if True:`) にする

2. **恒真・恒偽。** 新 gate が常に通る、または常に落ちる入力の族はあるか。
   `effective_clock_comparison_passes` の shape 要件 (expected は 2 key、observed は 1 key) に
   対して、実装が渡す dict は常に要件を満たすか。`profile["effective_clock"]` に
   `samples_mhz` や `tolerance_pct` が無い場合、実装は何を投げるか。その例外は
   どの except が捕まえ、attempt はどう終わるか。**publish されないことを確認せよ。**
3. **既存 gate との相互作用。** 新 gate の追加で、既存の
   `effective-clock-self-comparison-failed` / `post-attestation-mismatch` /
   `effective-clock-policy-changed` / `within-run-cv-invalid` のいずれかが
   **到達不能**にならないか。到達不能になるものがあれば名指しせよ。
4. **sidecar の書き込み。** 失敗分岐で `_write_exclusive` が例外を投げたらどうなるか。
   staging に同名 file が既にある可能性はあるか。sidecar の書き込み失敗で
   **publish が起きる経路**はあるか。
5. **sidecar の自己完結性。** sidecar だけから canonical 判定を再計算できるか。
   `policy_at_comparison` を含めて、再計算に必要な値が全部あるか。
   足りないものがあれば名指しせよ。実際に再計算する手順を 3 行で書け。
6. **published bytes 不変。** 合格する attempt の published artifact の bytes が
   変更前と一致することを、コードの経路から確かめよ。`_assemble_v2` の入力と
   serialization 設定に触れていないか。`notes` を含む既存 field に post 情報が混入していないか。
7. **テストが実装を変えずに緑にならないか。** 新設 3 test の各 assertion について、
   gate を削除しても緑のまま残る assertion を列挙せよ。
   とくに `test_cli_pre_post_clock_rejection_mechanisms` の `post-self-pass` と
   `policy-change` の 2 case を検算せよ (中央値・帯・policy 一致判定を自分で計算する)。

## 禁止

- file の作成・編集・削除、commit、git の状態変更。
- scope を広げる提案 (別 process verifier、外側 wrapper の改修、observer effect の是正、
  publish 順序の変更、canonical 述語の改訂、benchmark 中の clock 検査、成功時の証拠保存)。
  必要と判断したら **裁定パッケージ候補**として「scope 外だが real」と明記して返す。
- 仮想リスク向けの防壁の新設提案。

## 実行環境

sandbox は read-only で書込可能 tmp が無い。**pytest を実走しなくてよい。静的検査でよい。**
走らせていないものを緑と書かない。予算が尽きそうなら途中までの結論を出力形式どおり書いて終わる。

## 出力形式

H2 見出しだけを使う。所見ごとに「real / 疑わしい」「must-fix / nit」「根拠の file:line」を書く。
must-fix には、放置したとき成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
どう変わるかを 1 行で書く。書けないものは must-fix にしない。最後に必ず次の節を置く。

## 総括

- must-fix を 3 件まで、各 2 行以内。
- 帰属が成立しない変異の ID。
- このまま land してよいか (yes / 条件付き / no)。
