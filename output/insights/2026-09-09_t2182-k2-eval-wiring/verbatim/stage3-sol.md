## 攻撃した仮説と結果

| 仮説 | 判定 | 結果 |
|---|---|---|
| official job body で K2 identity と K2 consumer を分離できる | refuted | all-or-none 検査により、manifest を driver へ渡す経路では role も必ず渡る |
| driver 全体で同じ分離が不可能になる | real | job body を経由しない CLI では manifest-only が依然可能 |
| K2 拒否が全て事前構築前に行われる | real | bundle 完全性だけは早期だが、値域、manifest、proposal の拒否は gflags/glog build と prebuild の後 |
| manifest/proposal 本文が job body の命令として働く | refuted | job body は本文を読まず、quoted argv として渡すだけ |
| 変異候補が独立した正しさ防壁を証明する | real | 5 候補のうち一部は driver と重複または意味的に無作用で、全候補が静的 pin とも重複 |
| 既存契約テストが反転、緩和、skip、削除される | refuted | proposal pin は既存条件を保持した厳密な追加で、fixture 等は維持される |

official job body の環境行列は以下である。`M/R/C/D` は順に manifest、coder role、classification、de-novo env、`P` は proposal path。「集合に含む」は非空設定を表す。

| 非空 K2 env 集合 | 結果 |
|---|---|
| `-` | K2 argv は空。`P` 非空なら非 K2 proposal、無ければ fixture |
| `M` | role 欠落で rc=2 |
| `R` | manifest 欠落で rc=2 |
| `C` | manifest 欠落で rc=2 |
| `D` | manifest 欠落で rc=2 |
| `M,R` | classification 欠落で rc=2 |
| `M,C` | role 欠落で rc=2 |
| `M,D` | role 欠落で rc=2 |
| `R,C` | manifest 欠落で rc=2 |
| `R,D` | manifest 欠落で rc=2 |
| `C,D` | manifest 欠落で rc=2 |
| `M,R,C` | de-novo 欠落で rc=2 |
| `M,R,D` | classification 欠落で rc=2 |
| `M,C,D` | role 欠落で rc=2 |
| `R,C,D` | manifest 欠落で rc=2 |
| `M,R,C,D` | `P` 無し・空なら rc=2。`P` 非空なら四 flag 全てを proposal driver へ渡す |

設定済み空値は `[[ -v $name ]]` で K2 request と認識され、固定順の `-n` 検査で拒否される。根拠は `stage2-plan.md:19-46,67-79`。成功時の argv は `stage2-plan.md:85-99` の形になり、manifest と role が片方だけ渡る組合せはない。

## real 所見

1. driver の manifest-only CLI が残るため、保証は official job body にしか成立しない。

   `p3_s4_loop.py:2299-2309` は manifest と role の対応を CLI 入口で強制していない。K2 cfg と受領証は `p3_s4_loop.py:2432-2438` で作られる一方、proposal loader には次の条件式で knowledge input が消される。

   ```python
   knowledge_input=(
       knowledge_input if a.coder_role is not None else None
   )
   ```

   根拠は `p3_s4_loop.py:2473-2481`。結果として `p3_s4_loop.py:2058-2077` は両方省略された非 K2 contract と判断する。

   他の実行前提を満たした compute node では、次の argv が残る。

   ```bash
   python3 -B -m orchestrator.campaign.p3_s4_loop \
     --allow-coder-derived-build \
     --isolate-worktree \
     --fetchcontent-prebuild-receipt /absolute/prebuild-receipt.json \
     --knowledge-manifest /absolute/k2-manifest.json \
     --knowledge-classification reproduction_or_selection \
     --knowledge-de-novo-claim false \
     --run-iteration /absolute/legacy-non-k2-proposal.json
   ```

   `--coder-role` が無いため legacy proposal schema を通しながら、campaign cfg は K2 のまま `drive_iteration` へ進む (`p3_s4_loop.py:2485-2498`)。

   成果物への影響: この経路が運用上到達可能なら、K2 schema、anomaly、参照 index 検査を受けていない候補が K2 campaign の BUILD_START、certified 選択、レポート、WAL に入る。

   `brief.md:42-43` と `stage2-plan.md:104` の driver 非変更方針では、この全体保証を主張できない。少なくとも `--run-iteration` では manifest と role の同時指定を driver 入口でも強制する必要がある。

2. bundle 以外の K2 拒否は事前構築後である。

   新しい bundle preflight 自体は current job body の line 52 と 54 の間へ入るため、早期である (`stage2-plan.md:16-56`)。しかしプランは role、classification、de-novo 整合、manifest 内容、proposal schema を driver に残す (`stage2-plan.md:65,165-168`)。

   実際の段順は次になる。

   - gflags/glog build: `p3_s4_loop_pegasus.sh:363-417`
   - FetchContent prebuild と receipt: `p3_s4_loop_pegasus.sh:421-533`
   - driver 起動: `p3_s4_loop_pegasus.sh:535-547`
   - CLI parse: `p3_s4_loop.py:2322`
   - manifest 解決: `p3_s4_loop.py:2372-2375`
   - classification/de-novo receipt 検査: `p3_s4_loop.py:2433-2438`、`knowledge_manifest.py:524-534`
   - K2 proposal schema/anomaly/semantic 検査: `p3_s4_loop.py:1979-2004,2058-2087,2473-2481`

   成果物への影響: malformed K2 proposal でも reservation、gflags/glog build、prebuild receipt、compute-result が先に生成され、valid manifest なら K2 campaign directory と knowledge receipt まで残り得る。ただし K2 consumer は候補 BUILD_START より前なので、この所見単独では certified 受理集合は広がらない。

