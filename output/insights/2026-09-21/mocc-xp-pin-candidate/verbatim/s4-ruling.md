# 段 4 裁定 — dev-wave-mocc-xp-pin-candidate (2026-09-21 14:35 JST 起草、親)

## 事実 (段 3 が走らなかった理由)

- 段 3 相談 2 本 (`s3-consult-A` lane sol / `s3-consult-B` lane luna、14:32:57 投入) は両方 6 秒で rc=2。
  receipt `outcome=launcher_error`、`stop_reason=launcher_error`、出力 0 byte。
  `attempt-0001.events.jsonl` の `turn.failed` 本文 (逐語): 「You’ve hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 26th, 2026 7:35 PM.」
- 段 2 plan (`s2-plan`、14:22:03〜14:32:10、rc=0、41,946 byte、`check_codex_output.py` rc=0) は枠切れの直前に完了して受理済み。

## 裁定

1. **実装しない。** 段 5・6 を飛ばし `4→7→8→9` (DW-S04)。理由: 実装面 (submodule の `cc/mocc/transaction.cc`、driver、test、patch) は
   Codex `role=author` だけが書ける (D95、凍結境界)。枠は 2026-09-26 19:35 (表示どおり、時間帯の表記なし) まで復帰しない。
   親が直接編集して代替しない。従量経路 (credits 購入・API キー) へ切り替えない。
2. **submodule commit C は作らない。** 候補の中身は段 1 probe の blob `e393efbfd5fad7bbe05117b43669ccc0f44abb6a`
   (sha256 `712e31b5cbf2a3a63df442d50203c5c0787c98c83672d49a20210719bf32ebe4`、probe OID `eb8dc6fe`) として記録するが、
   これは親の scratch 上の測定対象であり、Codex author の成果物ではない。次 wave の author が同じ bytes を独立に作ったときだけ、
   この wave の D297 結果が内容同一性で引き継がれる (検査器の入力 = old/new の blob・差分 path 集合・祖先関係。C を作ったら同じ checker を 1 回走らせて確認する)。
3. **plan (段 2) は次 wave の段 2 成果物として流用可、ただし段 3 は未実施。** 次 wave は同じ plan に段 3 相談 2 本を当ててから段 4 を行う。
   (P1)〜(P6) は本 wave では provisional のまま確定しない。plan が brief を超えて足した要素 (hot 正負例 2 走、`.text` bytes 比較、候補固有 7 key、
   land 前 fetch) は段 3 レンズ B (過剰・削除) の点検対象として持ち越す。
4. **brief の訂正 (plan の指摘を採用、親が現物で確認):**
   - 「現行 pin の mocc 結果は常に indeterminate」は広すぎる。正しくは「pinned producer の source (e9e477ca、patch なし) は X/P emitter を持たず
     proof-surface の certification gate が偽 (p5 実測)。e9e477ca + T-2294 patch の診断実走は certified の正例を持つが、pinned producer ではなく
     materializer 登録簿で NON_ADMISSIBLE」。
   - p4 の D297 pass は TRACE=0 前処理 (GCC 11.4 / 12.3、各 16 context) の証拠であり、TRACE=1 の build・実行の証拠ではない。負例 4 本は `git apply --check` の成功まで。
   - p4 script 冒頭コメント (「`#line 17` を除き」) は処理本文 (`#line 17` を残す) と不一致。結果の解釈は本文に従う。
5. **変異 matrix は免除** (実装面の差分ゼロ、DW-S04)。**受入全走は免除しない** (land 対象 tip で 1 回)。
6. **I 面 ([T-2295]) は不足として記録。** 現行 pin で verifier が認識する I emitter は 0 (親 grep + plan の tree 検索)。certification gate は I を要求しない。
   mocc の I を閉じるには write-intent shadow の新設計が要る (plan §7)。
7. **次の一手として起票する:** 2026-09-26 19:35 以降、fresh wave で plan を段 3 に当て、段 5 (候補 patch → 親が C を commit → driver 候補 mode + test) へ進む。

## 記録の範囲 (段 7)

- insight: `output/insights/2026-09-21/mocc-xp-pin-candidate/README.md` + `verbatim/` (brief、plan、裁定、依頼、probe log、D297 report / stderr、相談子の失敗本文)。
  probe の `.sh` / `.py` は repo に入れず job dir に置き、path と sha256 だけ書く。
- worklog fragment 1 本 (完了事実、Codex 枠の復帰日時、次の一手)。decisions fragment 1 本 (D297 の include 規則を緩めず計装側を直す、の設計判断)。
- 敵対検査を受けていないことを insight 冒頭に明記する。
