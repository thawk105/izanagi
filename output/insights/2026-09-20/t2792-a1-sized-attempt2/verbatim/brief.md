# 段 1 brief — [T-2792] A-1 sized attempt-0002 を認可 record で投入し results 稿を書く (2026-09-20 18:1x JST)

- 研究前進: 論文 headline 証拠 paper-story A-1 の sized 本走について、D2172 項 2 が確定した研究目的「同一配置 (同 seed・同物理順) の反復」の
  観察機会 = attempt-0002 (独立再現) を初めて実機で取り、attempt-0001 稿 (`results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`) と
  並記できる単独稿を作る。完了判定 = authorize-rerun rc 0 → submit rc 0 → 3 job driver rc 0 → complete rc 0 → materialize rc 0 (兄弟 dir) →
  results 単独稿 + README 表 1 行 + insight + fragment を commit、受入緑、land。落ちた場合 = 落ちた層・受領証・request ID を insight に記録して
  止める (再投入しない、稿は「投入したが落ちた」までを書く)。
- 確定済みユーザー裁定: D2172 項 2 (択 1、attempt-0002 の 1 attempt 限定)。実装は entry 1736 (commit 886c19259 / ec696308a、D2178) で main に着地済み
  (起点 local main fec4a8187 に含まれることを `V3_SIZED_RERUN_AUTHORIZATIONS` の定数と `run_authorize_rerun` の実在で確認)。D2173〜D2183・spool
  (README のみ) に本件を止める裁定なし。
- scope: (1) fresh submit-tree (detached @fec4a8187、job dir 下、submodule 再帰初期化、lock) + hydrate 2 箇所、(2) authorize-rerun 1 回、
  (3) submit 1 回 → watch → complete → materialize (公開先 = 兄弟 dir `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002`)、
  (4) 公開 leaf を wave worktree へ byte 保持で複製、(5) results 単独稿 `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md`
  (attempt-0001 稿の値を並記、プールしない D1993 項 6、`formal=false` のまま、充足・formal 化は判定しない)、(6) README results 表へ 1 行
  (README は受入の owned-path に入れない)、(7) insight `output/insights/2026-09-20/t2792-a1-sized-attempt2/` + worklog fragment。
  実装面差分ゼロ (変異 matrix 免除、受入全走は免除しない)。図・formal 昇格・3 本目の認可・認可管理の一般化・gate / 検査 / 台帳の追加は scope 外。
- 不変条件: 規律 2 (既存 verifier の anomaly → reject をそのまま)。gate 緩和・先行 attempt-0001 の証拠移動・policy / base の変更をしない。
  submit-tree は投入後 1 byte も書かない。attempt-0001 の leaf・稿・fig9 は触らない (fig9 生成器が leaf と稿を pin)。事前登録 (6047eff0…)・
  policy (a6228bcd…)・追補 (ec696308a) の bytes は変えない。
- 実測環境: 投入は login node から job dir 下の submit-tree。実行は Pegasus 計算ノード (gen_S、1 workload = 1 job = 1 node)。18:06 JST 時点 gen_S
  QUE 13 / RUN 40 / HLD 25。attempt-0001 は投入 → 全終端 13 分 (bench 部)、queue 待ちが加わる。所要見込み 20〜60 分。
- 成果物の形: 上記 scope (4)〜(7)。decisions fragment なし (新しい設計判断なし)。
- 並列分割方針: 段 2・3 省略 (設計択一なし・正しさ防壁に触れない・受理集合不変、投入経路と study は D2172 項 2 が名指し)。段 5 実装子なし
  (実装面ゼロ)。段 6 = read-only codex review 1 本 (一次資料から事実を再抽出する docs-only、DW-C00 の例外規則。レンズ = 稿の数値・日付・
  判定の一次資料照合 + 「言わないこと」の逸脱)。
- 変更面 (実アンカー): `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/**` (新規、materializer 出力の複製)、
  `output/insights/2026-09-20/t2792-a1-sized-attempt2/**` (新規)、`docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md`
  (新規)、`docs/paper-story/README.md` results 表 1 行 (owned-path 外)、`docs/spool/worklog/*.md` (新規 fragment)。

## 条件 dispatch の再評価 (08/09/10/13)

- 08 (freeze / oracle gate / proof chain): 触らない。公開先は新規 dir、既存凍結物の bytes 不変。→ 不成立。
- 09 (凍結成果物の bytes): 変えない。→ 不成立。10: 09 不成立。
- 13 (gate・検証の新設): 無し。→ 不成立。
- 11 (削除): 無し。20 (背景 job + worktree): 成立 → 開始 gate rc 0 済み (`startup-gate.log`)。

## 親の provisional 裁定 (攻撃対象)

- (P1) attempt 名は `attempt-0002` (定数 exact)。record は `authorize-rerun` で置く。`--decided-on 2026-09-20` は定数値であり投入日ではない。
- (P2) hydrate は attempt-0001 と同じ 2 箇所 (submit-tree 既定 staging root + job dir `third-party-hydrated`)。cache 5 本。
- (P3) 段構成 1 → 4 (実装しない) → 親の実測 → 稿起草 → 6 (review 1 本) → 7 → 8 → 9。
- (P4) 稿は attempt-0001 稿と同じ骨格 (§0 位置づけ / §1 条件 / §2 結果 / §3 限定 / §4 欠落 / §5 一次資料)、attempt-0001 の値は「並記」の
  表として §2 に置き、差・比・平均・区間の合成は一切書かない。反復性の判定は書かない (2 attempt の並記は観察であって再現判定でない)。

## 模擬 / 実の差

- 模擬なし。authorize-rerun・submit・job・complete・materialize はすべて実機・実 tree・実 durable base。
- 棚卸し: attempt-0001 と同じ (job body の外部 command は cmake / gcc / g++ / qsub、qstat parser は scheduler_nqsv 委譲)。
  materialize v3 は raw path から attempt を導き、record 一致で兄弟 dir を受理する (`_exact_materialization_destination` の context 3 引数)。
