# 段 4 裁定 — [T-851] fan-out exact-N 本走

裁定日時: 2026-08-16 09:15 JST。親 (Claude) が単独で裁定。

## 中心裁定

**R0. 「実装しない」。fan-out の exact-N 本走は、この機体では構造的に実行不可能である。**
段 5・6 を飛ばし `4→7→8→9` とする。実装差分ゼロのため変異 matrix を免除する (DW-S04)。
受入全走は免除しない。

### 根拠 (親の実測 3 点 + 独立 2 レンズの一致)

1. **`memory.peak` がこの kernel に存在しない。** `uname -r` = 5.15.0-186-generic。
   `/sys/fs/cgroup/user.slice/user-31609.slice/` にも `.../session-1909.scope/` にも
   `memory.peak` は無い (`memory.current` / `memory.max` / `memory.oom.group` / `memory.stat` はある)。
2. **生きた cgroup に対して attestation が実際に `False` を返す。** 親が
   `tools/mutation_fanout.py` を import し、`populated 1` の実 cgroup へ
   `_attest_measurement_cgroup` を直接呼んだ結果は `False`。関数は try block の先頭で
   `memory.peak` を読むため (`tools/mutation_fanout.py:405-411`)、OSError で即 `False` になる。
3. **逃がし道が無い。** `validate_admission_receipt` は全 measurement log に対して
   `cgroup_attestation` の真を要求し (`:551-556`)、`run_fanout` は既定引数で
   `_attest_measurement_cgroup` を固定する (`:1421`, `:1546-1556`)。CLI に override は無い。
   したがって**どの admission receipt も必ず拒否され、shard は 1 本も起動しない。**
4. **代替実行面も無い。** 計算ノードでは PBS ジョブに user systemd session が無く
   `systemd-run --user --scope` が成立しない (`docs/decisions.md:8855`)。

### この欠陥の型

**正本 runbook が「存在しない」と実測記録した kernel field を、後発の gate が必須条件にした。**
`docs/pegasus-runbook.md:381-404` は **2026-08-01 実測**として
「`memory.peak` はこの kernel (5.15) に存在しない」と明記し、代わりに専用 scope の
`memory.current` を 3 回以上 sampling して最大値を採る手順を正本としている。
`tools/mutation_fanout.py` の `MIN_CERTIFICATION_REPETITIONS = 3` はこの手順に由来するが、
attestation だけが runbook に無い `memory.peak` の kernel 再読を足した。
**gate は恒偽であり、[T-808] の wave はそれに気づかずに land した** (既存テストは
attestation を stub で置換するため、この矛盾を検出できない)。

## 所見の裁定

| # | 出典 | 判定 | 処置 |
|---|---|---|---|
| A1 | receipt 前の 3 走が admission を通らない bootstrap | **real** | R0 により moot。裁定パッケージへ |
| A2 | 無関係 sleeper・lexical alias で receipt を通せる | **real (プロトタイプ基準では非 blocker)** | [T-849] と同族 (同一 Unix user による偽造)。既に「プロトタイプ基準で見送り」と裁定済みの族であり、本 wave で蒸し返さない。裁定パッケージへ併記 |
| A3 | `memory.peak` を `memory_current_bytes` sample として書く案は捏造 | **real / 採用** | 段 2 プランの当該案を**却下**。R0 の一因 |
| A4 | raw 受理集合は不変だが運用集合は拡大 | **real** | R0 により moot |
| A5 | identity は HEAD 束縛でなく caller 指定 commit の 2 blob のみ | **real** | scope 外。裁定パッケージへ |
| A6-7 | 親 brief の「pin 0 件」に検索証跡が無い | **real** | 本裁定で証跡を明示 (下記 R3) |
| A6-6 / B8 | 親 brief の flock 行番号が誤り・「競合は計算資源だけ」は過剰一般化 | **real** | **訂正する**。lock 実装は `tools/mutation_harness.py:2090-2111`。共有 Git registry・inode・quota も競合面である |
| A7 | plan の負例が「その wrapper がその cgroup で走った」を撃っていない | **real** | R0 により実装しないので moot。裁定パッケージへ |
| A8 | 計測反復の evidence が毎回削除され proof chain が再検証不能 | **real** | 裁定パッケージへ |
| B2 | 3 scope 保持に対し予約が 1 件 | **real** | R0 により moot |
| B3 | OOM/SIGKILL で qsub・worktree が孤児化 | **real** | R0 により moot。ただし fan-out を将来使うなら必須の前提 |
| B4 | registry 差分は path 集合だけで所有権証明にならない | **real** | 裁定パッケージへ |
| B5 | plan の `shutil.rmtree(GROUP_ROOT)` は他 wave を消しうる | **real / 却下** | 実装しないので発生しない。**この案は採らない** |
| B6 | request 全件対応は wave 所有権の保証ではない | **real** | 裁定パッケージへ |
| B7 | cancel 経路は cleanup ではない | **real** | 裁定パッケージへ |
| B9 | 4 セット 24 request の queue / fair-share 影響 | **real** | R0 により投入しない。他 wave を待たせずに済んだ |
| B10 | 1 回の走行から将来の既定採用は推論できない | **real / 採用** | 仮に走れても「採用可否」は 1 回では決まらなかった。R0 と併せて記録 |

