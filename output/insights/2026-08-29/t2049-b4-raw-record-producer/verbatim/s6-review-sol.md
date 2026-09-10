## 裁定 §2 の履行状況

| 項目 | 判定 | 根拠 |
|---|---|---|
| §2.1 事前確定 path | 効いている | `record_root` / `block_id` は request に入らず、publication を再読込したうえで `planned_result_artifacts` の 1 path だけへ書く。assembly も別 path を書かない。 |
| §2.2 排他 create | 効いている | producer 固有 slot は無く、hard-link による排他 publish、同一 bytes の冪等成功、異なる bytes の拒否になっている。ただし assembly が publish 経路を経ていない file を受理する欠陥は後記する。 |
| §2.3 WAL `ts` による割当 | 効いていない | publish 単体では WAL suffix 先頭 `ts` を使うが、最終 assembly は保存 file の `assignment_observation` を無検証で転記する。 |
| §2.4 終端性 | 効いていない | 3 分岐は存在するが、flock が B-4 iteration 全体を覆わず実行中を欠測にでき、terminal WAL と checkpoint の間でも早期封印できる。 |
| §2.5 block 単位 pair | 効いている | 最終 assembly で on/off の宣言 `pair_id` 一致を要求する。`admitted_view` 不一致は `protocol_ok=false`、off digest の赤節は `contaminated=true` へ分離される。 |
| §2.6 publication 内一意性 | 効いている | publish 前の既存 artifact 検査と、assembly 全件の set 検査があり、並行 publish の競合も最終 assembly で拒否される。 |
| §2.7 field の実体化 | 効いている | `terminal_reason`、`model_snapshot` を使い、根拠のない `crash` / `stopped-before` や `anomaly_class` は出していない。 |
| §2.8 数値 | 効いている | WAL token を再読して lexeme を保存し、非有限十進の reference は専用理由で拒否する。 |
| §2.85 D162 | 効いていない | publish request の判断 field は閉じているが、assembly の保存 file 経由で全判断 field を注入できる。また transitive evidence の symlink 拒否が完結していない。 |
| §2.9 変更面 | 効いている | 検査対象 production/test の 2 file 内に収まっている。 |
| §2.10 名乗り | 効いている | `authoritative`、file-drawer closed、verdict-ready に相当する名乗りは production code にない。 |

D824 について、screening loader は `make_critic_digest` の B-4 経路へ渡されておらず、screening 詳細の treatment 混入はない。広い correctness feedback 全体を名乗る記述もない。ただし、空の赤節でも treatment 発火とする別欠陥がある。

D1240 の同一 snapshot 要件は効いている。campaign lock は 1 回だけ snapshot され、分類と COMMIT receipt 検証の双方が同じ `lock_snapshot.data` を使う。不在 digest は producer 内では使われず、lock 不在を先に拒否する。

判断 field の直接入力は閉じているが、自由度は完全には閉じていない。

- `treatment_fired` / `contaminated`: receipt digest から計算する。ただし空の赤節判定と assembly 注入が残る。
- `protocol_ok`: publish 経路では列挙した証拠比較から計算する。ただし assembly は再計算しない。
- `execution_disposition`: WAL と flock から計算するが、flock の保持範囲と呼出時点で結果を動かせる。
- honest な off controller は赤節を生成しないため、`contaminated=false` は通常 writer の候補集合では恒真に近く、legacy critic や `policy_hint` 経路の不在を検査する保証ではない。

## 重大な所見

1. **所見:** 最終 assembly は issuer-planned file 内の caller 作成 `raw` を証拠なしで受理するため、閉じた publish request を迂回して全判断 field を注入できる。  
   **場所:** [orchestrator/campaign/p3_b4_raw_record_producer.py:1304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:1304)、[同:1355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:1355)  
   **なぜ欠陥か:** issuer 発行後、caller が planned path へ canonical file を直接作り、identity、同じ `pair_id`、期待 binding、任意の `raw` だけを入れればよく、`evidence`、receipt、snapshot hash、non-guarantees 自体が欠けていても assembly は raw の key setしか検査せず転記する。  
   **成果物への影響:** `treatment_fired=true`、`contaminated=false`、`protocol_ok=true`、`executed` と任意 throughput・assignment を選び、受理集合と B-4 verdict を直接変更できる。  
   **判定:** real。

