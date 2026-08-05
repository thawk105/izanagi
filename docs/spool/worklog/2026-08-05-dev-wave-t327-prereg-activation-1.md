---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t327-prereg-activation
seq: 1
title: [T-327] 8c 事前登録の自動発効を導出値として実装し、条件契約だけを凍結した — 12 述語は意図的に全て充足不能で出荷する (コード + docs、branch worktree-dev-wave-t327-prereg-activation)
---

## 本文

- **ユーザー裁定 ((115)、推奨を蹴って択 (b)) の実装**である。発効を宣言物でなく**導出値**とし、
  承認 record・active pointer・失効 record・activate/revoke 相当の API と CLI を作らなかった。
  条件文の凍結は「本文の複製」でなく保護 hash の世代台帳で行う。設計判断は
  {{D:s8c-automatic-activation}}。
- **本 wave の看板を段 4 で訂正した。** 当初 brief は「発効の実装」と読めたが、実装前の敵対 2 レンズが
  「判定器が起動・受入へ結線されないなら実効性がない」と実証したため、**「発効判定層 + 条件契約の
  凍結」**へ狭めた。結線は並行 wave [T-325] が改修中の同一入口であり、未 land の API へ結線すると
  衝突と二重実装になるため、後続タスクとして裁定パッケージへ送る。
- **出荷時点で 12 述語すべてが充足不能**である。段 6 の敵対レビューが「machine-checkable と称する
  6 述語は、対象機構でなく no-op と名前の存在を証明している」を反例つきで示したため、
  親裁定で 12 件すべてを `machine_checkable: false` に揃え、SATISFIED を返す経路を持たせなかった。
  したがって §6 の 12 機構を実装し §5 を埋めても、評価器を拡張しない限り発効しない。この射程を
  文書・decision・commit message に明記した。green 化は後続タスク。
- **敵対検証は 5 本**: 実装前 2 レンズ (blocker 11 / blocker 2 + must-fix 6)、実装後 2 レンズ
  (blocker 7 / blocker 4)、焦点再レビュー (新規 blocker 3、対応表 closed 16 / partial 6 /
  regressed 0)。real 裁定した所見は fix 3 巡で閉じた (`DW-O16` の上限)。棄却した所見は
  「capability の完全な偽造不能化」— Python の型は信頼境界にならないため、難度向上と正直な限界記述に
  留め、consumer 側の再検証を契約とした。
- **実装前の敵対検証が設計を 3 箇所で覆した。** (i) 発効版 commit を「文書の最終変更 commit」と
  定義する案は、未充足のまま測定して後から機構を実装すれば遡及 green になるため棄却し、
  「pin した commit `C` において発効していること」へ変更した。(ii) 凍結範囲を §5 欄名 + §6 だけに
  する案は、停止規則・全件報告規則・発効ポリシー自体が保護外になるため §1〜§4・§6・§7 へ拡張した。
  (iii) 改訂 (2 世代目以降) は記録さえ付ければ結果を見た後に条件を緩められるため、canonical な
  決定見出しの構造照合を必須にした。**都度承認ではない**ので裁定 (定型コマンドの排除) と両立する。
- **Codex の利用枠が枯渇して一度停止した。** 実装面は Codex `role=author` 必須という規約に従い、
  親が代行せず fail-closed で止め、保全 commit と再開手順を handoff に残した。数時間後に枠が回復し
  再開した。停止中に `gpt-5.6-sol` が一時的に「ChatGPT アカウントでは非対応」と拒否される事象も
  観測したが、その後回復した (モデル一覧キャッシュにも一時的に載らなかった)。
- **未 land の保全 commit を段 6 で畳んだ。** 焦点再レビューが「parser の意味が変わったのに同じ
  `normalization_version` を名乗る g1 が既に導入済みで、freeze 検査が `generation-mutated` になる」と
  指摘したため、保全 commit を soft reset して g1 と最終 parser を同一 commit へ入れ直した。
  local main への取り込みは行っていない段階での履歴整理であり、他 session の所有物には触れていない。
- **裁定パッケージ 8 件をユーザーへ返す。** とくに **[T-325] は未登録 trial ID の探索実走を許すため、
  H1/H2 の事前観測路 (hidden pilot → 結果を見てから §5 を決める) が開く**という所見は、本 wave の
  scope 外だが優先度が高い。逐語は
  `/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/` の `s4-ruling.md` §2 と
  `s6-fix-ruling.md` §2。

- **受入・変異の実測** (Pegasus 計算ノード dispatch): 専用 3 ファイル 134 passed / 0 failed、
  **受入全走 6035 passed / 19 skipped / 0 failed**、事前登録 10 変異は**全件 KILLED**
  (台帳 2 本と突合は `output/insights/2026-08-05_t327-prereg-activation/`)。1 回目の本走で
  m14 (merge の後継判定の緩和) が生存したため `DW-M02` に従い実効 gate へ再照準し、単一理由の
  負例を追加して塞いだ (実装は不変)。受入全走では新設 invariant が `git add -A` の 30 秒 timeout で
  フレークしたため、候補 commit 合成を session 共有にし timeout を延ばした (検査項目は不変)。

## 次の一手差分

### 更新

- [T-327] **P2・一部完了 (本エントリ) → 発効判定層と条件契約の凍結は実装済み、述語の green 化と
  起動・受入への結線が残る**: 自動発効を導出値として実装し、条件契約 (§1〜§4・§6・§7 の規範本文 /
  §5 欄名 / 発効ポリシー / 証拠契約) を hash 世代台帳で凍結した。**12 述語はすべて充足不能で
  出荷**しており、現 repository の判定は常に未発効である。残件 = (a) 条件ごとの充足判定器
  (production consumer を実証するもの)、(b) 起動・受入への結線 ([T-325] land 後)。
  base: 7a2395ef1b7bd0c47bced142aa8b2e4100f4135c1faba79f6f6cf22331cb759d
