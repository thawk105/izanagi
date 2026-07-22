# 方向性監査 (2026-07-22) — 敵対的方向性監査逐語 (codex)

実行: codex exec, model=gpt-5.6-sol, reasoning=high, sandbox=read-only。親 = claude-fable-5 (background job)。
監査の統合と裁定パッケージは `2026-07-22_direction-audit-recovery-plan.md`。

## プロンプト (逐語)

```text
あなたは izanagi プロジェクト (workload 特化の並行性制御を AI が合成・選択する研究システム) の
開発方向を監査する、率直で敵対的な外部レビュアーである。リポジトリは読み取り専用で自由に調べて
よい。出力はすべて日本語。忖度は不要。

# 背景
ユーザー (プロジェクトオーナー) の懸念: 「開発が正しい方向に進んでいるか疑わしい。石橋を叩いて
渡るでいうなら、ずっと叩いてて渡ってないような」。

# 読むべきもの (必要に応じて広げてよい)
- docs/roadmap.md §1 (究極のゴール)・§2 (三層)・§9 (Phase 計画)
- docs/phase3.md の「現行チェックポイント」と後続段 8b・9 (層3)
- docs/worklog.md の 2026-07-16 以降の全エントリ
- git log --oneline -120
- docs/decisions.md の D70 以降 (grep -n "^## D7" docs/decisions.md で位置特定)
- output/insights/ の 2026-07-20 以降のファイル名一覧 (中身は必要なものだけ)
- docs/failures.md の F 番号一覧 (防壁投資の正当化根拠として)

# 問い (すべてに answer せよ)

1. **方向整合**: 直近 1 週間の作業は、roadmap が定めた研究主経路 (8b workload descriptor + 層3
   材料レポートの最小 E2E) を前進させたか。それとも主経路の手前で別の何かが自己増殖しているか。

2. **プロセスの再帰的自己強化の検出**: 「プロセスがプロセスを生む」証拠を具体的に挙げよ。例えば:
   dev-wave が dev-wave の作法を追記し続ける、freeze 設計のための freeze 設計、裁定が新たな裁定
   パッケージを生む、T-xxx backlog が消化より速く増える、WAL の堅牢化が WAL の別の堅牢化を呼ぶ、
   など。各証拠に日付・commit・ファイルを付けよ。増殖率 (新規発生 vs 消化) を見積もれ。

3. **防壁投資の弁護側評価**: この防壁・freeze・裁定投資は、過去の実障害 (docs/failures.md の F 番号、
   reward hacking・偽 faster・偽緑の実例) にどの程度正当化されるか。「必要だった防壁」と「過剰品質・
   本線を止めてまでやることではなかったもの」を分けて評価せよ。判断基準も示せ。

4. **機会費用**: 07-16 (S' 確定) から今日までの約 6 日間、もし防壁・プロセス投資を最小限にして
   本線 (floor 実測 → v2 候補生成 → oracle 実走 → 層3 レポート) を走らせていたら、今頃どこまで
   到達できていたと見積もるか。

5. **最短経路の提案**: ここから最短で「8b oracle 実走 + 層3 実レポート」という科学的成果に到達する
   経路を具体的に描け。現在の backlog (worklog 末尾の次の一手) のうち、削れる・延期できる・
   本線と並行でよいものを名指しせよ。T-080 W-0→W-f を全部やってから floor 実測、という現在の
   計画が本当に必要かも検討せよ。

6. **総合判定**: 「方向は正しいが速度配分が誤っている」「方向自体が逸れている」「懸念は誤りで
   健全」のどれに近いか。severity 付きの所見リスト (最大 10 件) で締めよ。

出力: 構造化 markdown。各所見に根拠 (ファイル・日付・commit) を付けよ。
```

## 出力 (逐語)

# 外部監査結論

**総合判定は「方向は正しいが、速度配分が重大に誤っている」に最も近い。severity: High。**

