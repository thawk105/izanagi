## 所見台帳

### 1. BLOCKER — `P6Derived` の禁止集合に実 consumer がない

対象: [s2-plan.md:70–76](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:70)、[s2-plan.md:84–97](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:84)、P6 README [§3.9](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:337)・[§4](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:452)

構成的実証: SC-05/C-01 が検査するのは `forbidden_candidate_keys={k0,k1}` と `marginal_keys={k1}` を返すことだけである。SC-08/C-12 は exact cut の先行 append と「禁止外候補にも verifier を走らせること」を検査するが、`k1` を次 candidate admission に投入して実際に拒否されることは検査しない。したがって generalized-cut enforcer と admission 結線を完全に削除しても、handler が期待集合を返せば全ケースを通せる。元設計は `P6_PENDING` による admission 閉鎖を要求し、enforcer を未実装面として明記している。

影響: 受理集合を1点も変えない「計算結果を返すだけの P6」を実装済みと認定できる。

### 2. BLOCKER — 初回発火イベントが定義されていない

対象: [s2-plan.md:41–60](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:41)、[s2-plan.md:80–99](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:80)、[s2-plan.md:206–218](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:206)、[D150 (6)(c)](/work/1/SFC/tanab/izanagi/docs/decisions.md:7446)

構成的実証: 今日あるのは field 形状、raw counter、非 candidate failure の C-09 までである。candidate-bound 正例、3種の構造化 IntegrityWitness、hypothesis、matrix、calibration fixture、mutation harness はすべて将来所有である。一方、実装 land、cap-lift 申請、revision 変更のどのイベントが誰に独立検査を起動させるか、申請 package や起動 command はない。D150 自身も cap-lift 申請 artifact と入力 field が0件とする。欠損時の「承認保留」は [s2-plan.md:172](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:172) にあるが、保留から初回認定へ遷移する経路はない。

影響: 安全に停止はするが、将来実装が揃っても自動にも規範上にも認定手続が発火しない。

### 3. BLOCKER — T-434 境界が未定義の双方向依存を作る

対象: [s2-plan.md:74–76](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:74)、[s2-plan.md:96](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:96)、[s2-plan.md:186](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:186)、[s2-plan.md:208–213](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:208)、[worklog.md:1557–1561](/work/1/SFC/tanab/izanagi/docs/worklog.md:1557)

構成的実証: SC-09/C-11 は `claim` 値と per-run 束縛 artifact を入力に必要とするが、その定義を T-434 へ送っている。逆に T-434 の receipt は P1〜P10 status、裁定参照、witness hash を収容するため、T-433 の認定結果を必要とする。ところが T-433 は認定結果の名前、永続 artifact、authority、hash 対象を定義せず、status field 新設も禁止する。検査者が全項目 PASS と結論しても、その結論を receipt producer が読む境界がない。

影響: T-434 は人間の PASS 宣言を無検証で信じるか、P6 status を生成できず停止するかの二択になる。

### 4. BLOCKER — V1 の「run」が判定可能な単位になっていない

対象: [s2-plan.md:174–188](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:174)、[s2-plan.md:96](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:96)、[V1 原案](/work/1/SFC/tanab/izanagi/output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md:103)

構成的実証: revision・origin・運転構成が同じ run は複数存在し得るが、`run_id`、campaign、cap-lift 申請、generation allowance との量化関係がない。「任意の1 run が `NOT_CLAIMED` なら免責」と読めば shadow run を1本作るだけで global cap を開ける。「当該 run に allowance を与えない」とだけ読めば `NOT_CLAIMED` は cap-lift 判定へ何も寄与せず、免責経路が再び死ぬ。「全 run」を要求すれば1本の非主張 run が全体を人質にする。

影響: 択 (a) は同じ入力集合に対して許可・不許可の両方を導けるため、裁定案として未定義である。

### 5. MAJOR — 認定失効を検知する主体と証拠がない

対象: [s2-plan.md:27–32](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:27)、[s2-plan.md:155–161](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:155)、[s2-plan.md:184–188](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:184)

構成的実証: 対象 revision の fresh checkout で検査するとは書くが、認定済み revision、契約版、fixture、mutation 定義、toolchain/environment を束縛した認定 artifact がない。revision A の認定後に adapter や corpus が B へ変わっても、旧認定を読む consumerも、差分を検知して再認定を要求するイベントもない。「別 revision へ持ち越さない」は人間の記憶にだけ依存する。

影響: stale な PASS の再利用と、毎回ゼロから結論を作る運用の双方を防げない。