3. 変異事前登録は「5 本の独立した正しさ防壁」を証明しない。

   `stage2-plan.md:151-158` は同じ構文を静的逐語 pin と refusal pin にも加え、`stage2-plan.md:187-195` は別途各変異を単一 nodeid で走らせる。現行 `_assert_static_job_contract` は文字列欠落を必ず赤にする (`test_p3_s4_loop_job_contract.py:134-369`)。したがって runner を一 nodeid に限定しても、検査自体が単一理由になるわけではない。

   各候補の独立判定は次のとおり。

   | 変異 | 判定 |
   |---|---|
   | `-v` を非空検査へ変更 | 防壁は実質的だが、負例の完全な env vector が未登録。`M=""` だけなら検出できるが、他の K2 env が非空なら `k2_requested=true` のままで後段 `-n` が同じ拒否を出す |
   | 完全性 `-n` を `-v` に変更し role を空にする | shell の早期拒否検査にはなるが、最終 driver は `choices=("coder-v4-autonomous-k2",)` で空 role を拒否する (`p3_s4_loop.py:2301-2303`)。正しさ受理集合には効かない |
   | proposal-path refusal を `true` にする | load-bearing。K2 bundle が fixture 分岐で無視され、非 K2 fixture を走らせられる (`stage2-plan.md:93-99`) |
   | manifest pair と role pair を交換 | flag と値の組を保った交換なら argparse 上の意味は同一。certified 値、受理集合、参照は変わらず、固定順 test は書式だけを検査する |
   | proposal driver から array 展開を除く | load-bearing。legacy proposal を与えれば K2 request が非 K2 campaign へ黙って退化する。ただし proposal の逐語 pin とも重複する (`stage2-plan.md:141-145,151-152`) |

   成果物への影響: このままの変異レポートは、意味的に load-bearing な防壁と、早期拒否だけの重複防壁、単なる argv 書式を同列に「独立した正しさ保証」として記録してしまう。

## refuted 所見

1. official job body の K2 identity/consumer 乖離は refuted。

   四 env のどれか一つでも設定されれば全四 env の非空と proposal path が必須になる。完全 bundle では manifest と role が同じ `k2_argv` に入り、`p3_s4_loop.py:2477-2480` で knowledge input と role が同時に loader へ渡る。正しい role の場合、closed K2 schema と consumer は `p3_s4_loop.py:2064-2087` で必ず通過対象になる。

2. 新しい部分指定拒否が build 後に置かれるという仮説は refuted。

   挿入点は sanitize/export 後、repository path 解決前 (`stage2-plan.md:16-56`)。現行 job bodyでは path 解決が `p3_s4_loop_pegasus.sh:54`、trap が line 111、gflags build が line 387、prebuild が line 463、driver が line 535 である。部分指定拒否は全てこれらより前で、compute-result も生成しない。

3. manifest/proposal 本文が job body の命令になる経路は refuted。

   job body が見るのは env の設定有無、非空、proposal path の非空だけで、本文は読まない (`stage2-plan.md:25-46,85-99`)。各値は quoted shell array element であり、本文中の shell syntax は再評価されない。

   manifest 内の commit/path は既存 driver が厳格な形式検査後、引数配列形式の `git cat-file` に渡す (`knowledge_manifest.py:186-206,409-444`)。本文は planner projection の data に入るだけである (`knowledge_manifest.py:490-506`)。proposal は closed schema、instruction-like anomaly、semantic 検査を経てから proposal data に射影される (`p3_s4_loop.py:1979-2004,2067-2093`)。

   成果物への影響: 新設 seam によって外部本文が job body の分岐、argv 構造、repository/evidence path 解決を変更する経路は増えない。

4. 既存契約テストの弱体化は refuted。

   現行 proposal pin `test_p3_s4_loop_job_contract.py:350-352` は、prebuild receipt と run-iteration の間へ array 展開を足した厳密な三行 pin に更新される。fixture pin `test_p3_s4_loop_job_contract.py:354-357`、fixture-before-prebuild 検査 `test_p3_s4_loop_job_contract.py:824-844`、driver 二起動検査 `test_p3_s4_loop_job_contract.py:427-434` は維持される。plan に期待値反転、部分一致化、skip、削除はない (`stage2-plan.md:137-183`)。

## nit / backlog

- argv 内の pair 順序固定は保守上の規約にはできるが、K2 正しさ防壁ではない。正しさ変異 matrix からは外し、flag と env の対応関係を壊す変異へ置き換えるべきである。
- empty-role 変異は「事前構築前に拒否する」タイミング防壁として名前を付け直すべきで、最終受理集合の防壁とは数えられない。
- empty-manifest 変異は `M=""、R/C/D unset、P nonempty` のように全 env vector を事前登録しない限り、後段完全性検査との帰属を分離できない。
- 抽出した K2 block の `bash -c` test は局所検査である。driver の manifest-without-role 負例を別途置かない限り、system-wide の identity/consumer 結合は証明されない。
- pytest は指定どおり実行していない。

## 総括

official Pegasus job body の env-to-argv seam に限れば、プランの all-or-none 条件は K2 identity と K2 consumer を正しく結合しており、本文を命令として扱う新経路もない。既存契約テストの弱体化も見当たらない。

ただし、このままでは承認できない。driver の manifest-only CLI が残るため、非 K2 proposal を K2 campaign identity で評価できる実 argv が存在する。また、プランが「早期拒否」と呼べるのは bundle 完全性だけで、深い K2 検査は事前構築後である。変異 matrix も 5 本全てを独立した正しさ防壁としては扱えない。最低限、driver の `--run-iteration` 入口で manifest と coder role の同時指定を fail-closed にし、変異候補を意味的に load-bearing なものへ再分類する必要がある。