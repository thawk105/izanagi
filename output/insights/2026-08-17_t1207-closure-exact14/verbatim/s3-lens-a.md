### A-01 / must-fix

- **主張:** exact 14 が保証できるのは指定 14 source file の時点別 byte 一致だけであり、「serializability verifier の実行同一性」や「無効化経路を塞いだ」とは名乗れない。

- **根拠:** `orchestrator/campaign/campaign_lock.py:27-42` は固定 tuple だけを列挙する一方、`docs/decisions.md:12385-12388` は「`in-process` 改変・`__pycache__`・動的生成コードは検出しない」「未束縛 bootstrap は `campaign_lock.py`、`contract_loader_binding.py`、Git executable、既ロードの Python state」と明記する。さらに `orchestrator/campaign/loop.py:26-29` で pipeline は import 済みになり、source 検査は同 file `:190-194` まで行われない。残存面の全分類は次のとおり。

  | 分類 | exact 14 外に残る面 |
  |---|---|
  | 現行 entry file | `orchestrator/verifier/cli.py`、`__main__.py`、`orchestrator/verify.py` |
  | bootstrap | `campaign_lock.py`、`contract_loader_binding.py`、PATH から選ぶ Git executable |
  | import 前コード | `orchestrator/__init__.py`、`orchestrator/campaign/__init__.py`、閉包外 driver |
  | runtime state | `sys.modules` 注入、`pipeline.verify_trace_dir` 等の global alias 差替え、既ロード code object |
  | import resolution | `sys.meta_path` / path hook、`.pth` / `sitecustomize`、優先順位を得た `PYTHONPATH` |
  | bytecode | `__pycache__` / `.pyc`。`.gitignore:2` も `__pycache__/` を除外している |
  | runtime dependency | CPython、`dataclasses`、`typing`、`glob`、`os`、`hashlib` 等の標準ライブラリ、OS |
  | 時間・sink・版 | fresh lock、検査後 TOCTOU、WAL 直書き、detached な旧 E1 |

  依存 runtime は exact repo-path 集合の「欠落 file」には数えなくてよいが、「verifier identity」を名乗る場合は root of trust として必ず除外を書くべきである。

  **名乗ってよい逐語:**

  > `require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が実際に完了した呼出しについて、各 path を検査が読み取ったそれぞれの時点の listed enforcement-source set exact 14 path の disk bytes は、その呼出しが authority に採用した `contract_loader_commit` の同 path Git blob と一致した。exact 12 から増えた保証は、後続の source 検査が `orchestrator/verifier/__init__.py` と `report.py` の記録後 drift も拒否することに限る。実行済み code object、module origin/import state/cache、fixed-list 外 module、CLI/wrapper、bootstrap/runtime、全 certified sink の支配、fresh lock、cross-version E1 は保証しない。

- **反例または検算:** 実行する code object の origin/digest、Python/Git runtime、import state を別の信頼根で認証し、かつ全 certified sink が gate receipt を必須にすれば、この境界指摘は落ちる。

- **成果物影響:** 同じ `campaign_verifier_epoch` のまま別 code object が走り、偽の `STAGE_COMMIT`、CLI 成功、または虚偽 report が生成され得る。

### A-02 / must-fix

- **主張:** fixed exact list は将来追加される verifier module を自動では束縛せず、`__init__.py` の一行変更を含む fresh lock 作成後は、その新 module だけの drift が同じ epoch で通る。

- **根拠:** `orchestrator/verifier/__init__.py:16-20` は package export を import 文だけで決め、`orchestrator/campaign/pipeline.py:31` はその export を取得する。一方 `campaign_lock.py:29-42` は静的な file list である。対照的に `orchestrator/campaign/silo_ladder_rung1.py:262-285` は `verifier.rglob("*.py")` を用い、`orchestrator/tests/test_silo_ladder_rung1_driver.py:927-957` が package 全 `.py` の coverage を固定している。

- **反例または検算:** 既存 lock の後に `__init__.py` だけを変更する M2 型は exact 14 が検出するため、単なる一行 post-lock 変更だけでは反例にならない。問題は「一行 import と新 module を commitして fresh lockを作る、その後は新 module だけを変える」場合である。package 全 file と closure の一致を検査する census test があれば落ちる。

- **成果物影響:** 新 module が判定や payload を変えても E1 と lock map が不変になり、certified 受理集合または診断参照が無記録で変わる。

### A-03 / must-fix

- **主張:** campaign 側の返り値握り潰しと sink bypass は exact 12 の時点から残る別問題であり、exact 14 はこの面を一つも減らさない。

- **根拠:** `pipeline.py:1133-1143` は `vr.certified` を唯一の棄却分岐にし、同 file `:1247-1255` はその後 `res.certified=True` として COMMIT へ進む。pipeline 自体は既に旧 12 path に含まれていた。さらに `wal.py:621-628` の `log()` は任意の既知 stage/payload を `append()` するだけで verifier receipt を要求しない。D268 も `docs/decisions.md:12381-12382` で「停止点は certified sink の支配点ではない」「pipeline.evaluate と低層 WAL writer は ident を通さずに書ける」と明記する。

- **反例または検算:** 全 `STAGE_COMMIT` producer が、verifier の判定と lock identity に暗号的または capability 的に結び付いた一回限りの receipt を必須とし、artifact admission がそれを再検証するなら落ちる。

- **成果物影響:** 閉包外 caller または in-process 差替えから commit record を作ると、`EvalState.committed`、fitness 候補、oracle 入力の受理集合が偽に広がる。

### A-04 / must-fix

- **主張:** 「弱化してから作る fresh lock」の穴は exact 14 でも完全に残り、減るのは `__init__.py` と `report.py` の記録後 source drift だけである。

- **根拠:** D442 `docs/decisions.md:18540-18542` は「検出するのは lock 記録後の drift だけ」「弱めて commit し、その bytes で新しい lock を作れば新 E1 として受理」と明記する。`contract_loader_binding.py:324-337` は current HEAD と disk の自己整合性を採り、`ident.py:469-484` はその値をそのまま新 lock に符号化する。検査後、`ident.py:488` の lock acquisition まで再検査もない。

  実際に減る面:

  - 未 commit の `__init__.py` / `report.py` drift を新規 lock 作成時に拒否する。
  - 既存 lock 後の両 file の committed / uncommitted disk drift を resume と certified admission で拒否する。
  - v2 authority に両 path の key/digest を必須化する。

  減らない面:

  - 弱い bytes を commitしてから作る fresh lock。
  - 検査後の in-process 差替え、import cache、TOCTOU。
  - fixed-list 外 module、bootstrap、CLI、sink dominance。
  - detached artifact の cross-version E1。

- **反例または検算:** 新 lock が「current commit」ではなく批准済み known-good digest/signature と比較されるなら fresh-lock 指摘は落ちる。

- **成果物影響:** 弱い実装が正規の新 E1を得て、certified 選択・oracle・台帳の全てで正常な epoch として扱われる。

### A-05 / must-fix

- **主張:** 親の M2 は dispatch identity の変化しか実証せず、M3 は rejection payload の一 field しか変えないため、brief §7 の「certified 選択の受理集合が変わる」は測定結果から導けない。

- **根拠:** M2 は brief `:50-62` で `parse_trace_dir` への alias だけを測るが、`parse.py:323-328` の関数は `expected_commits` を受けず tuple を返す。pipeline は `pipeline.py:1106-1109` でその keyword を必ず渡し、例外は `loop.py:316-337` で certified false の abort になる。M3 については `pipeline.py:1113-1133` が `vr.certified` を直接判定し、その後にだけ `result_to_dict` を `:1140-1143` で呼ぶ。brief 自身も `:77-80` では「判定反転ではなく payload 偽装」と正しく区別するが、`:107-111` で両者を受理集合変化へまとめ直している。`critic/digest.py:615-623` も abort payload の `certified` field を選択には使わない。

- **反例または検算:** M2 は同じ署名で赤 trace に対し必要属性を全て備えた偽 green object を返し、E2E で COMMIT まで到達すれば gate 無効化を実証できる。M3 は現行 consumer が abort 内 `verify.certified` を採否に用いる証拠が出れば受理集合への影響になる。

- **成果物影響:** 測定した M2 は abort/DoS、M3 は WAL abort payload と Layer3 診断の不整合だけを起こし、どちらも現状の certified 受理集合拡大を実証していない。

### A-06 / must-fix

- **主張:** 発火テスト案は exact 12 の挙動を negative control に含むが、wave 前の production rollback を変異空間に登録しておらず、binding mutant の期待 failed-node 集合もプラン内で矛盾している。

- **根拠:** plan `:97-103` は独立 exact 12 と byte replacement を定義し、`:114-121` は exact 12 で capture/live が通り exact 14 で両方が落ちる対を提案する。しかし preregistration `:169-170` は新 path を一つずつ除く exact 13 mutant だけで、両方を戻す wave 前 production exact 12 がない。また `:118` は各 parameter case で capture と live の双方を assertするとしながら、`:171-172` は live 弱化で init node だけ、capture 弱化で report node だけが落ちると登録する。同一構造の二 parameter はどちらも落ちるはずであり、singleton 集合は成立しない。F358 `docs/failures.md:8813-8829` も共通核と delta の誤帰属を禁止している。

  exact 12 へ戻しても緑のままの assert は、提案された以下である。

  - 旧 byte が一箇所、新 byte がゼロという replacement 前提。
  - exact 12 mode の `capture_contract_loader_binding()` が返ること。
  - exact 12 binding の `verify_live_contract_loader_binding()` が通ること。
  - mutation bytes 自体の変更。mutated module は importも実行もされない。

  exact 12 を kill するのは exact 14 側の二つの例外 assert、clean test の独立 14-key/order assert、旧 12 wire 拒否である。restore 元を test literal ではなく実 `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` に固定しなければ恒真化する。

- **反例または検算:** production tuple を両 path とも戻す複合 mutantを登録し、restore が production object を参照することを assertし、各 binding mutant の実 failed-node 完全集合を再計測すれば落ちる。

- **成果物影響:** 誤った mutation matrix は exact 12 rollback の生存または偽 KILLED を台帳へ記録し、防壁の proof reference を無効にする。

### A-07 / should-fix

- **主張:** 正しい exact 14 実装でも、新設 clean/paired test は Git と checkout normalization の環境要因で product assertion 前に赤になり得る。

- **根拠:** `test_t671_source_binding.py:40-58` は Git 不在、30 秒 timeout、非ゼロ終了を即 `pytest.fail` にする。`:74-86` は current bytes を copyして通常の `git add/commit` を使うが、production の `_run_git` は `contract_loader_binding.py:257-267` で global/system Git config を明示的に無効化しており、test helper は同じ隔離を持たない。さらに F357 `docs/failures.md:8794-8806` は閉包 member の commit 前走が共通 `contract-loader-drift` で偽赤になることを実証済みである。

- **反例または検算:** test Git を `core.autocrlf=false` と config 隔離付きで実行し、Git 不在/timeout を infra failure と product failure に分離し、閉包変更後の広域走を統合 commit 後だけ評価すれば落ちる。

- **成果物影響:** 正しい実装が受入赤または mutation survivor と誤記録され、landing と台帳の受理が不当に止まる。

### A-08 / must-fix

- **主張:** exact 14 が直接効くのは lock producer・live/committed validator・fresh oracle projection・accepted Layer3までで、detached oracle judge、historical Layer3、qualification は別裁定のままである。

- **根拠:**

  | 層 | exact 14 の実効 | scope 外 |
  |---|---|---|
  | lock 生成 | `ident.py:469-484` が 14-key map を v2へ記録 | fresh weak commit、検査後 drift |
  | resume/live 検証 | `ident.py:369-377` が現在 disk と記録 commitを照合 | identを通らない sink |
  | artifact admission | `artifact_admission.py:737-753` が記録 epochを導出し、`:775-797` が certified purposeで current mapと比較 | historical purpose は `:781-782` で currentを見ない |
  | oracle report | `s8b_oracle_report.py:357-413` が live gate結果を `certified_eligible` へ射影 | 保存済み observation の版同一性 |
  | oracle validator/judge | `s8b_oracle_artifacts.py:167-183` は scope を非空文字列、E1を形だけ検査し、`s8b_oracle_judge.py:235-246` は E1/eligibleだけを見る | exact 14 grammarの再認証 |
  | Layer3 | accepted path は `layer3_report.py:593-618` で certified viewを再取得 | historical pathは `:424-427`、schemaは scope非空だけ |
  | certified consumer | `layer3_report.py:542-546` は「consumerは存在しない」と明記 | final certified selection |
  | T126 qualification | `qualification/contract.py:60-75` は verifierでは `core.py` のみ | T-1209 |

  `test_s8b_oracle_judge.py:35-45` は任意の `E1:` digestと任意 scopeを eligibleにし、`:123-129` で `unique-best` まで選ぶため、T-1208 の穴は恒真でなく実到達している。

- **反例または検算:** judge が対象 campaign.lock を current exact14 grammarで再検証するか、署名済み observation に closure schema/versionを束縛すれば detached E1 指摘は落ちる。

- **成果物影響:** 旧定義または偽の E1 observation が `certified_eligible=true` のまま winner 集合へ入り、historical report も current drift を拒否せず記録値を表示する。

  裁定パッケージ候補は、T-1208 の exact scope/version gate、全 sink の verifier receipt、future module census、runtime/bootstrap trust、T-1209 qualification 追随である。

### A-09 / should-fix

- **主張:** 末尾 append の epoch 順序と sorted JSON の分析は正しいが、同じ `campaign-lock/v2` と epoch `/v1` で受理言語を置換する外部互換性は M1 から一般化できず、cross-version semantic pin が欠ける。

- **根拠:** epoch は `artifact_admission.py:742-746` で tuple 順に raw digest bytesを連結するため、13=`__init__.py`、14=`report.py` で新 E1になる。一方 wire は `campaign_lock.py:127-135` の `sort_keys=True` で並び、`:171-184` の exact key 比較により旧 exact 12 mapを拒否する。plan `:64-76` はこの差を正しく把握している。だが brief `:44-48` の測定対象は checkout の32本だけなのに「既存成果物は1件も壊れない」と一般化し、plan `:129-131` は外部保存・別 branch・削除済み artifactを未測定と正しく限定している。また `layer3_schema.json:62-66` は E1形と非空 scopeだけを pinする。

- **反例または検算:** 全保管場所を含む artifact inventory が exact12 v2/E1ゼロを証明するか、wire/schemaまたは epoch domainを版上げし、旧版を明示分類すれば互換性指摘は落ちる。

- **成果物影響:** 外部の旧 exact12 v2 lock は current decoderで拒否される一方、detached な旧 E1は judgeで受理され得て、lock受理集合とoracle受理集合が不一致になる。

  追加の固定 SHA pin は source/test 検索では見つからなかった。plan記載の動的 E1 fixture、旧12 wire拒否、scope逐語、件数14が主要 pinであり、Siloの既存 hashは対象2 fileの bytesを変更しないため更新不要である。

## 総括

最も危険なのは、source-byte exact 14を「実行コード同一性」または「無効化経路封鎖」と呼ぶ過大な名乗りである。  
親は M2/M3 の受理集合主張を撤回し、上記の限定逐語を新 D に採る必要がある。  
裁定へ返すべき中心は T-1208、全 sink receipt、future module census、bootstrap/runtime trust、T-1209 である。  
pytest/build は実行しておらず、緑とは報告しない。