研究主経路そのものは間違っていない。7月16日には workload descriptor、selector、oracle driver、層3 renderer の骨格まで相当に前進している。しかし7月20日以降、実験を成立させるための防壁が、**開発プロセス・裁定・freeze の恒久制度を作ること自体**へ目的化した。

オーナーの「橋を叩き続けて渡っていない」という懸念は正しい。ただし「最初から何も進んでいない」のではなく、**橋の入口までは7月19日に到達し、その後3日間、渡らずに橋梁管理制度を作っている**というのが正確である。

定量的にも、7月20日直前から現在までの概算は以下である。

| 区分 | 追加行数（pathベース概算） |
|---|---:|
| 全体 | 52,905 |
| dev-wave/task-run/supervisor 等の開発プロセス実装 | 18,011 |
| freeze 恒久設計文書・逐語 | 9,106 |
| 8b 研究コード | 4,304 |

7月21〜22日の33 commit のうち、件名分類で **docs 27、コード4**。現在の速度配分は研究プロジェクトとして明らかに逆転している。

## 1. 方向整合

### 7月16〜19日: 主経路を実質的に前進させている

これは否定できない。

- 7月16日、層3最小 renderer と実レポートが完成した。`d6085a9`、`2230edf`。ただし対象は既存8a campaignであり、**8b oracle 実走レポートではない**。[phase3.md 段9](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:360)
- 同日、workload descriptor、holdout freeze、selector、oracle report/judge/driver が実装された。`6a975a1`、`911f6bc`、`1357461`、`31f20fb`、`1e9f740`。[worklog 2026-07-16 (3)〜(5)](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:739)
- 7月17〜18日、floor protocol、strict v2 verifier、launch lineage、oracle 結線を実装。`13a8848`、`fad6f0a`、`a87c107`、`d7ac2d7`、`d4cbf91`。
- 7月19日、Pegasus env contract が実測登録され、worklog 自身が「protocol JSON 実凍結→予測封印」の**前提は全充足**と明記している。`26a9ad6`。[worklog 2026-07-19 (2)](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:61)

この期間は過剰な部分を含むが、roadmap の「8b workload descriptor + 層3」に結びついている。

### 7月20日: 分岐点

8b の実穴を閉じる作業はまだ主経路に寄与した。

- attempt lifecycle、rep return code: `067f4b1`
- report truth table、reps件数、payload guard: `038e749`
- WAL readerのduplicate key/terminal位置: `f85fe92`

一方、同日から `/dev-wave`、task-run台帳、自己改善段、`/rulings`、backlog保存則が相次いで導入された。`9cbe36a`、`349cf4e`、`9360e25`、`be3a455`、`7ce5010`。

### 7月21〜22日: 主経路の手前で別系統が自己増殖

この2日間は性能計測・floor・selector予測・oracle実走がゼロである。その代わりに、

- freeze再発行の差し戻し2回: D71/D72、`d5028aa`、`77ad60b`
- bounded dev-wave supervisor: D74、`4042dcc`
- freeze恒久設計の第1・第2設計段: D75/D76、`417aad7`、`d97087c`
- WAL恒久修復: D77、`753d11c`

が進んだ。

とくに supervisor は12,862行追加されたが、real `claude -p` は未開放である。roadmapは8cを「8bと層3を1 cycle回してなお反復運営が律速なら」と定めているため、これは明白な順序違反である。[phase3.md 8c](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:352)

**判定:** 直近1週間全体では主経路を前進させた。しかし7月20日を境に、主経路よりプロセス系の増殖が優勢になった。

## 2. 「プロセスがプロセスを生む」証拠

### A. dev-wave が自分の作法を更新し続ける

7月20〜22日の3日間に、dev-wave/task-run/supervisor関連パスへ触れた commit は約30件ある。