## 派生裁定

- **R1. 段 2 プランの `certify` 設計は採らない。** R0 により実装しない。
  加えて A3 (peak を current sample として書く) と B5 (group root の再帰削除) は、
  仮に R0 が無くても**単独で却下**する。前者は記録の捏造、後者は他 wave 破壊の経路である。
- **R2. 正しさゲートを緩めて本走を成立させることはしない。** attestation を緩める・
  反復数を下げる・stub を production へ入れる・`memory.peak` 不在を警告に落とす、はいずれも
  絶対規律 2 の違反であり、本 wave の失格条件である。gate の再設計はユーザー裁定事項とする。
- **R3. DW-O09 の pin 閉包の証跡を明示する。** 実行した検索は
  `grep -rn "mutation_fanout" --include=*.py .` (truncate なし、全出力を確認) と
  `grep -rn "mutation_fanout" --include=*.md docs/ output/`。前者の hit は自 tool・自 contract・
  自テスト 3 file のみ、後者は archive worklog と insight の記述のみで、bytes を pin する
  manifest・trust root・review ledger は 0 件。**ただし実装しないため、この閉包は結論に影響しない。**
- **R4. [T-852] は触らない。** 段 4 で既に「既存逐次経路を変えない」と裁定済み。

## ユーザーへ返す裁定パッケージ (本 wave では実装しない)

**問い: 実行不能と判明した fan-out をどうするか。**

1. **(親の推奨) attestation を runbook の正規手順へ合わせる schema v2 を、別 wave で起票する。**
   `memory.peak` の kernel 再読をやめ、`docs/pegasus-runbook.md:381-404` が正本とする
   「専用 scope の `memory.current` を 3 反復 sampling し最大値 + margin」へ揃える。
   live scope の証明は `cgroup.events` の `populated 1` と `memory.max` 一致で残す。
   **これは gate の受理集合を変えるためユーザー裁定が要る。** 変異本走の wall-clock は
   dispatch queue 待ちが支配項であり、N shard の並行投入で queue 待ちを重ねられる利得は実在する。
2. **fan-out を「実行不能」と docs へ明記して凍結する。** 実装は残すが使わない。
   利点は安さ。欠点は、次に誰かが本走を試みるたびに本 wave と同じ時間を使うこと
   (本 wave の所要は約 1.5 時間)。
3. **fan-out を撤去する。** [T-849] [T-850] も同時に moot になる。
   ただし 3,400 行超の実装と契約テストを捨てることになる。

**推奨は 1。** 理由: gate が恒偽である事実は「設計が間違っている」のではなく
「実装が正本 runbook と食い違っている」だけであり、修正は局所である。
ただし受理集合を変える以上、親が独断で実装してはならない。
1 を採らない場合でも、**2 の docs 明記だけは本 wave で行う** (次の犠牲者を出さないため)。

なお A2 / A5 (同一 Unix user による receipt 偽造・identity の弱さ) は [T-849] と同族であり、
**プロトタイプ基準で見送り済みの族**である。1 を選ぶ場合も、この族を同時に閉じる必要はない。
