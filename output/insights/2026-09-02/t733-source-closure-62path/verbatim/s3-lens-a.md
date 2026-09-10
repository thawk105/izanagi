## 総括

段 2 はこのままでは差し戻し。明示 import の 36/131 は再現できたが、Python が先行実行する package 初期化 2 file が漏れており、直接 1 段目は少なくとも 38、全体は exact 62 path である。  
また、旧 exact-24 authority lock は `HISTORICAL_RAW` の目的判定前に decode 拒否されるため、親 brief の decode 互換条件と D1245 を満たさない。  
62 path 化、目的別の歴史 grammar、保証文言の縮小を条件に採用してよい。凍結 9 file は変更不要。  
静的読解と読取専用の独立測定のみで、pytest は実行していない。

## real な所見

1. **real: 36-path frontier は暗黙の package 初期化 2 file を落としている。**

   - 根拠: `orchestrator/campaign/guided.py:47` は `orchestrator.critic.online_digest` を import するが、その前に `orchestrator/critic/__init__.py:12` が実行される。同様に、現行 seed の qualification module は `orchestrator/qualification/__init__.py:7-19` を先行実行する。
   - 独立 AST 測定では明示 frontier 36、推移集合 131 は提供測定と集合差ゼロ。ただし package 初期化を加えると frontier は 38 となり、追加は `orchestrator/critic/__init__.py` と `orchestrator/qualification/__init__.py`。
   - **成果物影響:** この 2 file を lock 後に差し替えても 60-path epoch は動かず、critic/qualification import 時の副作用、受理、参照先を変更できる。
   - 推奨対応: 既存 24 を維持し、新規 suffix をこの 2 file を含む 38 path の辞書順にして exact 62 path とする。未収載数は 69。

2. **real: 旧 exact-24 E1 lock は `HISTORICAL_RAW` でも decode 不能になる。**

   - 根拠: `campaign_lock.py:215-234` が現行 tuple の exact key 集合を無条件要求し、`artifact_admission.py:868-877,898-927` で purpose 判定前に decode と committed verify が走る。目的分岐は後段の `artifact_admission.py:957-975`。段 2 はさらに pre-T733 exact-24 rejection を固定する予定である (`s2-plan.md:88-97`)。
   - **成果物影響:** 旧 exact-24 authority map を持つ campaign は、certified だけでなく歴史閲覧の受理集合からも消え、記録済み E1 epoch、WAL、provenance を参照できなくなる。
   - 推奨対応: certified/resume の current decoder は exact-62 のまま維持し、`HISTORICAL_RAW` に限って既知の歴史 key 集合と当時の tuple 順序を使う decoder/committed verifier を設ける。任意 subset や旧 grammar を certified 経路で許可してはならない。

3. **real: 提案 scope 文言は 60 path が直接委譲 1 段目を収載したと過大に読める。**

   - 根拠: 文言案は「直接委譲 1 段目までを収載」と断定する (`s2-plan.md:30-39`) が、所見 1 の package 初期化が未収載。また、D1128 は判定器自身が閉包内にある限界を明記させている (`rulings-verbatim.md:283-301`)。
   - **成果物影響:** 新規 report/provenance の `identity_scope` が、実際には束縛されない import 初期化、fresh-lock 弱化、外部委譲まで保証する診断として保存される。
   - 推奨対応: 下記「保証文言の評価」の文字列へ置換する。

4. **real: 非 import 委譲の列挙は非網羅的である。**

   - 根拠:
     - `buildcache.py:947-975,3319-3348,3366` は外部 Git、`nm`、ビルド command の結果を防壁に使う。
     - `source_digest.py:1820-1836,2120-2180` は PATH 上の Git で source identity と許可差分を決める。
     - `qualification/collector.py:371-399` と `qualification/identity.py:64-72,137-160` も外部 Git で receipt/source identity を検証する。
     - 段 2 の external Git 一覧は `contract_loader_binding`、`artifact_admission`、S8C、`t126_driver` までで止まる (`s2-plan.md:227-239`)。
   - **成果物影響:** 外部 command の実体や返値が変わると、source digest、build receipt、qualification receipt の受理集合が変わっても campaign epoch は変わらない。
   - 推奨対応: 完全列挙を保証文言に焼かず、「subprocess、外部 command/Git、toolchain、binary、data/schema を含む非 import 委譲一般は対象外」と明記する。包括的な別 binding は裁定へ返す。

5. **real: qualification schema は gate に実際に効くが、別 binding だけで実行 bytes まで閉じてはいない。**

   - 根拠: `qualification/artifacts.py:639-663,870`、`qualification/collector.py:287-305,1471-1518`、`t126_driver.py:1305,1334-1341` が live schema を直接使って受理を決める。schema は `qualification/contract.py:39-77` の code identity に含まれる一方、`qualification/identity.py:134-160` は記録 commit blob を検証するだけで、実際に読み込んだ live schema bytes と記録 blob の等値を確認しない。
   - **成果物影響:** schema の live bytes を緩めると、同じ campaign epoch と記録 code identity のまま qualification event/final receipt の受理集合が広がりうる。
   - 推奨対応: 本 wave では未保証として明記する。campaign closure へ入れるか、schema 読取と記録 blob を結ぶ別 binding を作るかは裁定パッケージへ送る。

## refuted な所見