### 6. MAJOR — 変異対応表を実装者が自己成就させられる

対象: [brief.md:68–69](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:68)、[s2-plan.md:113–133](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:113)、[s2-plan.md:198–209](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:198)

構成的実証: fixture と mutation harness は同じ将来実装 wave の所有で、実装前 freeze、独立作成、hash pin の順序がない。SC-08 は2義務に対し `または` で一方の変異だけを許す。SC-10 は P6 実装でなく検査手続の仮想変異、SC-11 は表の行削除を表の完全性検査で落とす自己参照である。また冗長な二重実装では片方を除く変異が生存し、P3 の規則どおりなら必要条項そのものが削除される。

影響: 弱い変異とそれ専用 fixture を選んだ出来レースが KILLED 11/11 を生成できる。

### 7. MAJOR — 独立検査者の独立性が監査不能である

対象: [s2-plan.md:135–172](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:135)、[.codex/agents/README.md:12–19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t433-p6-contract/.codex/agents/README.md:12)、[同:35–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t433-p6-contract/.codex/agents/README.md:35)

構成的実証: fresh context 自体はサブスク login の別 session で作れるが、プランは thread/session ID、入力投影、prompt digest、tool inventory、申請者 workspace 非継承の attestation を成果物にしない。現行 Codex role runtime は active 0 / blocked 13 であり、generic child の名前や自然言語の自己申告は隔離証拠に数えないという既存規律がある。SC-10 はこの不足を人間 gate と呼ぶだけである。

影響: 実装者が同じ context で reviewer を名乗っても、契約上それを反証する証拠が残らない。

### 8. MAJOR — 検査の実行場所・runner・失敗分類が運用へ落ちていない

対象: [s2-plan.md:155–172](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:155)、[Pegasus runbook §7.0](/work/1/SFC/tanab/izanagi/docs/pegasus-runbook.md:361)、[brief.md:56–59](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:56)、[AGENTS.md:31–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t433-p6-contract/AGENTS.md:31)

構成的実証: fresh checkout ごとの12系統 calibration、11個の変異、統合 case は build/test を伴うが、command、mutation checkout の所有者、計算ノード dispatch、工数上限、timeout/retry、infrastructure failure と mutant survival の区別がない。Pegasus で自動 dispatch される exact task は tests/provenance のみで、未分類処理は停止が規範である。さらに brief の「docs 影響テスト (login node)」は、Pegasus login で単一 pytest も禁止する入口規律と矛盾する。

影響: transient な計算資源障害まで永久保留へ畳まれ、同じ手続を別検査者が再現できない。

### 9. MAJOR — DW-G05 が機械受理集合と規範受理集合を混同する

対象: [brief.md:48–52](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:48)、[s2-plan.md:174–188](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:174)、[D150:7480–7483](/work/1/SFC/tanab/izanagi/docs/decisions.md:7480)

構成的実証: コード差分ゼロなので現在の production／機械受理集合が不変なのは正しい。しかし契約採用は「基準不在なら常に保留」だった人間 cap-lift gateに新しい合格経路を作り、V1 は `NOT_CLAIMED` の免責範囲を変更する。D150 は同型の変更について、機械受理集合は不変でも規範上の受理集合は変わると明示的に分離している。brief の「受理集合・参照は不変」はこの限定を欠く。

影響: normative cap-lift 境界を変える設計判断が「影響なし」として記録される。

### 10. MINOR — 「機械検査できる」が実装・結線済みと区別されていない

対象: [brief.md:26–34](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:26)、[brief.md:63–64](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:63)、[s2-plan.md:64–76](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/s2-plan.md:64)、[P6 README §3.12](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:428)

構成的実証: SC-01/SC-05 は checker も入力 artifact も無いまま「機械検査できる」と分類される。これは純粋な判定可能性にすぎない。親の4識別子・2 Python subtree の0-hitも文字列不在の証拠であり、producer/consumer/発火路の完全 inventory ではない。

影響: 「原理的に判定可能」が「現在作動する control」と誤読され、BLOCKER 1〜3を見えにくくする。

## 総括

- 判定: **NO-GO**
- 件数: **BLOCKER 4 / MAJOR 5 / MINOR 1**
- 最重要所見は **#1**。禁止集合を返すだけで実 admission に作用しない実装が、契約を通過できる。
- 欠損時の承認保留は明記されているが、発火・consumer・失効検知がないため安全に停止するだけである。
- P6 本体が現在未実装であること自体は既知事項として件数に含めていない。