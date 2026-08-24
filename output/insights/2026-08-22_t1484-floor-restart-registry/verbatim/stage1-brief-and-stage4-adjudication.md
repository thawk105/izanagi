# 段1 brief (原文)

(全文は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/stage1-brief.md`
と同一。この wave は docs-only のため brief 自体の再掲を以下に含める。)

---

# 段1 brief — [T-1484] 床値 (8b v1 freeze) crash 復帰救出経路の技術確認 (docs-only)

## scope
`docs/phase3-8b-restart-runbook.md` §3.6/§5 R-5 の crash 復帰袋小路について、(a) D510 決定4の
attempt registry 機構を 8b floor/v1 freeze 系にそのまま適用するか専用対応物を作るか、(b) 既存の
実走マーカー (freeze byte sha256 排他作成)・novelty search 要件との統合方法、の2点を技術確認し、
R-5 本文を更新して実装方針の推奨をユーザー裁定パッケージとして返す。**production 実装はしない**
(コード変更ゼロ、`4→7→8→9`)。

## 確定済みユーザー裁定
- D496 決定3 (2026-08-17): 測定が途中で落ちたら比べる構成ごと測り直す。設計上の終端は認めない。
- D510 決定4 (2026-08-18): 「8b §9項8の再走全拒否よりD496決定3を優先する」と明記。事前割当
  attempt registry (全slot事前割当・追記専用・失敗理由exact列挙・信頼側起動器が出力を読む前に
  分類・create-only受領証・freezeごと単一root) の5要件を定める。
- 2026-08-22 (今日) ユーザー裁定: D510 の設計・優先順位を床値/8b系にも適用する前提で [T-1484]
  を起票 (`docs/phase3.md:773` T-901 backlog 記載)。

## 一次資料で確認した事実 (handoff.md に file:line 詳細)
1. R-5 (`docs/phase3-8b-restart-runbook.md:422-438`) は「D496決定3と§9項8のどちらが優先するか」を
   2026-08-17時点で未決着と記す。**D510決定4はこの問いに `8b §9項8` を名指しして既に答えている**
   ((P1) この事実そのものは段2で再確認するだけの単純作業、攻撃対象ではない)。
2. `docs/phase3-8b-descriptor-design.md` §10.5 (518-543) が、D510 と同日 (2026-08-18) の再凍結で
   R-5 と同一論点への設計文を既に持つ (事前割当・消費範囲を「落ちた構成だけ」に限定・観測値不変・
   失敗分類事前確定・単一root の5点、D510決定4と同型)。§10.6 (545-555) がこれを「8c側の判定器・
   registry・結果judgeが追随するまで測定を認可しない」と epoch gate。command 引数はこの節を
   直接名指ししていない。
3. D649 (2026-08-22、`decisions.md:25912-25961`、T-1472の結果) は D510 追随実装の所在を監査し、
   judge/3表/attempt registryは `s8c_result_judge.py`・`trial_registry.py` に**8c系として**
   実装済みと確定。`between_run_floor.py`/`s8b_floor_campaign.py`等を土台にした重複実装は
   T-1472 の scope (judge・3表・validator の新規実装) に対して却下されたが、**R-5 の attempt
   registry 再利用可否そのものを裁定した記録ではない**。
4. `grep` 実測: `trial_registry.py` と 8b 系 (`s8b_*.py`) の import 結合は現状ゼロ。
   `AttemptSlotCapability` の schema version・ARMS・HOLDOUTS 定数は8cドメイン
   (on/off/swapped, rr80/rr20) 固定。8b の admission key (`s8b_holdout_admission.py:670-686`,
   freeze_sha256×freeze_holdout_key×configuration_id×ccbench_pin×env_tag×observation_role) と
   語彙が異なる。

## (P1) 親の暫定判断 (段3 攻撃対象)
D510 の attempt registry **機構パターン**は設計参照にするが、`trial_registry.py` の literal な
import/流用ではなく8b専用の対応物 (新schema version、8bの6要素admission key語彙) を作る方向を
推奨候補と暫定する。根拠は handoff.md 記載の (i)〜(iv)。反証 (共有基盤化が正しい設計、または
D649 が既に禁じている等) があれば歓迎。

## (P2) R-5 の3択そのものの扱い
§10.5 は「落ちた構成だけ」の再測定に限定するが、R-5 (b)「未知holdout freezeの引き直し」は
射程が広い別設計。R-5 は3択を残したまま更新するのではなく、§10.5 を正としてR-5本文を
書き換える (3択は「2026-08-17時点の検討過程」として履歴に残す) 方向を暫定する。段3で
「§10.5 と R-5 (a) の関係 (択(a)=復帰用generationでadmission keyをsalt、observation前限定、
は§10.5の設計と両立するか同一物か)」を検証する。

## 不変条件
- 絶対規律2 (正しさゲートを緩める変異を許さない) — 推奨案は再走の受理集合を広げるが、
  D510決定4の5要件 (事前割当・追記専用・exact失敗理由・出力を読む前の分類・create-only) を
  全て満たす形以外は推奨しない。
- 既存の実走マーカー (freeze byte sha256排他作成) とnovelty search機構
  (`s8b_holdout_freeze.py:985 verify_document`) の変更は本waveでは提案のみ、実装しない。
- D649・§10.6 のepoch gate (8c側前提) と矛盾する推奨をしない。矛盾する場合はその旨を明記して
  ユーザー裁定へ返す。

---

# 段4 裁定 (親、2026-08-22)

## 所見の裁定 (real/refuted/scope)

段3 両レンズの所見は次のとおり裁定する。全件 real として採用し、refuted 判定分もその
反証内容自体を採用する (「brief の主張の一部が不正確だった」という指摘そのものが real)。

| # | 所見 (要約) | 出典 | 裁定 |
|---|---|---|---|
| 1 | 8b の失敗分類は現状 `measure_fn` 後 (post-hoc) であり、D510決定4の「出力前分類」要件を
    現行実装は満たさない | sol・luna 独立に確認 (`s8b_floor_campaign.py:4773-4840`) | **real、
    採用。R-5に将来wave向けの明示ブロッカーとして書く** |
| 2 | novelty search (repo既知性検査) と再抽選バイアス (統計的独立性) は別問題。前者は
    `verify_document`、後者は §10.4 の測定近接性ラベルが担う | sol | **real、採用。両者を
    混同しない記述にする** |
| 3 | §10.5 の「落ちた構成の次slotだけ消費」は、crash点4 (観測開始後) の再抽選バイアスを
    閉じる具体策 (どのattemptを主値にするか等) までは規定していない | sol | **real、
    採用。未解決の設計点として明記** |
| 4 | `trial_registry.py` の literal 流用は不可 (8c固定のschema/path/ARMS/HOLDOUTS/
    acceptance) | sol・luna 独立に確認 | **real、確定 (段2から3回独立確認)** |
| 5 | 「汎用化するとD8c consumerを壊す」は非互換変更に限った話であり、名前空間を保った
    パラメータ化まで一律に否定する根拠にはならない | sol (unclear)・luna (real) | **real、
    採用。次点の所見6と合わせて (P1) を修正する** |
| 6 | 「8b専用の新規複製が最善」は未検証。attempt state machine 本体
    (`trial_registry.py:1818-3555`、約1,738行) はほぼドメイン非依存で、8c固有部分は
    acceptance (`:3432-3555`、約123行) に集中する。共通 core 抽出＋8c互換facade＋8b
    adapterの方が保守面で有利な可能性があり、段2はこの比較を行っていない | luna | **real、
    採用。(P1) を「専用複製」の確定推奨から「reuse形状は未決の設計択一」へ格下げする
    (下記「(P1) の修正」参照)** |
| 7 | D649 が却下したのは T-1472 scope (judge・3表・validatorの重複実装) であり、8b
    attempt registry の再利用可否そのものを裁定した記録ではない | luna | **real、確定
    (brief 自身の記述と整合、独立確認により確度が上がった)** |
| 8 | 8b は既に `s8b_holdout_admission.py` の共有root・claim・ledger・consume-ticket機構を
    持つ。新設 registry がこれと束縛されない第二の「master」になると、それ自体が新しい
    正しさの穴になる | luna | **real、採用。将来実装waveの必須設計項目として明記** |
| 9 | §10.6 (epoch境界) は実装そのものを止めない。8c側 (`judge()`) の production caller
    不在という D649 の指摘により、正式測定authorizationは実装後も引き続き閉じたままである | luna | **real、採用。「実装許可」と「正式測定不許可」を分離して書く** |
| 10 | D649 以降 (D650〜D659) および今日の worklog に、本件を覆す新規裁定はない | luna | **real、確定 (現状追随の裏取り完了)** |
| 11 | 並行 wave 衝突は現時点では実体として低リスク (対象3ファイルのうち `trial_registry.py`/
    `p3_autonomous_workload_trial.py` を直接触る生存 worktree なし)。ただし
    `autonomous_trial_completeness.py` 経由の遅延 import で間接結合が残る | luna | **real、
    採用。将来wave着手時の再確認事項として注記 (本waveの blocker ではない)** |
| 12 | 段2 の R-5 書き換え案は DW-G04 の出発点として抽象的すぎる (canonical path・receipt名・
    `campaign_run_id`・発火判定が未特定) | luna (具体案つき)、sol (添削案つき) | **real、
    採用。両者の具体案を統合してR-5本文へ反映する** |
| 13 | DW-G05 の「(実装しないと) 永久に出せない」は現行 v1 protocol/env 限定の運用上の
    袋小路であり、oracle judge が floor を消費しない以上「certified 受理集合を永久ゼロに
    する」への一般化はできない。救出経路の価値は性能主張の強化でなく D496 が求める
    再測定可能性の回復である | luna | **real、採用。記録の framing を是正する** |

## (P1) の修正 — 確定推奨からユーザー裁定事項へ

段3 luna の所見6により、「8b 専用対応物を新規に複製する」という当初の (P1) 暫定判断は
**確定推奨として維持できない**。次の2点は確定できる。

1. `trial_registry.py` の**公開契約 (schema version・path・ARMS/HOLDOUTS・
   `TrialManifest`)** を非互換に変更して 8b へ転用することはしない (所見4・5で確定)。
2. 8b 側は D510決定4/§10.5 と同型の **事前割当・追記専用・create-only** な attempt
   registry を持つべきである、という設計方向自体は確定 (D510決定4が `8b §9項8` を
   名指しし、§10.5 が同日付で仕様化済み)。

しかし **「その registry をどう実装するか」は次の2案のどちらが優れるか未検証であり、
本 wave (docs-only) の scope では確定しない。** 次のユーザー裁定へ返す。

- **案 X (専用対応物)。** `orchestrator/campaign/trial_registry.py` には触れず、8b 専用の
  新モジュールを作る。利点: 8c への影響ゼロ、隔離された blast radius。欠点: attempt
  state machine (~1,738行相当) の大部分を事実上複製する。
- **案 Y (共通 core 抽出)。** `trial_registry.py` の domain 非依存部分 (genesis/reserve/
  classify/observe/terminal/accept の状態機械) を共通 core へ抽出し、既存 8c 呼び出しは
  互換 facade で無破壊のまま維持し、8b は新しい adapter (6要素 admission key 語彙) を
  介して同じ core を使う。利点: 保守は一本化、案Xの複製コストを避ける。欠点: 8c の
  稼働中 consumer (`p3_autonomous_workload_trial.py`、`test_trial_registry.py`、
  `test_p3_autonomous_workload_trial.py`) への影響範囲の実測が必要で、本 wave では
  行っていない。

**推奨: 案Y (共通 core 抽出) を第一候補として調査すべきだが、確定はユーザー裁定に委ねる。**
根拠: attempt state machine の非依存部分が対 8c固有部分で約14:1の行数比であり (luna 所見6)、
規律5 (盛らない/汎用ツール化を避ける) は「CC合成という単一目的に必要なものだけ持つ」ことを
求めるものであって、domain が異なる2箇所で同一パターンの ~1,700 行を複製することを
正当化しない。ただし、この行数比は分割コストの下限であって実際の抽出コスト
(8c consumer への影響、テスト改修範囲) を測ったものではないため、次の実装 wave の段1
brief が最初に行うべき作業として明記する。

## R-5 更新方針 (確定、本 wave が実施)

`docs/phase3-8b-restart-runbook.md` の R-5 状態節を次の骨子で更新する (実際の diff は
本体 commit を参照)。

1. D496決定3 と §9項8 の優先順位は **決着** — D510決定4 が名指しで解決済み。
2. 設計は `docs/phase3-8b-descriptor-design.md` §10.5 を正本として参照する。R-5 の
   3択は歴史的記録として残し、(a) は §10.5 の狭い先行版・現行推奨から除外、(b) は
   trust root ごと変える別設計・不採用、(c) は D496/D510 に反するため不採用と明記する。
3. 「実装許可」と「正式測定不許可」を分離する。実装 (8b 専用 attempt registry の設計・
   構築) は §10.6 に妨げられないが、正式測定は 8c 側 epoch gate (D649: `judge()` に
   production caller なし) が閉じている間、認可しない。
4. 将来の実装 wave が最初に閉じるべき4つの設計・確認事項を列挙する: (i) reuse 形状
   (案X/案Y) の判断、(ii) 既存 `s8b_holdout_admission.py` の claim/ledger との束縛
   (どちらが master か)、(iii) 8b 自身の失敗分類を出力を読む前に確定させる trusted
   launcher 設計、(iv) crash点4 (観測開始後) の再抽選バイアスの扱い (主値の選定・
   §10.4 近接性ラベルとの連動)。
5. DW-G05 相当の framing を是正: 「永久」ではなく「現行 v1 protocol/env 限定」、
   価値は性能主張強化でなく D496 の再測定可能性回復。

## scope 内外

全所見は「次の実装 wave が着手前に読む設計メモ」の scope内であり、本 wave (docs-only)
自体が実装するものはない。案X/案Yの選択、および実装着手の可否そのものはユーザー裁定へ
返す。
