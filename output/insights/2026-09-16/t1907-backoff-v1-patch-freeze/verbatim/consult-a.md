## 所見

以下、`brief.md`・`plan.md`・逐語資料・probe は、射影された `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1907-backoff-v1-patch-freeze/` 配下を指す。その他は parent worktree 相対パス。判定 `refuted` は、記載した疑義が静的点検で退けられた意味である。

- [A-1] brief の「再走による pin 破壊経路は既に閉じている」「止めている研究は無い」は probe の射程を超える。

  判定: real  
  深刻度: should-fix  
  根拠: `brief.md:3,18`。`probe_campaign_id.py:39–46` が比較するのは `config_for` と admission bind で作った3構成だけである。実走の `backoff_sweep.py:410–419` は runtime contract と `p2_2._campaign_cfg_for_site` を通す。後者の `p2_2.py:262–279` は Pegasus で `measurement_env` を search_config に追加するため、probe の3 IDを Pegasus 実走の IDとは扱えない。

  一方、通常 resume の拒否には独立した根拠がある。`ident.py:141` は旧 lock の admission 不一致を拒否し、`:373` は完全な preimage を照合する。`:484` は WAL repair より先に identity を確認する。したがって、probe の不完全さから通常経路の防壁不在を導くことも誤りである。

  ID比較は研究の依存関係を調べておらず、「止めている研究が無い」の証拠にはならない。また、report 系は別経路である。`backoff_sweep_report.py:58` は `replay.py:129–152` の prefix discovery を使い、IDを再計算せず既存 campaign を選ぶ。report 出力は同ファイル `:123–132`。ただし admission を通るため、これを旧3 campaign への書込み成功や WAL pin 破壊の実例とまでは認定していない。  
  成果物影響: この変更自体による値の変更はないが、README・insight に「旧 campaign 全体への変更経路が閉鎖済み」という誤った保証が残り得る。  
  提案: brief を「probe の3構成で旧 IDと不一致。現行 sweep/repro の通常 resume は lock 検査でも拒否される」に限定する。「停止中の研究は今回確認していない」と区別し、研究全体や別 driver の安全へ一般化しない。追加 probe・gate は不要。

- [A-2] F2 の生成日一括指定は誤りで、ホスト帰属と生成時 patch bytes も確定していない。

  判定: real  
  深刻度: should-fix  
  根拠: `brief.md:12` は旧3 WALを「2026-06-22 cygnus」で生成と断定する。read-heavy の `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/runs/wal.jsonl:1` は `ts=1782624851.233902`。`date -u -d @1782624851.233902` の出力は `2026-06-28 05:34:11 UTC`。同ファイルの `git log -1` も `2c59dc3d3 2026-06-28` を示す。先頭の `env_tag="linux-baremetal"` は cygnus というホスト名を証明しない。

  また、`git diff 476a128 f7a5444` は noinline、マーカー、定義漏れ拒否等の差を示す。式の一致だけで「旧 WALを生成した bytes」とは呼べない。`plan.md` P1 と `:144–148` はこの区別を既に行っている。  
  成果物影響: WALや台帳の値は変わらないが、保存版の由来説明が旧実験の生成 provenance と誤認される。  
  提案: plan の訂正を brief に反映する。保存版は「v2 導入直前の v1」と記し、cygnus 帰属は裏取りできる資料がなければ省く。

- [A-3] f7a5444 の選択は誤りで、476a128 を保存すべきという疑義は退けられる。

  判定: refuted  
  深刻度: should-fix  
  根拠: `verbatim-ruling-package-A2.md:4–10` は合成枝の v1→v2 変更に対する旧版保存を論点としている。D1281 も「v1 patch の別名凍結」を選ぶ。静的確認では、`git rev-parse 4dfd3785b^:patches/silo-backoff-fixed.patch` が `f7a54445764025112317151106712bb9d97678ab`。`git diff f7a5444 06d272b` は hole の式1行のみの変更だった。したがって f7a5444 は問題となった変更の直接の前像である。

  `git show f7a5444 | sha256sum` は `35237d314df708c6a6cb6fece0a8a59cd199bb57337013f95f6ed50ea2a2f911` と一致。476a128 は旧 sweep 生成期の候補として合理性があるが、今回の裁定がその時点の bytes を指定した証拠はない。  
  成果物影響: 476a128 に替えると、保存対象が v2 直前の骨格から、noinline・マーカー・定義漏れ拒否を含まない初版へ変わる。  
  提案: f7a5444 を採用する。用途は plan のとおり参照・明示的な再適用に限定し、旧実験の完全再現を保証しない。

