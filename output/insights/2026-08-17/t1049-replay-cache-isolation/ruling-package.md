# RP-1 — spool fragment の `base:` を親が取る正規手段が無い

wave: `dev-wave-t1049-replay-cache-isolation-r2` / 2026-08-17 / 段 8 自己改善からの送り

## 実測した事実

1. `docs/spool/worklog/README.md` は `完了` / `更新` / `見送り` の item に
   `base: <sha256>` を要求する。対象が carry stub (`- [T-NNN] (N)`) のとき照合されるのは
   **stub 自身の digest ではなく、carry 鎖を遡った実体 item の digest** である。
2. その digest を計算する公開手段は repo に存在しない。
   `python3 tools/spool_fold.py --help` の option は `--dry-run` / `--show-diff` /
   `--fold-date` の 3 つだけで、digest を出す経路は無い。
   `tools/*.py` を全数検索しても、carry 解決付きの digest を出す helper は他に無い。
3. 実体は `tools/spool_fold.py` の `_extract_latest_active(worklog, archives)` が返す
   `_TaskItem.substantive_digest` にあるが、いずれも先頭 `_` の private であり、
   archives の Mapping を呼び手が組み立てる必要がある。
4. 本 wave の [T-1049] は carry 鎖が (622) → (621) → … と長く遡る典型例で、
   実体 item は `docs/archive/worklog-phase3-0813-535-536.md` にある。
   worklog 上の見た目の行 (`- [T-1049] (621)`) を sha256 しても通らない。

## この構造が親に強いること

親は `base:` を得るために、`spool_fold` の private API を呼ぶ script を自分で書くことになる。
ところが `docs/dev-wave/core.md` の `DW-C00` と `.claude/commands/dev-wave.md` の凍結境界は、
**実行可能な probe / harness / script を「実装面」と定め、Codex `role=author` の実装子に限っている**。
所在不問であり、probe-only も免除にならない。

つまり現状は次のどちらかを選ぶしかない。

- 親が凍結境界を破って script を書く (**本 wave が実際にこれをやった**。逸脱として worklog に記録した)。
- docs 1 行のために Codex author の実装子を 1 本立てる (docs-only wave では明らかに不釣り合い)。

`fold` が lock 内で fail-closed に照合するため、誤った digest が静かに通ることはない。
しかし「正しい値を取る正規手段が無い」ことは変わらない。

## 選択肢

- **(i) `tools/spool_fold.py` に読み取り専用の subcommand を足す** (親の推奨)。
  例: `python3 tools/spool_fold.py --base-digest '[T-1049]'` が carry 解決済み digest を 1 行で返す。
  実装面の変更なので Codex `role=author` が書く。既存の `_extract_latest_active` を呼ぶだけで、
  fold の書き込み経路には触れない。これ以降、親は script を書かずに `base:` を取れる。
- **(ii) 凍結境界に「台帳 field を導出するだけの read-only script は親が書いてよい」例外を作る。**
  安上がりだが、実装面の定義に穴を開ける。`DW-C00` は「小さい、軽量版、test-only、probe-only は
  免除理由にならない」と明示しているので、この方向は防壁を弱める。
- **(iii) 現状維持。** 親は毎回どちらかの不整合を選び続ける。

## 親の推奨と理由

**(i)**。理由は 3 つ。

1. 凍結境界に穴を開けずに解ける唯一の案である。(ii) は規律 2 と同型の「便利さのために防壁を緩める」
   方向であり、`DW-C00` の明文と正面から衝突する。
2. 追加は read-only の出力経路 1 本で、fold の書き込み・採番・ローテーションに触れない。
   受理集合を変えない。
3. 発火頻度が高い。`完了` / `更新` / `見送り` を含む fragment を書く wave は毎回これを必要とする。

## 成果物影響 (DW-G05)

入れない場合、certified 選択・材料レポート・試行台帳の値は変わらない。変わるのは
**dev-wave の凍結境界の実効性**である。台帳を終端する wave のたびに親が境界を破るか、
docs 1 行のために実装子を立てるかを選び続けることになり、前者を選ぶ限り
「親は実装面を書かない」という規律が実測上は成立しなくなる。