2. **所見:** liveness probe の flock は B-4 iteration 全体では保持されないため、実行中でも `terminal-record-absent` を排他 publish できる。  
   **場所:** [orchestrator/campaign/p3_b4_raw_record_producer.py:930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:930)、[orchestrator/campaign/p3_s4_loop.py:1180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1180)、[docs/orchestrator-design.md:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/docs/orchestrator-design.md:111)  
   **なぜ欠陥か:** lock は内側の `run_campaign()` だけを覆い、authorization、preflight、quarantine、checkpoint は外側なので、その実行中に終端 record がまだ無ければ producer は lock を取得し、終了済みと誤分類して immutable な欠測 artifact を作る。M14 は test 自身が手動で lock を保持しており production 配線を証明していない。  
   **成果物への影響:** 実行中の arm が `missing` へ固定され、block score、欠測数、最終 verdict が変わる。  
   **判定:** real。

3. **所見:** terminal WAL の durable 化から checkpoint 保存までの正規 window で producer を呼ぶと、完了済み試行を永続的な protocol failure に封印する。  
   **場所:** [orchestrator/campaign/p3_s4_loop.py:1190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1190)、[同:1569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1569)、[orchestrator/campaign/p3_b4_raw_record_producer.py:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:939)  
   **なぜ欠陥か:** `run_campaign()` が COMMIT/ABORT を書いて戻った後に whiteboard 射影と `save_loop_state()` が行われるが、producer は terminal record があれば lock を見ず、古い checkpoint から `checkpoint_ok=false`、`whiteboard_result=null` の bytes を publishし、正常 checkpoint 後の再実行は path conflict になる。  
   **成果物への影響:** 正常 COMMIT が adapter の status errorまたは protocol violation へ変わり、成立可能な publication が無効になる。  
   **判定:** real。

4. **所見:** terminal WAL が存在しても launch sidecar、consumption、loop state の欠落や schema 破損で planned artifact を一切残さず、protocol violation の全件報告から試行を落とす。  
   **場所:** [orchestrator/campaign/p3_b4_raw_record_producer.py:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:794)、[同:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:883)、[同:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:920)  
   **なぜ欠陥か:** valid terminal WAL と receipt がある campaign で例えば launch sidecar を欠落させると、`protocol_ok=false` を記録する前に `EVIDENCE_UNAVAILABLE` が返り、planned path は空のままなので assembly は `INCOMPLETE_SET` で止まる。  
   **成果物への影響:** protocol violation campaign が個別報告から消え、B-4 の全件報告を作れない。  
   **判定:** real。

5. **所見:** `treatment_fired` は赤詳細の実在ではなく常設の赤節 header の有無だけで真になる。  
   **場所:** [orchestrator/campaign/p3_b4_raw_record_producer.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:909)、[orchestrator/critic/digest.py:1313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/critic/digest.py:1313)  
   **なぜ欠陥か:** structured rejection が 0 件でも on digest は `# rejections` と「rejection なし」を含み、off digest はその prefixなので、lines 913-918 の条件は両 arm を `treatment_fired=true` にする。registry ラベルと実 campaign が未束縛なため、この入力は候補集合から排除されない。  
   **成果物への影響:** treatment 未発火 block が n 件に数えられ、判定不能になるべき publication が検定・verdict 分岐へ進む。  
   **判定:** real。

