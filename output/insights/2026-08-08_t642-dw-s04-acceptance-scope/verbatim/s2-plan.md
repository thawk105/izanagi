改訂案 O はそのまま実施可能です。独立検算は親 brief と一致しました。ファイル編集・pytest・受入全走は行っていませんが、案 O をメモリ上で仮想適用した `check_docs.main()` は rc=0 でした。

## file:line 実行プラン

[docs/dev-wave/core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79) の2行を、exact 1 件であることを確認して置換する。

置換前:

```text
段 4 で「実装しない」と裁定した場合だけ段 5・6 を飛ばして `4→7→8→9` とする。
worklog には、実装差分がないため変異 matrix と受入全走が対象外だと射程を明記する。
```

置換後:

```text
「実装しない」裁定のときだけ段 5・6 を飛ばして `4→7→8→9` とする。対象外は変異 matrix だけで、
受入全走は実 repo を読むテストがあれば走らせると worklog に書く。
```

2行から2行への置換なので、その後の行番号は変わらない。`## DW-S04 — 段 4 裁定` は [core.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:72) のまま変更しない。

変更対象外:

- [.claude/commands/dev-wave.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:1) は差分ゼロ。
- `tools/check_docs.py`、`orchestrator/tests/**`、他の `docs/dev-wave/**` は差分ゼロ。
- コード・テストの追加、修正、削除は行わない。

## byte 独立検算

旧2行は末尾 LF を除いて 227 bytes、新2行は 225 bytes。物理行の LF を含めても 228 → 226 bytes で、差分は同じく −2 bytes。

| ファイル | 現在 | 置換後 | 個別 cap | 置換後余白 |
|---|---:|---:|---:|---:|
| `core.md` | 8,646 | **8,644** | 9,600 | 956 |
| `workers.md` | 4,575 | 4,575 | 5,000 | 425 |
| `mutation.md` | 3,674 | 3,674 | 3,750 | 76 |
| `operations.md` | 8,301 | 8,301 | 8,400 | 99 |
| 4ファイル合計 | 25,196 | **25,194** | **25,200** | **6** |

これは現ファイルを `wc -c` で再計数し、案 O をストリーム上で置換した内容を再計数した値である。親 brief の「25,196」「案 O は正味 −2 bytes」と一致し、数値前提の覆りはない。

## 既存検査への影響

| 検査 | 赤にならない静的根拠 |
|---|---|
| dev-wave reference の4ファイル閉包 | [check_docs.py:3447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:3447) の登録集合と実体集合は引き続き同じ4ファイル。新しい reference は作らない。 |
| UTF-8・regular file 検査 | 既存 regular file 内のUTF-8文字列2行だけを置換する。symlink、改名、改行形式の変更はない。 |
| 個別 byte cap | [REFERENCE_LIMITS](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:176) に対し、`core.md` は 8,644 ≤ 9,600 bytes。 |
| 最長行 chars 予算 | `core.md` の `TextLimit(9_600)` は `max_line_chars=None` で、最長行検査自体が適用されない。新79・80行もそれぞれ 58 chars、40 chars。140 chars 制限がある入口は変更しない。 |
| 4ファイル合計 cap | [check_docs.py:3558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:3558) に対し 25,194 ≤ 25,200 bytes。 |
| 個別 cap 総和の構成上限 | [_check_dev_wave_reference_cap_sum](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:3362) が見る定数は無変更。26,750 ≤ 25,200×110%=27,720 bytes。 |
| 節 ID の実在・孤児 H2 | [REQUIRED_REFERENCE_SECTIONS](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:395) の `DW-S04` は引き続き exact 1 件。見出しを変更せず、新しい H2 も作らない。 |
| 段・条件 dispatch | 入口の段4参照は [dev-wave.md:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:64) のまま。入口、reference path、section pair を一切変更しない。 |
| core 固有 literal pin | 機械 pin は `DW-S09` の land helper・受入順序であり、`DW-S04` 本文ではない。[check_docs.py:3803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:3803) の対象外。 |
| workers の reasoning pin | `workers.md` を変更しないため `DW-S02`／`DW-S03` の `reasoning=max` は不変。 |
| living-doc 共通検査 | 新文には腐敗する行番号参照、`現在は Phase`、`次 =`、pin literal、D番号、拡張子付きの不存在 path がない。 |
| spool schema guard | 後述の frontmatter、exact 2 H2、`remaining`、`base` を守れば schema finding は生じない。`base` の鮮度だけは `check_docs` ではなく `spool_fold.py --dry-run` で確認する。 |

