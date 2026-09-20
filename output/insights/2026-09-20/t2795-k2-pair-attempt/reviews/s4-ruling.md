# 段 4 裁定 — [T-2795] pair 投入 wave (親、2026-09-20 19:35 JST、相談 A / B を読んだ後)

## 相談所見の real / refuted

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1 | P-A (launcher も claim leaf も変えずに同 job・同 campaign の stock 対照を得る既存経路は無い) 支持。`IZANAGI_EXPLORATION_OUTPUT_ROOT` は claim と layout の両方を動かすので同 WAL を満たさない。reservation 不要契約は Pegasus では選べない | real | 採用 |
| A-2 | 親の「stock は condition gate も走っていない」は誤り。`_require_condition_gate` は `run_campaign` より前で正常復帰している (traceback が `run_campaign` 内)。同 identity path は `_scan_protocol_conflicts` から除外され `O_EXCL` が生死を見ずに拒否。D464 の文面は同 path の永久拒否を明記していない | real | 採用 (診断メモを訂正、記録に反映) |
| A-3 | 「TL は stub だけ」は誤り。実 `run_campaign` を戻す test はあるが site `OTHER` (`linux-baremetal`、`single_process=False`) で claim 分岐に入らない。欠落 = 同 durable root・Pegasus 契約での候補→stock 連続起動の結合検査 | real | 採用 |
| A-4 | stock の claim 失敗は候補の certified 記録を無効にしない (取消処理なし、例外は WAL 修復前)。pair 成立は認定できない | real | 採用 |
| A-5 | claim 以外の独立した失敗原因は stdout / stderr に無い (CMake 警告は無害、残 walltime 10,726 s) | real | 採用 |
| B-1 | P-B 妥当。停止理由は「inert 不成立」でなく「STOCK 成立の確認前に claim 取得で停止」。本 wave 可 = 証拠照合・記録・停止判断・整合案の比較。不可 = launcher / claim 変更、claim 削除・退避、別 root 投入、4 巡目、STOCK 要件緩和 | real | 採用 |
| B-2 | (ii) は「同 process」だけでは不成立 (`run_campaign` は呼出しごとに認可 → 同 path の `O_EXCL`)。推奨 = 1 回の認可・claim の所有期間で候補と stock の両評価を行う設計 (呼出し契約の変更を伴う)。(i) は one-shot の受理集合変更、(iii) は防壁を外す、(iv) は同 WAL を破り「別 root = 別 ID」でもない。(v) 保留も択に | real | 採用 (裁定パッケージの形) |
| B-3 | failures は F1019 への再発追記 (F81 / F722 は補助参照、F1018 は主分類にしない、F321 は該当せず)。失敗の記述は「同 identity・同 WAL への二段起動を設計したが、reservation 必須の実認可経路との整合を検査できず、初投入の stock が claim 取得で停止した」。未測定の正直な開示は統合欠陥の不存在を保証しない | real | 採用 |
| B-4 | 「4 走目」は「4 巡目」と誤読される → 「pair 試行における既知候補 10 の追加評価」と書く。−0.49% は省略可。results 稿は本 wave では作らない (上限であり義務ではない、pair も 4 巡もない) | real | 採用 |
| B-5 | 記録先: phase doc の短い項、paper-story README の stale 注記 + results 表の追補、D2183 の事実訂正 (decisions fragment)、D2172 項 3 は撤回不要、launcher insight §0 / §7 に日付付き訂正導線 | real | 採用 (D2183 の「追記」は decisions fragment の新 D として本 wave の裁定を記録する形にする — spool は既存 D への追記機構を持たない) |

## 裁定

1. **正式停止 (DW-STOP: 承認前提を覆す新事実 + 許可範囲で復旧不能)。** pair は不成立 (stock は claim 取得で停止、STOCK 性未確認)。再投入しない。4 巡目は「成立したら」の条件が解除できないので投入しない。launcher / claim leaf を変えない。claim file を消さない・退避しない。r4 用 submit-tree は未使用のまま撤去する。
2. **候補 10 の再評価 (certified、811,956 tps) は保持する** — 当時の判定であり、pair 不成立で無効化しない (規律 7)。「pair 試行における既知候補 10 の追加評価」と位置づけ、round 3 の 3 走との差を改善・退行の根拠にしない。
3. **記録:** round3 README 末尾に pair 試行節、本 wave insight `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md`、worklog fragment (T-2795 更新)、failures fragment (F1019 再発)、decisions fragment (本裁定 = 事実と修復方向)、phase3.md 項 4 に 1 行、paper-story README の stale 注記 + results 表 K2 行の追補、T-2795 launcher insight §0 / §7 の訂正導線。results 稿は作らない。
4. **裁定パッケージ (実装せず記録):** 修復方向の推奨 = (ii') 「1 回の認可・claim の所有期間で候補と stock の両評価を行う driver 設計」(claim leaf は不変、`run_campaign` の認可契約または stock 評価の呼出し形を変える。D553 の sink-local `single_process` と D2183 の CLI 排他への影響を次 wave の段 1 で明示)。却下候補 = (i) 同 identity path の DEAD 再取得 (one-shot の受理集合変更)、(iii) claim の rename (防壁を外す)、(iv) 別 out_root (同 WAL を破る)。(v) 保留も択。修復は Codex author + 敵対検証子の別 wave (実装面・認可契約に触る)。修復後の pair 再投入 (1 job) と 4 巡目 (1 job) の認可は D2172 項 3 の予算の再提示 (ユーザー)。
5. **段 6:** read-only codex review 1 本 (記録の事実再抽出、round3 と同型)。段 5 なし。
6. **やらない理由の最も強い形 (記録):** 「DW-STOP の『直せる赤で終了しない』が勝つので本 wave で launcher を直して再投入すべき」— 却下: ユーザー依頼が launcher 改修を scope 外・再投入禁止と明記し、claim leaf は排他防壁 (D464 / D553) で受理集合の変更に当たる。

## 診断メモの訂正 (A-2)

`diagnosis-pair-0001.md` の「stock は condition gate も build も verify も bench も走っていない」→「stock は condition gate (`_require_condition_gate`、stock 形) を正常復帰した後、`run_campaign` の認可段 (`_authorize_measurement` → `acquire_claim`) で停止し、build / verify / bench に到達していない」。