6. **所見:** receipt bundle 外の executable と role file は symlink-following readerで検証され、§2.85 の全証拠 symlink 拒否を満たさない。  
   **場所:** [orchestrator/campaign/p3_b4_raw_record_producer.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:636)、[orchestrator/campaign/p3_b4_closed_critic.py:1610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:1610)  
   **なぜ欠陥か:** terminal bundle は regular snapshot へコピーされる一方、receipt 内 `evidence_executable_path` と固定 `ROLE_FILE` は `Path.read_bytes()` で別途開かれ、絶対 symlink を拒否する検査が無いので、symlink target の bytes が receipt hash と一致すれば通る。  
   **成果物への影響:** 再現不能な executable provenance を certified receipt として受理し、`protocol_ok=true` の source artifactへ流せる。  
   **判定:** real。

7. **所見:** genuine publisher の非保証 tuple は全項を置いているが、flock と closure の既知の帰結を裁定より弱く記述し、さらに assembly は tuple 自体の存在を要求しない。  
   **場所:** [orchestrator/campaign/p3_b4_raw_record_producer.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:57)、[同:1355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:1355)  
   **なぜ欠陥か:** 中核4項の precursor、flock、treatment causality、closure 外は列挙され、model hash と anomaly class もあるが、flock は「非協力 process と後日の再開を排除しない」、closure は「source hash が producer 意味論を識別しない」という必要な帰結を落としており、直接作成した planned fileなら全非保証を省略しても assembly が通る。  
   **成果物への影響:** B-4 source report が終端性と producer 認証の限界を実態より強く見せる。  
   **判定:** real。

## nit

1. **所見:** M03 は fixture の実行順と producer の処理順がともに on/off なので、publish 順を割当とする変異でも同じ期待値になり恒真である。  
   **場所:** [orchestrator/tests/test_p3_b4_raw_record_producer.py:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/tests/test_p3_b4_raw_record_producer.py:140)、[同:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/tests/test_p3_b4_raw_record_producer.py:377)  
   **なぜ欠陥か:** mutation が WAL `ts` 比較を外して固定処理順 `["on","off"]` を返しても、test の fixture と assertion は変わらない。  
   **成果物への影響:** 直接の artifact 影響はなく、M03 の kill 証拠だけが成立しない。  
   **判定:** real。

2. **所見:** production の 2 個の `assert` は直前条件から含意され、保証 gateとしては恒真である。  
   **場所:** [orchestrator/campaign/p3_b4_raw_record_producer.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:521)、[同:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:967)  
   **なぜ欠陥か:** 前者は exact type 不一致を既に拒否し、後者は `terminal_index is not None` から `terminal_raw` 非 None が定義上導かれる。  
   **成果物への影響:** なし。型 narrowing 以上の正しさ保証にはならない。  
   **判定:** real。

3. **所見:** D1240 の固定 absence digest は producer では使われず、physical lock 不在は receipt 検証前に拒否される。  
   **場所:** [orchestrator/campaign/p3_b4_raw_record_producer.py:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:768)、[同:981](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_raw_record_producer.py:981)  
   **なぜ欠陥か:** lockless + explicit absence receipt は `_snapshot_regular` で終了し、固定 digest へ到達しない。ただし producer は exact B-4 marker を要求し、D1240 の lockless 受理集合は COMMIT sink の non-B4 分類を含むため、この producerにも同じ受理集合を要求するかは射影資料だけでは確定しない。  
   **成果物への影響:** 要求されるなら lockless receipt の過剰拒否、要求されないなら影響なし。  
   **判定:** 要確認。

## 総括

path 固定、排他 publish、最終 `pair_id`、publication 内三つ組一意性、数値 token、名称制限は実効である。一方、最終 assembly が証拠なしの caller 作成 raw を受理するため、判断 field の閉鎖は最終成果物まで届いていない。さらに B-4 iteration と flock の範囲不一致、terminal WAL と checkpoint の正規 window、補助証拠欠落時の無記録化により、§2.4 の三分岐は実走境界で成立しない。重大所見は 7 件すべて real、D1240 absence の適用範囲のみ要確認である。