- `/dev-wave` 新設: 7/20 `9cbe36a`
- task-run台帳: 7/20 `349cf4e`
- wave終了時の自己改善常設化: 7/20 `9360e25`
- briefも攻撃対象、変異判定厳格化: 7/20 `206608a`
- fresh-context終端契約: 7/21 `ed72579`
- 実測作法、pin列挙、submodule init追加: 7/21 `3d7aa4a`、`a21fa2e`
- 変異ハーネス復元・単一走行・hang隔離: 7/21 `31c99c0`
- 両層変異・sandbox偽赤・task-run上限作法: 7/22 `fd622e6`

個々の追記には実事故がある。しかし「各waveの失敗→dev-wave規則追加→次waveのレビュー面増加」という正の帰還が成立している。

なお自己改善常設化など一部は明示的なユーザー指示であり、AI単独の暴走ではない。それでも研究資源配分として問題である。

### B. freeze設計のためのfreeze設計

- D71: 再発行を実装せず、6件の関連タスクを発生。`d5028aa`
- D72: 格下げも実装せず、さらに5件の裁定パッケージ。`77ad60b`
- D75: 第1設計段、R1〜R16。`417aad7`
- D76: 第2設計段、3,101行、173 check行、49変異候補、93行の所有表。`d97087c`
- 現在は W-0→W-a→W-b/W-c→W-d→W-e→W-f の7 waveが次の実装列になった。[freeze設計所有表](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2457)

第1・第2設計文書は計3,603行、逐語を含めると約9,100行である。まだ凍結成果物は1 byteも直っていない。

### C. 裁定が新しい裁定パッケージを生む

具体例:

- 7/21 (3): T-005着手 → T-063〜T-068を新規発生、完了0。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:130)
- 7/21 (6): 2回目の着手 → T-071〜T-075を新規発生、完全消化0。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:357)
- 7/21 (8): T-067のみ部分実装 → T-077/T-078を新規発生。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:530)
- 7/22: T-074/T-075をT-080へ束ねた結果、単一T番号の下に7 waveが生まれた。

増殖率は窓の取り方で変わる。

- freeze差し戻し期だけなら、新規freeze系T番号11件に対し完全消化2件程度、約 **5.5:1**
- D70導入後から現在までなら、新規T-060〜T-082が23件、既存を含む完全消化が22件で、見かけの純増は+1
- ただしT-080が7 waveへ展開されたため、**T番号の純増は実作業量を過小評価**している

したがって「無限増殖」ではないが、gross churn は非常に大きい。

### D. WAL堅牢化が別のWAL堅牢化を生む

`f85fe92` のreader堅牢化から、T-004/T-007/T-008が生まれ、`753d11c`で2,431行の修復実装になった。その結果、さらに約25 callerの移行T-082が発生した。[D77](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3068)

coreのbyte framingは必要だが、現在は「直す→全readerを同時に制度化する」方向へ広がっている。

### E. 8c supervisorの先行

`4042dcc` は12,862行追加、203テストnodeを持つがfake child限定である。これは「セッション運営が律速かを8b実走後に判断する」というphase契約より先に、自律開発プロセスを作り込んだものだ。

**最も明白なプロセス自己増殖であり、主経路から外すべきである。**

## 3. 防壁投資の弁護側評価

### 判断基準

必要な防壁と認める条件は次の4点である。

1. 偽の科学的結論、正しさ違反、試行台帳欠落を直接防ぐ
2. 実事故またはpositive controlで発火実績がある
3. 最初の8b E2Eのcritical pathにある
4. 最小変更で閉じ、汎用制度へ拡張しない

### 必要だった防壁

- **between-run floor:** D19では+2.4%、+2.6%の2構成が faster から no-difference に反転した。これは実在する偽 faster の是正であり、最優先防壁である。[D19](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:317)
- **実buildを含むdevelop相:** F19は単体検査緑のvariantが実buildで落ちた。develop相は実際に事故を本計測前に止めた。[F19](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:214)
- **report/judgeの双射・件数・rc検査:** 7/16監査ではcorrectness red上書き、holdout全落ちでもdeterminate、manifest自己申告など複数のfalse-greenが実在した。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:794)
- **Pegasus env contract:** F22のattempt 1〜9は実機前提の誤認を示した。環境登録と較正は必要だった。[F22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:259)
- **最低限のfreeze修復:** F27ではgeneratorを壊しながらfixtureへ現行hashを差し込んで全走緑になった。凍結系を無防備に実走する案は不適切である。[F27](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:325)
- **WAL byte framingの中核:** torn tailへの追記が黙って消える以上、proof chainの入力として放置できない。`753d11c`のcore修復自体は正当。

