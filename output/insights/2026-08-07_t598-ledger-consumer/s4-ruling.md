# 段 4 裁定 — [T-598] claude_session_ledger の consumer 結線先

段 2 プラン (`s2-plan-out.md`)、段 3 レンズ A (`s3-lensA-out.md`)、レンズ B (`s3-lensB-out.md`)
に対する親の裁定。**結論: 実装しない (`4→7→8→9`)。** ただし結線先の設計判断は確定する。

## 1. 所見の real / refuted 裁定

### レンズ A (測定妥当性) — 全 7 件を採用

| # | 所見 | 裁定 | 根拠 |
|---|---|---|---|
| A1 | task 単位の raw token 合計は比較可能な系列にならない (正規化子が台帳に無い) | **real / 採用** | 実 pilot の lead time が同一層内で 73.5 倍。台帳の task-level 属性は `task_kind` だけ |
| A2 | before cohort と介入 exposure が設計に存在しない | **real / 採用** | d-v2 payload に介入 ID・比較対象 identity が無い |
| A3 | cap 10 では交絡を分離できない (最良 4 対 4) | **real / 採用** | 実 pilot の実績 n と欠測率 |
| A4 | `worktree → project slug` は実データ上の関数ではない | **real / 採用 (親の M6/M11 を訂正)** | 305 file 集計で 145 file が非 worktree slug 配下に worktree cwd、37 file が cwd 混在、3 file が worktree 間移動。**本 session の transcript 自身も main cwd と worktree cwd を同一 file に持つ** |
| A5 | slug/window は 1 task-run を 1 session へ束縛しない | **real / 採用** | 背景 job・別対話 session を区別する key が無い |
| A6 | fail-open 欠測が施策の効きと相関する | **real / 採用** | 上限到達・strict issue・window 重複は「長い session」で起きやすく、施策は session を短くする |
| A7 | task window と transcript の時計・終端が同じ基準でない | **real / 採用** | task-run はローカル clock、台帳は record timestamp (欠損時 mtime fallback) |

### レンズ B (規約・scope) — 7 件中 6 件採用、1 件は nit 追認

| # | 所見 | 裁定 |
|---|---|---|
| B1 | 未分類 (`unknown`) の consumer を `task_end` 前へ自動結線すると admission 違反 + gate 化 | **real / 採用**。自動結線を今回採らない直接理由 |
| B2 | population payload は現行 privacy 契約のままでは git 追跡不可 | **real / 採用**。無 salt SHA-256 は永続 pseudonym であり、撤回不能 |
| B3 | 新 sibling root の非証拠分類が `output/README.md` と check_docs の lint 外へ出る | **real / 採用** |
| B4 | 選択肢 B は凍結 `task-run/v1` の受理集合を拡張する | **real / 採用**。同一 version 文字列が二つの受理集合を持つのは不可 |
| B5 | sibling root 切替の実 default は 6 箇所 + pilot 初期化の順序が未設計 | **real / 採用** |
| B6 | private な path→slug 複製は欠測でなく**偽ゼロ**を作る | **real / 採用**。段 2 が自認した最弱前提と同根 |
| B7 | 明示された文書変更に byte 予算違反は無い | **real / nit 追認**。`docs/README.md` は TextLimit 対象外を親も実測済み |

### 親 brief の自己訂正

- **M4 は refuted。** `tokens` は `agent_run` 専用 field であり、task 単位の空欄ではない。
  レポートの `0/0` は「token 欄が空」ではなく「agent event 自体が無い」。
  → 親の (P1) の動機付け「欄は設計されていて producer が居なかっただけ」は**崩れた**。
- **M6 / M11 は限定付き。** worktree ↔ project slug の一対一対応は実データで反証された (A4)。
- **M12 は親の記述より強い。** ID 衝突は `FATAL_ISSUES` にも含まれ、`--strict` でなくても失敗する。
- **M13 は限定付き。** 別 root なら現行 CLI (`init-pilot --root`) だけで v1 世代を開始できる。
  コード変更が要るのは task-level event を持つ v2 世代だけ。

## 2. 結線先の裁定

