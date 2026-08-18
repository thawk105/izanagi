### [A-1] real — 主張する時間窓が実装より広い

根拠: driver の終了点は terminal WAL 後の return であり、report は別 CLI であるため、差し替え可能な実時間窓は存在する。[s8b_oracle_driver.py:1742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_driver.py:1742) [s8b_oracle_driver.py:1820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_driver.py:1820)

ただし検査が保証する終点は「各 store を読んだ瞬間」であり、「report 生成まで」ではない。読み取り後にも observations の組み立てと create-only write が残る。[s8b_oracle_report.py:1959](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_report.py:1959) [s8b_oracle_report.py:2014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_report.py:2014) brief の「実走終了後から report 生成まで」「置換されていない」は連続不変性に読める。[brief.md:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/brief.md:12) [brief.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/brief.md:47)

修正案: 主張を「report が各 store を読んだ時点で期待 SHA と一致した」に限定する。一時改変後に復元された場合や、読み取り後の差し替えは検出しないと明記する。

成果物影響: 永続的な実走後改変は oracle と combined verdict を indeterminate にするが、一時改変または読み取り後改変では受理集合が変わらず、証拠鎖の説明だけが事実より強くなる。

### [A-2] real、land blocker — M10 の mutation killer は発火しない

根拠: resolver は絶対パスと `..` を字句段階で拒否してから resolve containment を行う設計である。[s2-plan.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:10) 一方、予定された負例は絶対パスと parent traversal だけである。[s2-plan.md:147](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:147) したがって containment を削る M10 でも両テストは字句検査で赤になり、mutation は生存する。[s2-plan.md:168](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:168)

修正案: out_root 内の親 symlink と leaf symlink が外部へ出る二つの負例を追加し、containment 削除時だけ成功側へ転ぶことを確認する。

成果物影響: containment が骨抜きでも suite が緑になり、外部ファイルの SHA が一致すれば report の `store_reverification.state` が誤って `verified` となる。

### [A-3] real、land blocker — resolve containment だけでは TOCTOU を閉じない

根拠: 現行 `_store_sha256` は絶対パスを許し、symlink を follow し、regular file を確認せず、`read_bytes()` で全体を一括確保する。[s8b_oracle_driver.py:837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_driver.py:837) `resolve()` 後に通常の open を行う実装では、その間の symlink 差し替えを防げない。巨大ファイルはメモリを消費し、FIFOやdevice等は停止要因になる。

修正案: 既にある no-follow 読み取り方式と同様、保持した root fd から各 component を `O_NOFOLLOW` で開き、leaf を `fstat` で regular file と確認し、チャンク単位で hash する。[s8b_ratified_freeze.py:1598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_ratified_freeze.py:1598) driver の既存 helper 強化は report 実装とは分けた裁定パッケージにするべきである。

成果物影響: race では外部または別 inode の内容を `verified` と記録でき、巨大・特殊ファイルでは report と台帳参照の生成自体が停止する。

### [A-4] real、land blocker — 空集合、部分集合、外側 state の恒真性検査が不足

根拠: plan は non-empty と outer state 再導出を要求するが、具体的な負例は authority の missing/extra、絶対/parent path、receipt の extra cell までである。[s2-plan.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:34) [s2-plan.md:142](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:142) receipt 自体の `{}`、`cells=[]`、予定 cell の一件欠落、重複 cell、outer/cell の矛盾は明示されていない。全 receipt 欠落の C は部分集合比較を検査しない。

必須負例:

- 空 mapping、空 `cells`
- schedule の一件だけを receipt から削除
- cell 重複
- outer=`verified` かつ cell=`mismatch`
- outer=`unverified` かつ全 cell=`match`
- `mismatch` なのに expected=actual
- `missing` なのに actual が非 null

成果物影響: equality、non-empty、state 再導出のいずれかが欠けても forged receipt が determinate となり、oracle および combined verdict の受理集合が広がる。

### [A-5] real、scope限定 — `ReverifiedFreeze` は権威値だが権威トークンではない

根拠: `ReverifiedFreeze` は通常の公開 dataclass で、説明にも forgery resistance を提供しないと明記される。[s8b_ratified_freeze.py:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_ratified_freeze.py:798) plan 自身も `dataclasses.replace` による偽 token をテストへ渡す。[s2-plan.md:153](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:153) exact type check は raw mapping の事故を防ぐが、期待 SHA の自己申告を防がない。

公式 CLI は `reverify_published_freeze` の返り値を直接渡すので現行 trust boundary 内では安全である。対処は、型を seal するか、「certifying path は公式 main の直接配線のみ」と明文化して call-site を静的に pin するかの裁定が必要。

成果物影響: 新しい直接 caller が constructed/replaced token を渡すと expected=actual の自己証明 receipt を作れ、report と oracle の受理集合が不正に広がる。

### [A-6] real、既知の非目標 — judge は receipt を freeze に再結合できない

根拠: `judge_oracle` の API は observations、verified manifest、schedule projection だけで、`ReverifiedFreeze` を受け取らない。[s8b_oracle_judge.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_judge.py:313) CLI は freeze を再検証するが、その token は receipt の expected SHA/path と比較されない。[s8b_oracle_judge.py:575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_judge.py:575) observations loader も schema marker に過ぎない。[s8b_oracle_artifacts.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_artifacts.py:264)