### 過剰品質または本線を止めるべきでなかったもの

- **bounded supervisor全体:** 8cの発火条件前、fake限定、12,862行。延期すべきだった。
- **task-run pilot、backlog保存則、dev-wave自己改善:** 運用効率には効くが、8b科学成果の前提ではない。並行または成果後でよい。
- **freeze恒久設計の全W-0〜W-f:** 問題は実在するが、最初の1 cycleに必要なのは「内容検査を維持した一回限りの移行契約」であり、全freeze族の将来世代・revocation・expiry・173 check registryではない。
- **T-082の全reader移行:** D77 coreの後でよいが、floor/oracleを止める理由にはならない。
- **全findingを裁定パッケージ化する運用:** finding数は科学的進捗ではない。新しい受理集合や主張に影響しない診断精密化は、最初の実走後へ送るべきである。
- **変異ハーネスの過度な再帰:** F28/F32/F33は、変異テスト自身が複数回偽判定したことを示す。[F28](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:343) [F32/F33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:400)。防壁の検証は必要だが、全waveの中心成果にしてはいけない。

要するに、**防壁の存在は強く正当化されるが、防壁を汎用ガバナンス基盤へ昇格させる投資量は正当化されない。**

## 4. 機会費用

保守的な反実仮想は次の通り。

| 日 | 最小防壁路線で可能だった作業 |
|---|---|
| 7/16 | descriptor・selector・oracle・層3renderer実装 |
| 7/17〜18 | strict verifier、実験数値、最小freeze契約 |
| 7/19 | Pegasus較正・env登録。ここで前提充足 |
| 7/20 | protocol JSON実凍結、selector予測6セル封印、floor投入 |
| 7/21 | floor完走、holdout freeze数値充填、v2候補生成・承認 |
| 7/22 | oracle実走、層3実レポート生成 |

oracleの事前見積りは96 verifyで約11.6時間であり、floorも純bench時間は数時間級。PBS待ちや人間承認を含めても、6日間あれば少なくとも、

- protocol/prediction凍結済み
- Pegasus floor実測完了
- v2候補生成済み
- oracleが進行中または1 cycle完走
- 8bの層3レポート候補が生成済み

まで到達できた可能性が高い。

控えめに見ても、現状との差は「数日」ではなく、**科学的成果1 cycle分**である。

task-runの記録だけでも、supervisor約9.6時間、freeze設計2本約5.2時間、freeze差し戻し2本約2.1時間のwall spanがある。計測は非排他的で欠測も多いが、明白な迂回だけで約17時間分が観測されている。

## 5. 最短経路の提案

### 結論: T-080 W-0→W-fを全部終えてからfloor、は不要

それは「恒久freeze制度を完成してから初めて科学を再開する」という政策選択であり、科学的必然ではない。

特にW-0はhooks/task-run契約であり、floorやoracleの正しさとは無関係である。W-dも全consumerを一括移行する必要はなく、最初はfloor/oracle/reportの必要consumerだけでよい。

### 推奨する72時間の科学レーン

1. **プロセスfreezeを宣言する**
   - supervisor、dev-wave自己改善、task-run配線、T-082、追加裁定パッケージを停止
   - 新規T番号を「実走を不可能にするblocker」に限定