- **(d) task-run 世代 v2 への結線 — 不採用。** A1〜A3 で測定として成立せず、B1〜B6 で規約衝突が
  6 件、production 差分は実見積り 645〜816 行 (段 2 の 350〜500 行は過少)。D205 に照らして過大。
  **再訪条件**: task-run 台帳が次世代 pilot として再開されるとき、その設計の一部として扱う。
- **(a) cron 定期観測 — 不採用。** 基盤が repo に無く、admission 分類は `unknown` (= 自動実行不可)。
  workload 量と交絡し単独では before/after を支えない。
- **(c) claude 側 A/B endpoint — 不採用。** `codex_reasoning_ab.py` は Codex binary・model・
  effort・Codex session ledger を固定した専用 harness で、汎用 provider seam が無い (B のレンズが検算)。
  Claude arm の新設は D205 に照らして過大。**D207 の原則 (因果主張は paired A/B だけ) は維持する。**
- **(b') wave 単位の前向き収集 — 第一候補として確定。ただし本 wave では発効させない。**
  - 形: canonical CLI の `--json` 出力を wave ごとに 1 件、typed artifact として保存する。
    第 3 parser を作らないので D206 に抵触しない。`output/insights/` には構造化 JSON の先例が実在する
    (例 `2026-07-20_task-run-ledger-mutation-ledger.json`)。
  - **slug を repo 側で導出しない。** 導出は Claude 内部実装の複製であり、B6 の偽ゼロを生む。
    呼び出し側が project を明示し、該当 0 件は観測値 0 ではなく**欠測**として記録する。
  - **発効には dev-wave 側の契約行が要り、予算残 13 bytes では land できない** (M10)。
    → **[T-597] (dev-wave 予算の捻出先) に従属する。**

## 3. 本 wave の最重要の発見 (T-598 の前提そのものへの反証)

[T-598] は「結線先が決まるまで削減施策は起票しない — before/after を測れないため」と書いた。
段 3 レンズ A は、**結線を決めても但し書きは解除されない**ことを示した。

前後比較が成立するには、結線に加えて次が要る。いずれも本 wave の scope 外である。

1. 最初の施策より**前に**前向き baseline cohort を完了すること (M8 により遡及は不能)。
2. run ごとの介入 exposure と、比較可能な task identity / 事前層別を固定すること。
3. 想定効果量・分散に基づく n を事前に決めること (cap 10 の標本は評価に使えない)。
4. 欠測 (上限到達・strict issue・slug 失敗・window 重複) が施策の効きと相関しないこと。

したがって **[T-598] の但し書きは、結線の決定ではなく上記 4 条件の設計で解除される。**

## 4. 本 wave で実装する範囲

**実装面はゼロ。** Codex 実装子を起動しない。段 5・6 を飛ばし `4→7→8→9` とする。
実装差分が無いため、**変異 matrix と受入全走は対象外**である。

docs-only の変更として親が行うのは 1 件だけ。

- `docs/README.md` の tools 地図へ `claude_session_ledger.py` の 1 行を足す (親 brief の M3、
  レンズ B が予算対象外を検算済み)。**発見可能性ゼロという実害を塞ぐ最小の変更**であり、
  結線の裁定を待たない。

## 5. ユーザー裁定へ返す項目

- **(U-1) 前向き baseline を今から貯め始めるか。** 貯め始めないと、最初の削減施策は永久に
  before を持てない (M8)。貯めるなら、(b') の発効を [T-597] より先に部分的に許すかを決める。
- **(U-2) 記録先を tracked (`output/insights/`) にするか repo 外にするか。**
  tracked にすると作業時間窓・走査件数・project 識別子が git 履歴へ**撤回不能に**残る (B2)。
  repo 外にすると durability と参照可能性を失う。
- **(U-3) task-run 台帳の次世代 (v2) を開くか。** 本 wave は不採用としたが、開くなら
  claude 消費の task-level event はその設計の一部として再訪する価値がある (B3〜B5 の 6 箇所切替を含む)。
- **(U-4) 「削減施策の起票条件」の再定義。** §3 の 4 条件を [T-598] の但し書きの正式な解除条件に
  置き換えてよいか。置き換えないなら、結線だけで起票を解禁するかを決める必要がある。
