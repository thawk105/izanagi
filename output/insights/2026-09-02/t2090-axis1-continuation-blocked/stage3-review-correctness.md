## 重大な所見

- **`reset_seconds` による失効は、契約が固定していない時刻意味論を導入する。real。**  
  file:line: `contract-excerpts.md:20-31`、`plan.md:7-23,103-104`、`runner.py:241-244,695-699,1645-1749`。契約は reset を観測値としてだけ記録し、窓長・request 数による運転を禁じている。`observed_at + reset_seconds` は、reset を「観測から境界までの有効期間」と解釈するため、名称を窓長と呼ばなくても新しい時間意味論である。特にプランは 0 を非負整数として受理するので、`reset_seconds=0` の低残量観測が即失効し、本来 `paused_quota` になる入力で HTTP が通る。`True` を整数と誤認する実装も F574 型 (`docs/failures.md:16079`) である。未来の観測時刻・時計の後退・欠測・負値はプランどおりなら停止側だが、0・小さすぎる正値・型混同が未閉鎖である。  
  なぜ受理集合が変わるか: `remaining=10, cost=10, reset=0` が変更前の 0 request から変更後の 1 request 以上へ移る。  
  成果物への影響: `request_count`、WAL、raw、page evidence、ledger、runtime quota、`manifest.json`、`MANIFEST.sha256` が変わり、新 checkpoint が作られる場合もある。

- **失効判断と HTTP 発行が原子的でなく、「1 request だけ」の保証は成立しない。real。**  
  file:line: `plan.md:23-29`、`runner.py:608-648,695-709,1684-1749,1765-1778,1908-1909`。runtime lock は quota を読む間だけ保持され、HTTP 前に解放される。複数 leaf が同時に走ると、全 process が同じ古い観測を `None` として読み、その後 host limiter を順番に通って全員発行できる。さらに 503・通信失敗などで新しい quota evidence が得られなければ、同一 process の retry も毎回同じ観測を失効扱いする。  
  なぜ受理集合が変わるか: 失効観測につき「1 本」ではなく、同時 leaf 数および retry 数だけ HTTP 発行が受理され、30-credit 予約を割りうる。  
  成果物への影響: `request_count` と WAL attempt 数が増え、複数 raw/page evidence が生成され、runtime の `remaining`、checkpoint の quota、manifest digest が想定と異なる。quota の失効判定・予約・発行権を一つの bundle-wide lease として原子的に予約する必要がある。

- **案 A の validator 置換は弱体化であり、3 束縛だけでは登録 provenance を保存しない。real。**  
  file:line: `plan.md:41-51,97,105-107`、`validator.py:1088-1166,1199-1263`、`runner.py:1086-1130`。次の反例が提案後に通る。

  1. 旧 bundle の checkpoint/page/ledger を一切増やさない。
  2. `manifest.registration_commit` だけを `C_reg2` にし、manifest と自己 digest を再生成する。
  3. checkpoint↔ledger と page↔ledger は全て旧 commit のまま一致させる。

  3 束縛と catalog request 再構築はすべて成立するが、新 commit で生成された artifact はゼロである。逆に、旧 page・ledger・checkpoint の commit field を全部まとめて新 commit に張り替えても、相互一致と現 catalog request は保てる。validator は artifact が名指す各 commit の Git tree、凍結 path、catalog blobを検証しない。

  3 束縛自体は局所的には恒真ではない。片側だけ変えれば checkpoint↔ledger、page↔ledger は発火し、checkpoint request を catalog と整合的に改竄すれば再構築検査も発火しうる。しかし両側が同じ producer 引数から作られるため、両方を同時に誤る変異には効かない。これは F699/F788 型 (`docs/failures.md:18814,20439`) であり、外部の登録事実への束縛ではなく内部自己整合性である。  
  なぜ受理集合が変わるか: 現行 `validator.py:1105` が拒否する「manifest は新 commit、全 artifact は旧 commit」が受理側へ移る。  
  成果物への影響: 新 HTTP・新 page がゼロでも、`manifest.registration_commit` と `MANIFEST.sha256` だけが新値になり、検査理由が `checkpoint_registration_mismatch` から baseline の `interpreted_query_mismatch` まで進む。

