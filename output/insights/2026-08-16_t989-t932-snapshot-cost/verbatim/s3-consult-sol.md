1. **所見 1**: `.git/shallow` は seal と verifier の双方の盲点であり、方式 B でも 834 commit 未満の閉包を緑にできる

- 根拠: `tools/codex_reasoning_ab.py:770-846,1347-1382`、`plan-s1b.md:23-25,62,82`、`brief.md:49-53`
- 反例の構成: `git init` 後の `checkout` で `.git/shallow` に `BASE_COMMIT` を書く構成を作る。例えば `init.templateDir` の `post-checkout` hook で注入できる。seal は shallow 境界より前の親を `repack/prune` の到達集合から落とせる一方、verifier は `.git/shallow` を列挙せず、`git fsck` も shallow 境界を正当な履歴端として扱う。HEAD、working-tree hash、ref は同じまま、commit/object 数だけ減らせる。通常の方式 B で余分な object を増やして緑にする経路は見つからない。余分な object は prune されるか `fsck --unreachable` で赤になる。`index-pack --fix-thin` も未解決 delta を rc=0 にはしないが、commit が参照する欠落親までは検査しないため、semantic な不完全 pack は rc=0 になり得る。方式 A は生 SHA 拒否時に `_run` が例外化するため、fallback を足さない限り静かな別物にはならない。
- 深刻度: BLOCKER
- 成果物影響 (DW-G05): `git_object_closure.base_only=true` のまま object 数と利用可能履歴が減り、certified snapshot、oracle、レポートが現行 834 commit / 8,209 object と異なる受理集合を参照する。

2. **所見 2**: 通常ファイルは消せても、`remote.*` config と dangling symlink の `packed-refs`／grafts／`FETCH_HEAD` は残せる

- 根拠: `tools/codex_reasoning_ab.py:792-797,816-846,907-912,1340-1371`、`tools/codex_reasoning_ab.py:1144-1169`、`plan-s1b.md:50-60`
- 反例の構成: init template の config に `[remote] pushDefault = latent` を置く。`git remote` は named remote を列挙するだけなので、`remote.pushDefault` は `remote remove` の対象にならず verifier も緑になる。さらに checkout hook から、現在は存在しない外部 target を指す `.git/packed-refs`、`.git/info/grafts`、`.git/FETCH_HEAD` の symlink を作る。cleanup と verifier は `exists()`／`is_file()` を使うため dangling symlink を不在扱いする。copy 後に target が現れると snapshot bytes を変えず Git の意味が変わる。なお alternates と commit-graph は `objects/info` 全消去で通常・dangling とも除去される。
- 深刻度: MAJOR
- 成果物影響 (DW-G05): metadata に symlink/config が載っていても closure reason は 0 件となり、レポートは remote・grafts・packed refs が空の自己完結 snapshot と誤記録する。

3. **所見 3**: `submodule_manifest_sha256` は literal pin ではなく、S1 の初期化欠落を同一走行内で再凍結できる

- 根拠: `tools/codex_reasoning_ab.py:695-712,915-1037,1692-1699,2475-2483,3904-3912`、`orchestrator/tests/test_codex_reasoning_ab.py:319-347,1821-1846`、`brief-addendum-2.md:42-43`
- 反例の構成: `_build_snapshot_base` から `_init_submodules_from_local_source` を削る。空の gitlink directory は `initialization="uninitialized"` として正規に manifest 化される。既定 `_snapshot_spec` には期待 `submodule_manifest_sha256` が無いため `verify_snapshot` は拒否せず、生成後の schedule が変更後 hash を取り込み、POS/NEG が同じなら検査も通る。`CASE_HASHES`、`TRACKED_HASHES`、`ARTIFACT_HASHES`、`CASE_NUMSTAT` は root working tree の値なので変わらない。正しい方式 B でも `.git` bytes が変わるため `snapshot_manifest_sha256` は変わり得るが、こちらは同一走行内 pin であり literal ではない。
- 深刻度: BLOCKER
- 成果物影響 (DW-G05): schedule／launch／oracle の `submodule_manifest_sha256` が新値へ移り、submodule source と再帰 object store を欠く snapshot が certified 選択・レポート・台帳へ入れる。

4. **所見 4**: commit-graph 補強は helper 内配線しか戻さず、S2 と組み合わせると build→seal 全体の削除変異が生存する

