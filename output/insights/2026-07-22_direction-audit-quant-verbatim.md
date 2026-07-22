# 方向性監査 (2026-07-22) — 定量スイープ逐語 (codex)

実行: codex exec, model=gpt-5.6-sol, reasoning=high, sandbox=read-only。親 = claude-fable-5 (background job)。
監査の統合と裁定パッケージは `2026-07-22_direction-audit-recovery-plan.md`。

## プロンプト (逐語)

```text
あなたは izanagi プロジェクト (CC 自動合成システム) の進捗を定量監査する外部監査者である。
リポジトリは読み取り専用で自由に調べてよい。出力はすべて日本語。

# 背景
ユーザー (プロジェクトオーナー) の懸念: 「なんか全然進捗が進んでいないように見える。石橋を叩いて
渡るでいうなら、ずっと叩いてて渡ってないような」。この懸念が事実か、データで検証したい。

# タスク (すべて根拠付きで)

1. **コミット分類**: `git log --date=short --pretty='%ad %h %s'` で 2026-07-05 以降の全コミットを
   次の 3 分類で集計せよ (日別または 2〜3 日ビン)。
   (a) 研究本線 = 新しい計測・campaign 実走・S-1 本走・8b selector/oracle/floor の実装や実走・
       層3 renderer・軸探索の実 LLM iteration など、roadmap の科学的成果に直接つながるもの
   (b) 防壁・検証基盤 = verifier/identity/hooks/freeze 設計/WAL 堅牢化/テスト衛生/監査対応
   (c) プロセス・運用 = /dev-wave や /rulings 等のコマンド整備、task-run 台帳、worklog/docs 整理、
       裁定記録、handoff
   各分類の件数推移と、直近 1 週間 (07-16 以降) の比率を出せ。

2. **計測の空白期間**: docs/worklog.md のエントリ見出しには「計測なし」等のタグがある。全エントリを
   走査し、実際に新しいベンチ計測・campaign 実走が行われた最後の日を特定せよ。また 07-16 以降の
   エントリ数と、そのうち「計測なし」の数を数えよ。

3. **backlog の構造**: worklog 末尾の「次の一手」リスト (T-xxx 番号群) を、
   (i) 研究本線 (floor 実測 → v2 候補生成 → oracle 実走 → 層3 レポート) の前進に直接必要、
   (ii) 防壁・堅牢化 (やらなくても本線は走る)、
   (iii) プロセス・文書、
   に分類せよ。T-080 (freeze 族恒久設計) の実装 wave W-0→W-f の規模感を、設計文書
   (output/insights/ の 2026-07-22 前後の freeze-design 系ファイルや docs/ 配下の s2 doc) から
   見積もれ (wave 数・想定作業量)。

4. **本線までの gate 連鎖**: docs/phase3.md の「現行チェックポイント」着手順 (a) に従い、
   次の科学的マイルストーン「floor 実測開始 → v2 候補生成 → oracle 実走」までに残っている
   gate・裁定・実装 wave を全部列挙し、連鎖の深さを示せ。ユーザー裁定待ちが何箇所あるかも数えよ。

5. **結論**: 「叩いてばかりで渡っていない」は定量的に正しいか。正しいなら、いつから・どの程度か。

出力: 構造化 markdown。各主張に commit hash / ファイルパス / 行の根拠を付けよ。推測と実測を区別せよ。
```

## 出力 (逐語)

# 定量監査結果

## 0. 監査条件

- 対象: `2026-07-05 00:00` 以降、HEAD `fd622e6` までの全 **466コミット**。merge commit も1件として含めた。
- 分類は件名に加え、曖昧なものは変更対象・成果の性質で判定した。
- 本線には実走だけでなく、8b selector/oracle/floor、S-1、層3、実LLM探索の直接実装・科学設計も含めた。したがって本線に比較的有利な分類である。
- 永続 freeze、identity、launch certificate、WAL、監査・テスト強化は、たとえ現在の blocking gate でもコミット分類上は「防壁・検証基盤」とした。

## 1. コミット分類

### 2〜3日ビン集計

