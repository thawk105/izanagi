## consumer 全数照合の検査

**B-01 主張:** consumer 表は全数ではない。関数内 import と再 export の先にある `orchestrator/verifier/commit_receipt.py` が欠落している。これは表の 22 file に加えるべき 23 番目の consumer-bearing file である。ただし新 nonzero helper は不要で、既存の exact COMMIT source 述語が非ゼロを含意する。

**根拠:** `orchestrator/verifier/commit_receipt.py:387-438` の `admit_replay_evidence()` は関数内で `CertifiedCampaignView` を import し、view と source record を受けて `ReplayVerificationEvidence` を発行する。`orchestrator/campaign/artifact_admission.py:97-113` は source record が発行済み view.records の同一 object で、かつ `stage == STAGE_COMMIT` であることを検査する。API は `orchestrator/verifier/__init__.py:21-34,40-55` から再 export される。計画の全数結論は `s2-plan.md:116`。

**誤っていた場合に何が壊れるか:** consumer 閉包が偽になり、今後 `_assert_replay_admission_source` が弱体化しても新しい件数契約の照合対象外になる。D1246 の「現に存在する consumer の列挙」に反する。

**親が何を測れば決着するか:** 表へ `commit_receipt.py` を追加し、source identity または COMMIT stage 判定を除く変異が `test_t1286_commit_receipt.py` で落ちることを測る。新 nonzero helper の呼出追加ではなく、既存 exact source 述語を load-bearing として固定する。

**B-02 主張:** 列挙済み行のうち、root field だけで分類した行は見つからなかった。一方、「要求する」3 行の helper は正規 view では失敗不能であり、挙動上の gate ではなく構造上の宣言である。

**根拠:** `backoff_sweep_report.py:65-79` は commit 由来の static 点が無ければ helper 到達前に skip する。`backoff_overthrottle.py:172-192` は committed binding の期待全集合一致を先に要求する。`backoff_extended_sweep_report.py:472-512` は committed point からだけ `perf_statuses` を作り、0 commit なら helper 到達前に `len(perf_statuses) != 1` で拒否する。計画上の追加位置は `s2-plan.md:105-106,114`。alias `L`、`_artifact_admission`、動的 module 保持、view の `make_critic_digest()` 受け渡しは表に含まれていた。

**誤っていた場合に何が壊れるか:** spy test は配線を証明しても、helper 削除変異を挙動として kill できない。「consumer gate が実効的」という主張が過大になる。

**親が何を測れば決着するか:** 3 consumer から helper 呼出だけを除く変異を走らせる。既存出力が変わらなければ「明示的な契約マーカー」と記録し、挙動 gate や mutation kill と主張しない。実効的な zero-commit 拒否は replay、certifying Layer3、certifying autonomous chain で別に測る。

**B-03 主張:** current brief は在庫を 9 direct-helper file に修正済みだが、provisional P3 と計画は古い 10 file のままで内部不整合が残る。

**根拠:** `brief.md:45-54` は外部 8 と定義元 1 の計 9 とする一方、`brief.md:120-123` はまだ 10 file と書く。`s2-plan.md:8,181` も「不明な 1 file」を残す。現 checkout の direct name は `artifact_admission.py` を含む 9 file である。

**誤っていた場合に何が壊れるか:** author が存在しない 1 file を探索し続けるか、B-01 の hidden consumer と direct helper 数の差を混同する。

**親が何を測れば決着するか:** 同じ除外条件で file 単位の検索を再掲し、direct helper は 9、名前検索和集合は 22、semantic consumer-bearing file は B-01 を足して 23、と三つを分けて brief と plan を揃える。

## field 追加の波及の検査

**B-04 主張:** must-fix。新 field 自体を report に射影しなくても、計画どおり `artifact_admission.py` と `layer3_report.py` を編集すると、保存済み Layer 3 report と fresh rebuild が byte 不一致になる。計画の「schema と bytes は変わらない」は成立しない。

**根拠:** `artifact_admission.py:1039` は現在の同 file 全体の SHA を `validator_sha` とし、`:1225` で decision に入れる。`layer3_report.py:651` は現在の `layer3_report.py` 全体の SHA を `meta.generator.sha256` に入れ、`:662` は decision receipt を report に入れる。計画は両 file を編集する (`s2-plan.md:72-75,112`)。fresh rebuild は `autonomous_trial_completeness.py:4666-4670`、比較は `:5015-5032`。比較正規化 `:4687-4721` は `generated_from_head` だけを除き、generator SHA と validator SHA は除かない。cross-binding も `:4431-4446` で decision を exact 比較する。

**誤っていた場合に何が壊れるか:** 実装前 bytes で保存された v3 Layer 3 report は、新コードでの fresh rebuild と必ず異なる。テストで persisted 側と fresh 側を同じ新コードから生成すると緑のままで、実成果物だけが拒否される。

