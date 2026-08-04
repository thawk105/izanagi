静的検査のみを実施した。pytest・書込みは行っていない。

## BLOCKER

### B1. token 省略で全 gate を迂回でき、P5 が恒真化する

**(a) 主張:** `token is None` を「非 formal」とみなす PROV-3 は、formal 性を caller の自己申告にしている。これは P5 の拒否 gate ではない。

**(b) 根拠:** `brief.md:27,44-49`、`s2-plan.md:88-90,111-113,150-159,267-270`。現行 `p3_autonomous_workload_trial.py:1531-1533,1636-1647` は token なしで三 seam を受理し、既存 `test_p3_autonomous_workload_trial.py:1295-1314` も注入受理を固定している。

**(c) 失敗シナリオ:**  
`run_trial(provider_kind="claude-headless", providers=偽4-role, drive=偽drive, preview=偽preview, token=None)`  
→ 注入した role 群が実行され、report は `provider="claude-headless"` のまま受理される。新 gate は一度も発火しない。

**(d) 最小修正:** formal 性を token の有無以外で決める。最低でも `provider_kind=="claude-headless"` は issued token と正準 seam を必須にし、token なしを拒否する。これは brief の「token 非提示は完全保存」と両立しないため、PROV-3 は**不採用**として段 4 の再裁定へ戻す。

### B2. formal producer の閉集合に direct driver がなく、未予約 token 拒否を名乗れない

**(a) 主張:** plan は `drive_iteration()` を「非 formal」と再分類して放置するが、現行では実 LLM proposal の正式な一 iteration producer であり、campaign state・provenance・digest を書く。

**(b) 根拠:** `brief.md:65-66` は direct 反復を token の成果物影響として挙げる一方、`s2-plan.md:270` は同入口を残す。`p3_s4_loop_trigger_gating.py:604-666,690-697,705-707,756-781` に token はない。D114 `docs/decisions.md:5390-5395` と D121 `:5863-5866` も direct 反復を保証外と明記する。D121 `:5842-5848` は P5 の検査対象閉集合が必要としている。

**(c) 失敗シナリオ:** 同じ campaign に対して `drive_iteration()` または `--run-iteration` を直接反復する  
→ P5 token を一度も予約・提示せず checkpoint、provenance、WAL 到達可能成果物が生成される。

**(d) 最小修正:** formal producer/consumer の閉集合を先に列挙し、driver を gate に含めるか、その成果物が formal consumer に入らない機械拒否を置く。これは現 brief の編集面外なので、driver への黙示的配線は**不採用**。scope 拡大の裁定がなければ P5 は未充足と記録する。

### B3. session 共有ではなく、untrusted な `session_id` 文字列の重複しか検出しない

**(a) 主張:** 同一 session の不使用は、provider 自身が返す文字列の相異からは証明できない。さらに formal CLI は任意 executable を許し、「owned provider」も閉じていない。

**(b) 根拠:** `s2-plan.md:90,112,134-137,198-199`。現行 `p3_autonomous_workload_trial.py:1529,1642,1710,1770` は `claude_executable` を caller から受け、`claude_projected_provider.py:104-105,128-137,203-222,255-280,290-296` はその任意 binary が返した `session_id` を信頼するだけである。絶対規律 6 はプログラム出力を untrusted data とする (`CLAUDE.md:88-95`)。

**(c) 失敗シナリオ:** 共有 backend session を使う shim を `--claude-executable` に指定し、planner では `session_id="p1"`、coder では `"c1"` を返す  
→ token、正準 seam、tracker の全検査を通り、実際には planner→coder session 共有した run が受理される。

**(d) 最小修正:** formal 経路では executable の独立 authority/pin と session 非共有を証明する launch 契約を要求する。単なる executable SHA の記録は検査ではない。そこまで scope に入れないなら、閉じるのは「cross-role の同一 reported ID」だけと明記し、P5 の session 共有充足および receipt の `owned-claude-projected-provider-set` 表現は**不採用**。

### B4. optional receipt は両側削除で fail-open になる

**(a) 主張:** PROV-5 は formal consumer を名乗るが、receipt 両側欠落を受理するため formal artifact を非 formal artifact にダウングレードできる。

