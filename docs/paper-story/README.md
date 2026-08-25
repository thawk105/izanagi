# docs/paper-story/ — 論文ストーリーの横断合成

論文で「何を新規性として主張し、どういうストーリーで語るか」の横断合成を集約するディレクトリ。
`docs/roadmap-history/` や `docs/related-work/` と同じく、**凍結スナップショットを時点ごとに束ねる**構成。

## このディレクトリの位置づけ

- 各スナップショットは**特定時点の凍結物**（新規計測ゼロ・その時点の正典からの導出）。**書いた後は更新しない。**
  内容を更新したいときは上書きせず、新しい日付のスナップショットを追加する。
  ただし**新しい日付の版は、その日付時点の正典全体からの導出でなければならない。**
  一項目だけを直した差分改訂を新しい日付の版として置くと、更新しなかった項目の stale が
  「その日付時点でそう主張した」という新しい嘘に変わる。一項目の決着を届けたいだけなら、
  版を足さずに本 README の「最新スナップショット以後に確定したこと」で指す。
- **図 (`figures/`) も同じ凍結物である。** 複数の版が同じ path を共有するので、誤りが見つかっても
  上書きしない。後継図は別 filename で、再現可能な生成器を伴うときだけ作る。
- 日付なしの入口はこの `README.md`（ポインタは腐らない・スナップショットは腐る、の原則）。
- **正典（矛盾があればこちらが勝つ）:** `docs/roadmap.md` §8（ポジショニング）・`docs/decisions.md`（設計判断）・
  `docs/worklog.md`（時系列）・`docs/phase3.md` + `docs/phase3-main-experiment.md`（Phase 3 完了定義・事前登録）。
  本ディレクトリの文書はそれらの導出物。

## 版の履歴

| 日付 | ファイル | 時点 | headline |
|---|---|---|---|
| 2026-07-03 | `2026-07-03.md` | Phase 2 完了・Phase 3 kickoff 進行中 | 否定的結果 + 空間外合成（P2-4/P2-5） |
| 2026-07-10 | `2026-07-10.md` | Phase 3 段 5 完了（sort 軸 iteration 1 が実 LLM で E2E certified） | 同上（Phase 3 進捗を反映、図つき） |
| 2026-08-23 | `2026-08-23.md` | 縮小主張 S' が headline 不成立で確定（2026-07-16）した後。8b descriptor・層3 事実層 v2・8c bounded MVP・床値 protocol まで機構は進行、新 protocol による床値の実測は未取得 | 同上（第 3 幕を「機構は深化し性能主張は後退した」として再記述。未取得証拠の一覧を A/B/C の 3 群で付す） |

**最新 = `2026-08-23.md`。** 図は `figures/` に、2026-07-10 版の作成時に気づいた示唆は
`notes-2026-07-10.md` に分離。`figures/fig3_arc_status.png` は 2026-07-10 版（Phase 3 段 5 時点）の
現況図であり、2026-08-23 版の第 3 幕の記述とは一致しない（同版 §0 に明記）。

## 最新スナップショット以後に確定したこと（stale 注記）

スナップショットは凍結物なので腐る。ここは腐らない入口として、最新版の記述が既に古くなった箇所を
指す。**矛盾があればここが指す一次資料が勝つ。**

- **P2-4 の利得値（§8 の A-3、および第 2 幕 P2-4）は決着済み。** 2026-08-23 版は「未解決」と
  書いているが、論文採用値は同一 sweep 内の no-backoff control（`BACK_OFF=0`）を分母として
  write-heavy +38.3% / balanced +11.3% / read-heavy -6.6% に固定された。
  `backoff_profile_t48_skew0p9_rr5.json` 由来の +38.5% は D20 により headline 非採用の機序診断値である。
  条件表・再計算・一次資料ポインタは
  `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md`
  （先行分は `output/insights/2026-08-24_paper-story-a3-evidence-integration/README.md`）。
- **`figures/fig2_backoff_mechanism.png` は baseline を誤って label している。** 図中の横破線には
  `stock adaptive backoff` と書かれているが、その値は無 backoff（`BACK_OFF=0`）である。
  2026-07-10 版と 2026-08-23 版のキャプションも同じ誤りを持つ。**旧図と旧キャプションは凍結物なので
  訂正しない。** 詳細は上記 insight。
  **後継図 `figures/fig2b_backoff_sweep_3workload.png`（ベクター版は同名の `.pdf`）を作った。**
  headline 適格な sweep 系列を 3 workload 分描き、基準線を無 backoff 対照 1 本に限定し、
  tracked な生成器 `tools/plotting/plot_backoff.py` で再現できる。再現コマンド・入力・
  キャプション正文・旧図との対応は `figures/README.md` にある。
  **論文で P2-4 の図を使うときは後継図を使い、旧図を使わない。**
- **§8 の A-1・A-2 も 2026-08-23 版の時点から進んだ。** 現況は `docs/worklog.md` と
  `docs/phase3.md` が正本であり、A/B/C の一覧を最新状態として読まない。

## 読み方

- 論文執筆・ポジショニング検討のときに読む。日常セッションのブートには不要（ブートコスト規律 D35）。
- 各版の §（過大主張チェックリスト）は執筆フェーズで消し込み式に運用してよい唯一の例外。
- Phase 3 主実験（phase3.md 後続段 6）が成立すれば headline はそちらへ移動する予定 —
  その時点で新しい日付のスナップショットを追加する。

## 運用ルール（check_docs.py との関係）

- 本ディレクトリの文書は追記型の凍結記録なので `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外。
- 他文書からは**ファイル名（basename）で参照**する（行番号参照は禁止・節名参照にする、check_docs.py 準拠）。
