## 所見

1. `_registered_clock_self_audit` の恒真性懸念

   - **対象 (file:line):** `orchestrator/tests/test_env_contract.py:839-898,913-940`
   - **何が問題か:** 懸念は現行 registry 世代については成立しない。helper は activation 済み世代だけでなく `ec.GENERATIONS` の全世代を返し、現在は linux g1・Pegasus g1/g2 の3件を検査する。失敗集合は宣言と等号比較され、件数も1に固定される。単一出所化後、宣言だけを空にする・g1を落とす・余分な ref を足す変更はすべて赤になる。
   - **裁定にどう効くか:** 登録世代を pin する production 経路について、未宣言の自己不整合を静かに通す余地はない。`resolve_by_contract_sha256` も登録済みかつ ever-active の世代に限定される (`env_contract.py:881-913`)。
   - **性質 (real / refuted):** **refuted**
   - **推奨する扱い:** plan どおり production 宣言を import し、`len == 1` と集合完全一致を残す。新しい検査は不要。

2. 直下候補による環境系列への再流入

   - **対象 (file:line):** `orchestrator/campaign/layer3_report.py:393-463,507-568`、`brief.md:65-71`、`s2-plan.md:35-37`
   - **何が問題か:** plan は除外対象を `_validated_pin_path` が返した一つの resolved path に限定する。このため g1 bytes の copy / hardlink が `output/env/pegasus/calibration/*.json` に別名で置かれると、直下由来の別 `Path` として候補へ残る。直下 symlink が登録 file 自身を指す場合は `resolve()` 後に同じ key となるので除外されるが、別の in-output copy を指す symlink は残る。自己監査も registry ref しか見ないため、この変更は緑のままである。
   - **裁定にどう効くか:** D1537 の「当該環境系列の within-run は一致なしのまま」は、現在の「Pegasus 直下 within-run 0件」という配置に依存し、恒常的には保証されない。linux-baremetal は pin 自身が直下に同居するため同じ resolved key、Pegasus は `registered/` 配下なので通常は pin-only という差がある (`env_contract.py:261-280,301-307`)。exploration root の suffix 解決自体は returned path を除外すれば抜けない。
   - **性質 (real / refuted):** **real**
   - **推奨する扱い:** D1537 の文言を守るなら、bad pair を pin する campaign では validation 後にその環境系列の within-run 候補全体を一致不能にする。少なくとも既存 Pegasus 負例へ直下 g1 copy / hardlink を置き、値が戻らないことを固定する。

3. validation 前の除外による fail-closed 弱化

   - **対象 (file:line):** `brief.md:65-67,83-84`、`orchestrator/campaign/layer3_report.py:393-463,515-527`、`s2-plan.md:35,58`
   - **何が問題か:** brief P2 の「`_validated_pin_path` を呼ばずに除外」は、logical `(path, sha256)` が宣言に一致したまま file bytes が改竄された場合、登録 path が directory・外向き symlink・非 file になった場合の例外を隠す。missing の既存 `pin-file-missing` 診断も飛ばす。
   - **裁定にどう効くか:** D1537 は候補不採用を決めただけで、SHA・directory・file 検査の免除を認めていない。brief 自身の不変条件とも矛盾する。既存 SHA end-to-end 回帰はこの短絡を検出する (`test_layer3_report.py:3555-3576`)。
   - **性質 (real / refuted):** **real**（brief P2 の欠陥。plan は是正済み）
   - **推奨する扱い:** plan の validation-first を必須とし、`Layer3ReportError` と `pin-file-missing` を従来どおり確定してから within-run 採用だけを止める。

4. 候補削減が新しい一致を生まない、という前提

   - **対象 (file:line):** `orchestrator/campaign/layer3_report.py:579-593`、`env_contract.py:253-280`、`s2-plan.md:61`
   - **何が問題か:** 候補削減は値域として単調でも、report の受理結果は単調ではない。一致候補が2件なら現行は `Layer3ReportError` になるため、Pegasus g1 pin と直下の別 g1 copy がともに一致する campaign は、変更前は重複エラー、path-only 除外後は直下1件の新規一致になる。
   - **裁定にどう効くか:** 変更前の一致から一致なしへ転じる正確な集合は、authority hash `e576e9cd…`、WAL env `pegasus`、protocol `silo`、records `1_000_000`、threads `48`、YCSB `0.9/50/0`、g1 pin 検証成功、かつ別の直下一致がない campaign である。逆方向の具体例は、同じ条件で `calibration/direct-copy.json` が1件一致する campaign。現 repo にその実 campaign はないが、production 受理関係には存在する。linux hash `1b2ee853…`、v1、env mismatch、never-active g2 は不変。
   - **性質 (real / refuted):** **real**
   - **推奨する扱い:** 「新規一致なし」を acceptance の主張にするなら、所見2の系列単位抑止を採る。path-only 案のままなら、その主張を撤回する。

