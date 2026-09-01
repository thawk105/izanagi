---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2067-residual3-impl
seq: 1
title: [T-2067] 床値選択規則を g1 限定で s8c の load-only consumer へ強制し、残る 4 項目は実装しない理由を確定した (code + tests + insight、branch worktree-dev-wave-t2067-residual3-impl、変異 5/5 KILLED)
---

## 本文

- 依頼は残件 3 点の実装。**実装したのは残件 1 のうち s8c 床値 verifier / publish の 1 群だけ**で、
  残り 4 項目 (oracle manifest 群 / C06 予算群 / 起動証明書の実時間性 / s8c production final claim
  配線) は実装しなかった。理由は項目ごとに異なり {{D:floor-residuals-not-implemented-scope}} に置いた。
  設計の形は {{D:floor-selection-consumer-enforcement-g1-only}}。
- **D1241 / D1313 の advisory / non-certifying 上限は解除していない。** 本 wave が追加で主張する
  ことは無く、D1313 の (a)(b)(c) を超える文言も入れていない。強制点が増えたのは実装事実であって
  主張の水準ではない。
- **現 HEAD に `s8c_result_judge` の production caller は 0 件である** (親・段 3 レンズ A・
  段 3 レンズ B が独立に確認)。この強制は直接 API を呼んだときにだけ効く。
  「production final claim を配線した」とは主張しない。
- s8c 事前登録の C07 述語は本 wave の前後とも `EVIDENCE_UNDEFINED` /
  `completion-proof-not-machine-checkable` (= 全構造検査を通過した終端) のままである。
  `SATISFIABLE_CONDITION_IDS` は C10 だけなので C07 は設計上 SATISFIED に到達しない。
  **C07 が改善したとは書かない。**
- 本 wave は active g1・official floor run・予算承認を生成しない。現 tree にそれらは 0 件で、
  `BUDGET_APPROVAL_SHA256` は `None` のままである。

### 段 6 が検出した製品の穴 (fix 済み)

選択規則だけを切り出した helper には、探索先 namespace を批准文書・記録 protocol へ束縛する
前提が無かった。選択 identity の helper は selected path の env_tag から namespace を自分で
組み立てるため、別 env を指す `floor_source.path` を持つ g1 は、真の namespace により早い導出
適格 run があっても探索から外せた。full validation では同じ束縛が選択呼出しの後段にあり合成
として守られるが、切り出した側には後段が無い。fix で proto8 と env_tag 連鎖の束縛を選択呼出しの
前へ足し、失敗は既存の `floor-selection-unverifiable` へ畳んだ (拒否理由は増やしていない)。

fix 子が修正前に実測した診断: 別 env namespace を指す g1 は helper を素通りし、適格性導出の
呼出しは **0 回**だった。

### 段 6 が検出した偽緑 (fix 済み)

既存の publish 現行束縛 test は、loader だけを後から別 object へ上書きしていたため本来の
current-binding 比較へ到達せず、古い selection stub の identity assertion で落ちていた。
例外理由を検査していなかったので緑になっていた。loader と selection assertion を同じ批准物へ
束縛し直し、例外文言を固定した。**既存 assert は変更していない。**

### 採用しなかったレビュー所見

段 6 レンズ B は選択検査へ「selected certificate と path 起動秒の検証」も足すよう勧めたが
**採らなかった**。launch 側の強制点は certificate 検証を既定で行わず、ここで足すと consumer が
launch より厳しくなって選択強制の範囲を超える。

### 親の実測の訂正

- 段 1 の「C06 経路は無条件に塞がれている」は gate 設置可否の文脈では過大だった。freeze 読込は
  C05 常時拒否より手前にあり gate 自体は発火できる (段 2 plan が反証、親が実行行で再測)。
  ただし成果物影響が 0 なので実装はしない。
- 段 1 の「別 wave が該当 3 file を未 commit で保有」は段 6 時点で古く、branch へ commit 済み・
  未 land が正しい。所有は継続する。
- 段 1 の「起動証明書は凍結時に再計算できない」は理由が不正確で、正しくは「launch 時点の独立した
  commitment が保存されていない」である。

