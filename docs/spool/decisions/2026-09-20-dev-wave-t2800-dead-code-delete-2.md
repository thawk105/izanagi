---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2800-dead-code-delete
seq: 2
---

## {{D:dead-code-r3-classification}}. 一回限り tool 15 対は 4 対を削除し 11 対を残す — 専用でない test と別裁定の維持指定は対削除の前提を崩す

**決定:** D2172 項 5 R3 (c) の 15 対のうち、`s6_canary_rename.py`、`insights_date_layout.py` + test、`migrate_output_gzip.py` + test、
`plot_t2266_tail_mechanism.py` + test の 4 対を削除し、残る 11 対を残す。R1 (a) の 6 file は裁定どおり削除する。
削除できる条件は次の 3 つの連言で、module ごとに現物 (docstring、git 履歴、決定・事前登録・runbook の名指し、
live module と test からの参照、成果物の所在) で確認できたときだけ削除する。

1. 一回限り — 実施済みで、以後に別の作業が同 module を library・driver として再利用していない。
2. 結果が凍結済み — 成果物・insight・図に結果があり、module が無くても成果物の読み方が変わらない。
3. 現行機構の実装でない — 有効な決定・凍結事前登録が実装として名指ししておらず、live な producer / consumer の対の片側でなく、
   live な test がその module の定数・述語を照合先にしていない。

さらに対削除の前提として、**専用 test が本当に専用であること**を要求する。専用 test に live code の性質を検査する test 関数が含まれる
場合 (例: dispatch の環境除去、registry の包含 pin、残る patch の意味検査) や、その test 関数を別の有効な裁定が維持対象に
名指ししている場合は、対削除の前提が成立しないので module ごと残す。被覆を残すための test 分割は削除でなく新しい編集であり、
削除 wave の scope に入れない。

**理由:**
- 段 3 の敵対相談で、段 1 が「専用」と数えた test 2 本のうち 1 本が live な dispatch 経路の検査を持ち、もう 1 本の 1 関数が
  D2172 項 6 (派生値 pin は削らない) の維持対象に載っていた。棚卸しの「module → 参照する test」の対応は import graph から
  機械的に出したもので、test の中身が module 専用かどうかは見ていない。
- 「現行機構の実装でない」は名前検索で prod import が 0 でも成立しない。凍結事前登録が解析器に契約を課す (counterfactual)、
  live な producer の診断 consumer である (床値 job の checkpoint)、live な test が定数を照合先にする (cohort2 の seeds)、
  別 wave の probe が library として関数を再利用する (非単調性解析) のいずれも、prod import 0 のまま module を現用にする。
- 2 つの有効な裁定が同じ test 関数で重なるとき、どちらかを優先する順位を親が新設せず、両方を満たす側 (残す) を選ぶ。
  優先を望むならユーザーが例外を指定する。

**却下した選択肢:**
- 対削除の前提が崩れた module だけ削り、専用 test から live 被覆の関数を別 file へ移す — 削除でない編集を削除 wave に混ぜ、
  受理集合の変化が 2 種類になる。移す価値があるかは別依頼で決める。
- 項 5 R3 の名指しを項 6 より優先して science-slice の対を削る — 逐語に優先の根拠が無く、派生値 pin を消す。
- 「結果凍結済み」を満たす module を「現行機構でない」の確認なしに削る — cohort2 の seeds や D2035 の errno 連言のように、
  live な test が結果でなく module 自体を照合先にしている場合を見落とす。