| 期間 | (a) 研究本線 | (b) 防壁・検証基盤 | (c) プロセス・運用 | 合計 |
|---|---:|---:|---:|---:|
| 07-05〜07-07 | 12 | 13 | 26 | 51 |
| 07-08〜07-10 | 22 | 3 | 36 | 61 |
| 07-11〜07-13 | 26 | 23 | 32 | 81 |
| 07-14〜07-15 | 19 | 13 | 26 | 58 |
| 07-16〜07-18 | 57 | 19 | 39 | 115 |
| 07-19〜07-20 | **0** | 31 | 36 | 67 |
| 07-21〜07-22 | **0** | 10 | 23 | 33 |
| **全期間** | **136 (29.2%)** | **112 (24.0%)** | **218 (46.8%)** | **466** |

研究本線の代表根拠は、kickoff E2E `4c167b5`、S4 consumer 実走 `e576312`、sort 実LLM E2E `c6e7fba`、8a偵察実測 `68b55f2`、8a実LLM iteration `d485a48`、S6本走 `0e37bd0`、S-1本走 `694c32d`、oracle v2結線 `a87c107`。

07-19以降の代表は、Pegasus attestation `950757e`、WAL堅牢化 `f85fe92`、backlog保存則 `7ce5010`、freeze恒久設計 `d97087c` であり、いずれも新しい科学的観測ではない。

### 直近1週間、07-16以降

| 分類 | 件数 | 比率 |
|---|---:|---:|
| 研究本線 | 57 | **26.5%** |
| 防壁・検証基盤 | 60 | 27.9% |
| プロセス・運用 | 98 | 45.6% |
| 合計 | 215 | 100% |

つまり直近1週間の **73.5%は本線以外**である。さらに本線57件は07-16〜07-18に集中し、**07-19以降の100コミットは本線0、防壁41、運用59**だった。

境界の感度分析として、Pegasus登録wave全体（merge `9d0ae8d` と配下13コミット）を本線へ最も寛大に移しても、直近1週間の本線は最大 **71/215 = 33.0%**。なお、07-20以降69コミットはその解釈でも本線0である。

## 2. 計測の空白期間

07-17にworklogがarchiveへ移されたため（`ffebd7b`）、現行worklogと正規archiveを連結して数えた。

| 日付 | エントリ数 | 見出しに「計測なし」を含む |
|---|---:|---:|
| 07-16 | 12 | 0 |
| 07-17 | 9 | 4 |
| 07-18 | 13 | 13 |
| 07-19 | 9 | 8 |
| 07-20 | 17 | 17 |
| 07-21 | 9 | 9 |
| 07-22 | 6 | 6 |
| **合計** | **75** | **57 (76.0%)** |

これは見出し文字列だけの保守的な集計である。07-17のテスト高速化など、実際には性能campaignでないがタグがないエントリも「計測あり」側へ残っている。

### 最後の新規bench/campaign

最後は **2026-07-16のS-1本走**。`S-1a不成立 / S-1b成立`、hard gate全通過、計測wall約6.4時間と記録されている（commit `694c32d`）。[worklog archive](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:676)

07-19のPegasus作業は実機を使用したが、正本自身が「**較正のみ、性能計測なし**」と区別している。[07-19 worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:26)

したがって監査時点では、**新しい科学的bench/campaignが6日間空白**である。

なお07-16にはS' headline不成立も確定した。これは「渡っていない」のではなく、橋を一度渡って**否定的結果を得た**実績である。[phase3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:23)

## 3. 最新backlogの構造

最新「次の一手」は14項目。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:952)

| 分類 | ID | 件数 | 判定 |
|---|---|---:|---|
| (i) 本線に直接必要 | T-080、T-068、T-077、T-078、T-011 | 5 | 現在のfreeze発効とfloor開始gateを構成 |
| (ii) 防壁・堅牢化 | T-066、T-067、T-001、T-002、T-010、T-082 | 6 | テスト・identity・report API・reader移行。なくてもコード上は本線を走らせられる |
| (iii) プロセス・文書 | T-009、T-060、T-012 | 3 | AGENTS規律、用語是正、task-run pilot方針 |

T-080は内容的には防壁だが、backlog依存分類では(i)である。現行のfreezeがofficial runを拒否しており、最新worklogが明示的に「次の実装waveはここから」としているためである。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:954)

### T-080の規模

実測できる設計規模は次のとおり。

