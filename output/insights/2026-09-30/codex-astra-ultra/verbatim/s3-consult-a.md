### A-1 全履歴 fork の正例を、plan は不正 meta として拒否する

**重大度: must-fix**

**根拠:** `tools/codex_worker_launch.py:494` は `session_meta_count != 1` を拒否する。実物の `rollout-2026-09-30T16-01-00-01a0f11d-d7ed-7f23-9d9d-421c214778e6.jsonl` は、L1 が子の meta、L2 が複製された親の meta。L7 は親の context、L14 は子自身の context である。plan は identity 条件を変更するが、この複製構造を扱っていない。

さらに TUI 子 `rollout-2026-09-30T14-46-19-01a0f0d9-7a7e-7b82-b764-3856e4b3e37e.jsonl` では、L7 の複製 context が sol/xhigh、L22 の子自身が astra/ultra。全 context の同一性を要求すると、子自身が正しくても拒否する。

**放置時の成果物影響:** `fork_turns` 省略という通常の継承を受理できず、P1 の正例が成立しない。

**推奨の修正:** 子自身の identity と複製履歴を分離する。`subagent_history_start_ordinal`、`forked_from_id`、turn ID 等の実際の対応を確定し、履歴内 meta/context/spawn/完了イベントを現行子の証拠として数えない。単に「meta 複数可」へ緩めず、説明できない追加 meta は拒否する。online 検査・sealed 再検証・ledger に同じ境界を適用する。

### A-2 depth 1 の発見は可能だが、孫と別 job の分類規則が未確定

**重大度: must-fix**

**根拠:** L3 の子 `…01a0f109-a29d-72a2-908a-36d95c1786d5.jsonl:1` は、`id=子ID`、`session_id=rootID`、`source.subagent.thread_spawn.parent_thread_id=rootID`。plan の depth 1 条件は到達可能である。一方、`s2-parent-measurements.md:12` は孫未実測と明記する。plan の「全子孫の session_id は stdout root ID」という条件は depth 2 では未証明。

親の追加案である `task_name` と `agent_path` の照合も、`/root/probe` は nodeleg・maxthr1・maxdep0・forkall で重複しており、単独では job identity にならない。

**放置時の成果物影響:** 孫を見逃す、正常な孫を拒否する、別 job の子を誤帰属する可能性が残る。

**推奨の修正:** 受理規則を次のように固定する。

| ケース | 落とす先 |
|---|---|
| L3 と同じ同一設定の子 | 受理し、合算 |
| 自身の実行 context が別 model／effort の明示 override | 拒否し、観測済み消費は会計 |
| cwd 不一致、identity・parent 不整合 | 拒否 |
| 正当な depth 2 | 実物で形式を確定後、再帰的に受理・合算 |
| 同時刻・同 cwd・同 agent_path でも別 root の job | 当該 attempt の対象外 |
| 当該 root の spawn 証拠に対応するが identity が矛盾 | 無関係扱いせず拒否 |

spawn の call/result を `call_id` で対応付け、期待集合を **root identity＋直接の parent thread＋canonical agent_path** で管理する。孫についても各子の実行部分から再帰的に期待集合を作る。depth 2 の実物確認までは対応済みとしない。

### A-3 manifest V2 が「1 attempt＝1 session」を強制している

**重大度: must-fix**

**根拠:** `tools/codex_worker_launch.py:1284` の `_append_manifest()` は、同一 `(job_id, attempt_index)` の別 session を拒否する。`tools/codex_worker_ledger.py:360` も同じ重複を拒否する。plan は receipt V6 を提案するが、manifest V2 fixture に root・子・孫を追加するだけでは通らない。

**放置時の成果物影響:** 子を正しく発見しても、最初の子の manifest 登録で失敗する。

**推奨の修正:** manifest の新世代も設計対象に含め、root と delegated thread の表現・一意キー・親子関係を定義する。旧 V1/V2 の意味は維持する。B の所有範囲に manifest writer/validator、ledger と両テストを明記する。

receipt V6 では `tools/codex_worker_launch.py:4516,4598` の `modern` 判定や、`:4713` の evidence issue 再照合など、世代集合の全分岐を更新する。`collect_wave_usage.py:22` は Claude ledger の import であり、Codex schema consumer ではないという plan の判断は正しい。

### A-4 子の完了・再開・seal 後追記を閉じる条件が不足している

**重大度: must-fix**

**根拠:** L3 の子には `task_complete` が L26 と L42 にあり、L28 から再実行されている。最初の完了イベントだけでは子の終了を証明できない。現行は root process 終了で `tools/codex_worker_launch.py:2247` 付近から監視を抜ける。

また `:4690` は rollout の prefix seal を認め、追記を `rollout_grew` として記録するが、`:4793` は accepted のまま rc=0 を返す。plan の bounded grace と最終再走査だけでは、grace 後の子追記を閉じられない。

