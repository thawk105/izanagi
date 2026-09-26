# 段 4 裁定 — [T-2838] 択 A (2026-09-26 14:16 JST)

軽量版 (DW-C00): 設計択一は D2211 項 4 で裁定済み、正しさ防壁・受入の受理集合に触れないので段 2・3 は省いた。
一次資料から数値を再抽出する docs-only 記録を含むので段 6 の独立 read-only レビュー 1 本は残す。

## 採否
- (P1) 採用: 雛形は親が既存 script を写して JOBDIR/WT/SLUG を placeholder にし、先頭コメントを写し方の説明に替える。論理・条件値・周期・leader 行は bytes のまま。repo の実装面差分ゼロ。
- (P2) 採用: 真の leader の判定は `/proc/<pid>/cmdline` の引数単位、比較は同時刻の `ps -eo args` に対する裁定の正規表現。採用条件 = 見逃し 0 かつ誤検出 0。
  他 wave の門番を乱さないため、偽 leader の負例を live で作らない (部分文字列一致の門番に 1 本余分に数えられる)。負例は固定文字列 (記憶の codex 子 argv の型、`bash -c …` 型) に正規表現を当てて確かめる。
- (P3) 採用: 採用後の取り直しは同じ probe を逐語で走らせる。雛形経由の門番 log の件数を併記し、効果の判定に足りないことを明記する。

## 採用の順序
1. 雛形を job dir に staging (`staging/run-acceptance-gated.sh`) し、写し元との差分が 3 値 + コメントだけであることを diff で確認する。
2. 生きた受入 leader で (P2) を実測し、合格したら `_shared-templates/` へ置き、記憶を更新する (= 採用)。不合格なら置かず、測った argv を添えて再裁定へ返す (正規表現の改変は裁定の逐語の変更なので親は行わない)。
3. 本 wave の受入は雛形を写して使う (親の実データ dogfood)。

## 変異
repo の実装面差分ゼロのため変異 matrix は免除 (DW-S04)。受入全走は免除しない。

## gate の禁止と正例
新しい gate は作らない。雛形の leader 行が拒否 (数えない) するもの: interpreter 以外で始まる argv (例 `bash -c … dev_wave_wait.py acceptance`、`codex exec … dev_wave_wait.py acceptance …`)。
通る正例: `python3 tools/dev_wave_wait.py acceptance --wave <slug> …`、`/usr/bin/python3 /abs/tools/dev_wave_wait.py acceptance …`。

## 成果物影響 (DW-G05)
certified 選択・レポート・台帳の値・受理集合・参照は変わらない (開発運用のみ)。
