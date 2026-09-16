## 総括

**現 plan のまま完了扱いにはできない。** 主な問題は、①T-585 の同一 wave 完了という裁定からの逸脱、②実 consumer の使用証拠を取る実行計画の不足、③親 brief が T-2625 の解決済み障害を現在の blocker と扱っている点である。

指定14資料は読取り可能だった。以下は静的読解の結果であり、編集・テスト・ジョブ投入は行っていない。repo 内の相対パスは指定 worktree 配下、`brief`・`plan`・`verbatim-*` は指定された射影資料を指す。

## 1. 親の実測の一般化

- **実測1：「system package が無い」は観測した configure の探索条件に限定される。** 一度の失敗から login 全体のインストール状態、別 host、将来の状態までは確定できない。ただし、当該 CCBench が module finder を使用する構造はコードから確認できる。  
  **根拠・影響：** `brief:23–25`、`external/ccbench/CMakeLists.txt:5,33–34`。一般化すると、材料レポートの環境条件を過大に断定し、別環境で成立した試行の解釈を誤る。

- **実測2：残骸 prefix の成功は、新経路の build 成功を証明しない。** finder は library と header を別々に探す。残骸の `.a` を発見できたことから、今回の pin・build option・install layout で両方が供給されるとは言えない。fresh prefix で両解決先を確認する必要がある。  
  **根拠・影響：** `brief:26–27`、`external/ccbench/cmake/Findgflags.cmake:5–18`、`Findglog.cmake:5–18`。放置すると、新調達物ではない library/header に依存した成功を材料レポートで受理する。

- **実測3・4・7：registry 件数、source の現存、DNS 成功は、その時刻・環境だけの観測。** registry の存在は計算ノードでの可視性を、HEAD 一致は専有・不変・全 dirty 検査の成立を、名前解決は HTTPS clone と pin checkout の成功を含意しない。  
  **根拠・影響：** `brief:28–33,40`、`verbatim-d200:34–39`、`tools/pegasus/fetch_third_party.py:154–165,501–505,572–583`。放置すると、未取得・未検証の source を「供給可能」として試行準備の受理集合へ含める。

- **実測5・6は環境観測と分けるべきである。** 5 の exact list 制約は同じコード・policy bytes なら成立する静的契約。6 の本数は検索対象・literal／動的参照・履歴コピーの扱いに依存する inventory である。  
  **根拠・影響：** `orchestrator/campaign/silo_ladder_rung1.py:875–930`、`fetch_third_party.py:82`、`plan:131`。本数を移行完了の根拠にすると、動的 consumer を落として機体固有参照を残す。

## 2. plan の file:line の実在

**指定された主要範囲・P3 S4 node ID に、存在しないものは見つからなかった。**

| plan の参照 | 照合結果 |
|---|---|
| fetch `540–602` | `_fetch` と一致 |
| hydrate `605–679` | `_hydrate` と一致 |
| verify `525–537` | `_verify_cache` と一致 |
| verify-deps `682–694` | `_verify_dependencies` と一致 |
| parser `697–715`、dispatch `723–751` | 一致 |
| P3 S4 `369–404` | policy の path/pin 読取りと一致 |
| P3 S4 `409–463,465` | 依存 build/install、prefix export と一致 |
| P3 S4 `539–549` | 実 prebuild 呼出しと一致 |

P3 S4 テストも次が実在する。

- `test_job_body_static_contract`：518行
- `test_static_contract_orders_all_job_stages`：558行
- `test_registered_fragment_mutants_have_one_static_failure`：783行
- 指定された5つの parameter ID：717、749、761、767、774行
- `test_commented_dependency_policy_field_is_rejected`：939行

**根拠・影響：** `plan:21–26,76–93` と上記実体。指定 node の不存在によって検査が空振りする問題は確認されなかった。ただし、静的な実在確認を pytest 成功とは扱っていない。

## 3. 互換層に当たるか

**`--include-build-deps` 単体は対象選択であり、直ちに互換層とは言えない。しかし plan 全体は旧供給経路を併存させる設計になっている。**