2. **一回限りの移行契約でfreeze gateを復旧する**
   - dangling ancestryはtypedなprovenance observationとして扱う
   - ただしD73が指摘した後段の`ccbench_pin`・機械再構成検査を必ず実行し、例外を丸ごと握り潰さない
   - holdoutのdesign/generator二重driftを、人間同席の明示receiptで再pin
   - exact bytes、source closure、generator、protocolを固定
   - revocation、expiry、全世代一般化、173 check registryは後回し

3. **protocol JSON実凍結とselector予測封印**
   - master seed/env tagは既に確定済み
   - on/off/swappedの6セルを1回だけ生成

4. **Pegasus floor実測**
   - T-011の残存限界受諾を直前に実施
   - 異常検出gate以外の追加設計を入れない

5. **v2候補生成・人間承認**
   - floor/budgetをholdout freezeへ充填
   - 候補全件をcorrectness/identity gateへ

6. **oracle実走**
   - crash時は既定どおり判定不能
   - 全件報告を維持

7. **既存rendererで8b実レポートを生成**
   - v3機序仮説層は必要な原料だけ追加
   - まず事実層を完成させる

### 現backlogの処置

| 項目 | 処置 |
|---|---|
| T-080 W-0 | critical pathから削除 |
| T-080 W-a〜W-f | 一回限り移行に必要な最小部分だけ抽出。恒久一般化はoracle後 |
| T-068/T-077/T-078 | 1本の「legacy→first-cycle移行」waveへ統合 |
| T-066 | freeze公開前に並行実装 |
| T-067残り | oracle前に並行。floorは止めない |
| T-001 | floor実測と並行、最終report前までに完了 |
| T-002 | 同上。公式report発行前には必要 |
| T-011 | floor直前に実施。現計画どおり |
| T-009/T-060/T-010/T-012 | 延期 |
| T-082 | 延期。まず公式consumerのみ |
| supervisor real開放 | 8b+層3を1 cycle回すまで凍結 |

## 6. severity付き総合所見

1. **[Critical] 主経路が恒久freeze制度の完成待ちに置き換わっている。** 現在の次手はW-0→W-fであり、roadmapの最小E2E優先と矛盾する。根拠: 7/22 `d97087c`、[worklog末尾](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:954)。

2. **[High] 7/21〜22の資源配分が逆転した。** 33 commit中docs 27、コード4、性能計測0。根拠: git履歴、worklog各見出しの「計測なし」。

3. **[High] 8c supervisorは明確な早すぎる実装である。** 8b実走前に12,862行を投入し、real runtimeは未開放。根拠: 7/21 `4042dcc`、[phase3 8c](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:352)。

4. **[High] freeze修復が自己増殖した。** 実装0 byteのD71/D72から、2設計段・7実装waveへ膨張。根拠: `d5028aa`、`77ad60b`、`417aad7`、`d97087c`。

5. **[High] backlogは純増よりgross churnが問題である。** 全体の純増は+1程度だが、freeze差し戻し期は新規対消化が約5.5:1で、T-080が7 waveを1 IDに隠している。

6. **[High] 防壁を単純に削る提案も誤りである。** D19の偽faster反転、F19、F27、複数false-greenは実在する。必要なのは防壁撤去でなく、最小防壁で実験へ戻ること。

7. **[Medium] WAL core修復は妥当だが、全reader移行は後回しでよい。** 根拠: 7/22 `753d11c`、T-082。

8. **[Medium] 層3最小E2Eは既にあるため、研究方向そのものは失われていない。** ただし既存8a campaignのレポートを8b成果と混同してはいけない。根拠: 7/16 `d6085a9`、`2230edf`。

9. **[High] 現状を続ければ「速度配分の誤り」から「方向逸脱」へ移行する。** 次の1〜2 waveを科学レーンへ戻せなければ、総合判定を一段悪化させるべきである。

**最終判定:** オーナーの懸念は正しい。方向はまだ正しいが、現在は渡るための防壁ではなく、防壁を管理する制度を作っている。次の成果物は設計文書でもテスト件数でもなく、**Pegasus上のfloor、v2候補、oracle WAL、そこから生成された8b材料レポート**でなければならない。