# [T-338] 投入gate 単位1・単位2 実装 — 一次資料

## 対象

D509 決定(7)の6分割 (`docs/decisions.md`) のうち、依存のない単位1 (manifest/binding/Git基盤)・
単位2 (受領証IO/schema) の実装。Q-B (必須kill3件の帰属段=validator/consumer段)・Q-C (B1は申告値の
拒否専用化で閉じる) の確定裁定 (「/rulings 全件 第7回」、`docs/archive/worklog-phase3-0819-676.md`)
を実装へ反映する。単位3(semantic validator)・単位4(全履歴検査+attempt authority)・
単位5(writer+conformance vectors)・単位6(統合+4名前export) は依存未充足のため対象外。

## 段2 codex plan

`orchestrator/submission_gate/` を新設 (既存 `orchestrator/preregistration/` はD264により
「投入gateではない」契約が機械固定されており同居させない)。見積り: production 1,250–1,850行、
test 2,600–4,200行。

## 段3 敵対相談 (2レンズ、収束したreal所見)

1. D550型の二段束縛 (anchor commit) を構築する入力経路が計画に無い。
2. schema loaderがcaller-selectableな`ref`を受け取る形でD264の閉集合意図に反する。
3. fd相対IOのpath traversal防御 (絶対path/`..`/空component拒否) が計画に明記されていない。
4. `blobref.py`のwrapper化が既存monkeypatchベースのtestと例外契約 (4型) を壊しうる。

## 段4 親裁定

上記4件を採用しplan v2へ反映。B1のreject-only・必須kill3件の帰属は単位3/4の責務として
docstringで明記するに留め、単位1/2自体には実装しないと確定 (record-items-v2.md §6.10/§7で
単位5/3の責務と確認)。変異事前登録7件を確定。

## 段5 実装

2並列codex author (専用worktree)。単位1: production 1,198行・test 457行。単位2: production
842行・test 488行。統合commit `94aa3a54`。

## 段6 敵対レビュー・fix (1巡目)

裁定準拠監査・独立コードレビューの2レンズがreal所見11件を検出 (最重要: `ApprovedManifest`が
偽造可能なpublic dataclassのまま、addendum A/Bの実blobが未検証、`objects/pack`のsymlink経由
外部object store混入見逃し、FIFO leafでの無期限block、Git stderr無制限)。fix1 (`6bd9e724`) で
11件すべて対応、実測66→65 passed (焦点走)。

## fix後の焦点再レビュー・fix (2巡目)

fix1自身が作った新規regression2件を検出: (R1) 受領証/schemaの再帰凍結 (MappingProxyType/tuple)
がjsonschema (3.2.0) のexact型判定と衝突し、正当な受領証まで拒否される機能回帰。(R2) FIFO負例
テストにtimeoutが無くhangしうる。fix2 (`ad828076`) で解消、実測66 passed, 0 failed。

## 変異matrix

`docs/dev-wave-jobs.../mutation-spec.json` (7件)。実行はローカルmode、baseline PASSED。
初回投入でparametrize testの実node ID不一致により2回spec補正 (M2/M3のparametrize全ケース列挙、
M1/M5で想定より広く多重防御が検出されexpected_nodesを拡張)。最終: baseline PASSED・7/7 KILLED・
SURVIVED 0・MISMATCH 0。

## 成果物影響

certified選択・材料レポート・proof chain・受理集合は不変 (D509の枠組み通り、単位1/2は
構造的基盤でありadmission判定を持たない)。次wave (単位3/4) が着手できる状態として、
`_binding.py`/`_event_chain.py`のdocstringにhandoff契約を明記した。
