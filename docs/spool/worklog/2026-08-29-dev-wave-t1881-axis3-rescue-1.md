---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t1881-axis3-rescue
seq: 1
title: [T-1881] 軸 3 検索の救出物を file 単位で裁定し、規則の正本 1 件を着地させ実行器と凍結物 9 件を後継へ送った (docs のみ、branch worktree-dev-wave-t1881-axis3-rescue、実装面差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

ユーザー起票。main へ一度も着地していない軸 3 検索の実装一式が、4 本の重複した作業コピーに
残っていた。依頼は「最完全版を bytes で特定し、機構の要否を確かめ、file 1 件ごとに land / 破棄 を
判定して fragment へ残し、破棄と判定した対象は branch と worktree ごと撤去する」である。

- **機構は今も要る。要否を理由にした一括破棄は成立しない。** T-1881 の残作業は登録済み query の
  実行である。前登録 §13.1 の blocking 5 件のうち、人間裁定待ちだった B3 は D1206 が閉じた。
  B2 は live preflight、B4 は network-zero の registration preflight、B5 は全 stream の preflight が
  閉じる。**B1 だけは preflight で候補を発見しても alias / work-family の個別裁定まで要り、
  実行器を回すだけでは閉じない** (段 3 が親の説明を訂正した)。
- **bytes 最大の copy が最完全ではなかった。** 実装は resume2 版が 364846 bytes で他 3 本の path を
  全包含する。しかし**テスト file の sha256 は 2 つの author copy で完全に同一**で、実装だけが
  917 insertions / 242 deletions、net +675 行動いていた。現行 main の bytes に対して親が実走すると
  46 passed / 22 failed / 10 errors で、赤 32 件は resume2 が新設した 2 つの契約違反に集中する。
  テストを追随させないまま止まった作業途中の状態である。
- **旧版は緑だったが、その緑こそが採用できない理由だった。** 旧実装 + 旧改訂文書 + 同テストは
  78 passed / 0 failed で完走する (親実測、26 分)。旧実装の production / nonproduction 境界は
  `getattr(transport, "_axis3_artifact_class", None)` を読むだけで、読み取りは module 内 1 箇所しか
  なく独立に裏付ける検査が無い。テスト側は自前の transport クラス 2 つにこの属性を `production` と
  1 行書いて通していた。**緑は境界を偽装して得たものである。**
- **偽装経路は属性 1 行より広い、と段 3 が示した。** 旧 `LiveHTTPTransport` は任意の
  `connection_factory` を受け取ってそれを通信元に使うため、属性を触らずとも模擬応答を production
  として通せる。取得結果が本物か模擬かを決める境界にこの関門を置くことはしない (規律 2)。
  resume2 の著者自身が、これを exact type 検査と private 構築 receipt へ置き換えていた。
- **旧実装と新改訂文書は構造的に組めない。** 旧実装は改訂文書の sha256 を凍結 digest として pin する
  ため、新文書と組むと 35 件すべてが setup 段階で `amendment bytes が段 5 凍結 digest と不一致` で
  落ちる (親実測)。旧実装を採ることは旧文書を採ることと同義である。
- **land したのは 1 件だけである。** `docs/related-work/README.md` の 38 行追加・削除 0 は、
  D1183 / D1206 / D1207 / D1209 を関連研究の規則の正本へ書き下ろした規範文である。main はこの
  4 裁定を 1 度も引いていなかった (実測 0 件)。追加行は改訂文書名も実行器も schema も 1 箇所も
  名指しせず、破棄した 9 件のどれにも依存しない。
- **新改訂文書は正しい版だが、今 land しない。** 新版は旧版より主張を狭め、manager の release gate と
  executor の receipt を分離し、未実装の resume action・tier enforcement・同一 UID 攻撃を限界として
  明記している。しかし header が claim-survey の要求 5 項目のうち**入力 digest の所在と文献 cutoff を
  欠く**。bytes は後継実装の `FROZEN_AMENDMENT_SHA256` が exact に pin しており、凍結物は上書きでき
  ないので、規約を満たさない版でこの file 名を焼かない。header ごと後継 wave が決め直す。
- **親が救出 manifest の field を読み違え、着地可能な変更を破棄しかけた。** {{F:manifest-untouched-since-misread}}
- **段 3 の敵対検査が親の裁定を 1 つ反証し 4 つ訂正した。** 反証は「全 file 破棄」。訂正は事実 8 の撤回、
  B1 の閉じ方、行数、後継 scope である。親は段 1 の途中で事実 8 を自ら実測して撤回していたが、
  段 3 は独立に同じ結論へ到達した。
- 撤去は損失ゼロを 3 経路で確かめてから行った。4 branch とも ahead=0、`check_branch_rescue.py
  --ledger-check` が `not_landed=0` / `indeterminate=0` / `deletion_loss_closure.complete=true` /
  `commit_count=0`、救出物 30 件すべてが manifest・救出複製・worktree 現物の 3 点で bytes 一致。
  rc=2 の不完全は別セッションの登録残骸 3 件と稼働中 wave の root 変動が原因で、対象と無関係である。
  読めない root は損失を過大に数える向きに効くので、0 件という結論は安全側にある。
- 変異 harness は 2 本稼働していたが、どちらも `--repo` が自分の codex worktree で、共有木を見る
  `mutation_worktree.py` / `mutation_fanout.py` は非稼働だった。主 checkout は観測されていない。

## 次の一手差分

### 更新

- [T-1881] **P2・更新**: 軸 3 検索は、規則の正本への裁定反映だけを着地させた。残るのは実行器と
  凍結物であり、救出物はそのままでは採らない。後継は本エントリの新規項が持つ。
  base: 2d3910f720c15377b3c4746bfd6522e2fe60fc888f4d0b5ba308ba9fa4b7c865

### 新規

- {{T:axis3-executor-successor}} **P2・新規**: 軸 3 検索の実行器と凍結物を後継 wave で閉じる。
  対象は実行器本体、launcher、schema 4 本、追随テスト、改訂文書、claim-survey の一覧行である。
  出発点は救出物の resume2 版 (bytes は救出 directory が保持)。要るのは 3 つ。(i) exact type 検査と
  private 構築 receipt を入れた production 境界に**追随したテスト** — 旧テストは自前 transport の
  自己申告で境界を通していたため、そのままでは 32 件が赤になる。(ii) 改訂文書 header へ入力 digest の
  所在と文献 cutoff を足し、実装側の凍結 digest を新 bytes へ張り直すこと。(iii) 新 gate を
  remote attestation として主張しないこと — 同一 UID による一括改変は保証範囲外である。