案 O の仮想置換だけを本番 `check_docs` 読取経路へ注入した静的確認結果は rc=0、`check_docs: 違反なし`。これは最終ファイル群やpytestの実測ではない。

### `orchestrator/tests/` の関連テスト

- [test_check_docs.py:6396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/orchestrator/tests/test_check_docs.py:6396) `test_real_repo_clean` は実 repo の `tools/check_docs.py` を実行する。上記仮想適用で同経路が rc=0 になることを静的確認済み。
- [test_s8c_preregistration_invariant.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/orchestrator/tests/test_s8c_preregistration_invariant.py:257) は `check_docs.main()` 経由で全 living docs、したがって `core.md` も読む。新2行は共通検査の検出語を含まない。
- `test_check_docs.py` の予算・節・dispatch positive-control 群は合成 `docs/dev-wave/**` と定数を検査する。checker、定数、見出し集合を変更しないため期待値は変わらない。
- reasoning pin 群が実 repo から直接読むのは `workers.md` だけで、今回の対象外。
- テスト木と `check_docs.py` には旧文、新文、`4→7→8→9` の exact 本文 pin はない。

`test_real_repo_clean` が存在するため、「実 repo を読むテストがあれば」の条件は成立する。親は repo root で `python3 tools/run_tests.py` を追加 flag なしで実行する必要がある。ここでは未実行であり、結果は主張しない。

## 規範の保存照合

| 失ってはならない規範 | 置換後の根拠 | 判定 |
|---|---|---|
| 段5・6の skip | `「実装しない」裁定のときだけ段 5・6 を飛ばして` | 残る |
| 遷移順 | exact literal `` `4→7→8→9` `` | 残る |
| worklog への射程明記 | `対象外は…だけで、受入全走は…走らせると worklog に書く` | 両方の射程を記録 |
| 変異 matrix が対象外 | `対象外は変異 matrix だけ` | 「だけ」により限定 |
| 受入全走の条件 | `実 repo を読むテストがあれば走らせる` | 残る。本 repo では条件成立 |

## 記録側の手順

[docs/spool/README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/spool/README.md:28) と [worklog/README.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/spool/worklog/README.md:5) に従い、canonical `docs/worklog.md` は直接編集しない。

現ブランチ規約では、追加先を次とする。

```text
docs/spool/worklog/2026-08-08-dev-wave-t642-s04-scope-1.md
```

frontmatter:

```yaml
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t642-s04-scope
seq: 1
title: T-642 DW-S04 の受入射程を改訂した (docs のみ、実装差分なし、branch worktree-dev-wave-t642-s04-scope)
---
```

本文は exact に `## 本文`、`## 次の一手差分` の2 H2だけをこの順で置く。

- `## 本文` には、段5・6を skipしたこと、`4→7→8→9`、変異 matrix が対象外であること、実 repo テストの存在により親が受入全走を行ったことを記す。
- 受入コマンド、checkout、rc、passed/skipped/failed、各静的検査結果は、親の実測後にだけ書く。予測値や未解決の結果欄を先置きしない。
- `## 次の一手差分` は `### 完了` だけでよく、他の active T は fold が自動 carry する。

```markdown
### 完了

- [T-642] `DW-S04` の受入射程改訂と必要な受入・記録を完了した。
  remaining: none
  base: ba6a72db24c2b9f9782ecb7693c7f6b769be751adb1d45f56f6e09c70ef1e282
```

この `base` は現在の T-642 実体3行を末尾 LF 1個に正規化して再計算した値。並行 fold があり得るため、fragment 作成直前にも再計算し、[spool README:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/spool/README.md:72) に従って次を親が実行する。

1. `python3 tools/check_docs.py`
2. `python3 tools/spool_fold.py --dry-run`
3. `python3 tools/run_tests.py`
4. `python3 tools/check_codex_agents.py`
5. commit 後に `python3 tools/check_ai_provenance.py`

wave 側では fold しない。親 brief 指定の insight 1本は `output/insights/2026-08-08_t642-dw-s04-acceptance-scope.md` とし、冒頭に `authority: none` と `default_effect: no-state-change` を置く。これは記録物であり、`docs/dev-wave/**` のbyte合計には入らない。

## 総括

- `core.md:79-80` の exact 2行だけを案 O へ置換し、入口・節 ID・コード・テストは変更しない。
- 独立検算は `core.md` 8,644 bytes、4ファイル合計 25,194/25,200 bytesで、親 brief の前提を覆す相違なし。
- 変異 matrix は対象外だが実 repo テストが存在するため受入全走は親が実施する。pytestは本回答では未実行。