**放置時の成果物影響:** accepted receipt の確定後に子の追加 call/token が生じ、会計と上限判定が古いままになる。

**推奨の修正:** 期待する spawn と followup に対応する実行完了、全子孫の停止、最終 flush の条件を明文化する。root 終了後の行は期限内なら回収・再判定し、未完了なら拒否する。V6 の当該 attempt に属する seal 後追記を、単なる参考フラグで受理しない。停止・flush の保証が取れなければ、grace の経過を完全性の証明にしない。

### A-5 sandbox の上限照合が plan に存在しない

**重大度: must-fix**

**根拠:** `tools/codex_worker_launch.py:1518` の context 検査は model/effort のみ。plan が追加するのは cwd までで、`sandbox_policy` は検査対象になっていない。L3 の子自身の context は read-only だが、これはその probe の事実に限られる。

**放置時の成果物影響:** model・effort・cwd が一致すれば、root より広い sandbox の子も受理し得る。

**推奨の修正:** root の要求 sandbox と子自身の実効記録を照合する。read-only root に対する workspace-write／danger-full-access、欠落・未知 policy は拒否する。workspace-write は書込み root、network 等も含めて非拡張性を判断する。複製履歴の policy は A-1 の境界で除く。検査は事後検出であり、権限拡張そのものを防止する機構とは記述しない。

### A-6 guard の子への実効性は、現在の証拠では主張できない

**重大度: must-fix**

**根拠:** `hooks/README.md:115` は `SubagentStart` の子の書込み面を開いた面として明記する。`.codex/hooks.json:9,18` は配線の存在を示すが、子での発火を示さない。`s2-parent-measurements.md:13` にも子の guard 拒否記録なしとある。

**放置時の成果物影響:** 「子にも guard が効いた」という未確認事項を、依頼の必須実測を満たした成果として報告してしまう。

**推奨の修正:** 本 wave の記述は次に限定する。

> 指定 probe の root・子で read-only 記録と touch 拒否を観測した。root の guard 拒否は観測済み。委任子の PreToolUse guard 発火・継承は未確認であり、保証しない。

未観測は逸脱の証明でもない。原依頼の必須確認は未達として残し、受動観測がなかったことを成功扱いしない。guard 改修や代替運用の採用は別途裁定する。

### A-7 新検査の到達と単一理由性を示すテスト契約が足りない

**重大度: must-fix**

**根拠:** `orchestrator/tests/test_codex_worker_launch.py:1330` の既存 fake は root 型 meta と単純 context を生成する。これに子らしい値を足すだけでは、A-1 の履歴複製も A-3 の manifest 制約も検証できない。`docs/dev-wave/mutation.md:5` は到達不能・他層での拒否を kill と数えない契約である。

**放置時の成果物影響:** 子検査を削除しても緑、または別の不備で赤になるテストを「委任検査の証明」と誤認する。

**推奨の修正:** B のテストを、少なくとも次の独立 fixture として事前登録する。

- **L3 正例:** root stdout は root usage のみ。子発見数=1、子の検査済み context 数>0、receipt/manifest/ledger の消費が root＋子に一致。
- **fork 省略正例:** 親 meta/context を含む実物構造で accepted。
- **単独負例:** 子自身の effort、model、cwd、meta、sandbox をそれぞれ一項目だけ変更し、対応理由で拒否。
- **完全性:** 孫先着、別 job 同時出現、期待子欠落、root 終了後追記、followup 後の追加 usage。
- **consumer:** 子だけの消費で上限を超えるケースと sealed 再検証。

online と再検証が同じ拒否を重ねる場合、片方だけの変異は他方に mask される。共有判定部へ照準するか、冗長 gate と明記して両層変異を登録する。診断文字列の変化だけを kill にしない。

### A-8 予算見積もりは raw total と CLI-reported を分ける必要がある

**重大度: should**

**根拠:** `tools/codex_worker_launch.py:873` の定義は **input − cached_input + output**。`token-summary.txt` の `total` は、この上限の値ではない。

| probe | root＋子 calls | raw total | 上限対象 CLI-reported |
|---|---:|---:|---:|
| deleg1 | 10 | 149,544 | 10,664 |
| nodeleg | 4 | 57,667 | 5,187 |
| maxthr1 | 4 | 57,675 | 5,195 |
| forkall | 4 | 58,242 | 7,479 |

deleg1 は root のみなら 6 calls／6,023 tokens で、子を除外すると 4 calls／4,641 tokens を落とす。実 rollout の root duration は約53.3秒、forkall は約15.8秒。

**放置時の成果物影響:** 1,000,000 token 上限や週枠消費の評価を誤り、子込み予算の実効性を過大評価する。

