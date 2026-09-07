---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2293-8c-wiring-r1r4
seq: 1
---

## 新規

### {{F:ordering-fix-orphaned-the-failure-terminal}}. 順序是正が「開始だけあって終端がない」台帳行を作った [手順漏れ]

- 事象: 受入要件 11 の順序是正で lifecycle start が observation 開始より前へ移った結果、
  observation 開始後に失敗した起点試行が terminal を書けなくなった。台帳には start だけが残り、
  その行は再試行を阻止しながら acceptance も成立させない。段 6 の敵対レビューが実測で見つけた。
- 根本原因: 順序を動かす前に、動かした後の失敗経路が既存の終端契約を通れるかを確かめなかった。
  `record_trial_terminal` は origin binding と projection の有無が食い違う terminal を拒否する。
  順序変更が新しい失敗状態 (projection をまだ作れていない起点試行) を生むことを見落とした。
- 恒久対応: {{D:origin-failure-terminal-without-projection}} で失敗 status に限って
  projection 無しの終端を許した。成功終端の受理集合は動かしていない。
- 再発検知: `orchestrator/tests/test_trial_registry.py` の負例 3 種
  (complete かつ projection 無しは拒否、失敗 status かつ failure_reason 空は拒否、
  失敗 status かつ failure_reason 非空は受理) と、
  `orchestrator/tests/test_p3_autonomous_workload_trial.py` の
  「terminal が在ること」まで見る test。

### {{F:loader-used-a-proxy-for-a-bit-it-could-not-see}}. 読み取り側が見えない情報の代理を使い、受理集合を広げた [恒真ゲート]

- 事象: lifecycle loader が `origin_terminal_projection` の有無を `origin_binding` の有無の
  代理にしていた。その結果、起点でない start 行に起点専用 key を足したもの、
  および起点の start 行から key を落としたものが、どちらも loader を素通りした。
  変更前の exact-key 拒否より受理集合が広い。段 6 の敵対レビュー 2 本が独立に指摘した。
- 根本原因: 親が段 4 で「読み取り側でも必要十分条件を強制せよ」と裁定したが、
  読み取り側が受け取るのは台帳の bytes だけで、行には要約値しか無く、
  そこから元の情報を復元できないことを確かめていなかった。**強制できない層に強制を命じると、
  実装は代理を作る。**
- 恒久対応: {{D:origin-lifecycle-loader-cannot-enforce-the-iff}} で、
  必要十分条件を情報が実在する層 (書き手・終端・受入) へ移し、
  読み取り側は自分が見えるものだけを検査する形に戻した。代理は除去した。
- 再発検知: `orchestrator/tests/test_trial_registry.py` の書き手側 iff 試験 3 種と
  acceptance 側 iff 試験。読み取り側単独では判定できない限界は decisions の
  「保証しないこと」に明記した。

### {{F:expected-red-nodes-were-not-in-the-collection}}. 期待した赤テストが収集集合に存在しなかった [恒真ゲート]

- 事象: 変異事前登録で、期待する赤テストを素の関数名で書いた。対象テストは 3 通りに
  parametrize されており、素の関数名の node は pytest の収集集合に存在しない。
  変異 harness が投入前に fail-closed で止めた。
- 根本原因: 関数名を grep しただけで node 名を書き、parametrize の有無を確かめなかった。
  止められなければ、存在しないテストを期待集合にしたまま「kill された」と記録するところだった。
- 恒久対応: 期待 node は関数定義の直前 8 行に parametrize が無いことを機械検査してから書く。
  本 wave では 10 変異すべてについてこの検査を行い、1 件で id 3 つへ展開した。
- 再発検知: `tools/mutation_harness.py` の「期待 node が pytest collection に実在しない」検査。
  この検査自体が今回発火した。
