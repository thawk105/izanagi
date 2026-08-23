---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1477-d58-ablation
seq: 1
title: [T-1477] D58 bench-first screening v2 初回ablationのPegasus実装を完了しoff/on実測を試行、批准台帳gapで区切った (コード+テスト、branch worktree-dev-wave-t1477-d58-ablation)
---

## 本文

- `orchestrator/campaign/between_run_floor.py` をPegasus対応拡張 (env_tag選択・
  measurement profile・site-aware compiler・use_perf切替、M1-M6変異事前登録・確認済み)、
  `orchestrator/campaign/backoff_sweep.py` にofficial外部output_root向け
  `durable_root_policy`配線を追加 (M7、`orchestrator/campaign/s8b_oracle_driver.py`の
  既存パターンを移植)。両方とも段5-6のCodex role=author/fixが実装し、親が全diffを直接確認した。
- Pegasus計算ノードでの実PBSジョブ投入 (queue混雑下、gen_S実測でこのアカウントだけQUE=41件、
  D662着地前) を5回試み、4件の環境gapを発見・修正して完走させた: (1) gflags/glog未bootstrap
  (`tools/pegasus/certify_calibration.sh`の既存手順を移植)、(2) perf不在への未対応
  (`docs/pegasus-runbook.md`の「perf-optional-measurement」裁定どおり`use_perf=False`配線)、
  (3) job出力先`/work/1/SFC/tanab/dev-wave-jobs`自体がgit repositoryだった環境的な罠
  (output-rootを変更、コード変更不要)、(4) 上記durable_root_policy配線。
  calibration (read-heavy rr95のPegasus側between-run floor) は実測成功 (計算ノード174秒、
  between_run.cv=0.0021739527783741987、job dir証跡保存済み)。
- 5回目の投入で、`hooks/enforcement-source-closure-ratifications.v1.jsonl`
  (enforcement-source批准台帳、D526/worklog entry 660で2026-08-18に意図的に0行のままland、
  AI実装者は機構的に追記不可) により`backoff_sweep.py`(`declared_use_class="official"`固定)
  の新規campaign初期化がfail-closedで止まると判明した。詳細は{{F:backoff-sweep-official-ratification-gap}}。
  この経路は同機構land以降、環境を問わずおそらく未実行のままだった可能性が高い
  (2026-07-15 positive controlは同機構landより1か月前の実行)。
- AskUserQuestionでユーザーへ経緯を提示し、「waveをここで区切り記録する」の選択を得た
  (2026-08-22)。off/on実測 (insight §7の4基準判定) は批准台帳が人間の手で埋まった後の別waveへ
  引き継ぎ、既存実装 (Pegasus対応・durable_root_policy配線) はそのまま再利用する。
- queue混雑対応 (受入lease廃止・自ブランチ受入→land・merge後再テスト省略) の
  D662着地をpeerセッション2件から独立に確認した (`docs/decisions.md` D662)。本waveの受入は
  D662に従う。

- 2026-08-23 再開: branch を新しい worktree へ復元し (前セッションが worktree だけ撤去、branch と
  commit は無傷)、submodule を再帰初期化して local main (248 commit、tip
  `b89ea755400924179c9a6ba8bf4d9bb2ec6660c3`) を取り込み、受入全走を通して land した。ablation
  本走 (insight §7 (i)〜(iv)) は再開時点でも実行不能であることを、推定でなく現行 main 上の直接
  呼出しで再現して確認した (詳細は {{F:backoff-sweep-official-ratification-gap}} の 2026-08-23
  追試)。`declared_use_class` を `exploration` へ落として迂回する案も、批准検査が
  `require_environment_contract` にだけ従い use class と独立であることを実測して却下した
  (規律 2)。よって 2026-08-22 のユーザー裁定 (wave をここで区切る) をそのまま維持した。
- main 取り込みの競合は AI provenance の known-violation 台帳 2 file
  (`tools/check_ai_provenance.py`、`orchestrator/tests/test_check_ai_provenance.py`) だけで、
  両親が独立に別 entry を追記したことによる位置競合だった。解決は和集合 (本 wave 側 2 件 +
  main 側 7 件、registry 合計 53 件、畳み込みなし) で Codex `role=author` が書き、親は転記だけを
  行った。親は解決結果の全行がどちらかの親に存在することを機械照合し (どちらの親にも無い行 0 件、
  追加は構文成立用の区切りのみ)、merge commit に Codex `role=author` trailer を付けた。
  焦点走 `orchestrator/tests/test_check_ai_provenance.py` は 320 passed / 19.36 秒で緑。
- 人間が批准台帳へ追記すべき行の中身を確定して報告した (`schema_version` = 1、
  `closure_digest_sha256` = `db511c3d841128bfdbf5ba7c6bbdb2ce4da1fe0fdefe8d52aaacb0906ddeea44`、
  現行 closure 版に対する値)。

## 次の一手差分

### 更新

- [T-1477] **P1・人間アクション待ち**: off/on実測 (D58 insight §7 4基準判定) は
  `hooks/enforcement-source-closure-ratifications.v1.jsonl`への人間による批准追記を待つ。
  実装 (between_run_floor.py Pegasus対応・backoff_sweep.py durable_root_policy配線) は
  landしそのまま再利用可能。calibration実測データ (rr95 floor=0.002174) も証跡保存済み。
  再開時は`output/insights/2026-07-14_bench-first-screening-design.md` §5 item7の
  2026-08-22進捗注記から辿る。
  批准時の注意 (2026-08-23 実測): 追記する行は
  `schema_version` = 1 と、その時点の closure に対する `closure_digest_sha256` の 2 key だけ。
  批准は closure 版ごとにしか効かないため、追記後は `CONTRACT_LOADER_RELATIVE_PATHS` の
  25 file を触る wave が着地する前に campaign を起動する。また過去 5 回の投入では毎回
  別の環境 gap が出ているので、批准解除後も 6 件目が出る前提で着手する。
  base: 12def7e4fafc6b15d27c0c901e58d09cdd328c402bc5571b347a0addb2417b39