- **移行鎖と WAL が artifact 単位の束縛から漏れている。real。**  
  file:line: `runner.py:1192-1199,1448,1607,1740-1745`、`validator.py:1041-1046,1088-1166`。`previous_checkpoint` は新 checkpoint に path/bytes/digest として書かれるが、bundle validator は参照先を読まず、digest を照合しない。したがって旧→新の移行鎖を保証しない。また WAL は leaf 単位の同じ JSONL へ追記され、append 呼び出しには `registration_commit` が無い。validator も WAL の状態遷移を構文検査するだけで page/checkpoint/commit と結ばない。旧 commit と新 commit の attempt が一つの file 内に混在するため、「artifact 単位」に分割できない。  
  なぜ受理集合が変わるか: 任意の旧 checkpoint digest を申告した新 checkpoint、および出所 commit を特定できない混在 WAL が、3 束縛を満たしたまま通る。  
  成果物への影響: `previous_checkpoint.sha256` を変えても判定が変わらず、WAL bytes とその manifest SHA だけが増える。旧 manifest の全 entry が新 manifest の同一 digest subset として残ったことを検査する仕組みも無いため、旧証拠の無改変を証明できない。

## 軽微な所見

- **テスト計画が新しい受理境界を十分に叩いていない。**  
  file:line: `plan.md:73-85`。不足している負例は、reset の 0・`true`・float・異常な小正値、未来時刻、時計後退、同時 leaf、quota header 無し retry、checkpoint↔ledger の片側 commit 改竄、page↔ledger の片側改竄、`previous_checkpoint` digest 改竄、旧 manifest entry の subset 不一致である。F734 型 (`docs/failures.md:19459`) の「正例は緑だが実際の危険経路を通らない」状態になる。  
  なぜ受理集合が変わるか: 実装がこれらを受理しても、提案された 3 test は緑のままになりうる。  
  成果物への影響: transport call 数、reason code、各 artifact の commit/digest が誤っても検出されない。

- **`exact_identity_map=true` は mixed-commit 保証として使えない。**  
  file:line: `plan.md:70`、`validator.py:933-955,1406-1419,1665-1670`、`bundle-baseline-mainchecker.json:1`。validator は evidence が無い leaf にも結果要素を作るため、baseline ですら 77 leaf が `not_run` なのに `exact_identity_map=true` である。これは catalog の ID 集合を完全に列挙したという値で、artifact provenance や evidence 完備性ではない。  
  なぜ受理集合が変わるか: 変わらない。だからこそ案 A の弱体化を検知する保証にはならない。  
  成果物への影響: 不正な mixed-commit bundle でも同値は `true` のままになりうる。

## 親 brief への所見

- **「blocker は quota の自己施錠だけ」は、次の 1 HTTP に限れば正しいが、Q1 継続・次 checkpoint までという成果には誤り。**  
  file:line: `handoff.md:50-61,138-144`、`runner.py:2040-2167`。Q1 の次頁を新しい窓で取得すると、新 quota が十分なので `runner.py:2102` の quota 優先停止を通過し、その直後 `runner.py:2160` で条件 1 の `interpreted_query_mismatch` により `blocked_on_ruling` へ戻る。ここでは後継 checkpoint を作らない。T-2091 を緩めなくても、Q1 は 1 頁だけ進んで再び停止する。  
  なぜ受理集合が変わるか: 受理集合は変わらないが、親が見積もった実行経路が存在しない。条件 1 を通す変更を加えれば初めて受理集合が広がり、それは T-2091 の先取りになる。  
  成果物への影響: `request_count=1`、新 page/ledger は増えるが、結果は `blocked_on_ruling`、`checkpoint_path=null`、`axis_complete=false` のまま。baseline にはさらに `controls_valid=false`、`family_ledger_complete=false`、未実装 schema 5 層もあるため、軸完走の blocker は一つではない。