旧3依存の FetchContent 契約を維持すること自体には理由がある。一方、plan は旧絶対 path の `verify-deps`、floor 系などの live consumer、その受理挙動を維持したまま、gflags/glog の新経路を opt-in にする。同じ pin を参照しても、供給経路は二本残る。「fallback が無い」だけでは D1737 の二重経路という指摘を解消できない。

是正は、**同一 wave 内で gflags/glog の live consumer を共通調達出力へ付け替えること**。3依存と2依存の列挙は分けてよいが、旧 locator を選ぶ運用経路を温存するための入口にはしない。履歴 evidence の参照は変更しない。

**根拠・影響：** `plan:41–45,125–129,212`、`verbatim-d1737:28–29`、`fetch_third_party.py:682–694`。放置すると、同じ依存 pin の試行でも供給元・検証条件が異なり、材料レポートと試行台帳の参照が旧機体 path と hydrate 出力に分裂する。

## 4. 完了の下限は取れるか

**取得可能ではあるが、plan は必要な実行条件を詰めていない。**

実 P3 S4 consumer の使用証拠には計算ノードが必要である。job は `bnode` 以外を拒否し、現在の `.claude/worktrees/` 配下も拒否する。変更を含む固定 SHA の専用 checkout、clean 状態、外部 evidence directory、PBS allocation が必要になる。

さらに、この job は configure で終わらない。masstree target build を行ってから driver 本走へ進む。依存段だけでも timeout 上限は合計540秒、prebuild は configure／target 各900秒であり、3時間予約の充足も既存 README では未実測である。queue の現在の可用性・待ち時間は今回確認しておらず、wave 内完了は断定できない。

**根拠・影響：** `tools/pegasus/p3_s4_loop_pegasus.sh:5,17–28,116–119,214–226,433–463,539–549,581–594`、`tools/pegasus/README.md:368–386,400–408`。放置すると、「configure の成功」と「実 consumer 使用」「driver 完走」を混同し、失敗・未到達の試行を完了証拠として扱う。

既存テストは fragment と順序を守るが、実 build・scheduler 待ち・walltime 充足は証明しない。source の付け替えでは、単に旧 policy-field fragment を消すだけでなく、**新しい source-root の代入と、その値が configure に届くこと**を既存契約テスト内で検査する必要がある。

**根拠・影響：** `orchestrator/tests/test_p3_s4_loop_job_contract.py:318–360,522–559,783–791`。放置すると、新 source を使わない実装でも検査が緑になり、試行台帳の供給元説明と実体が食い違う。

login で fresh 依存を建て、実 CCBench を configure すれば、**同じ finder の局所的成功証拠**にはなる。ただし所定の build 実行経路を通す必要があり、P3 S4 job 使用の証拠にはならない。計算ノードを確保できない場合は、これを部分成果として残し、**P3 を黙って下げず、完了条件の変更を裁定へ返す**ことを推奨する。

**根拠・影響：** `plan:97–105,178`、`external/ccbench/CMakeLists.txt:33–34`、`p3_s4_loop_pegasus.sh:26–28`。局所証拠から計算ノード全体へ受理範囲を広げないことが必要である。

## 5. 裁定との距離 (T-585 同一 wave)

**反する。親 brief の scope 除外から修正が必要である。**

裁定の逐語は次のとおり。

> 「[T-585] (機体固有 path 結合の除去) と同じ面なので同一 wave で閉じる。」

これに対して brief は一括移行を scope 外とし、plan は残りを T-585 に残している。「1本だけでも consumer がある」は、この同一 wave 完了要求への回答になっていない。

反しない最小形は、本数を先に固定せず、**現在の live な機体固有 path 参照を列挙し、供給準備・consumer・対応テストまで同じ wave 内で付け替えること**。例えば `floor_campaign.sh:514`、`floor_scoping.sh:171`、`certify_calibration.sh:141` は現に旧値を読む。これを扱わないなら、T-548/T-585 完了を名乗る前に裁定変更が必要である。

**根拠・影響：** `verbatim-ruling-t548:11–12`、`brief:47–48,73–75`、`plan:5,125–126`。放置すると、certified 較正や floor の新規試行が旧 source path に依存し続け、成果物の参照面で裁定した構造変更が完了しない。

## 6. 研究前進の実効

**T-2625 は、引用された資料上では既に解決済みである。**