1. **refuted: 新規 36 path の存在、可読性、生成物性により capture が常時失敗する。**

   36 file はすべて tracked、HEAD blob あり、regular file、現在 readable で、生成物を示す header もなかった。`contract_loader_binding.py:348-401` は欠落、非 regular、読取不能、HEAD drift のいずれも fail-closed にする。

2. **refuted: 明示 import の 36/131 という測定値自体が再現しない。**

   相対 import を package 階層込みで解決する独立 AST 解析で、明示 frontier 36、推移集合 131、いずれも提供集合との差はゼロだった。ただし 36 は実行時 package 初期化を含まないため、保証上の「直接委譲 1 段目」には使えない。

3. **refuted: tuple 順序を維持しても epoch が非決定になる。**

   `artifact_admission.py:920-928` は map の JSON 順序ではなく production tuple 順に pathとdigestを連結する。既存 24 の順序維持と新規 suffix の exact literal 固定は、新しい current epoch の決定性には十分。ただし歴史 epoch の再導出には grammar ごとの旧 tuple が別途必要。

4. **refuted: 凍結 fig2b、fig2c、fig4 は間接的な再生成が必要。**

   `test_s1_9pair_figure_provenance.py:654-668,734-738` は live validator と生成時 validator hash を分離し、current/frozen epoch も別 golden にしている。fig2b は生成時 generator hash を literal 固定 (`test_backoff_figure_provenance.py:670-690`)、fig2c も生成時 source/output hash を固定している (`test_b10_extended_figure_provenance.py:784-837`)。今回の編集対象はこれら generator ではない。

5. **refuted: tracked lock に authority map が存在する。**

   tracked 32 file、物理 32 fileはいずれも schema-less v1で、authority key と closure map はゼロ。repo 内で今回新たに失効する E1 campaign はゼロという実質結論は正しい。

6. **refuted: `legacy_admission_overlay_v1.json` は certified 受理を広げる correctness gate である。**

   overlay は deny-only (`artifact_admission.py:487-574`)。v1 の非 overlay 歴史 artifact も certified では E0 として拒否される (`artifact_admission.py:963-975`)。この JSON が変えるのは主に `HISTORICAL_RAW` の分類・受理集合であり、certified acceptance を正に昇格させない。

7. **refuted: `tools/pegasus/policy.json` は一様に未束縛の correctness gate である。**

   `loop.py:83-109` で使うのは perf candidate と観測可否で、verifier の serializability 判定そのものではない。T126 では request/admission に効くが、`qualification/contract.py:39-77` と `qualification/identity.py:155-160` により別の Git identity と live/committed 比較がある。campaign epoch 外ではあるが、全面的に無束縛という説明は正しくない。

## 親 brief 自身の誤り

1. `parent-brief.md:29-31,43-45` の 30/54 path は誤り。明示 AST frontier は 36だが、実行時 package 初期化まで含む直接 frontier は38であり、推奨 current scope は 62 path。

2. `parent-brief.md:33` の「authority = null」は wire 上は誤り。32 file はすべて authority key が存在しない schema-less v1であり、decode 後に `authority is None` となる。実質的な「closure map なし」は正しい。

3. `parent-brief.md:51-52` の「受理集合を狭める方向だけ」は誤り。`campaign_lock.py:222-234` の exact grammar は旧集合から新集合への置換であり、旧 map を除外する一方、旧コードが拒否した新 map を受理する。

4. 131 module と repo 内の追加失効 0 件は確認でき、誤りではない。ただし repo 外の旧 authority lock と `HISTORICAL_RAW` 互換まで含む 0 件主張には使えない。

## 保証文言の評価

段 2 の文言案はそのまま採ってはならない。62 path 修正後は、少なくとも次のようにする。

`CAMPAIGN_VERIFIER_EPOCH_SCOPE`:

> E1 記録 map の対象となる curated enforcement source files (exact 62 path; 2026-09-01 の静的明示 import 発見集合 131 module 中、既存 24、明示 import 先 36、実行時 package 初期化 2 を収載; source-import 推移閉包ではない)

`CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE`:

> 同発見集合の未収載 69 module、orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、orchestrator/verify.py、data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 import 等の非 import 委譲は本 map 外であり、完全性を主張しない。この診断は記録後 drift の同一性に限り、判定器の外側からの認証、弱化後に作る fresh lock、旧 epoch との意味互換性、certified sink の支配を保証しない

これなら「推移閉包が閉じた」と読めず、D1128 の自己参照限界も隠さない。

## nit / 裁定パッケージ候補

- **裁定パッケージ候補:** 既知の歴史 grammar 8/12/14/25/27/24 を `HISTORICAL_RAW` だけで読む versioned grammar registry。current certified decoderを緩めないことを必須条件とする。
- **裁定パッケージ候補:** qualification schemas、S8C markdown/contract/freeze、外部 Git/toolchain/binaryを campaign closureへ含めるか、別 binding の責務とするか。
- **裁定パッケージ候補:** 同じ `campaign-verifier-epoch/v1` domain が複数の path grammar を指す cross-version 意味互換問題。
- **nit:** `authority-null` ではなく「schema-less v1、authority key absent、decode後 authority None」と記述すると wire contract と一致する。
- **nit:** 段 2 の非 import 一覧は「例示」と明記し、完全一覧として扱わない。