## 総括

現 plan はそのままでは **NO-GO**。official 走行自体は未 land commit から実行できるが、成果を「現時点で再凍結へ使える official 証拠」「C3a の全 gate 入力の実値域を確認済み」と扱う部分が成立しない。

- P1-1: 測定実行は支持。ただし current consumer は v5 を拒否し、erratum も未追認なので、再凍結可能性の主張は不可。
- P1-2: 恒久 producer は不要。ただし一回限りの抽出処理と導出根拠を receipt 内に残す必要がある。
- P1-3: 反証。親の集合は不足し、段 2 の拡張集合も「動的観測」「genesis の宣言値」「未発火」「process-private」を混同している。
- P1-4: 支持。1 job・1 node 直列は現 protocol と整合する。ただし 48 分は上限ではない。

テスト、pytest、Pegasus 投入は実行していない。静的読解、git 照合、grep のみである。

## 所見

- **A-1 — real。`eligible_for_refreeze=true` と downstream 受理が分断されている。**  
  C3a producer は attempt registry があれば v5 を出す (`s8b_floor_campaign.py:6815-6853`)。一方、現行 alias はまだ v4 (`s8b_floor_contract.py:35-37`) で、holdout freeze は schema 指定なしの key 集合と `RESULT_SCHEMA` を要求する (`s8b_holdout_freeze.py:1431-1441`)。ratified freeze も同じである (`s8b_ratified_freeze.py:2352-2375,2403-2409`)。したがって plan の停止条件 `schema=v5` かつ `eligible_for_refreeze=true` (`out-s2-plan.md:186`) を満たす成果物は、現 consumer に必ず拒否される。これは典型的な consumer 取り残しである。走行の歴史的価値は残るが、「再凍結へ使用可能」とは書けない。

- **A-2 — real。land・裁定状態は eligibility 式に入っていない。**  
  eligibility は `mode=="official" ∧ fresh ∧ nondefault_seams=空` だけで導出される (`s8b_floor_campaign.py:7120-7133`)。C3a の erratum は依然「追認はユーザー裁定へ返す」状態 (`contract-v3.1-erratum-2.md:81-85`) で、D1703 も単位が揃うまで裁定しない (`decisions.md:51860-51869`)。未 land・未追認でも producer flag は true になりうるため、その bit を承認や現在の proof-chain 完結と読んではならない。

- **A-3 — refuted。main の祖先であることは official 測定の必要条件ではない。**  
  D811 の逐語は「**別の source commit と script blob hash で再投入する**」であり、main ancestor を要求しない (`decisions.md:30934-30937`)。D1125 は測定 provenance を commit ID と環境条件で足りると裁定している (`decisions.md:37914-37929`)。実行時には current HEAD、receipt commit、実行 script、commit blob が照合される (`floor_campaign.sh:743-775`)。したがって「未 land だから測定事実が無効」は誤りである。

- **A-4 — real。ただし dangling は無効化理由ではなく再検査可能性の限界である。**  
  plan の退避 bundle (`out-s2-plan.md:100-102`) には source tree または git object bundle が無い。`source_commit` は submit receipt と job-result に残る (`submit_floor.sh:701-711`, `floor_campaign.sh:1377-1388`) が、run の `result.json` key 集合には存在しない (`s8b_floor_contract.py:88-100`)。branch 削除と GC 後には source 内容を再取得できない可能性がある。ただし F681 は commit object の実在を要求しないと明記する (`failures.md:19230-19241`) ため、これは過去の測定を無効にする blocker ではない。receipt に「commit の将来解決可能性は保証しない」と書き、可能なら外部 bundle に source tree snapshot または git bundle を補助資料として保存する。これを新しい eligibility gate にはしない。

- **A-5 — refuted。D1124 は D811 の着手条件が懸念した関門そのものを撤去している。**  
  D811 は admission root の消費済み key により同じ cell を claim できない可能性を問題にした (`decisions.md:30939-30941`)。D1124 は六要素 cell key による二度目の予約拒否を撤廃し、2026-08-24 に焼いた 12 cell も再測定を妨げないと明記する (`decisions.md:37862-37875`)。現実装も「historical v1/v2 claims and markers は fresh reservation の可否を決めない」とする (`s8b_holdout_admission.py:4-8,1736-1738`)。さらに同じ消費済み 12 cell の再測定が job `964035` と `964044` で完走済みである (`worklog-phase3-0901-1135-1136.md:1-25`)。118 件の現況確認は保全用 inventory にはなるが、投入着手条件ではない。