5. 既存成果物の測定範囲と派生成果物

   - **対象 (file:line):** `brief.md:36-41`、`test_layer3_report.py:1673-1720`、7件の `output/campaigns/.../reports/layer3_report.json:1`、`output/reports/layer3_paper_evidence_dossier.md:201-222,451-460`
   - **何が問題か:** report の `env_tags` と `noise_floor.within_run.source` だけでは lock authority は判定できない。v2 authority は report へ投影しないことがテストで明示されている。その測り方から直接言えるのは「7件すべて linux WAL、5件 null、2件 linux source」までである。隣接 `campaign.lock:1` を別途読むと7件すべて実際に v1 なので、結論自体は正しい。さらに dossier が7件を要約し、T2136 mutation ledgers も Pegasus g1 値を保持しており、「他 path に写しがない」は成り立たない。
   - **裁定にどう効くか:** 既存7 report の noise-floor 値が変わらない主張は成立する。ただし「既存 artifact 全般に写しがない」「report 全 bytes が同じ」までは言えない。再生成すれば `meta.generator.sha256` は変わる (`layer3_report.py:845`)。
   - **性質 (real / refuted):** **real**（測定根拠の過大一般化。値不変の結論は refuted されない）
   - **推奨する扱い:** 7件については隣接 lock の v1 確認を根拠へ含め、主張を noise-floor 値に限定する。既存 report・dossier・mutation ledger は再発行しない。

6. 宣言を `calibration_verify.py` に置く場合の bytes 閉包

   - **対象 (file:line):** `s2-plan.md:19-27`、`silo_ladder_rung1.py:266-307,3737-3759`、`test_env_contract_activation.py:382-410`、`qualification/contract.py:39-77`、`qualification/t126_driver.py:356-381`、`test_t126_pegasus_tools.py:1473-1502`
   - **何が問題か:** `calibration_verify.py` は silo ladder の runtime-module binding と T126 の code identity に含まれるため、bytes 変更は将来の binding / qualification series ID を変える。ただし repo 内の既存 silo artifact は同 file を含まない旧17-member bindingで、現行 closure に対して既に不一致である。T126 の committed実 receipt は見つからず、activation record 自体のキーは env・generation・contract hashだけで code bytesを含まない (`env_contract_activation.py:17-28,113-163`)。したがって今回の定数追加が既存 golden を新たに赤にしたり、activation receipt の人間再発行を必須にしたりする証拠はない。
   - **裁定にどう効くか:** plan の置き場は機能上可能だが、無関係な測定 identity を余分に前進させる。対して `layer3_report.py` は本 wave で元々変更され、その bytes は新規 report の自己 provenance にだけ反映され、silo/T126 identity 集合には含まれない。
   - **性質 (real / refuted):** **real**
   - **推奨する扱い:** bytes 閉包を基準に `layer3_report.py` 自身へ宣言を置く方が狭い。test 側の逆向き import という plan 記載の欠点はあるが、追加の production identity を変更しない利点が上回る。

## brief と plan が正しかった点

- Pegasus g1 は47個の `2101` と1個の `3080.935`、tolerance 2%で、中央値由来の帯 `[2058.98, 2143.02]` を1標本だけ外れる。g2 は48標本すべて `2101` で通る (`execution_guard.py:324-337,399-445`、両 registered JSON:1)。
- g1 artifact の `quality.status` は `accepted`、`notes` は空であり、自己不整合の production 表示はない。
- plan の `_validated_pin_path` 後に除外する修正は、brief P2 の fail-closed 矛盾を正しく解消している。
- 現在の Pegasus pin は `registered/` 配下なので直下 glob に入らず、exploration root でも suffix 解決後の returned path を除外すれば pin 自身は戻らない。
- schema は no-match 時の `search` を単なる object としており、`contract_pin.status` の値を列挙していない (`layer3_schema.json:299-303`)。新 status は schema 変更なしで入る。
- `ExecutionEnvironmentContract` や `GenerationEntry` に field を足さない限り、module 定数の追加は contract hash・generation hash・activation record を変えない。
- repo 内7 report はすべて linux-baremetal の v1 lock で、今回の Pegasus g1 v2 除外により既存 noise-floor 値は変わらない。
- 現 worktree は clean で、brief に列挙された t2262 の4 path と本 wave の編集面の集合積は空である。ただし t2262 側 dirty 一覧の完全性は許可された読取範囲外で独立再測定していない。

## 総括

最も重い所見は、exact pin path だけの除外では D1537 の「環境系列を一致なしに保つ」が直下 copy / hardlink で破れることです。
同じ抜け道により、重複エラーから直下1件の新規一致へ転じる受理拡大も生じます。
validation-first と登録全世代の集合完全一致監査は正しく、ここは plan を維持できます。
宣言の置き場は、追加の silo/T126 identity を動かさない `layer3_report.py` が狭いです。
repo 外の artifact copy と t2262 の実 dirty 状態は読取境界上未確認で、親が再実測すべき残存点です。pytest・probe は実走していません。