---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t989-t932-snapshot-cost
seq: 3
---

## 新規

### {{F:mutation-expected-node-is-held}}. 変異の期待赤 node に恒久保留 node を指定し、変異が必ず生存する構成を作った [恒真ゲート] [テスト代表性]

- 事象: 段 2 のプラン子が挙げた変異の期待 kill node 6 件のうち **4 件が D335 の恒久保留対象**
  だった。保留 node は既定 skip なので、production を壊しても赤にならず、
  **すべての変異が SURVIVED になる**。親が段 4 で気づき、既定で走る node へ再照準した。
  気づかなければ「変異 matrix を回して全部 SURVIVED だった = 検出力なし」と誤って結論するか、
  逆に「登録どおり回した」として無効な matrix を台帳へ載せるところだった。
- 根本原因: 保留機構 (D335) が広く効いている repository では、
  **テストの実在と実行は別問題**である。子は `grep` で node の実在を確かめたが、
  `orchestrator/tests/growth_test_holds.py` の `_HOLD_ROWS` を見ていない。
  親の brief も「既定で走る node に限る」と書いていなかった。
- 恒久対応: {{D:mutation-expected-nodes-must-be-runnable}} —
  期待赤 node は (a) 既定 skip されない、(b) error でなく failure として記録される、
  (c) `xdist_group` に属さない、の 3 条件を満たす node に限る。
- 再発検知: 変異 harness の事前検査は node の **collection 実在**しか見ない。
  保留 node は collection されるので通ってしまう。
  `_HOLD_ROWS` との突き合わせは未実装であり、当面は親の目視に依存する。

### {{F:mutation-harness-cannot-score-fixture-errors}}. module fixture を壊す変異が PARSE_ERROR になり採点できなかった [手順漏れ]

- 事象: `_build_snapshot_base` から seal 呼出を削る変異を流したところ、
  共有 module fixture の構築が例外で落ち、consumer 3 node が **error** になった。
  変異 harness の失敗 node 抽出 (`tools/mutation_harness.py` の `_failed_nodes`) は
  短縮要約の `FAILED ` 行しか読まないので、**error だけの走行からは node を 1 件も取り出せず**、
  `_observed_status` の「rc≠0 かつ抽出 0 件」経路で PARSE_ERROR になった。
  変異は現に殺せているのに、機械的には「採点不能」である。
- 根本原因: 抽出器が failure だけを対象にしており、pytest の error を node として扱わない。
  共有 fixture を持つ suite では、production の初期化経路を壊す変異は必ず error になる。
- 恒久対応: {{D:mutation-expected-nodes-must-be-runnable}} の (b) に従い、
  本 wave は実効 gate をテスト側へ再照準した — 新設 node が転送直後に sentinel を注入し、
  seal の効果 (`.git/logs` 不在 / `objects/info` 空 / unreachable object 無し) を
  自前で検査する形にした。これにより同じ変異が **failure** として記録される。
- 再発検知: 本 wave が新設した
  `orchestrator/tests/test_codex_reasoning_ab.py::test_build_snapshot_base_pack_transfers_unreferenced_base_closure_only`
  が seal 呼出削除で赤になる (変異 M6 で実測、KILLED)。
  harness 側の抽出器の是正は起票のみで未実施。

### {{F:parent-wrote-repo-during-mutation-run}}. 変異走行中に repo へ記録を書き、共有木の事後検査を落とした [手順漏れ] [計測汚染]

- 事象: 親が変異 matrix の走行中に `docs/spool/` の fragment と
  `output/insights/` の成果物を書いた。変異結果自体は 6/6 KILLED で有効だったが、
  wrapper の走行後検査が「source/main 共有木の観測 bytes が変化した」で落ち、
  **「共有木を触っていない」という保証が無効**になった。
  親が記録を commit してツリーを clean にし、走行を撮り直して解消した。
- 根本原因: 変異 harness は source 共有木の `git status` / `submodule status` の
  stdout bytes を走行前後で比較する。**テスト投入だけでなく docs 執筆も同じ検査に掛かる。**
  親は「待機中に独立作業を進める」規律に従って記録を書いたが、
  変異走行はその「独立作業」の対象外である。
- 恒久対応: memory `no-tree-writes-during-mutation-run` (既存)。
  本件はその再確認であり、待機中に進めてよい作業から**repo への書き込みを除く**。
- 再発検知: wrapper の走行後検査が現に落ちた (fail-closed)。
  検知は効いており、失われたのは走行 1 回分の時間だけである。

### {{F:hold-guard-breaks-self-loading-test-module}}. 保留 guard が同 file 内の正規 consumer を壊し、受入で差し戻された [受理集合の過剰縮小] [手順漏れ]

- 事象: 成長比例テストの恒久保留を `test_s8b_floor_campaign.py` へ登録し、
  契約どおり module 末尾へ guard binding を置いた。受入全走
  (11,648 passed / 93 skipped) で同 file の
  `test_deterministic_artifacts_across_roots_and_subprocess_environments` が**帰属赤**になった。
  このテストは自分自身の module をサブプロセスで
  `spec_from_file_location("floor_test_helper", __file__)` として読み込む characterization test で、
  guard がその読み込みを `GrowthTestHoldBypassRefused` で拒否した。
- 根本原因: `enforce_held_functions` は、pytest 経由でも解除 env でもなく
  `__name__ == "__main__"` でもない module 読み込みを**必ず拒否する**設計である
  (T-930 の plain runner 迂回を塞ぐため)。サブプロセスは別名で読むので
  `plain_runner` にどの値を与えても通らない。
  **保留可能性の前提条件「その file に standalone 読み込みの正規 consumer が無いこと」を、
  段 2 の選別も段 4 の裁定も見ていなかった。** 選別は実行コストの比例だけで行われた。
- 恒久対応: 本 wave は当該 1 件の保留を取り消した (登録 57 → 56)。
  機構側の解 (guard に「読み込みは許すが呼出だけ拒否する」モードを足すか、
  helper 閉包を切り出すか) と、選別条件への追加は
  {{T:hold-guard-blocks-standalone-module-load}} へ起票した。
- 再発検知: 受入全走が現に検出した (fail-closed)。
  ただし検出は受入 lease を 1 本消費した後である。
  静的に前倒しするには、保留登録時に「同 file 内に `spec_from_file_location(..., __file__)` /
  `runpy` / `exec(open(...))` 相当の自己読み込みがあるか」を検査する必要がある (未実装)。

## 再発

### F45

- **再発: 2026-08-16** — 段 6 の敵対レビュー A (レンズ = 正しさ防壁) が rc=1 / 成果物 0 byte で
  不受理になった。evidence_status は complete、40 model call・660 秒を消費して出力ゼロ。
  prompt は「これは防御目的の事前レビューである」と明記していたが**それだけでは通らなかった**。
  **今回は書き直しで通った点が本エントリの既存記述と異なる。** 効いたのは語彙の言い換えではなく
  **成果物の形の変更**である。「検知を迂回する構成を作れ」「反例の構成を書け」という
  手順書を求める形をやめ、「各項について守れている / 守れていない / 判定不能を file:line 付きで
  判定し、破れの成立条件を 1〜2 文で述べよ」という**判定形**にしたところ、
  同じ攻撃面・同じ対象で通った。同 wave のもう 1 レンズ (整合・実効性) は
  元から手順書を求めない形だったので初回で通っている。
  したがって恒久対応「エンジンを切り替える」の前に**出力形式を判定形へ変える**手が 1 つある。
  ただし本件 1 例であり、エンジン切替が不要になったとまでは言えない。
