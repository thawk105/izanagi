単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate

## 必読事項の射影

次の絶対パスだけを読む。**この節が列挙した file を読めなければ即停止する** (停止規則の射程は
この射影 file に限る。ここに無い path の不在は停止理由にしない)。

- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/brief-t559.md — 親 brief (本 wave の scope と不変条件)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-T559-entry250.md — [T-559] 本文 (逐語)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-T559-entry944.md — 裁定行 (逐語)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D191.md — D191 全文 (逐語)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D218.md — D218 全文 (逐語)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D155.md — D155 全文 (逐語)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-F108.md — F108 全文 (逐語)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/cli.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/effective_clock_policy.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/report.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/model.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/campaign/execution_guard.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/tests/test_calibrator_certify.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/schema_v2.py

## 依頼

[T-559] の実装プランを **file:line 粒度**で起草する。実装はしない。file を書き換えない。
commit しない。git の状態を変えない。

課題: 較正取得 CLI (`orchestrator/calibrator/cli.py` の `_certify_main`) は、benchmark 後の
実効クロックを一度も検査しないまま publish する。既存の `_effective_clock_self_comparison_passes`
は benchmark 前に凍結した profile の **自分自身**を見るだけで、benchmark 後の観測値を見ない。
外側の wrapper が撮る `attestation-post.json` は publish より後に走り、誰も評価せず publish を
取り消さない。

ユーザー裁定 (確定・覆さない): 択 (a) 採用 —
**凍結した pre profile の effective clock と、benchmark 後に観測した clock の canonical 比較を
publish の前に課す。** publish transaction 自体を後ろへ移す案は採らない。

## 守る不変条件

1. canonical 述語は `orchestrator/campaign/execution_guard.py` の
   `effective_clock_comparison_passes` を**経由**する。帯計算を再実装しない (D191 決定 1)。
2. 述語・policy 定数 (`EFFECTIVE_CLOCK_TOLERANCE_PCT`) を変更しない。受理を広げない。
3. **gate を通った attempt の published artifact の bytes を変えない。** 既存の登録済み較正 2 件は
   sha256 で事前登録文書と `orchestrator/campaign/env_contract.py` に pin されている。
4. publish (rename) の位置と、publish 後の `_published_self_comparison_receipt` を動かさない。
5. 拒否時に published artifact を削除しない (D191 却下済み)。publish 前に止めることで達成する。
6. 比較の expected 側は凍結した pre profile とし、post 側の値で上書きしない。

## 答えること

1. 新しい比較を差し込む **正確な行**と、その前後の制御フロー。なぜその位置が「publish 前」を
   満たすかを、`status = "accepted" if not reasons else "rejected"` との関係で示す。
2. post observed clock の供給源。`static_post = _profile_dict(probe_fn())` の
   `effective_clock.samples_mhz` で足りるか。足りないなら何が足りないかを file:line で示す。
   **新しい probe 呼び出しを足す案は、既存で足りない理由を示せた場合だけ**提案する。
3. 新しい reason code の名前と、既存 reason 群 (`orchestrator/calibrator/report.py` の
   `certification_quality_reasons`、`_acquisition_reasons`) との衝突・重複の有無。
4. 失敗時に何を成果物として残すか。D191 決定 5 が early 拒否に要求する「成果物だけから
   hash と判定を再計算できる」要件が、今回の late 拒否にも及ぶかを逐語から判断して答える。
   及ぶなら残す場所 (attempt staging 配下) と形を file:line で示す。
5. **published bytes を変えずに済むか**の判定。`_assemble_v2` と `schema_v2.validate_calibration_v2`
   を読み、artifact に新 field を足す案と足さない案の差分を bytes 影響つきで比較し、1 案を推す。
6. 正例・負例テストの設計。`orchestrator/tests/test_calibrator_certify.py` の既存 fixture の形
   (実 probe に寄せた 48 標本・`tolerance_pct=100.0`・3 回の profile 取得) を読み、
   **既存 fixture を壊さずに**「pre は帯内だが post が帯外」という**新 gate だけが落とす**入力を
   どう作るかを、既存 helper 名を名指しして示す。この入力が既存の self 照合を通ることも示す。
7. 実装が触る file の一覧と、それぞれの編集行数の見積り。scope 外の file を触る案は出さない。
8. この plan の弱点 — 自分の案が間違っている可能性が最も高い箇所を 1 つ挙げる。

## 禁止

- file の作成・編集・削除、commit、branch 操作、git の状態変更。
- canonical 述語 (`effective_clock_comparison_passes`) と policy 定数の改訂提案。
- publish 順序の変更提案、別 process verifier ([T-560])、外側 wrapper
  (`tools/pegasus/certify_calibration.sh`) の改修提案、observer effect (F108) の是正提案、
  benchmark **中**の clock 検査の提案。いずれも本 wave の scope 外である。
- 一般化・framework 化・新しい gate 族・新しい台帳の提案。
- 仮想リスクに備える追加の防壁。brief が名指した穴だけを塞ぐ。

## 実行環境

sandbox は read-only であり書込可能 tmp が無い。**pytest を実走しなくてよい。静的検査でよい。**
テストの実測は親が行う。走らせていないものを「緑」と書かない。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終わる (無出力が最悪)。

## 出力形式

H2 見出しだけを使う。最後に必ず次の節を置く。

## 総括

- 推す案を 1 つ、3 行以内で。
- 実装が触る file:line の一覧。
- 自分の plan で最も弱い点。