**(b) 根拠:** `s2-plan.md:141-159,163-177,267-269`。現行 consumer は report/run-start の exact-key 閉集合を持たず、`autonomous_trial_completeness.py:347-423,839-853`、既存正例 `test_autonomous_trial_completeness.py:218-254,448-468` は receipt なしを受理する。

**(c) 失敗シナリオ:** formal run の run-start と report から receipt を両方削除し、journal SHA を再計算する  
→ plan の optional pairing は発火せず、同じ artifact が completeness を通る。逆に片側だけ残すと拒否されるため、攻撃者には両側削除が最適となる。

**(d) 最小修正:** formal 性を provider/schema 等の独立な既存 field から決定し、その場合は receipt 両側を必須化する。durable authenticity まで求める変更は P3/P7 なので本 wave へ混入させない。PROV-5 の optional consumer は検出力が純増しないため**不採用**。

## MAJOR

### M1. token claim が入口検査より後で、拒否 run 後に再使用できる

**(a) 主張:** 「提示時点で claim」と plan 自身が書く一方、実際の挿入位置は既存引数検査後である。

**(b) 根拠:** `s2-plan.md:89,124,192`。現行の前置検査は `p3_autonomous_workload_trial.py:1536-1568`、run-root 検査は `:1569-1574`。

**(c) 失敗シナリオ:** parser-issued token を不正 `trial_id` の run に提示  
→ trial-id 検査が先に拒否し token は未 claim。その同じ token を正常 run に再提示すると受理される。

**(d) 最小修正:** token 非 None の場合は exact-type・issued・claimed 検査と claim を関数入口で先に行い、seam 判定を後段に分離する。上流拒否後の再使用負例も追加する。

### M2. 受理集合表が新 API 次元を変更前から存在したものとして扱っている

**(a) 主張:** D96 用の before/after が不正確で、実際の受理拡大を記録していない。

**(b) 根拠:** `s2-plan.md:146-159` は「formal token＋正準 seam」を変更前から受理可能と扱う。しかし現行 `run_trial()` には当該 keyword がなく (`p3_autonomous_workload_trial.py:1518-1535`)、D96 は受理集合変更を新 D と境界テストへ残すよう要求する (`docs/decisions.md:4271-4279`)。

**(c) 失敗シナリオ:** `run_trial(..., formal_trial_gate_token=issued_token)`  
→ 変更前は unexpected keyword の `TypeError`、変更後は受理。これは明白な受理拡大である。

**(d) 最小修正:** API signature 拡大、token-present 入力の新受理集合、consumer の縮小、tracker 引数追加を別々に表へ載せ、新 D の「研究状態への影響」に記録する。

### M3. 親 brief の scope と plan の編集面が一致しない

**(a) 主張:** brief の scope 内・成果物形は既存 production 2 ファイルだけを列挙するが、PROV-5 と plan は三つ目の consumer を変更する。

**(b) 根拠:** `brief.md:11-16,34-37` 対 `brief.md:48-49`、`s2-plan.md:139-145,248-260`。

**(c) 失敗シナリオ:** 現行 v2 artifact が同名の任意 metadata を report 側だけに持つ  
→ 現在は未知 field として受理、変更後は新 consumer により拒否される。scope に明記されていない受理縮小である。

**(d) 最小修正:** 段 4 で brief を明示改訂して consumer を scope 内へ入れるか、consumer 変更を落とす。現状の曖昧なまま第三 production file を編集してはならない。

### M4. receipt producer と validator が同じ literal を共有し、自己 oracle 化する

**(a) 主張:** 独立 golden が事前登録されておらず、schema/policy 定数の一行変異が producer と consumer を同時に変えうる。

**(b) 根拠:** `s2-plan.md:30-31,80-105,202-243`。mutation 表は「policy 検査を `if False`」だけで、共有 literal 自体の変異を扱わない。

**(c) 失敗シナリオ:** 共有 `FORMAL_TRIAL_GATE_RECEIPT_SCHEMA` または policy 定数を別文字列へ一行変更  
→ emitter と validator が同じ新値を使い、生成 receipt 起点の正例・負例がすべて通る一方、契約外 receipt が正式値として受理される。

