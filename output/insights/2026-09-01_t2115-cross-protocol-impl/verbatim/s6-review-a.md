## 所見

### 1. trace-hook admission はビルド対象 source に束縛されていない

- 主張: admission は source 依存ではあるが、実際にビルドされる current-pin source の hook には束縛されていない。任意の未追跡・未使用 `.cc` を置くだけで受理へ反転できる。
- 根拠:
  - 述語は protocol directory 以下の全 source 拡張子を `rglob` し、3 個の正規表現が同一 file に現れるだけで真になる。コメント内の hook、`#if 0` 内の include、TRACE guard 外の hook も受理する一方、docstring は include を `active` と表現している。[between_run_floor.py:111](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:111)
  - mocc の build graph は `transaction.cc`、`util.cc`、`lock.cc` を明示列挙しており、例えば `cc/mocc/decoy.cc` は走査されてもコンパイルされない。[CMakeLists.txt:1](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/external/ccbench/cc/mocc/CMakeLists.txt:1)
  - 後続の source evidence は未追跡 file を明示的に無視するため、その decoy は build admission receipt に入らない。[source_digest.py:2134](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/source_digest.py:2134)
  - source 判定は boolean のまま先に消費され、その後に別 snapshot の `resolve_evidence` と build が行われるため、TOCTOU にも束縛がない。[between_run_floor.py:290](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:290)
  - 合成 source 正例自体は実在し、述語は恒真・恒偽ではない。しかし main 経由の正例は `resolve_evidence` と build を stub しており、検査 source と build source の同一性を通していない。[test_between_run_floor.py:282](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:282)
- 成果物影響: hookless な mocc build でも floor JSON を生成でき、その値が screening threshold または Layer 3 の `env-record` として採用され、従来の拒否・no-match が公式レポートの値と source 参照へ変わる。
- 判定: must-fix
- 確信度: 高

### 2. 「canonical genome」検査が body を検査せず、malformed record を受理する

- 主張: 共有 helper は `|` より後を完全に無視するため、`mocc|garbage`、非整数値、重複 flag、非正準順序を canonical genome として受理する。
- 根拠:
  - helper は型、`|`、空 protocol だけを検査し、`_body` を捨てている。[genome.py:121](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/genome.py:121)
  - 正規の canonical 契約は `Genome.canonical()` の `name=int` を名前順に並べた形式である。[model.py:56](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/model.py:56)
  - screening は弱い helper を通った同 protocol record の CV をそのまま返す。[screening_driver.py:150](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/screening_driver.py:150)
  - Layer 3 は同じ入力を `protocol_match_basis="canonical-floor-genome"` と表示して一致候補にする。[layer3_report.py:391](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/layer3_report.py:391)
  - 追加 test は欠落、非文字列、separator 欠落、空 protocol だけで、malformed body の負例がない。[test_screening_driver.py:260](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_screening_driver.py:260)
- 成果物影響: malformed calibration record の CV と source hash が screening policy・公式 Layer 3 report に入り、しかも canonical provenance と表示される。
- 判定: must-fix
- 確信度: 高

### 3. M1 の追加 test は単一理由ではない

- 主張: M1 の protocol 比較を除去すると、同じ workload の silo/mocc 2 file がともに `matches` へ入り、後段の一意性検査が拒否する。したがって test の赤は protocol 比較だけを理由にしない。
- 根拠:
  - 正例は同 workload の 2 protocol file を同時に置く。[test_screening_driver.py:231](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_screening_driver.py:231)
  - protocol 条件の後ろに `len(matches) != 1` の独立した拒否層がある。[screening_driver.py:157](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/screening_driver.py:157)
  - wrong-protocol 1 file だけを置く M1 用負例は追加されていない。対して M2 にはその形の負例がある。[test_layer3_report.py:2865](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_layer3_report.py:2865)
- 成果物影響: runtime の受理集合は直ちに変わらないが、M1 の単一理由 mutation 証拠は成立せず、protocol 防壁の退行診断を誤帰属する。
- 判定: nit
- 確信度: 高

## 裁定契約への適合表

| 項目 | 判定 | 根拠 |
|---|---|---|
| §3.1 編集面 | 満たす | 作業木は指定 production 8 file と test 8 file のみ。docs、`output/`、submodule、commit 済み変更は認めなかった。 |
| §3.2 genome 空間 | 満たす | mocc は 3 boolean 軸・制約なし・8 genome。RWLOCK、delay、YCSB 限定性も notes に明記。[genome.py:87](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/genome.py:87) |
| §3.3 floor/admission | 部分的 | baseline、stem、create-only、現 mocc の build 前拒否、合成正例は実装。ただし所見 1 のとおり build source への束縛がない。 |
| §3.4 Layer 3 照合 | 部分的 | `(protocol, records, threads, workload)`、WAL 解決、missing/multiple の no-match、legacy 根拠は実装。malformed body を canonical として通すため完全ではない。 |
| §3.5 canonical 解析 | 部分的 | screening と Layer 3 は helper を共有するが、所見 2 のとおり canonical body を検証しない。 |
| §3.6 受理集合 | 部分的 | genome 欠落等の明示 4 類型、mocc space、現 mocc の拒否は実装。未使用 source による admission 反転と malformed body の受理が宣言集合を広げる。 |

## 実装のどこが正しいか

- 現行 tree では silo source が正、mocc source が負、hook を持つ合成 mocc source が正となるため、trace 述語は固定 protocol allowlistや恒真検査には退化していない。
- silo baseline の genome と既存 stem は維持されている。既存 4 floor JSON も canonical silo genome を持ち、各 caller は実 baseline の `protocol` を転送している。[backoff_sweep.py:167](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/backoff_sweep.py:167)
- protocol 欠落・複数 campaign は両 floor が no-match、wrong-protocol floor も不一致へ倒れる。[layer3_report.py:419](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/layer3_report.py:419)
- legacy within-run は mocc に一致せず、silo 一致時には `genome-absent-legacy-record` を明記しており、値の出所を確認済み silo genomeとは表示していない。[layer3_report.py:449](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/layer3_report.py:449)
- screening 候補は引き続き `pipeline.evaluate` を通り、verify 完了後だけ COMMIT する。accepted Layer 3 report も verified receipt と certified campaign view を要求しており、候補 fitness の新しい verify bypass は見つからなかった。[pipeline.py:1410](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/pipeline.py:1410)
- M2 は wrong-protocol 1 file、M3 は current mocc、M4 は `SPACES` 直接 lookup を使えば、前後の別拒否層なしで単一理由になる。
- 既存 test の期待反転、skip、削除、緩和は見つからなかった。

## 総括

最重要所見は、trace-hook admission が実際にビルドされる source evidence に束縛されていない点である。  
さらに malformed genome を canonical と表示して公式 report へ採れる経路が残る。  
M1 の mutation test は後段の一意性拒否が重なるため単一理由ではない。  
pytest は依頼どおり実走せず、本結論は静的読解による。