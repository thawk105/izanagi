## 所見

- **must-fix** — `codex/s2-plan.md:32,69–72`、`orchestrator/campaign/layout.py:42–48,594–602`、`tools/pegasus/p3_s4_loop_pegasus.sh:332–339,365–406`。別 checkout と共有 base の配線は、この逐次 E2E には不要。配線を増やすと login と job の指定漏れで履歴が分かれ、coder 入力が自系列の結果を失う。**代案:** AI worktree 容器外の submit checkout １本から stock job、login の emit・preview・reject・proposal 作成、pair job を順に行う。既定の `output/` が一致し、tracked-clean 検査は未追跡の出力を無視する。evidence root は attempt ごと、scratch は PBS job ID ごとに新しくする。D2261:27 の別 tree 判断は別 job による変更との衝突であり、逐次使用へそのまま一般化できない。
- **must-fix** — `codex/s2-plan.md:65`、`orchestrator/tests/test_p3_s4_loop_job_contract.py:546–559`。既存の呼出し数検査は `p3_s4_loop_policy` を `p3_s4_loop` の接頭辞として数えるため、plan の「既存期待値を変えずに済む」は誤り。**代案:** module 名の直後まで区切る照合へ直し、既存２呼出しと方策１呼出しを別々に検査する。放置すると正しい job body が契約 test で拒否され、E2E が止まる。
- **must-fix** — `brief.md:17`、`orchestrator/campaign/p3_s4_loop_policy.py:345–359,383–411`、`orchestrator/campaign/p3_s4_loop.py:1371–1381`。login で `record-reject` すると、その時点の `start_wall` が保存される。「loop state を job 内で作る」だけでは queue 待ちを避けられない。**代案:** 拒否が出た系列では投入前に残り walltime を確認し、超過なら既存履歴を消さず停止として記録する。放置すると後続候補が `stopped-before` となり、同 job の比が得られない。
- **should-fix** — `codex/s2-plan.md:18–19,21,34,87–88`、`orchestrator/campaign/loop.py:755–780,877–885`。bootstrap と loop の分離は必要だが、新 `--purpose` と必須 R2 run ID は必要条件ではない。**代案:** `search_config` の用途 key を `bootstrap`／`loop`／`r2` にする。今回の R2 は保存候補を一度評価する入口とし、同一候補を繰り返し測る時にだけ識別子を追加する。bootstrap を同じ campaign に入れると pair の stock は terminal skip になり、新しい比を失う。
- **should-fix** — `codex/s2-plan.md:19,21,82`、`request.md:6–12`、`tools/pegasus/p3_s4_loop_pegasus.sh:773–789`。R2 を driver CLI だけに置いても、現 job body から計算ノードで呼べない。反面 `replay-pair` は今回の入口に不要。**代案:** job mode は `stock|pair|replay` の３値にし、replay は保存 `{coder,auditor}` を再照合して別 campaign で単独評価する。旧 loop の iteration・履歴を進めず、R2 の評価入口が成立する。
- **should-fix** — `codex/s2-plan.md:42–63`、`orchestrator/tests/test_p3_s4_loop_job_contract.py:546–559,1936–1962`。８ test・７変異には、既存の順序検査や argv 実行検査と重なる項目がある。**代案:** 実 source の STOCK 分類、同一 attempt の WAL からの baseline、候補→stock の同 session、login／compute の campaign 一致、実 shell の receipt・pin・保全 env を優先する。`driver_runs_once_after_prebuild` の独立 test と前処理順序変異、stock への coder authority 変異は、実際に成果物の判定差を示せない限り削る。R2 test は再照合と loop 非進行に絞る。
- **nit** — `codex/s2-plan.md:10`、`tools/pegasus/admission_registry.json:124–129`。登録済み body の説明文更新は受理集合も投入可否も変えない。**代案:** 新 entry を作らず README と runbook の使い方だけ更新する。説明文を残しても、成果物の比・履歴・trace は変わらない。

## plan / brief への代案

stock 単独は `bootstrap` campaign、候補と stock の pair は `loop` campaign に置き、同じ submit checkout の既定 base を使う。stock は原型 source、方策 flag なしの genome、別の build context で測る。`orchestrator/campaign/p3_s4_loop.py:2304–2315,2333–2336` と `orchestrator/campaign/loop.py:755–780` が分離の根拠である。pair の比は job rc や stock JSON のみから確定せず、双方の attempt を WAL で確認して記録する (`tools/pegasus/README.md:375–389`)。

計算経路では plan の site 契約・receipt・依存 prefix の受渡しを残す。さらに `find_compiler` が job body の限定 PATH で `g++` を見つけられること、`_assert_single_tenant` が実走前に発火することを焦点確認に入れる (`orchestrator/campaign/silo_policy_compile.py:37–42`、`tools/pegasus/p3_s4_loop_pegasus.sh:350–355,553–554`、`orchestrator/campaign/p3_s4_loop_policy.py:455–463`)。これは E2E の起動と計測値に直結する。brief の 217〜509 秒は評価固有費であり、前処理込みの job Elapse へ一般化しない (`brief.md:6,16`、`codex/s2-plan.md:73`)。台帳説明の更新や４値 mode はその確認に寄与しない。

## 総括

所見７件：must-fix ３、should-fix ３、nit １。親への裁定依頼は、**単一 submit checkout の逐次使用**と、**R2 を単独 replay までに絞ること**。bootstrap の campaign 分離は維持する。静的点検のみ行い、build・pytest・実測は行っていない。