- [A-4] consumer 再配線・新 pin が必須という疑義は退けられる。P4 も限定された文書補足なら scope 内である。

  判定: refuted  
  深刻度: should-fix  
  根拠: D1098 の理由には「旧消費者はそのまま動き、新版は別の名前で積み上がる」とある。しかし最新依頼は「対象は既存 v1 の保存に限定する」「本題の凍結だけ」で、追加 gate・検査・台帳・一般化を除外している。`plan.md:125` は今回が旧 consumer の自動的な v1 使用を実現しないことを明記する。この限定の下で、再配線・v3 改名・新 pin を要求する根拠は成立しない。

  P4 の `plan.md:135–146` は既存の resume 禁止を維持し、隣接する保存版の用途と現行通常経路の説明を補う。実行機構や検査の追加ではなく、由来・用途の説明に付随する範囲と判断する。ただし `brief.md:19` の「P3 実測と食い違うので」という説明は粗い。既存警告は旧 consumer／歴史的コードも含めれば矛盾とは限らない。  
  成果物影響: 再配線しないため現行 consumer の参照先は変わらず、保存版を追加しても旧 consumer が自動で v1 を使用することはない。  
  提案: 不足する実装は認めない。README は保存節を中心に、警告への補足を現行 sweep/repro の通常 resume に限定する。D1098 の理由全体を今回実現したとは報告しない。

- [A-5] `patches/` 直下への追加で正しさの受理集合が変わるという具体的経路は成立しない。

  判定: 成立しない  
  深刻度: should-fix  
  根拠: path 検索に加え `projection`、`allowlist`、`template`、`TEMPLATE_PATCH`、`patch_rel`、`EVOLVE_BLOCK` を検索した。P2 の主要な境界は次のコードで裏付けられる。

  | 経路 | 静的確認 |
  |---|---|
  | define 在庫 | `test_ccbench_spawn_sites.py:632–679` は追加ファイルを読む。`:2676–2689` は macro key の一致と登録 path の包含を要求する。固定された f7a5444 の追加から新 macro key は予測しない。 |
  | 裸 token 在庫 | `test_p3_s4_loop.py:7842–7878` は全文を読むが、保存 blob に該当する `IZANAGI_` token はない。 |
  | condition gate | `condition_meaning_gate.py:76,141,2191` は `DEFINE_SPECS` の固定 `patch_rel` を読む。新ファイルを自動登録しない。 |
  | source identity | `source_digest.py:85–100` は CCBench 内の固定ソースと allowlist。repo の patch 在庫ではない。 |
  | template／coder | `p3_s4_loop.py:128,743,1891,1903` は現行 template と適用後ソースを使う。保存版を自動選択しない。 |
  | projection | `projection_guard.py:200–219,395–409` は ledger の登録 entry・除外字面を使う。`patches/ledger.json:38` 以下の除外対象は rung1。 |
  | planner 入力 | P2 表に補足すべき `p3_s4_loop.py:1222–1247`、`knowledge_manifest.py:430–437,490–505` は明示された入力／commit・path の資料を射影する。直下追加による自動流入ではない。 |
  | ledger | `silo_ladder_rung1_contract.py:511–518` は registered entries と entry 数1を検査する。在庫追加とは別。 |
  | hook | `guard_write.py:58,315–334`、`guard_bash.py:81–90,2540–2565` の保護対象に通常の新 patch は該当しない。live 発火の証明ではない。 |
  | provenance | `check_ai_provenance.py:78–80,1589` により新 `.patch` は実装面になる。 |

  P2 表にない固定 template consumer として `backoff_requested_us.py:1062`、`b10_backoff_static_tail_formal.py:752`、`s8b_expected_materialization.py:792` も見つかった。いずれも既存定数経由であり、新ファイルの自動選択経路ではない。verifier／grammar についても追加を入力へ取り込む経路は見つからなかったが、全動的経路の不在を証明したものではない。  
  成果物影響: 在庫テストの走査対象と macro 供給元 path 集合は増える。certified 選択・台帳値・実行時受理集合の変更は確認できない。  
  提案: P2 の reader 表に上記の明示入力経路を補足する程度でよい。allowlist・gate・ledger の追加は不要。「無反応」は自動選択がない意味に限定する。