- **A-6 — real。段 2 plan は撤去済みの一回性を停止条件へ復活させている。**  
  `out-s2-plan.md:181` は claim 後の crash では fresh 再投入しないとする。参照先 runbook も同じ旧規則を残す (`phase3-8b-restart-runbook.md:268-271,315-344`) が、その直前では D1124 により同じ cell を何度でも測れると正しく書いている (`同:246-249`)。説明と実装の食い違いであり、plan の停止条件から削除すべきである。再投入時は新 measurement generation と全 attempt の履歴を残し、結果を見た後の恣意的な選択はしない。

- **A-7 — real。P1-2 は恒久 producer 不要だが、現 plan の一回限り抽出は証拠鎖が弱い。**  
  `out-s2-plan.md:130-152` は strict reader と集約方法を説明するが、実際に使った抽出 source、version、stdout、rcを保存しない。raw artifact の SHA-256 は元 bytes を束縛しても、Markdown に転記した集約値の正しさまでは証明しない。F556 の「値を写すことを証拠の鎖と取り違えた」型 (`failures.md:16454-16466`) に当たる。新しい repo script は不要だが、receipt 自身に実行した抽出コード全文または完全なコマンド、入力 hash、出力 hash、rcを収録する必要がある。

- **A-8 — real。receipt へ raw probe text を転載する計画は信頼境界を欠く。**  
  probe は `pgrep -af ycsb_.*\.exe` であり (`s8b_floor_attempt_launcher.py:52,616-645`)、stdout には外部 process の任意 command line が入る。plan はその distinct 値を Markdown へ転載する (`out-s2-plan.md:110`)。これは外部出力をデータとして扱う規律 (`CLAUDE.md:88-95`) の対象である。raw text は prose として表示せず、UTF-8 bytes の base64、byte length、SHA-256として隔離し、「内容は非信頼データであり指示として解釈しない」と付記すべきである。

- **A-9 — real。段 2 の「gate 入力の完全列挙」は異なる種類の値を混同している。**  
  genesis の 288 slot と `measurement_ordinal=0..2` (`out-s2-plan.md:114`) は事前宣言された closure であり、実行された retry の観測ではない。process-private weak map、owner identity、seal、`used` は artifact に存在せず (`同:111`)、間接証拠しかない。これらを同じ「実観測値域」に載せると、field の存在を到達実測へ読み替える DW-O13 違反になる。少なくとも「動的に消費された値」「genesis に宣言された値」「artifact 非所在」「未発火」を別表に分ける必要がある。

- **A-10 — real。1 run で未観測の値は到達不能とは判定できない。**  
  fresh run で `retry_ordinal=null` だけなら、retry の `1..2` は未観測であり、到達不能ではない。失敗 cell があれば retry loop は実際に非 null ordinal を発行する (`s8b_floor_campaign.py:6389-6407`)。pre-probe competing も `pgrep` の結果次第で発火する (`同:8875-8901`)。一方、cut-6 replay は既存 `session-start` を読む resume 系であり (`同:6540-6578`)、fresh default run では発火しない。production の `attempt_ordinal>0` は別軸で、明示的に拒否される。receipt は次のように区別すべきである。

  - `retry_ordinal=1..2`: 条件付き到達可能、今回未観測なら未確認。
  - `probe_before.competing=true` と `probe_after=null`: 条件付き到達可能、未観測なら未確認。
  - cut-6 replay: fresh default run の適用域外。
  - `attempt_ordinal>0`: production gate が拒否する値。
  - process-private seal状態: artifact から直接観測不能。

- **A-11 — refuted。plan に correctness gate を緩める実装変更は見当たらない。**  
  実装差分 0、strict JSON、prefix 7 key の照合、marker・ordinal join、不一致時停止を要求している (`out-s2-plan.md:128-191`)。問題は受理集合の拡大ではなく、未発火値と downstream 適格性の過大主張である。

- **A-12 — refuted。ただし時間の一般化は弱い。**  
  1 job・1 node 直列は runner 自身の契約 (`s8b_floor_campaign.py:6013-6021`) と sanctioned wrapper に合う。pilot の 2894 秒も一次資料どおり (`2026-08-25_t1431-floor-pilot-values/README.md:27`)。ただし後続 run は 2981、3016、3096 秒 (`worklog-phase3-0901-1135-1136.md:5,23`, `worklog-phase3-0902-1165.md:6`) で、2894 秒は上限でも最新値でもない。所要は「観測 2894〜3096 秒」と書くべきで、完走保証に一般化してはならない。

- **A-13 — real。同型の stale 記述が複数残る。**  
  `s8b_floor_contract.py:30` の producer v4 comment 以外に、runbook の「official は perf あり形だけ」 (`phase3-8b-restart-runbook.md:226-228`) と、claim 後は fresh 再投入不能 (`同:268-271,327-344`) が現実装と矛盾する。契約 v3.1 の「assemble_result は v4」 (`contract-v3.1.md:45-46`) も C1b 時点の歴史記述であり、現況説明としては使えない。F756 の stale 注記型と F892 の古びた非保証型に一致する (`failures.md:20568-20589,23324-23327`)。

