---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t843-coder-value-integrality
seq: 2
title: [T-843] 非整数 coder.value が受理される経路を塞いだ。計算式による同種の帰属不一致は未閉鎖で裁定へ返す (コード + テスト、branch worktree-dev-wave-t843-coder-value-integrality、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

段 4 backoff 軸で、非整数の `coder.value` が受理側を通る一方 genome は `int()` で切り詰めた値を
記録していた穴を塞いだ。設計は {{D:coder-value-exact-integral-domain}}。

**方向の決め手は親の probe 実測だった。** 台帳側を実値へ揃える案は `BACKOFF_FIXED` が C++ 前処理器の
`#if` で評価されるため成立しない (`g++ -E -DBACKOFF_FIXED=20.5` が
`floating constant in preprocessor expression` で compile 不能、`=20` は成功)。受理側で拒否する
以外に選択肢がなく、これは受理集合を狭める方向なので絶対規律 2 とも整合する。

**段 1 brief の主張を 1 件訂正した (段 3 の 2 レンズが独立に指摘)。** brief は「非整数拒否の検査は
repo に存在せず純増検出力 100%」と書いたが誤りだった。`orchestrator/codex_roles/manifest.json` が
同 role の `value` を `type: integer` と定義し、`orchestrator/codex_roles/events.py` の
`_validate_schema` が role result に対して実際にこれを検証している。正しくは
**「Codex role の正式出力経路では既に閉じており、harness 境界 (CLI・proposal JSON loader・
直接 `CoderProposal` 構築) で初めて閉じる」**。同 role の semantic policy 側は bool・有限性・
1..1000 を見て整数性だけ欠くが、schema 検証が先に立つため生きた穴ではなく、実装しなかった。

**未閉鎖を明示する。** 本 wave が閉じたのは非整数という 1 つの door だけである。段 3 レンズ A が
別 door を見つけ、親が実測で再現した — 値が整数でも、hole の初期化子に計算式を書けば同じ
食い違いが起きる (`value=20.0` / `now_backoff = 20.0 * 2.0;` は通り実効 40、
`value=50.0` / `now_backoff = std::ceil(50.0 * 1.5);` も fallback 枝で通り実効 75)。閉じるには
`src/coder-spec.md` が coder へ明示的に与えている合成自由度の撤回が要り、正しさの修正ではなく
研究上の能力設計判断であるため実装せず {{D:backoff-hole-expression-attribution-open}} として
裁定へ返した。**帰属の穴が塞がったとは主張しない。**

**段 3・段 6 の内訳。** 段 3 は 2 レンズ計 9 所見。real 6 (うち blocker 2)、nit 3。blocker 2 件は
(a) 計算式経路 = scope 外へ、(b) `drive_iteration` の入口停止経路が sink 再検査を迂回する =
採用し実装した (兄弟軸の trigger-gating driver が入口で候補契約を検査する先例に倣った)。
段 6 は敵対レビュー 2 本とも must-fix / real ゼロ、nit 1 (焦点走の集合表記)。nit は対象 2 file を
追加実走して主張を正確にした。親の焦点走は 14 file で 1501 passed / 10 skipped。

**refuted。** 親 provisional 裁定 (P3) の「role 文書を 1 文字でも変えれば review ledger の pin
3 本が必ず全部変わる」は 2 レンズが独立に反証した。source・manifest entry・description は
それぞれ独立の hash である。role 文書を触らない結論自体は維持したが、根拠は pin コストではなく
「manifest が既に整数を要求しており、欠けていたのは harness の強制側」である。

**エージェント工数.** 段 2 plan 1 本、段 3 敵対 2 本、段 5 実装 1 本、段 6 レビュー 2 本 (レンズ A は
launcher 側の `evidence_status=invalid` で 1 度不採用になり再投入。不採用分の子出力は完全で
`check_codex_output.py` を通っており、再走と合わせて独立 2 走とも所見ゼロで一致した)。
実装子は sandbox 制約で pytest を実走できず「実装済み・未実走」と申告し、実走は親が行った。

**変異 matrix.** 事前登録 7 件。DW-M07 に従い全件 SURVIVED 期待の probe を先に回して観測 node を
集め、その完全集合を KILLED 期待として本走した。baseline PASSED、7/7 KILLED、SURVIVED 0、
MISMATCH 0。受理集合を縮小する wave のため、上限境界を狭める変異 (承認済み正例 1000 が
過剰拒否される) を正例側 control として含めた。

**踏んだ罠.** 段 7 の記録 fragment を変異走行の前に起草したところ、未追跡ファイルとして
変異 harness の clean-tree gate に止められた (rc=2)。fragment を先に commit して再走した。

**段 8 自己改善.** 実測した罠 2 件はいずれも既知型の再発だったため、新規 F を採らず既存 F へ
再発を追記した (F106 = 変異走行中に段 7 の記録を worktree へ書いた 5 度目、F531 = 健全な子出力が
`evidence_status=invalid` で不採用になる 6 度目)。F531 は台帳が定める判定法どおり
`parse_jsonl` へ events を通して `Unterminated string` を得て確定した。docs 本文の編集は行わない。
候補 2 件をユーザー裁定へ返す。(1) F531 の回収手順 (不採用でも `attempt-*.output.md` が
`check_codex_output.py` rc=0 なら `-o` へ複製して採る) を `DW-O01` へ機械化する案 — これは
**採否境界の変更**にあたり、自己改善契約が「実装せず裁定パッケージへ送る」と定める類型なので
親の判断では入れない。加えて `docs/dev-wave/**` の単節予算にも余地が乏しいことを実測した。
(2) 変異 spec の必須 field `timeout_seconds` が `DW-M05` / `DW-M06` に書かれていない — harness の
拒否メッセージが欠落 field を名指しするため自己診断的で、予算を使ってまで書く価値は薄いと判断した。

## 次の一手差分

### 完了

- [T-843] 非整数 `coder.value` が受理される経路を 3 つの seam で塞ぎ、正負例テストを置いた。
  変異 matrix は baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0。
  remaining: none
  base: a803791238b5cbf0144cb169f1196a331e0473e5e1e2870c5150ed4e6cb6863e

### 新規

- {{T:backoff-hole-expression-attribution}} **P1・ユーザー裁定待ち**: hole の初期化子が計算式のとき、
  宣言値と実効値が食い違ったまま整合検査を通る。値が整数でも成立するため整数性の強制では閉じない。
  案 (a) 初期化子を宣言値そのものの数値 literal 1 個へ限定し `src/coder-spec.md` の該当記述を
  撤回する。案 (b) 現状維持とし帰属主張を「宣言値が実装に現れること」まで弱めて明記する。
  推奨は (a)。詳細と実測した通過例は {{D:backoff-hole-expression-attribution-open}}。
