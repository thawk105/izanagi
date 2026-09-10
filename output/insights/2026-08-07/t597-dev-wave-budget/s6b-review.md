## 所見

### B-01

- **ID:** B-01
- **主張:** `DW-S09` の縮約は意味等価でない。「全非成功結果を `DW-STOP` へ送る」と「既存 branch を報告する」が移設先に残っていない。
- **根拠:** 削除前は `60314069^:docs/dev-wave/core.md:107-109` が両義務を明記する。変更後の `docs/dev-wave/operations.md:129-131` は branch の再利用を定めるだけで報告を要求せず、入口終端 `\.claude/commands/dev-wave.md:112-114` の報告項目にも branch がない。helper には複数の非成功 status がある (`tools/dev_wave_land.py:40-50`) 一方、checker は残した 2 literal だけを pin する (`tools/check_docs.py:3750-3775`)。
- **深刻度:** **must-fix**
- **成果物影響:** stale/busy・未知 status 後の fresh context に既存 branch が伝わらず、安全な再利用や停止判断を失う。

### B-02

- **ID:** B-02
- **主張:** 待ち手 3 条を `DW-C00` に置くと、必要な操作時点に再 dispatch されず採録が空振りする。
- **根拠:** 本文は `docs/dev-wave/core.md:17-18`、dispatch は wave 開始時だけ (`.claude/commands/dev-wave.md:60`)。事故は通知ごとの再生成・生産者停止後の残留であり、義務が必要なのはその都度である (`rulings-inbox/2026-08-05-background-waiter-duplication.md:8-17,23-28`)。reference は操作直前に読む契約 (`docs/dev-wave/operations.md:3-4`) ともずれる。`DW-O01` を generic な背景 process lifecycle へ広げ、条件 01 を「背景 process／待ち手の生成・再利用・停止・通知処理直前」に変更するのが既存 leaf を使う最小案。
- **深刻度:** **must-fix**
- **成果物影響:** wave 後半の land・supervisor 待機で同条件待ち手の大量生成と孤児化が再発しうる。

### B-03

- **ID:** B-03
- **主張:** 段 4 の raw-byte 会計は 1 byte 過少である。
- **根拠:** `DW-C00` 追記は本文 185 bytes に段落区切り LF 1 byteを加えた **186 bytes**。したがって core は `8,534−238+186=8,482`、総計は `25,187−404+249=25,032`。段 4 の `+185 / 8,481 / 25,031` は誤り (`s4-adjudication.md:59,85-89`)。
- **深刻度:** **nit**
- **成果物影響:** gate は通るが、裁定記録の採録量 `248` と余白 `169` は raw-byte 証拠として使えない。

## 静的照合結果

raw UTF-8 byte gate はすべて通る。

| 文書 | 計算 | 実測 | cap |
|---|---:|---:|---:|
| core | `8,534−238+186` | **8,482** | 9,600 |
| workers | `4,668−93` | **4,575** | 5,000 |
| mutation | 不変 | **3,674** | 3,750 |
| operations | `8,311−73+63` | **8,301** | 8,400 |
| 合計 | `25,187−404+249` | **25,032** | 25,200 |

cap 総和も `9,600+5,000+3,750+8,400=26,750 ≤ 25,200×110%=27,720`。

そのほかの判定は以下のとおり。

- checker/test の literal pin、必須 H2、段・条件 dispatch、allowlist、Codex-first literal は静的に整合。`DW-S09` の required literal は各 1 件、helper は core の節内 1／節外 0、operations の `DW-O23` 内 1／全体 1。
- `.agents/skills/dev-wave/SKILL.md:43-49` は共通 dispatcher 委譲と generic な失敗終端を保持し、leaf helper path を重複していない。ただし B-01 の branch 報告欠落は補えない。
- Sup-1、Sup-2 と残留 `.done` の dispatch は適切。特に `.done` は条件 01 の再投入直前に読まれる。
- 裁定束は worklog の 4 件と一致する (`worklog-phase3-0806-263-264.md:429-430,798-802`)。既採録の pgrep と既 pin の期待 node 完全一致を除き、残る `.done`・待ち手だけを採録する線引き自体は正しい。機構名検索・解除条件棚卸し・その他需要の見送りにも過不足はない。
- 余白 168 bytes を束外需要へ自動配分しない判断は、予算を quota とせず未裁定変更を routing する `docs/skill-self-improvement.md:24-37,48-51` と整合する。
- trailer は適合。実装面に Codex author があり、author 2 行はいずれも scope 付き。最終 trailer block は連続し、`Co-Authored-By` は存在しないため位置違反もない。

## 総括

- **must-fix:** 2 件
- **実測:** core **8,482** / workers **4,575** / mutation **3,674** / operations **8,301** / 合計 **25,032 bytes**
- **判定:** **NO-GO**
- pytest・checker・実行系検査は行わず、commit blob と契約本文だけを静的に照合した。