- **「登録 commit の木を再構成すればコード変更なしに実行も検査もできる」は過度な一般化。**  
  file:line: `handoff.md:28-38,119-136`。再構成で解けたのは registration preflight と絶対 path 束縛である。旧 runner は quota で 0 request、旧 validator は部分 bundle を途中打切りするため、実際には「旧 commit の runner + main の validator + 復元 bundle」の三者が必要だった。  
  なぜ受理集合が変わるか: 受理集合ではなく、利用可能な実行・検査経路の数え違いである。  
  成果物への影響: 旧 checker では `status=null`、main checker では `bundle_validation_complete=true`、runner は `request_count=0` となり、同じ「再構成済み」でも値が一致しない。

- **「1 窓 ≒ 96 request」は契約違反の仮定を含み、算術も 1 request 少ない。**  
  file:line: `handoff.md:99,150-158`、`contract-excerpts.md:26-31`、`runner.py:241-244`。1000 から毎回 10 減る仮定なら、96 request 後の remaining は 40 で、`40 - 30 >= 10` は真なので 97 本目を発行でき、残り 30 で止まる。上限は 97 である。ただし契約は cursor、429/503、複雑 query の cost が同じと確認しておらず、request 数による運転自体を禁じているため、97 も運用値にはできない。  
  なぜ受理集合が変わるか: この見積りを停止条件に使えば、96 本で早く止めるか、未知 cost で予約を割る入力を誤受理する。  
  成果物への影響: request 数、最終 remaining、checkpoint 番号、取得 page/occurrence 数が変わる。

- **より小さい代替について、親の読みは「同じ root」を固定した場合だけ正しい。**  
  file:line: `tools/run_axis1_search.py:115-125,157-176`、`validator.py:1088-1117`。旧 root に `--query-id` で新 commit の artifact を追記すれば、manifest が新 commit になり旧 checkpoint が残るので現行 `validator.py:1105` が拒否する。ここまでは親の読みどおりである。一方、77 leaf を新 root で開始し、旧 root と Q1 checkpoint を封印したまま残せば、各 root 内は単一 commit なので validator 変更は不要である。部分 bundle は現行 checkerで最後まで診断できる。  
  なぜ受理集合が変わるか: 新 root 案は validator の受理集合を一切広げない。  
  成果物への影響: bundle が二つに分かれ、Q1 は旧 root の `incomplete_with_evidence` のまま、77 leaf の進捗は新 root の別 manifest に載る。合成 checker が無いので「単一 bundle の完走」とは主張できない。また fresh root が quota 履歴を消すと予約回避になるため、旧 quota state の引継ぎまたは別の原子的な host/account quota state が必要である。

## 検査したが問題を見つけられなかった面

- 完走条件 1〜6 の計算自体に、案 A が直接加える緩和は見つからなかった。`validator.py:162-230,547-631` は条件別結果と `axis_complete` を再計算し、bundle の宣言値を信用しない。T-2091 を先取りして受理側へ動かす計画記述も無い。
- checkpoint の選択 request と catalog request の実行前比較は `runner.py:2291-2307` で実際に発火する。提案する bundle 側の完全再構築も同様の全 field 比較にすれば恒真ではない。
- 既存 runner には raw・page・ledger の内容を直接上書きする通常経路は見つからなかった。問題は旧 bytes の無改変を新 validator が証明しないこと、WAL・runtime・manifest が既存 file の追記／置換面であることに限られる。
- プランどおり厳密に実装される限り、未来の観測時刻、時計の後退、欠測、parse 不能、負の reset は失効せず停止側になる。

## 総括

案 A は現状のままでは NO-GO である。quota 失効は契約外の reset 時刻解釈と非原子的な発行を含み、validator の全 checkpoint 同一 commit 防壁を3つの内部自己整合性へ置き換える案は、manifest・移行鎖・WAL・旧 manifest subset を登録事実へ結べていない。

最小案は、T-2091 待ちの Q1 と旧 bundle を封印したまま、77 leaf を新 root・新 commit の単一 provenance で進め、現行 validator を変えない道である。ただし quota state を root 変更で消してはならない。同一 root で Q1 を移行するなら、原子的な quota lease、各 distinct commit の登録 tree 検証、`previous_checkpoint` 実 digest 鎖、WAL の commit 帰属、旧 manifest entries の不変 subset 検査が先に必要である。