**(d) 最小修正:** production 定数・戻り値・validator から期待値を作らない独立 literal 正例を置き、schema と全 policy literal の一行変異を matrix に追加する。

### M5. 変異の「kill」が他の拒否理由で偽陽性になる

**(a) 主張:** exact-type と片側欠落の mutant は、対象 predicate を消しても後続検査が同じ入力を拒否できる。

**(b) 根拠:** `s2-plan.md:190-193,222-224,238-243`。既存先例 `test_build_admission.py:175-194` も wrong-type と unissued membership が別層であることを示す。

**(c) 失敗シナリオ:**  
- exact-type 条件を削除しても、`True` は `_nonce` access で、未発行 fake は issued-set で拒否される。  
- 片側欠落条件を削除しても、欠落側 `None` の receipt validator が拒否する。  
テストは例外文の差で赤くなり得るが、「危険入力が受理されたため kill」ではない。

**(d) 最小修正:** wrong-type vector は実発行 token と同じ nonce を持つ異型 proxy にする。片側欠落 mutant は validator まで含めて欠落を受理させる operator にするか、その predicate を冗長防壁として mutation credit から外す。各 node は第一拒否理由まで固定する。

## MINOR

### m1. `--provider` 重複時の token 状態が未定義

**(a) 主張:** custom action が非 Claude 値で token dest を必ず消す契約がない。

**(b) 根拠:** `s2-plan.md:55-61,110,194-195`。既存 argparse は同じ option の反復を許し、最後の値を採る。

**(c) 失敗シナリオ:** `--provider claude-headless --provider fixture --no-build`  
→ first action の token が残れば、最終 provider は fixture なのに formal gate が拒否する。変更前は最後の fixture が受理される。

**(d) 最小修正:** action 呼出しごとに token dest を確定し、fixture では明示的に `None` へ戻す。両順序の重複境界テストを追加する。

### m2. tokenless `_provider_set()` の factory 互換性が未固定

**(a) 主張:** tracker keyword を常時 `None` で渡すと、既存の strict factory seam を指示外に縮小する。

**(b) 根拠:** `s2-plan.md:121,132-137`。現行 `_provider_set()` の factory 呼出しは `p3_autonomous_workload_trial.py:938-959` で tracker keyword を持たない。

**(c) 失敗シナリオ:** 現行引数だけを明示定義する `projected_provider_factory` を tokenless 経路へ渡す  
→ 現在は受理、変更後に余分な `cross_role_session_tracker=None` で `TypeError`。

**(d) 最小修正:** tracker keyword は formal context がある場合だけ渡すか、互換性縮小を D96 の受理集合へ明記する。

## 不採用

- PROV-3 の「token 非提示なら無条件 no-op」。
- PROV-5 の「両側欠落を受理する optional formal receipt consumer」。
- session_id の一致だけで「role 間 session 共有を閉じた」とする名乗り。
- 任意 `claude_executable` を残したままの `owned-claude-projected-provider-set` 表現。
- current wave 内での direct driver・durable origin・Layer-3 origin proof への無裁定な scope 拡大。

## 総括

**BLOCKER は 4 件、MAJOR は 5 件、MINOR は 2 件である。plan をそのまま実装してはならない。** 最大の問題は、formal 性を token の存在で自己申告させながら token 省略を完全保存し、consumer も receipt 両側欠落を受理する二重の fail-open である。この構造では provider 注入も未予約 run も、攻撃者が formal と名乗らないだけで gate に到達しない。さらに direct `drive_iteration()` は現行の正式な proposal producer のまま token 閉包外に残り、session tracker は任意 executable が返す自己申告 ID の重複しか見ない。したがって P5 の三要件のうち実際に追加されるのは、parser-issued main/Claude 経路における「同一 reported session_id の process-local 重複拒否」と「提示された bogus token の拒否」という限定 predicate だけであり、P5 全体は閉じない。段 4 では少なくとも PROV-3/5 を撤回し、formal producer/consumer の閉集合、token 必須条件、executable/session authority、D96 上の正確な受理集合を再裁定すべきである。