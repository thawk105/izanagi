# 方向性監査 (2026-07-22) — 診断と最短復帰案 (裁定パッケージ [T-083])

- **発端:** ユーザーの懸念「全然進捗が進んでいないように見える。石橋を叩き続けて渡っていないのでは」。
- **方法:** 親 (claude-fable-5) が roadmap / phase3 / worklog / git 全履歴を確認し、精査を codex 2 本
  (gpt-5.6-sol, read-only) に委譲 — 定量スイープと敵対的方向性監査。逐語 =
  `2026-07-22_direction-audit-quant-verbatim.md` / `2026-07-22_direction-audit-direction-verbatim.md`。
- **位置づけ:** 本文書は診断の凍結と**提案**。採用は [T-083] のユーザー裁定による。採用した場合、
  2026-07-22 に承認済みの [T-080] W-0→W-f 実装列の**執行順序を変更する**ことになるため、
  運用系の自動執行 (routine ruling) には該当しない。

## 1. 診断の確定所見 (要旨 — 全文は逐語 2 本)

- **総合判定: 方向は正しいが速度配分が重大に誤っている (severity: High)。転換点は 07-19。**
- 最後の新規計測は 07-16 の S-1 本走。以後 6 日間、性能計測ゼロ。07-19〜07-22 の 100 commit は
  本線 0 / 防壁 41 / プロセス運用 59。07-16 以降の worklog 75 エントリ中 57 件 (76%) が「計測なし」。
- 07-19 時点で worklog 自身が 8b 実測の「前提は全充足」と記録していたのに、その後に前置された
  freeze 恒久設計 ([T-080]: 設計 + 逐語 約 9,100 行・実装 wave 7 本・所有表 93 path) により、
  floor 実測までの前工程が **10 段** (macro stage 15 段中 11 段目) に積み上がった。
- プロセスの自己増殖の代表 4 系統: (A) dev-wave が自分の作法を追記し続ける正の帰還、(B) freeze 設計の
  ための freeze 設計 (実装 0 byte のまま 2 設計段・7 wave へ膨張)、(C) 裁定が裁定パッケージを生む
  (freeze 差し戻し期の新規:消化 ≈ 5.5:1)、(D) 8c supervisor 12,862 行の先行実装 (phase3 の発火条件
  「8b + 層3 を 1 cycle 回して律速なら」より前 — 明白な順序違反)。
- **弁護側:** 防壁自体は実事故 (D19 偽 faster 反転、F19、F27、07-16 監査の false-green 群、F22) に
  裏付けられ正当。過剰なのは防壁の存在ではなく「防壁を恒久制度・汎用ガバナンスへ昇格させる投資量」。
- **機会費用:** 最小防壁路線なら 07-20〜22 で protocol 凍結 → floor 実測 → v2 候補 → oracle 実走 →
  層3 レポートの約 1 cycle 分に到達できた見積もり。

## 2. 最短復帰案 (科学レーン 7 手)

原則: **T-080 W-0→W-f の全完了を floor 実測の前提にしない。** 最初の 1 cycle に必要なのは
「内容検査を維持した一回限りの移行契約」であり、revocation・expiry・全世代一般化・173 check registry
などの恒久一般化は oracle 後に回す。correctness / identity / measurement gate は一切緩めない
(規律 2/3 は不変 — 削るのは制度化の量であって検査ではない)。

1. **プロセス freeze の宣言** — supervisor real 開放・dev-wave 自己改善・task-run 配線・[T-082]
   全 caller 移行・新規裁定パッケージ化を停止。新規 T 番号は「実走を不可能にする blocker」に限定する
2. **一回限りの移行契約で freeze gate を復旧** — dangling ancestry は typed な provenance observation
   として扱う。D73 の ccbench_pin・機械再構成検査は必ず実行 (例外の丸握り潰しはしない)。holdout の
   design/generator 二重 drift は人間同席の明示 receipt で再 pin。exact bytes / source closure /
   generator / protocol を固定。恒久一般化は後回し
3. **protocol JSON 実凍結 + selector 予測封印** — master seed / env tag は確定済み。on/off/swapped の
   6 セルを 1 回だけ生成
4. **Pegasus floor 実測** — 直前に [T-011] 残存限界 (§5-(viii)) のユーザー受諾。追加設計は入れない
5. **v2 候補生成 + 人間承認** — floor/budget を holdout freeze へ充填、候補全件を correctness/identity
   gate へ
6. **oracle 実走** — crash は既定どおり判定不能、全件報告を維持
7. **既存 renderer で 8b 実レポート生成** — まず事実層を完成、v3 機序仮説層は必要な原料だけ

## 3. backlog 処置の推奨 (worklog 2026-07-22 (6) 次の一手に対して)

| 項目 | 推奨処置 |
|---|---|
| [T-080] W-0 (hooks/task-run 契約) | critical path から外す (floor の正しさと無関係) |
| [T-080] W-a〜W-f | 一回限り移行に必要な最小部分だけ抽出して実施。恒久一般化は oracle 後 |
| [T-068] [T-077] [T-078] | 1 本の「legacy→first-cycle 移行」wave へ統合 |
| [T-066] 恒真隠蔽除去 | freeze 公開前に並行実装 |
| [T-067] exact 化残り | oracle 前に並行。floor は止めない |
| [T-001] [T-002] | floor 実測と並行。公式 report 発行前までに完了 |
| [T-011] | floor 直前に実施 (現計画どおり) |
| [T-009] [T-060] [T-010] [T-012] | 延期 |
| [T-082] reader 移行 | 延期。まず公式 consumer のみ |
| supervisor real 開放 ([T-076] 系) | 8b + 層3 を 1 cycle 回すまで凍結 |

## 4. 裁定項目 [T-083]

**問い: 最短復帰案 (§2 + §3) を採用するか。**

- **(a) 採用 (推奨)** — プロセス freeze を宣言し、次の実装 wave を §2-2 (一回限り移行契約) から始める。
  [T-080] の W 列は §3 のとおり最小抽出へ再構成 (承認済み設計は破棄せず、恒久一般化部分の執行を
  oracle 後へ繰延)。phase3 現行チェックポイントの着手順をこの順序で改訂する
- **(b) 部分採用** — 科学レーンは開始するが、W 列の特定 wave (例: W-a) は先行して完了させる。
  どれを残すか指定が必要
- **(c) 現行計画維持** — W-0→W-f 全完了 → floor 実測の現行順を維持する (「恒久 freeze 制度を完成して
  から科学を再開する」という政策選択として明示的に選ぶ)

推奨は (a)。根拠 = §1 の機会費用と、severity 所見 9 (「現状を続ければ速度配分の誤りから方向逸脱へ
移行する」)。なお (a) 採用時も、W 最小抽出の中身 (どの check/detector を first-cycle に含めるか) は
実装 wave の brief で敵対相談にかけ、正しさ検査の実質を落とさないことを確認する。