- 実装wave: **7個** — W-0、W-a、W-b、W-c、W-d、W-e、W-f。
- 依存深さ: W-b/W-cだけ並列なので、critical pathは **6 wave層**。依存順は設計に明記される。[freeze design](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:432)
- exact ownership: 合計 **93 path項目**。
  - W-0: 7
  - W-a: 11
  - W-b: 5
  - W-c: 10
  - W-d: **46**
  - W-e: 9
  - W-f: 5  
  [S2 ownership](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2472)
- W-dだけでproduction consumer **19件**を一斉にpointer化する。[S2 consumer registry](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2594)
- 最終manifestは **42 test node**、内訳は既存12、新規detector 29、meta-test 1。[S2 node manifest](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design-s2.md:2663)
- 設計資料自体が9,105行。第1段 `417aad7` は2,578行追加、第2段 `d97087c` は6,724行追加。

**推測:** これは単一修正ではなく、少なくとも7回の実装・変異・レビュー・全走サイクルである。直近T-004の1 waveが9回のCodex走を要した実績を単純外挿すると、数十回規模の作業単位になり得る。[T-004工数](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:943)  
文書には時間見積もりはないため、日数への換算はできない。

## 4. floorからoracleまでのgate連鎖

`phase3.md`自身は07-18更新で、「既存前提はすべて充足」としたうえで、protocol凍結からfloor、v2、oracleへ進むとしている。[phase3](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:61)

しかし、その後の07-21〜22にfreeze自己pin問題が見つかり、T-080が前置された。最新正本を重ねると、実際の連鎖は以下になる。

```text
S2最終patch
  → W-0
  → W-a
  → W-b / W-c（並列）
  → W-d
  → W-e（G → R → literal 1 → literal 2 → 人間承認A）
  → W-f（人間による発効X）
  → protocol JSON実凍結
  → selector予測封印
  → T-011 残存限界のユーザー受諾
  → floor実測
  → calculator充填 + 独立再計算一致
  → v2候補生成
  → ユーザー承認 + active pointer
  → oracle実走
```

根拠:

- W-0〜W-fの依存順とW-e/W-fの意味。[freeze design](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/freeze-permanent-design.md:437)
- protocol → 予測封印 → floor → 機械充填 → v2候補 → 承認 → oracleの凍結順。[8b design](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3-8b-descriptor-design.md:362)
- T-011はfloor直前まで意図的に据え置き。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:966)
- U-A1は07-22に解決済みだが、S2文書への反映と整合確認は未了。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:881)

### 連鎖の深さ

- macro stageで数えると、S2最終patchからoracleまで **15段**。
- floor実測は11段目、つまり実測開始前に **10段**残る。
- W-e内部のG/R/literal×2/Aを別々の必須commitとして展開すると、全体は **19段相当**。
- 7実装waveのcritical pathだけでも **6層**。

### ユーザー待ち

厳密に「まだ選択結果が決まっていない裁定」と数えると、本線上は **2箇所**。

1. floor直前の残存限界受諾（T-011）。
2. floor後のv2候補承認。

U-A1、R10〜R16はすでに裁定済みであり、未決としては数えない。

ただし、択一ではない「人間によるcommit・確認停止点」まで含めると、W-e生成時同席、A承認、W-fのX、protocol JSON凍結、T-011、v2承認の **少なくとも6接点**がある。さらに本線外ではT-012の継続・縮小・撤去裁定が別途残る。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:967)

## 5. 結論

**「叩いてばかりで渡っていない」は、07-19以降について定量的に正しい。全期間については正しくない。**

- 07-05〜07-18には、実LLM探索、campaign偵察、S6本走、S-1本走、8b実装という明確な本線前進がある。
- 07-16にはS-1を実際に完走しており、結果はS' headline不成立だった。科学的には有効なnegative resultである。
- その後は07-19〜07-22の **100コミット中、本線0、防壁41、運用59**。
- 新しいperformance bench/campaignは07-16を最後に **6日間ない**。
- 07-16以降のworklog 75件中、少なくとも57件、**76.0%**が見出し上も「計測なし」。
- 次のfloor実測には、新たに追加されたT-080の7実装waveを含む **10段の前工程**がある。

したがって転換点は **07-19**。そこから監査時点まで、科学的証拠の追加は止まり、工数は防壁・恒久設計・開発運用へ100%移っている。進捗がゼロなのではなく、**工学的進捗はあるが、オーナーが見たい「新しい計測・候補・oracle結果」への変換率が0%になっている**、というのが最も正確な診断である。