親 brief が引用する README は、失敗 job 998862 の後に **job 999363、bnode001、`overall=true`、59 checks、3 build case 完走**を記録している。依存不足も policy pin の source から build して解決したと明記されている。今回の研究前進は、未取得 artifact の取得ではなく、既存の成功手順から機体固有 source locator を除くことになる。

**根拠・影響：** `brief:5–12`、`output/insights/2026-09-15_t2625-sealed-snapshot-qualification/README.md:11–18,63–69`。放置すると、既存成功 artifact を欠落扱いし、新 wave の材料レポートに誤った因果・達成記録を残す。

段4 loop についても、供給 prologue は既に存在する。今回の変更で除去できるのは、その入力の機体固有 path 結合である。以後の依存 build、masstree target、attestation、driver、walltime の成立は別途確認が必要。既存 WAL に同じ候補の terminal record があれば、driver は build 前に skip するため、「receipt を渡した」だけでも不十分である。

**根拠・影響：** `p3_s4_loop_pegasus.sh:409–465,539–549`、`tools/pegasus/README.md:394–408`。放置すると、試行台帳で skip・未到達の候補を新調達経路の実使用例と誤認する。

「誰も使わない」risk は、1本の結線でコード上は減る。しかし opt-in hydrate を実施せず既存3 source の root を渡せば、新 consumer は依存不在で停止する。準備手順の更新と実投入証拠まで揃える必要がある。

**根拠・影響：** `plan:41,82,99–103`、`tools/pegasus/README.md:305–308,369–370`。放置すると、新経路は到達可能でも研究試行を一件も前進させない。

## 7. 所有範囲と並列分割

**「密結合なので素集合に割れない」という説明は成立しない。**

plan 自身の編集集合は、入口仕様を確定すれば次に分けられる。

| 単位 | 所有ファイル |
|---|---|
| 調達 | policy、fetch、fetch テスト、golden |
| consumer | P3 S4 job、P3 S4 契約テスト |
| 統合 | README、実行証拠の整理 |

source-root 配置と pin の読取り契約を先に固定すれば、前二者の編集 path は重ならない。さらに親 brief が密結合の理由に挙げる `silo_ladder_rung1.py` は、plan では変更不要である。同一 wave と単一実装単位も同義ではない。

**根拠：** `brief:82–86`、`plan:109–133`。成果物の値・受理集合への直接影響は示せないため、これは実装分担上の **nit**。単一担当を選ぶこと自体は誤りではない。

## 8. 攻めたが壊れなかったもの

- **既存3依存の exact 列挙をそのまま5依存へ広げられない点。** 名前集合と CMake literal 同期が実在する。  
  **根拠・影響：** `silo_ladder_rung1.py:875–930`。既存の受理契約を弱めず、2依存の列挙を分離する判断には根拠がある。

- **cache 取得と offline hydrate の実装上の分離。** HTTPS clone、file-only clone、no-hardlinks、HEAD・dirty・origin 検証が存在する。  
  **根拠・影響：** `fetch_third_party.py:388–425,572–583,633–679`。新2依存にも適用すれば、pin 不一致 source を拒否する既存の受理条件を利用できる。ただし実取得成功は未確認。

- **現行 policy hash と歴史 evidence binding の分離。** plan が挙げる2 node と golden は実在する。  
  **根拠・影響：** `test_t126_pegasus_tools.py:1490–1499`、`test_silo_ladder_rung1_evidence.py:1263–1278`、`pegasus_policy_expected_goldens.py:5–10`。歴史的な certified 証拠の参照を書き換える必要はない。

## 9. nit

- `plan:220` は親の「現行3命令」を訂正しているが、指定 brief にその記述はない。`brief:34` の「3依存」との混同が疑われる。
- README 更新箇所は `plan:119` の範囲だけでは足りない。旧 locator と3 source を説明する `tools/pegasus/README.md:336–346` も対象になる。
- finder は library/header の cache 変数を最後に消すため、証拠採取を終了後の `CMakeCache.txt` だけに頼れない。`plan:102` の確認には configure 時の探索ログ等、実際の解決先が残る採取方法を指定する必要がある。根拠：両 `Find*.cmake:23–24`。