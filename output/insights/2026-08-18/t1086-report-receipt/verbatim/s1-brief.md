# 段 1 brief — [T-1086] oracle 実走後の store 再読を報告 receipt で塞ぐ

## 確定済みユーザー裁定 (2026-08-15 /rulings 全件)
- **報告の receipt で塞ぐ。** judge API の変更は consumer が広いため採らない。最終 store seal は
  [T-1103] と重複するため採らない。
- 起動時の重複検査 = [T-1103] は `docs/phase3.md` 見送り棚に「(b) 現状維持」で確定済み。二重着手なし。
- 恒真にならない負の対照を同じ land で足す。実装面は Codex author (D95)。

## 塞ぐ穴 (実測)
実走**前**は二重防壁がある: `s8b_oracle_driver._prepare_v2_execution` が全 schedule 行の store 実体を
再 hash し (第一防壁)、`pipeline.py` が build 直後に `expected_perf_sha256` で照合する (第二防壁)。
実走**後**は `s8b_oracle_report.build_observations` も `s8b_oracle_judge.judge_oracle` も store bytes を
一切読まない。純増検出力 = **実走終了後〜報告生成までの窓で store bytes が差し替わったことの検出**。
既存被覆の性質検索 (`store_path` の production 読み手全件) = admission validator / floor campaign の
書き込み・resume / driver の実走前 gate / freeze の形検査のみ。post-run の再読は repo に 0 件。

## 実アンカー表
| 位置 | 事実 |
|---|---|
| `orchestrator/campaign/s8b_oracle_report.py:1996`–`2028` | `main()` が `load_ratified_freeze` → `reverify_published_freeze` を既に呼び、`reverified` を捨てて `build_observations(manifest=, output_root=, repo_root=)` を呼ぶ |
| `orchestrator/campaign/s8b_ratified_freeze.py:797`–`809` | `ReverifiedFreeze.binaries_by_cell: Mapping` が存在する (`LaunchValidatedFreeze` と同 field) |
| `orchestrator/campaign/s8b_oracle_driver.py:974`–`987` | 実走前 gate の形: `_store_sha256(out_root, rec["store_path"])` を `rec["binary_sha256"]` と厳密照合 |
| `orchestrator/campaign/s8b_oracle_driver.py:837`–`846` | `_store_sha256(out_root, store_path)` — out_root 相対/絶対の両方を解決し、不在は `None` |
| `orchestrator/campaign/s8b_binary_admission.py:38`–`44` | `PORTABLE_BUILT_KEYS` に `store_path` / `binary_sha256` が含まれる |
| `orchestrator/campaign/s8b_floor_campaign.py:3441`–`3443` | artifact 側 `store_path` は out_root 相対の portable relpath |
| `orchestrator/campaign/s8b_oracle_report.py:1959`–`1978` | observations document の組み立て地点 (`_artifacts.OfficialObservations`) |
| `orchestrator/campaign/s8b_oracle_judge.py:313` / `575`–`600` | `judge_oracle(observations, schedule_projection=, verified_manifest_sha256=, approved_spec_sha256=)`。judge CLI に `--output-root` は無く、store を読む経路を構造的に持たない |
| `orchestrator/tests/s8b_v2_freeze_fixture.py` | v2 freeze fixture (store_path を含む) — 発火条件を満たす既存 fixture |

## 不変条件 (破ってはいけない)
1. `judge_oracle` の呼び出し規約 (位置引数 1 + keyword 3) を変えない。receipt は observations 文書の中を通す。
2. 期待値の権威源は `ReverifiedFreeze.binaries_by_cell` であり、run 自身が WAL に書いた自己申告ではない。
3. report は store を読むだけで書かない。既存 observations key の削除・意味変更をしない。
4. 主張の限度は [T-1103] の条件どおり「単独 oracle 改竄まで」。receipt を封印・偽造耐性として謳わない。
5. receipt 欠落を「緑」に落とさない (fail-closed)。

## provisional 裁定 (親の暫定・攻撃対象)
- **(P1) 受け口**: `build_observations` に keyword-only `binaries_by_cell: Mapping | None = None` を足し、
  `main()` の official manifest 経路だけが必ず渡す。legacy manifest 経路のみ `None`。
- **(P2) 置き場**: observations top-level に新 key `store_reverification`。`SCHEMA_VERSION` は据え置く
  (既存 optional key `spec_sha256` / `measurement_conditions` と同じ扱い)。
- **(P3) 形**: cell ごとに `{cell_id, store_path, expected_sha256, actual_sha256|null, state}`、
  `state ∈ {match, mismatch, missing}`。全件 match のときだけ receipt 全体が `verified`。
- **(P4) judge 側**: `manifest_kind == "official"` の observations に receipt が無い / `verified` でない場合、
  judge は `unknown` (refuse) を返す。**receipt 欠落は緑にしない。**

## 成果物影響 (DW-G05)
実装しないと、certified 選択の proof chain は「実走後に計測 binary の bytes が入れ替わっていない」ことを
一切主張できず、改竄後 store を持つ run でも oracle verdict が緑のまま受理される (受理集合が広すぎる)。
実装すると verdict に refuse 経路が 1 本増え、observations に optional key が 1 本増える。

## 恒真回避の対照 (同じ land)
- 負の対照 A: store bytes を書き換えた木で receipt が `mismatch` を立て、judge が refuse する。
- 負の対照 B: store 実体を消した木で `missing` を立て、judge が refuse する。
- 負の対照 C: official observations から `store_reverification` を丸ごと落とすと judge が refuse する。
- 正の対照: 無改竄で全 cell `match` → receipt `verified` → judge が既存どおり通る。

## 分割方針
実装面 1 本 (report + judge + テスト、所有が同一の証拠鎖のため分割しない)。段 2 プラン 1 本、
段 3 敵対 2 レンズ (正しさ防壁・受理集合が変わるため軽量版は採らない)。