**推奨の修正:** この小標本の平均が一定という仮定なら、100 calls 時点の CLI-reported は約10.7万〜18.7万で、call 上限が先に来る。ただし長い文脈では増えるため、本番容量の保証にはしない。

3600秒は並列子の時間を足すのではなく、同じ admission 時計で全子孫の監視・回収を覆う。call/token は観測後の停止なので、並列実行と flush 遅延による超過可能性は残る。週枠消費率はこれらの token 値から換算できず、実測値未取得とする。

### A-9 P4 は成立条件を明記しないと、古い起動器による実走になる

**重大度: must-fix**

**根拠:** `s1-brief.md:37` は段6を最初の ultra 起動器実走とする。`tools/dev_wave_codex.py:260` は **`--repo-root` 配下の launcher** を実行する。レビュー対象の木を prompt に書くだけでは、その木の launcher を使わない。

**放置時の成果物影響:** 古い effort 語彙で ultra が拒否されるか、P1 未実装の launcher による accepted を dogfood 成功と誤認する。

**推奨の修正:** 段5の A・B・ledger・manifest 対応を統合し、workers の ultra pin と整合した snapshot を確定してから、**その統合木を `--repo-root` に指定して**段6を起動する。受領証の authority commit/digest、実行 launcher の所在、委任数>0、子込み actuals を照合する。子が出なかった review は ultra 疎通の証拠にはなるが、P1 dogfood の証拠にはしない。

P4 の段順自体はこの条件で可能。docs だけ先に ultra に変える順序は不可。

### A-10 rulings の P2 は誤り。effort pin の plan は概ね追随している

**重大度: must-fix**

**根拠:** `.claude/commands/rulings.md:58` に reasoning 指定はなく、`tools/dev_wave_codex.py:218,285` は plan/consult の呼出側入力を必須として転送する。DW-S03 からの自動導出はない。

effort 側は、plan が挙げる `test_check_docs.py:8241,8427,8459,8482,8518,8859,8999,9025` 等の現行値・負例・decoy の追随箇所と、`test_dev_wave_launch_authority.py:70` の合成 fixture を確認できた。

**放置時の成果物影響:** docs pin が ultra でも、rulings の記述どおりの呼出しは起動不能になる。

**推奨の修正:** plan の提案どおり起動例へ `--reasoning ultra` と DW-S03 参照を追加する。plan/consult の転送正例も ultra で示す。

各 pin の旧 medium 負例は、置換が exact 1 件であることと、finding 集合が対象1件であることを確認する。合成 fixture の意図的な medium/high/low は維持する。

### A-11 supervisor digest の影響は「変わる」だけでは説明不足

**重大度: should**

**根拠:** `tools/dev_waves/daemon.py:179` は effort module の内容を hash する。`:1114,1211` の前後値が違えば、`tools/dev_waves/checker.py:626` が `CODE_DIRTY / supervisor-changed` を返す。brief の daemon 0件は観測時点の情報である。

Claude 側は `tools/dev_waves/cli.py:21`、`schema.py:16` が別定数 `CLAUDE_EFFORTS` を import するため、Codex tuple だけの追加で語彙が漏れる経路は見当たらない。

**放置時の成果物影響:** 稼働 supervisor のコード木へ変更すると、wave の完全性検査が赤になる。

**推奨の修正:** 変更を入れる木が稼働 daemon のコード所在かを設置直前に確認し、wave 前後比較を跨ぐ変更を避ける。digest 除外や期待値の固定更新は不要。`test_effort_levels.py:40` は Claude の厳密 tuple を維持し、Codex だけ ultra を追加する。

## scope 外の real 所見 (裁定パッケージ候補)

- **guard の委任子経路:** A-6 は既存の開いた面。配線変更を本 wave の達成済み事項に含めず、直接 probe と必要な運用判断を別パッケージにする。
- **model×effort の互換性:** `tools/dev_waves/effort_levels.py:7` 自身が要求語彙とモデル対応を分離している。ultra の追加は luna 等への適合保証にはならない。恒久対応は既存所有 T-183/T-184 の範囲。
- **P3 の外部 script:** 原本退避・Codex author 成果物の byte 一致設置という方式に明白な矛盾はない。ただし今回許可された参照範囲では外部 script の現物を独立照合しておらず、plan の行番号・差分・1800秒での疎通を確認済みとはしない。

## 総括

**現 plan のまま P1 を accepted 実装として進めるのは不可。** 実物から確定した大きな欠落は、全履歴 fork の複製 meta/context、manifest V2 の1 attempt・1 session 制約、sandbox 照合、子の最終完了と追記の扱いである。

depth 1 の発見可能性と root 単独 stdout usage は確認できた。孫の形式、子の guard 発火、週枠消費率は未確認。静的検査のみを行い、ファイル変更・テスト・新規実走・sub-agent 起動は行っていない。