**親が何を測れば決着するか:** base commit のコードで作った実 v3 report を保存し、実装 commit のコードで同じ campaign を `build_report()` し、`_layer3_comparison_projection()` 後の canonical bytes を比較する。実 external autonomous-trial root も対象にする。互換方針を決めるまで author を開始すべきでない。

**B-05 主張:** default 無し field の constructor 波及がテスト計画から漏れている。また「caller は件数を渡せない」は事実ではなく、現 token は Python module 属性として参照可能である。

**根拠:** token は `artifact_admission.py:71`、constructor は `:339-362`。`test_t1286_commit_receipt.py:431-438,531-535` と `orchestrator/tests/commit_receipt_support.py:185-204` は token を直接使って `CertifiedCampaignView` を構築する。計画が明記する更新は `test_artifact_admission.py` の token test だけ (`s2-plan.md:126-127`)。test support は多数の test file から利用されている。

**誤っていた場合に何が壊れるか:** 必須 keyword 欠落で replay receipt 系の広い test 群が constructor 呼出時に落ちる。また token と count を直接渡した exact instance は nonzero helper を通せるため、「検査済み件数を偽装不能」は信頼済み repo code 内の規約にすぎない。

**親が何を測れば決着するか:** `CertifiedCampaignView(` の全 call site を再集計し、3 箇所すべてへ count を配線する。private construction で未検査 COMMIT と count 1 を作り helper が通るかも測り、通る設計を許すなら「内部発行規約」と主張を限定する。

**B-06 主張:** B-04 の source-hash 波及を除けば、新 field の直接的な schema、正規化、等値比較、identity hash への取り残しは見つからない。

**根拠:** report は `CampaignAdmissionDecision.as_receipt()` の明示 dict (`artifact_admission.py:271-292`) を使い、view 全体への `asdict()` や `_canonical_bytes()` は無い。`CriticIdentityProjection.admitted_view` は `p3_s4_loop.py:483-489` で `compare=False`。通常 view では count は records の COMMIT 数から一意なので、dataclass 等値は変わらない。生成 hash を view に適用する production consumer も静的検索で見つからなかった。

**誤っていた場合に何が壊れるか:** report top-level key、JSON schema、view 等値、hash-keyed cache のいずれかが予期せず変わる。

**親が何を測れば決着するか:** field 追加後に `dataclasses.fields(CertifiedCampaignView)`、正規 view 2 個の等値、report exact keys、保存 JSON に field 名が存在しないことを静的または焦点 test で固定する。hash は現に consumer が無いことを source inventory で確認すればよい。

## 隠れた pin の検査

**B-07 主張:** projection closure の波及記載が不足している。`artifact_admission.py` だけでなく、計画が編集する `p3_s4_loop.py` も全 driver 共通 closure member である。

**根拠:** `p3_b4_closed_critic.py:633-667` は `p3_s4_loop.py` と `artifact_admission.py` を base、sort、trigger 全 closure に含める。計画は `p3_s4_loop.py:1202-1228` を変更する (`s2-plan.md:41`) が、pin 節 `s2-plan.md:184` は contract closure 内の artifact と replay だけを記す。projection hash は terminal receipt の `p3_b4_closed_critic.py:1015` に保存される。

**誤っていた場合に何が壊れるか:** 3 driver の projection SHA がすべて変わることを見落とし、作成済み controller、receipt、事前登録値が stale になる。文書欄が未記入でも in-flight object までは安全にならない。

**親が何を測れば決着するか:** 実装前後の `projection_sha256(base|sort|trigger)` を三つとも記録し、登録文書が未記入であることに加え、in-flight controller や保存済み B4 receipt が無いことを確認する。

**B-08 主張:** acceptance ledger の既存 node 名維持方針は正しい。ただし追加対象は named test 1 本ではなく、実装で新たに collect される全 node でなければならない。

**根拠:** 現 key は `acceptance_duration_ledger.json:43`。計画は rename せず新 node の実測 duration を追加する (`s2-plan.md:120-141`)。一方、計画は constructor 負例、replay zero-commit、Layer3、autonomous chain など複数の新 test を予定する。add-only 契約は `tools/update_acceptance_duration_ledger.py:83-87`。

**誤っていた場合に何が壊れるか:** node 名自体は保たれても、新規 node が duration ledger から漏れ、acceptance shard の重み付けと ledger coverage が stale になる。

**親が何を測れば決着するか:** 実装後の全 collect-only nodeid と成功 JUnit を使い、add-only 更新で追加された全 node と `nodeid_count` を同じ commit に入れる。推定 duration は使わない。

## 既存テストの分け方の検査

