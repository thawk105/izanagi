---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-b10-overthrottle-grid
seq: 3
---

## 新規

### {{F:tautological-onset-guard}}. 判定規則の主要条件が恒真で 1 件も拒否していなかった [恒真ゲート]

- 事象: 過抑制開始点の判定に「床を超える低下が 2 点連続したときだけ開始点にする」条件を置き、
  裁定・実装・レビューの 3 段すべてを通過した。しかし変異 matrix でこの条件を
  「1 点でも可」に緩めても 1 件も赤にならなかった。追うと、候補点はノイズ同値なピーク台地の
  右端より右の点だけなので**定義上すべて床を超えて低下しており**、条件は 1 件も拒否していなかった。
  ループ末尾の同種条件も同じく恒真だった。
- 根本原因: 条件の述語だけを見て、その述語へ到達する入力集合を見なかった。
  候補集合の構成 (`equivalent` の補集合) が述語をすでに含意しているため、
  条件は文面としては保護に見えるが、実行時には常に真になる。
  さらに、単発の落ち込みを開始点にしない働きを実際に担っていた同値集合の連続性検査には
  テストが 1 本も無く、実効の gate が無検査のまま残っていた。
- 恒久対応: 恒真条件を候補数による明示的な分岐へ挙動保存で書き換え、恒真である理由を
  コードのコメントに残した。実効 gate である連続性検査に positive control テストを足し、
  その検査を無条件に真へ変える変異で赤になることを確認した
  (`orchestrator/tests/test_backoff_extended_sweep_report.py::test_single_mid_grid_drop_then_recovery_keeps_onset_unresolved`)。
  裁定文書の記述も実際の規則へ訂正した ({{D:b10-adaptive-state-coverage}} と同 wave)。
- 再発検知: 判定規則を新設する wave では、各条件について
  **その条件が偽になる入力が候補集合に存在しうるか**を変異で確かめる。
  変異が SURVIVED したとき、まず等価変異を疑い、等価なら実効 gate へ再照準する
  (`docs/dev-wave/mutation.md` の `DW-M01` / `DW-M02`)。

### {{F:uncommitted-registry-blocks-children}}. 実装子が裁定どおり登録簿を変えた直後から codex 子が全部起動不能になった [手順漏れ]

- 事象: 裁定に従って実装子が `tools/pegasus/admission_registry.json` へ新しい計算ノード job を
  登録した。その直後から段 6 のレビュー子 2 本が起動時に rc=2 で落ちた。
  原因は `tools/check_codex_hooks.py` の exact 検証で、この file は
  **working bytes が HEAD blob と一致しないと codex 子が段を問わず起動できない**。
  同種の停止を `orchestrator/campaign/loop.py` でも踏んだ — こちらは contract loader の閉包に入り、
  未 commit の間 fixture が setup で落ちて 19 件のエラーが出る。どちらも偽赤である。
- 根本原因: 既存の知見は「authority docs の未 commit 差分」を対象としていたが、
  registry と contract loader 閉包の file は**実装子が裁定に従って変更することが期待されている**
  ため型が違う。「変更してはいけない file」ではなく「変更したら段 6 の前に commit が要る file」である。
  この順序制約はどの手順書にも書かれていなかった。
- 恒久対応: `docs/dev-wave/workers.md` の段 6 契約へ、
  「HEAD blob 束縛のある file を段 5 で変更した wave は、段 6 の子を起動する前に親の統合 commit を行う」
  を統合する。束縛される file の一覧は `tools/check_codex_hooks.py` と
  `orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` が正本である。
- 再発検知: 起動前検査の rc=2 本文に file 名が出るので、それを未 commit 差分と照合する。
  起動に失敗した子の receipt は残るため、**原因を直して同じ job-id で投げ直すと
  「既存の完全な receipt は上書きできない」で再び落ちる** — `--job-id` を変えて投げ直す。

### {{F:content-scanning-inventory-missed}}. 内容走査で production を集める inventory test が焦点走から漏れた [テスト代表性]

- 事象: 新設した 2 つの production module が perf に言及するため
  `orchestrator/tests/test_official_perf_closure.py` のレビュー済み一覧から外れて赤になった。
  この赤は段 5 の直後からあったが、段 6 の fix 後に初めて検出された。
- 根本原因: 焦点走の consumer を「変更した production module 名で `orchestrator/tests/` を grep」で
  引いた。この inventory test は module 名を書かず、**production file を内容で走査して**
  対象集合を作るため、名前検索では hit しない。
- 恒久対応: `docs/dev-wave/operations.md` の焦点走 consumer 拡張へ、
  「新規 production file を足す走では、production を内容で走査する inventory test も焦点に含める」を統合する。
- 再発検知: 新規 production file を足したら、`orchestrator/tests/` のうち
  production ディレクトリを走査する test (glob / `rglob` / ディレクトリ列挙を行うもの) を
  機械的に列挙して焦点へ入れる。