### 実測 (親が実走)

- 変異 matrix: anchor commit `88c45eeaa`、baseline PASSED (赤 0)、**KILLED 5 / SURVIVED 0 /
  MISMATCH 0 / TIMEOUT 0**、期待 node 完全一致 5/5。probe 段 (全件 SURVIVED 期待) で観測 node を
  集めてから本走した。
- 焦点走 (実装後): 324 passed。main 取り込み後に再走して 324 passed。
- consumer 走: 631 passed / 7 skipped、815 passed / 2 skipped、1009 passed / 7 skipped。
  `test_s8b_approved.py` の collection error は `from tests import` 未確立による file 選択走の
  偽赤で、本 wave の差分と無関係。
- AI provenance 全史監査: 実装 commit 後 7320 件・新規違反なし、main 取り込み後 7339 件・
  新規違反なし。

### セッション異常

- 段 5 の初回投入は prompt 先頭が単独段 dispatch の宣言形式でなかったため、実装子が
  rc=0・ファイル変更 0 で fail-closed した。宣言を直して別 job-id で再投入し成功。
  同じ形式不備で段 2 plan と段 3 consult 2 本は成果物を出しており、read-only 子と author 子で
  挙動が非対称だった。
- 変異 probe の初回は、親が起動と同 turn で記録用 insight の写しを worktree へ置いたため
  「未追跡 file を検出」で test 実行前に中止した (rc=2)。写しを repo 外へ退避して再走。
- 変異本走の待ち手が、launcher と harness の生存中に空出力で rc=0 を返した。`.done` 非空と
  成果物実在で判定していたので誤って先へ進まず、待ち手を張り直して完走させた。

### 段 8 — 自己改善候補 2 件は予算に阻まれて実施しない

いずれも実測由来だが、D782 / D730 の手順を適用した結果 **収容しない**。

1. `DW-O02` へ単独段 dispatch 宣言の exact 形式を書く。実測: 段 5 初回投入が形式不備で
   差分ゼロ停止。read-only 子は同じ不備で素通りしたので気づけなかった。
2. `DW-M05` へ「起動と同じ turn の書込みも含む」を書く。実測: 変異 probe 初回が
   起動同 turn の untracked 追加で test 実行前に中止。

適用結果: 段階 1 (既存記述の削減) は、削れるのが安全義務を担う文だけで、
「予算のために安全義務を削除・弱化してはならない」に反するため断念。
段階 2 (独立 3 例以上の例外収容) は各 1 例で要件未達。段階 3 (上限引き上げ) は
手順の明確化 1 件に対して不釣り合いなので採らない。

**実測した予算**: 両節とも L2 ではなく L1.5 (段の無条件読了層)。
L1.5 の余裕は **4 bytes** しかない (`DEV_WAVE_L1_5_BYTES_MAX = 9696`)。
必要だったのは `DW-O02` に +365 bytes、`DW-M05` に +301 bytes。
同型の実測が 3 例に達した時点で D730 の例外収容へ回せるよう、ここに数値ごと残す。

## 次の一手差分

### 更新

- [T-2067] **P1・一部完了 (設計択一 2 件は D1325 で終端、選択強制は s8c judge 群まで実装済み)**:
  実装したのは load-only consumer 3 群のうち s8c の床値 verifier / publish だけ。残るのは
  (a) oracle manifest 群への同種の強制 — 設計は確定済みで、対応 test file を保有する別 wave が
  着地したら fixture 追随とあわせて実装する、(b) s8c C06 予算群 — C05 schedule authority が
  着地して budget ledger を生成できるようになった時点で再評価する、(c) 起動証明書の実時間性 —
  独立した外部 commitment 無しには閉じられず、必要な機構は D1241 が禁じている、
  (d) s8c production final claim 配線 — 反復 schedule・attestation authority・判定パラメータ正本・
  3 表と receipt の失敗原子的束縛がいずれも不在。**いずれも D1241 / D1313 の
  advisory / non-certifying 上限を解除しない。**
  base: ef88ba8f9ab1b476d1ee20e0cfc2449bbeffda0e0971dee53ff395301774326e