- 根拠: `tools/codex_reasoning_ab.py:806-811,1123-1141,1480-1484`、`orchestrator/tests/test_codex_reasoning_ab.py:892-944,947-1009`、`plan-s1b.md:82,86-92,113-114`、`plan-s2.md:52-54`、`brief-addendum-4.md:38-65`
- 反例の構成: build が graph を作らなくなると、cleaned node は「最初から無い」状態を見るだけになり `_remove_git_object_info_caches` の build 配線を検査しない。stale node は graph を自作するので verifier の拒否力は維持するが、build cleanup は検査しない。提案された helper 拡張は line 811 削除を殺せる一方、`_build_snapshot_base` の `_seal_git_object_closure(base)` 呼出自体を削る変異には効かない。さらに S2 は、追補 4 が保留禁止とした残り 3 consumer を全て hold 候補にしている。新 synthetic test の列挙 assert は reflog／全 closure reason を含まず、direct helper test は seal を自分で呼ぶため、この変異が既定 suite で生存する。
- 深刻度: BLOCKER
- 成果物影響 (DW-G05): テストの受理集合が unsealed build を許し、実 experiment では snapshot verification が失敗して certified 選択・レポート・台帳を生成できなくなる。

5. **所見 5**: measurement の 11 consumer を全て保留すると、各 `collateral_note` に無い module fixture 内の固定検査も消える

- 根拠: `orchestrator/tests/test_s1_measurement_freeze.py:43-60,111-282`、`orchestrator/tests/conftest.py:390-414`、`plan-s2.md:70-80,268-353`、`orchestrator/tests/growth_test_holds.py:41-55`
- 反例の構成: 提案どおり fixture consumer 11 件を登録する。collection 時の skip により fixture 自体が起動せず、full SHA 形式、`CURRENT_PIN` prefix、独立 golden、`K.verify_document` の検査がまとめて止まる。例えば build_document が短縮 pin を返す変異は、現状 line 51-57 で赤だが、この path では実行されなくなる。個別 collateral は各 test body だけを説明し、この共有損失を提示していない。なお `correctness_gate=False` の node は存在せず、`_hold` は全行を強制的に `True` にしている。問題は boolean ではなく提示内容の不足である。
- 深刻度: BLOCKER
- 成果物影響 (DW-G05): known-axes／measurement freeze の pin・golden・自己検証が既定受入から外れ、certified 材料レポートと台帳が依拠する検査集合が、ユーザー提示より広く縮小する。

6. **所見 6**: 追加探索 primitive に `copytree` 系が無く、現存する成長比例 node をなお漏らす

- 根拠: `plan-s2.md:34-40`、`orchestrator/tests/test_dev_waves_checker.py:60-71,171-323`、`orchestrator/tests/test_codex_agents.py:37-53`、`orchestrator/tests/conftest.py:170-261`、`orchestrator/tests/growth_test_holds.py:65-160`
- 反例の構成: `tools/task_runs/` に tracked file を追加する。`test_dev_waves_checker._fixture` は各 consumer ごとに実 repo の同 subtree を `shutil.copytree` するため、費用が tracked file 数・bytes に比例する。しかし提案探索は glob、read、主要 Git command しか sink にしておらず、これらの node は serial 集合にも hold 台帳にも無い。同型は `test_codex_agents._fixture` の複数 real subtree copy にもある。
- 深刻度: MAJOR
- 成果物影響 (DW-G05): T-932 の棚卸し台帳と件数が不完全なままになり、未保留 node が受入 wall を成長させ続ける。後日保留する場合は trust-root 系の正しさゲートも別途提示が必要になる。

7. **所見 7**: 追補 3 は init と aggregate seal を分離したが、root seal／submodule seal と成長傾きをまだ分離していない

- 根拠: `brief-addendum-3.md:9-20,34-40`、`tools/codex_reasoning_ab.py:1123-1141,1461-1484`、`plan-s1b.md:98-104`
- 反例の構成: 元 brief の「submodule 約 12.3 秒」は追補 3 で正しく取り消されており、「init と seal が未分離」という旧前提は既に refuted である。ただし計時された `_seal_git_object_closure` は root、全 submodule、config cleanup の合算である。さらに現在の 3 方式比較は同じ 3,920-commit source だけである。BASE 閉包を固定したまま BASE 後へ N commit を追加し、source を多数 pack に分割した系列を作ると、`pack-objects` の pack-index探索費が N／pack 数に比例する可能性を検査できる。出力 object 数が固定であることだけでは時間の定数性を証明しない。
- 深刻度: MAJOR
- 成果物影響 (DW-G05): 現時点の約 5 秒という改善値は有効でも、「commit 数から切り離した」というレポート・実測台帳・T-989 完了判定が過大になる。certified 選択値自体は変わらない。

pytest、fixture 構築、性能測定は実行していない。

## 総括
NO-GO  
BLOCKER 4 件。特に shallow 拒否、submodule の実 literal pin、非保留の build→seal 統合検査、S2 collateral の再提示が必要。