これは T-1103 見送りと整合するが、receipt を「封印」「report 後にも独立再検証可能」と説明してはならない。[phase3.md:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/docs/phase3.md:688)

成果物影響: oracle 生成前に observations の expected/actual/state を自己整合的に改変すると determinate oracle を作れ、生成後は observations と oracle の組を同時改変すると再検証を通せる。

### [A-7] real、land blocker — M1 の CLI wiring test が欠落 receipt のまま通り得る

根拠: 現行 CLI test は reverify/manifest verify と rc/output を確認するだけで、`build_observations` に同一 token が渡ったことや receipt が `verified` であることを確認しない。[test_s8b_oracle_report.py:1456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/tests/test_s8b_oracle_report.py:1456) また test の `--output-root` は `root/report-output` で、driver fixture の store root と一致しない。plan が M1 の killer とするには条件不足である。[s2-plan.md:159](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:159)

修正案: 正しい store root で全 cell が `match` となる CLI baselineを作り、出力 receipt の exact contentを検査する。併せて spy で reverify の返り値と build に渡った object identity を固定する。

成果物影響: main が token を捨てる実装へ戻っても report CLI は成功し、全公式 report が receipt 欠落となって judge の受理集合を空にする過剰拒否を検出できない。

### [A-8] real — M7 は acceptance mutation ではない

根拠: receipt failure が `top_reasons` に入れば、configuration 集約から除いても `unknown = bool(top_reasons)` により各 holdout は既に indeterminate になる。[s8b_oracle_judge.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_judge.py:515) overall も同じ理由で indeterminate となる。[s8b_oracle_judge.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_judge.py:541) したがって plan の M7 は nested configuration evidence の検査であり、受理ゲートの mutation ではない。[s2-plan.md:165](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:165)

成果物影響: M7 生存時に configuration status、median、理由参照は変わるが、top-level oracle status と combined verdict の受理集合は変わらない。

### [A-9] real、scope package — combined verdict の負例が不足し、「certified 選択・台帳」への効果は未実在

根拠: combined verdict は oracle を再 judge し、holdout が `unique-best` でなければ floor 条件を成立させないので、production 変更なしでも receipt failure は伝播する。[s8b_verdict.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_verdict.py:247) [s8b_verdict.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_verdict.py:763) しかし plan は verdict fixture に正常 receipt を足すだけで、欠落・mismatch の end-to-end propagation を固定しない。[s2-plan.md:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1086-report-receipt/s2-plan.md:22)

一方、現 checkout には certified-selection consumer が存在しないと明記される。[layer3_report.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/layer3_report.py:576) `s8b_oracle_n_pilot` も非権威で certified/floor/oracle/n decision input ではない。[s8b_oracle_n_pilot.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_n_pilot.py:2)

裁定パッケージ候補: verdict に receipt 欠落/mismatch の負 E2E を追加する。n-pilot は scope 外のままにする。将来の certified-selection consumer や台帳記録への接続は別タスクとし、本 wave の成果として主張しない。

成果物影響: 現在変わるのは observations report、oracle verdict、combined verdict であり、certified 選択値や台帳行は現 checkout では変化しない。

### [A-10] 疑いは反証 — legacy manifest は黙って緑にならない

根拠: legacy report が receipt を持たない設計でも、judge は `manifest_kind != "official"` を top reason とし、各 holdout と overall を indeterminate にする。[s8b_oracle_judge.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_judge.py:334) [s8b_oracle_judge.py:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_oracle_judge.py:515)

成果物影響: legacy 経路は受理集合を広げず、公式判定から除外されたままである。

### [A-11] 疑いは反証 — 公式経路の期待 SHA は run/WAL から独立している

根拠: `reverify_published_freeze` は historical contract を使って launch validation を再実行する。[s8b_ratified_freeze.py:3462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3462) そこで G/H、worktree、manifest/result/journal を再取得し、result の binaries と manifest の binaries を一致検査してから deep-frozen mapping を返す。[s8b_ratified_freeze.py:3078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3078) [s8b_ratified_freeze.py:3151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3151) [s8b_ratified_freeze.py:3341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1086-report-receipt/orchestrator/campaign/s8b_ratified_freeze.py:3341)

ただしここで再検証するのは凍結文書と admission receipt の結合であり、`store_path` の現在 bytes は読まない。その空白を今回の receipt が埋める。

成果物影響: 権威源の独立性には修正不要だが、今回の実ファイル読み取りを省くと凍結後の store 置換が report と oracle の受理集合へ反映されない。

## 総括

- 静的レビューのみ実施し、指示どおり pytest は実走していない。
- land blocker は A-2、A-3、A-4、A-7。
- 期待 SHA の公式な出所は WAL/run から独立しており、この点は成立している。
- 実在する保証は「report の各読み取り時点で一致した」であり、連続不変性ではない。
- receipt は observations の封印でも第三者向け証明でもない。
- 空・部分 receipt、重複、outer/cell 矛盾の負例を追加しない限り恒真性を排除できない。
- path 検査には symlink mutation killer と fd-based no-follow 読み取りが必要。
- combined verdict への論理的伝播は既存実装で成立するが、負 E2E を追加すべきである。
- n-pilot は非権威なので scope 外が正しい。
- 現 checkout では certified 選択 consumer と台帳更新は存在せず、その効果を本 wave の成果として主張してはならない。