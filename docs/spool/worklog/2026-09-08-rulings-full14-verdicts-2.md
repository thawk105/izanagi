---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: rulings-full14-verdicts
seq: 2
title: /rulings 全件 第 14 回の裁定 — 索引 17 件を推奨どおり裁定した。うち 3 件は相談が起草推奨を覆し、1 件は射程を広げる側へ倒れた (docs のみ、branch worktree-rulings-full14-verdicts)
---

## 本文

- **ユーザー裁定は「推奨通りで。過剰実装や過剰ガードレールは無しで。main land までよろしく」。**
  索引 17 件すべてが対象で、うち 14 件が推奨のある項、3 件は推奨を付けない
  ユーザー手番 (別 OS 利用者の配置・実行場所分類の実測・push) である。
  横断の scope 制約は {{D:rulings14-scope-minimal}} に置いた。
- **索引だけを出した回は裁定にならないことが 2 回続いた。** 第 13 回は推奨を付けなかった 3 件が
  [T-2405] として持ち越され、本回も初回提示 (`all` = 索引のみ) に対する「推奨通りで」が
  及ぶ先を持たなかった。ユーザーが「推奨をつけてないのってなぜ？」と問い、親が理由
  (入口の出力規則で `all` は索引のみと定めている) を答えたうえで推奨を起草し直した。
  **入口の出力規則そのものが誤解を招く**ため、是正は {{F:rulings-all-mode-yields-unrulable-output}}
  と別 wave の入口修正へ送る (本 wave は裁定の記録に限る)。
- **別系統モデルの相談が起草推奨を 3 件覆した。**
  (1) WAL 束縛 — 起草は「gate を作らず限界を明記」で D1744 を先例に引いたが、
  **D1744 は実検査を足したうえで限界を明記した決定であり誤引用だった。**正しい先例は D1197 で、
  その却下欄は「限界の明記だけで足りるとする」を逐語で退けている。親が現物で確認し、
  **閉じる側へ反転した** ({{D:b10-wal-fields-into-digest}})。本回で唯一、射程を広げる側へ倒れた件である。
  (2) B-4 凍結 spec — 起草の「blob hash だけで束縛」は、期待 blob hash を独立に保持する consumer が
  **0 件**であること (親が実測) から自己整合にしかならず、子孫関係による束縛へ形を変えた
  ({{D:b4-spec-binds-ancestor-not-head}})。
  (3) 起点入口と排他権の世代 — どちらも前提の実測を先に置く条件付きへ変えた
  ({{D:genesis-entry-after-provenance-probe}}、
  {{D:exclusive-generation-needs-consumer-and-prod-evidence}})。
- **明記で足りる件と足りない件の分岐点を裁定の中に書いた。** WAL 束縛と OpenAlex の取得時刻は
  どちらも「gate を作らず明記」の形だったが、前者は明記しても報告の判定が同じ強さで出続けるため
  閉じ、後者は明記が主張の強さを実際に下げるため明記で閉じた。D1197 型かどうかは
  「明記すると主張が弱まるか」で切る。
- **不可逆な発行を 2 回に分けない条件を付けた。** B-10 の限定受理 (lock 記録値への束縛) と
  WAL 3 field の digest 取り込みは、既存 2 系列の literal 再発行が要ると分かった場合に
  同じ変更単位で行う。片方ずつ発行すると「発行しなかった状態」へ戻せない状態を 2 度作る。
- **相談の子は launcher の受理形で 2 度不受理になったが、中身は 2 回とも回収できた。**
  1 回目は走査範囲を repo 全体に開いて `max_model_calls` (既定 100) で打ち切り、
  2 回目以降は範囲を絞って 11〜23 call で完走したが、read-only の子は出力 file を書けないため
  launcher が `f43_fragment` と判定する。判定は受理形の問題であって子の失敗ではない。
- 工数: codex 子 3 本 (consult、うち 1 本は打ち切り)。実装子ゼロ。計算ノード投入は受入と
  provenance 監査のみ。

## 次の一手差分

### 更新

- [T-2410] **P1・裁定済み ({{D:old-grammar-historical-decoder-affirmed}}、2026-09-08
  /rulings 全件 第 14 回、推奨どおり) → 実装待ち**: D1653 を追認し D1563 を supersede する。
  新規実装は不要で、既着地の実装を維持する。残るのは D1653 の「再発行は規律 7 に反する」の
  射程を「live capture された時間付き束縛について」へ狭める記述修正だけである。
  base: 2b93741ba8db28408764c8090a6d49cdc115dece0285267553247581d3d02b44