- [A-6] M1 を保存成果物の検出力として数えることはできないが、plan は既にその限界を記している。

  判定: refuted  
  深刻度: should-fix  
  根拠: `plan.md`「変異の事前登録候補」は M1 の拒否理由を未登録 `IZANAGI_` token としている。`test_p3_s4_loop.py:7847,7871–7878` はコメント中の token でも拒否し、保存版の式・由来・bytes 一致を検査しない。したがって M1 は新 path が既存在庫検査に入ることの確認であり、凍結の正しさの証拠ではない。

  plan は M2〜M5 の生存予測と bytes 比較を別の評価集合に分け、全受入層を含めた M1 の単一拒否も主張しない。この記述自体に過大主張は認めない。  
  成果物影響: M1 の kill だけを凍結保証に使うと、誤版・式改変・欠落・README の誤 SHA を見逃したまま完了と誤認し得る。  
  提案: M1 は「既存在庫 gate の適用確認」と記録する。M2〜M5 は未実行の間は `SURVIVED 予測` とし、実測結果へ格上げしない。保存時の blob／SHA／cmp 確認を別途記録し、新 pin は追加しない。

## 成立しなかった点検

- 明示的な旧 campaign directory 指定だけで、現行 `ensure_resumable_wal` の lock 照合を回避できるという反例は得られなかった。layout を指定しても identity 検査が先行する。
- report 再生成を WAL SHA pin 破壊の反例にはできなかった。report writer は存在するが WAL writer ではなく、さらに artifact admission を通る。旧3 campaign で書込みまで到達することは未確認。
- f7a5444 の追加により verifier・grammar・condition gate が緩む具体例は得られなかった。
- D1098 の文言だけから、最新の保存限定依頼に反して consumer 再配線や v3 改名を必須とする論拠は成立しなかった。
- P4 を一般化した安全機構の追加と見なす論拠は成立しなかった。限定的な文書補足として扱える。

## 未確認事項

- pytest・build・計測・patch 適用・mutation・hook live 発火は実行していない。テストの緑／赤は報告しない。
- 旧 WAL が実際に使用した patch bytes、cygnus へのホスト帰属、f7a5444 と生成期 patch の preprocess／binary／性能の一致は未確認。
- probe は再実行していない。提示された出力と実装、関連コードを静的に照合した。
- 全 reader の形式的な不在証明、外部利用者・任意の歴史的 driver の網羅、親の全128 worktree overlap 調査の再検証はしていない。
- 推測した `orchestrator/coder`・`planner`・`grammar`、`campaign/certified_view.py` 等は存在しなかった。実在する campaign 側実装へ探索を切り替えた。WAL も実在する `runs/wal.jsonl` を読み直した。必読射影ファイルはすべて読めた。

## 総括

**f7a5444 の別名1ファイル保存＋限定的な README 説明という実装方針を通してよい。実装を止める正しさ境界の欠陥は確認できなかった。**

修正対象は主に brief の証拠の扱いである。全破壊経路の閉鎖・研究停止なしという一般化、旧3 WAL の生成日・ホストの一括断定を訂正する。plan の保存用途の限定は維持し、M1 を凍結 bytes の検出力として数えない。consumer 再配線、新 pin、gate、ledger、追加の歴史版保存は要求しない。