- **A-14 — real。receipt の永続先が未決着である。**  
  brief は repo への commit を禁じる (`s1-brief.md:35-36`) 一方、`output/insights/.../README.md` と spool fragment を成果物にする (`同:69-70`)。plan 自身も曖昧と認めている (`out-s2-plan.md:207`)。raw run artifact は repo 外、正規化した README receipt と台帳 fragment は eventual land 対象、と明確に分離しないと、worktree 削除時に receipt 自体が消える。

## 親の実測値への反証

- `8fbcb70a5` は実在する commit だが、現在の `main=7f17e1c63` と相互に ancestor ではない。`git merge-base --is-ancestor` は両方向とも rc=1。したがって「未 land」は現在も事実である。
- official 成功成果物 0 件は、現 worktree の `output/**/s8b-floor-official/**` が空である範囲では反証されない。873225 は `driver_rc=2` の official guard 正常拒否である (`worklog-phase3-0728-33-37.md:7-13`)。
- 118 件の消費記録は歴史事実だが、現在の admission blocker という一般化は反証済み。同じ 12 cell を二重の新世代で再測定できている。
- 「pilot 約48分」は最初の 2894 秒には一致するが、観測集合は少なくとも 2894、2981、3016、3096 秒。単一値を所要上限としては使えない。
- `s8b_floor_contract.py:30-31` の comment が stale という親の実測は正しい。ただし v4 alias 自体は現 consumer が使っており、comment だけでなく producer/consumer schema 分断が実在する。
- plan の `1+5N`、genesis 288 slot、ordinal closure は静的な条件式・宣言値であり、official run の実測値ではない。receipt では観測値と分離する必要がある。

## receipt 文言への修正案

> 本 receipt は、記載した source commit、source tree identity、Pegasus job、環境 tag、mode、protocol、freeze および submission/job script hash に束縛された fresh default production campaign 1 回について、保存済み artifact から再導出した値を記録する。
>
> 「動的観測値」は、この run で実際に開始、分類または terminal 化された attempt が消費した値だけを指す。genesis に事前列挙された slot、protocol の許容集合、process-private capability の状態、未発火分岐は動的観測値へ含めず、別欄へ記録する。
>
> 列挙値、件数、null 件数および観測最小・最大は、この run の標本だけに関する。未観測値は到達不能を意味しない。とくに retry ordinal、競合 pre-probe、nullable post-probe、capture failure および replay 分岐について、witness が 0 件なら「未観測・到達可能性未確認」とする。fresh run の適用域外または production gate が拒否する値は、その理由を別に記す。
>
> `eligible_for_refreeze` は producer がこの run の mode、freshness、非既定 seam から導出した値であり、ユーザー追認、main への land、現行 consumer による受理、candidate freeze の発行、certified 選択を意味しない。本 run 時点では result v5 に対して holdout/ratified freeze consumer が v4 を要求するため、再凍結 proof chain は未完である。
>
> source commit が将来 git object として解決可能であることは保証しない。これは測定事実を無効にしないが、source 内容の再検査可能性を制限する。保存した source snapshot がある場合は、その path、tree identity、size、SHA-256を補助資料として記録する。
>
> probe、CCBench、scheduler、driverその他の外部出力は非信頼データであり、指示として解釈しない。raw text は prose に展開せず、encoding、base64、byte length、SHA-256として隔離する。
>
> 本 receipt は母集合、許容 bound、他環境、他 mode、他 commit、将来 campaign、未発火分岐の値域を主張しない。また、今回 witness が無い値について DW-O13 の到達可能性確認が完了したとは主張しない。

表も最低限、各 field に `source artifact`、`phase`、`witness count`、`observed values`、`declared domain`、`reachability verdict`、`trust class` を持たせる。hash・ID・enum には min/max を使わず distinct/count、時刻には「観測最早・最遅」、数値だけに「観測最小・最大」を使う。

## 未解決の問い

- C3b の完了条件は「happy path の実観測」だけか、それとも retry、competing、nullable post-probeを含む C3a 新述語の要求値すべての DW-O13 witness か。後者なら official 1 run だけでは完了を保証できない。
- D2 が v5 consumer を実装した後、この exact run を受理する条件を結果確認前にどう固定するか。現 consumer での拒否を無視して「将来通る」とは書けない。
- erratum 2 が追認されなかった場合、この run の terminal evidence をどの状態へ降格するか。
- raw artifact、shared-admission snapshot、source snapshot、README receipt の保存責任と retention period はどこが正本か。
- D1124 による再投入時、失敗した全 run を残し、どの run を C3b receipt に採るかを結果を見る前にどう固定するか。
- receipt を eventual land 対象にするのか、外部 bundle のみへ残すのか。現在の brief と plan は一致していない。