- [T-2408] **P1・裁定済み ({{D:b10-admit-binds-lock-recorded-prereg}}、2026-09-08
  /rulings 全件 第 14 回、推奨どおり) → 実装待ち**: 限定受理の identity を live 事前登録では
  なく campaign lock 記録値から取る形へ 3 系列そろえて変える。射程は D1597 のまま。
  {{D:b10-wal-fields-into-digest}} の実測結果しだいでは同じ変更単位に畳む。
  base: cfe6f8682c00172ed3397f1babf2559b23b986fad7a4c5c4c6a53ca1d27330db
- [T-2409] **P1・裁定済み ({{D:b10-wal-fields-into-digest}}、2026-09-08 /rulings 全件 第 14 回、
  相談で推奨が逆転) → 実装前に実測**: WAL の `anomalies` / `certified` / `verdict` を既存の内容
  digest へ含めて閉じる。**起草時の「gate を作らず明記」は D1744 の誤引用に基づいており撤回した。**
  着手前に既存 2 系列の literal を再発行せずに重ねられるかを実測する。
  base: 7d356f86ec1b5ff7e0c265c0033763e8c1d0dfbc05e6e68975e5567bd45b1b87
- [T-2406] **P1・裁定済み ({{D:s4-loop-gflags-prologue-port}}、2026-09-08 /rulings 全件 第 14 回、
  推奨どおり) → 実装待ち**: 兄弟 job body の prologue をそのまま移植する。policy 依存の新設は
  認め、provenance file は作らない。契約テストの期待 node と admission registry は同じ commit で
  更新し、`CMAKE_PREFIX_PATH` は driver 本走まで持たせる。
  base: fd13838a2fb944fe8b2e2d3628eed19363aa12d260f8d6faf59b37d5b05e594a
- [T-2412] **P1・裁定済み ({{D:b4-spec-binds-ancestor-not-head}}、2026-09-08 /rulings 全件
  第 14 回、相談で形が変わった) → 実装待ち**: `provenance.source_commit` を spec を著した時点の
  commit とし、load 時は HEAD がその子孫であることを要求する。HEAD 完全一致は外し、blob 一致は残す。
  **起草時の「blob hash だけで束縛」は、期待 blob hash の独立保持者が 0 件と実測されたため撤回した。**
  実 VCS の正例と、spec 改変・別 HEAD の負例を同時に足す。
  base: 908c557e5adc6cf4613d64c7043ce0e6aa019dad847959335168f55e2e1d99fc
- [T-2392] **P1・裁定済み ({{D:genesis-entry-after-provenance-probe}}、2026-09-08 /rulings 全件
  第 14 回、相談で条件が付いた) → 実測が先**: 起点入口を CLI へ足す。ただし着手前に、既存経路で
  起点の commit・argv・入力・lifecycle が記録されるかを read-only で確かめ、記録されているなら
  足さない。
  base: 6d7f9f7f2eb4a5f8436c012af4c5d210f3987bf825df92614467ba1635eaf8f6
- [T-2389] **P1・裁定済み (D1731) → ユーザー手番 (配置) のまま**: 第 14 回で再確認し、
  推奨は付けない。実効層の別 OS 利用者の配置と権限設定は D1436 によりユーザーの手番で、
  AI は代行せず代行案も作らない。閉じるまで D1197 のとおり未閉鎖と明記する。
  base: f83f67183d1aa2b7d899d7c90cbeff4cd0ce46a5161868e8e2e8b7c4d55ebe49
- [T-2148] **P2・裁定済み ({{D:exclusive-generation-needs-consumer-and-prod-evidence}}、
  2026-09-08 /rulings 全件 第 14 回、相談で条件が増えた) → 実測が先**: 鍵配置の完了だけを理由に
  採用しない。世代を強制する production の読み手の実在を read-only で実測し、候補が filesystem の
  性質に依存するなら本番同等条件の証拠も取る。両方揃ってから shortlist の最有力を採用する。
  base: 63a98ad49d3b9cedcd32d6cfe21b272cf26db2597602de9a77e0a164f76e1e32
- [T-2184] **P2・裁定済み ({{D:exclusive-generation-needs-consumer-and-prod-evidence}}、
  2026-09-08 /rulings 全件 第 14 回) → 実測が先**: 鍵儀式の完了は着手条件の 1 つにすぎない。
  残る 2 条件 (読み手の実在・本番同等条件の証拠) を満たすまで最終採用は行わない。
  base: f7020823c908985166d7a55ea4e8b96ec8980428c75264d730de2974cc41c0f2