**B-09 主張:** must-fix。計画された 2 test は、現記述のままでは独立した命題にならない。同じ production admission から view を作ると、admission 側だけを壊す変異で両 test が落ちる。

**根拠:** 現 no-commit fixture と admission は `test_artifact_admission.py:1296-1372`。計画は同じ形の campaign で第二 test を作る (`s2-plan.md:122-127`)。admission を zero-commit reject に変えると、第一 test は期待どおり失敗するが、第二 test も helper 到達前の view 構築で失敗する。M6 と M10 は `s2-plan.md:166-170` にあるが、この独立性を指定していない。

**誤っていた場合に何が壊れるか:** 「admission は通る」と「nonzero helper は拒否する」を別々に壊せず、分割が見かけだけになる。第二 test の `pytest.raises` 範囲が admission 呼出まで含む場合は、誤った admission 拒否を helper 拒否と取り違えて pass する危険もある。

**親が何を測れば決着するか:** helper test は production admission に依存しない private zero-count exact view を使う。次の二変異を別々に走らせる。

- admission だけ zero-commit reject: 第一 test だけ失敗、helper test は成功。
- helper だけ zero-commit accept: 第一 test は成功、helper test だけ失敗。

## 分割方針の検査

**B-10 主張:** 単一 author 子の方針は妥当である。素集合は概念上二つあるが、並行に独立実装できる単位ではない。

**根拠:** producer kernel は `artifact_admission.py` の scan、count field、nonzero helper と core tests。consumer adapter は replay、Layer3、autonomous chain、backoff 群、既存 raw helper caller と consumer tests。この後者は前者の新 API と constructor 契約を import し、acceptance ledger と `commit_receipt_support` を共有する。D1246 は一つの共通 helper を要求する (`verbatim-rulings.md:7-15`)。D95 は実装面を Codex author に戻す (`:28-37`)。

**誤っていた場合に何が壊れるか:** 並行 author が count 名、例外型、helper の適用位置を別々に仮定し、producer と consumer が別契約になる。特に B-04 の互換方針を別 author が独自判断すると保存 report の扱いが割れる。

**親が何を測れば決着するか:** B-04 と B-09 を先に裁定し、単一 author の最終 diff で producer API、全 consumer、test support、ledger を一括照合する。二 author にするなら producer を先に確定する逐次分割だけが可能で、並行分割ではない。

## 親 brief の実測の検査

**B-11 主張:** checked-in WAL 30 件について「zero commit 2 件はいずれも E0」は整合するが、「保存済み成果物では現在未発火」から互換対応不要とは導けない。

**根拠:** WAL 実測の射程は `brief.md:21-26`。一方、B-04 の fresh rebuild は source file SHA を report に持ち込み、`autonomous_trial_completeness.py:4666-4670,5015-5032` で保存 report と比較する。この経路は WAL の commit 件数と無関係である。checked-in Layer3 は legacy v1/v2 だが、実 external root の v3 report はこの探索に含まれていない。

**誤っていた場合に何が壊れるか:** zero-commit の保存 campaign が無いことを理由に、v3 report 互換性を must-fix から外してしまう。実成果物だけ fresh rebuild で拒否される。

**親が何を測れば決着するか:** `output/campaigns` の WAL だけでなく、実 autonomous-trial output root の保存 v3 Layer3 report を全数対象にし、base bytes 対実装後 rebuild bytes を比較する。

**B-12 主張:** 126 は uniform admission gate の影響値であり、P1 実装全体の赤 node 数の上界ではない。

**根拠:** 測定対象は selected consumer test 群への zero-commit 一律拒否 probe (`brief.md:27-44`)。P1 は必須 dataclass field、8 raw helper caller の共通化、Layer3 と replay の source hash 変更、test support の constructor 変更を含む。特に `commit_receipt_support.py:129-204` は多くの test から利用され、uniform gate probe では触れていない。

**誤っていた場合に何が壊れるか:** acceptance 規模と修正範囲を過小評価し、「P1 は 126 未満のはず」を regression 上限として使ってしまう。

**親が何を測れば決着するか:** 126 は「uniform zero-commit policy を却下する証拠」にだけ使う。P1 の赤 node 数は実装後の全 acceptance で新たに測り、126 と大小比較して事前上界だったとは報告しない。

## 総括

プランはそのまま author へ渡せない。must-fix は B-01 の hidden consumer 追加、B-04 の保存 Layer3 互換方針、B-05 の全 constructor site、B-07 の projection closure、B-09 の独立 test 構成である。単一 author 方針と、admission 自体では zero commit を拒否しない P1 の中心判断は維持できる。

pytest は実行しておらず、緑とは報告しない。検査は source、schema、保存比較経路、pin、test node の静的追跡だけである。