- [T-2407] **P2・裁定済み ({{D:pegasus-runbook-submodule-checkout-step}}、2026-09-08
  /rulings 全件 第 14 回、推奨どおり) → 実装待ち**: 手順書 §7 へ submodule を対象 PIN へ
  checkout する手順を足す。
  base: 3511f557d663b078d0b79b744f0b30e48ab552f6d88c48aa1c61219959c217cf
- [T-2413] **P2・裁定済み ({{D:b4-no-rep-interleaving}}、2026-09-08 /rulings 全件 第 14 回、
  推奨どおり) → 採らない**: rep 単位の交互測定は採らず現状の手順を維持する。
  再訪条件 = 区間内ドリフトが実際に判定を反転させたことを実測で示せたとき。
  base: d97e7525de1741a07fade1bcf45a2f8fdab35dbec8b3ab52963b71687743e2b4
- [T-2414] **P2・裁定済み ({{D:b4-prereg-cost-paragraph-rewrite}}、2026-09-08 /rulings 全件
  第 14 回、推奨どおり) → 実装待ち**: 事前登録 §11.2 の費用の目安を現構成へ書き直す。
  正式標本の実走前に行う。
  base: 85775dd40f2d3c0d1158d650734bad358e64512aeb0ff3dfc7e2572072c98204
- [T-2267] **P2・裁定済み (D1677) → ユーザー実測待ちのまま**: 第 14 回で再確認し、推奨は付けない。
  実行場所分類の実測はログインノード上のユーザー端末で行うユーザー手番のままとする。
  base: 986c5e512c512989ecdde771e20b5158357a35cee3bfde78061002724f7503d3
- [T-2105] **P2・裁定済み ({{D:freeze-ax-remaining-fields-not-started}}、2026-09-08 /rulings
  全件 第 14 回、推奨どおり) → 着手しない**: 残る approval / pointer / revocation / cancellation の
  各欄は着手せず、関門は `nonconforming` のまま維持する。
  再訪条件 = 3 family bundle が別の理由で実在するようになったとき。
  base: 8515c5322e102e28fa9ed863abebc8afdd21164b2aaa3bfb38876deaf301f783
- [T-2405] **P2・裁定済み (2026-09-08 /rulings 全件 第 14 回) → 終端**: 第 13 回で推奨を付けな
  かった 3 件は本回で推奨つきに再提示し、いずれも裁定された — (1) 起点 producer は
  {{D:genesis-entry-after-provenance-probe}}、(2) 排他権の世代は
  {{D:exclusive-generation-needs-consumer-and-prod-evidence}}、(3) 見送り 7 件は
  {{D:deferred-seven-stay-deferred}}。**同じ形の持ち越しが再発しない仕組みは
  {{F:rulings-all-mode-yields-unrulable-output}} が持つ。**
  base: f6a55d65f9de2f791f6566c9e6112e47ab9415e1aeb6cef7fb11b44ec9a46bf7

### 新規

- {{T:openalex-u12-u13-rulings-recorded}} **P3・新規**: OpenAlex の未採番 2 件を台帳へ載せた。
  窓をまたぐ継続取得は今は決めない ({{D:openalex-quota-window-not-decided-now}}、
  再訪条件 = 窓を最後まで使い切りたくなったとき)。証拠の取得時刻は束縛せず契約へ
  「検査器は取得時刻を検証していない」と明記する ({{D:openalex-evidence-time-unbound-documented}})。
  後者の明記の実装だけが残件で、稼働 branch `worktree-dev-wave-t2090-openalex-fetch` の
  未 land fragment が実体を持つ。
- {{T:rulings-all-mode-entry-fix}} **P2・新規**: `/rulings` の入口の出力規則を直す。
  `all` が索引のみを返す現行規則は、裁定できない形の出力に対してユーザーが「推奨通りで」と
  返す事故を 2 回連続で生んだ ({{F:rulings-all-mode-yields-unrulable-output}})。
  入口の byte 予算 (5,623、現在 5,607) の中で直す。予算の引き上げは独立審査対象なので行わない。

### 見送り追記

- [T-281] 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 ({{D:deferred-seven-stay-deferred}})。相乗り時に直す。
- [T-436] 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 ({{D:deferred-seven-stay-deferred}})。相乗り時に直す。
- [T-982] 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 ({{D:deferred-seven-stay-deferred}})。相乗り時に直す。
- [T-993] 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 ({{D:deferred-seven-stay-deferred}})。相乗り時に直す。
- [T-1007] 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 ({{D:deferred-seven-stay-deferred}})。相乗り時に直す。
- [T-1008] 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 ({{D:deferred-seven-stay-deferred}})。相乗り時に直す。
- [T-1015] 2026-09-08 の /rulings 全件 第 14 回で維持を裁定 ({{D:deferred-seven-stay-deferred}})。相乗り時に直す。
