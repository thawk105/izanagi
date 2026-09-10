# 段 1 brief — [T-682] provenance 既知違反 23 件の登録 + probe の .md 逐語移行

base = bcda1c02 / branch worktree-dev-wave-t682-provenance-known-violations
worktree = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations

## scope (ユーザー指示 2026-08-09、裁定 2 本に束縛)

1. `tools/check_ai_provenance.py` に形式違反用 kind 定数を追加し `_LEDGER_FINDING_KINDS` へ加える。
   追加 kind の entry は `note` 必須を機械強制する。
2. `KNOWN_PROVENANCE_VIOLATIONS` へ 23 件を裁定参照つきで登録
   (形式違反 22 件 + `2c1929533a6f641b513f4f7990fe06e6cdb383b1` の missing-codex-author 1 件)。
3. `output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py` を
   同 directory の markdown fenced block 逐語へ移す。
4. 上記に必要な既存テストの更新 (7 entry literal 固定の解除を含む)。

**scope 外**: F37 の land 関門 (`tools/dev_wave_land.py`)、`DW-S01` 系 leaf 節への追記。
並行 wave t139 が担当し所有は素集合 (peer 実測回答: 差分ゼロ・codex 子 0 本)。

## 確定済みユーザー裁定

- 処置は (b) known-violation 登録。**(c) `ROLES` / `IDENT` の許可値拡張は不採用** — 過失に gate を
  合わせない (規律 2)。(a) forward-correction、(d) 履歴書き換え、(e) 放置も不採用。
- 追加 kind の entry は `note` 必須。「内容は正確で綴りだけの誤り」である理由を 1 件ずつ書く。
- 各 entry は `ruling` 参照必須 (既存検査を維持)。
- probe 本体の .md 逐語移行を承認。実行可能体が要るなら repo 外へ置く。
- 実装面なので Codex `role=author` 必須。親は書かない。

## 不変条件

- 未登録の形式違反は今後も赤のまま。登録は列挙した 23 SHA だけを抑止する。
- 既存 7 entry の値・意味・`note` 既定 `""` を壊さない (note 必須は追加 kind に限る)。
- `AGENT_VALUE` / `ROLES` / `IDENT` の受理集合を変えない。
- 移行後も `2c192953` の entry は必要 (履歴 diff は不変)。
- worklog / archive の probe 言及は凍結記録なので触らない。

## 成果物影響 (DW-G05)

実装しない場合、`python3 tools/check_ai_provenance.py` は rc=1 / 23 新規違反を返し続ける。
全 wave が段 7 の commit 後監査で恒久的に赤を見るため、(i) 真の新規違反が 23 件のノイズに埋もれて
検出されず、(ii) 裁定済みの F37 land 関門 (peer wave) が有効化された瞬間に**全 wave の land が
fail-closed で停止**する。台帳・certified 選択の数値は変わらないが、land 経路の可用性が変わる。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 形式違反 finding への kind 付与は、`:963-971` の完全一致ではなく
  `f"{label}: AI-Agent の形式違反: "` の **prefix 一致**で `NormalFinding` へ付ける。
  代案: `validate_message` が `(text, kind)` を返す構造へ変える。
- **(P2)** note 必須は `_known_violation_registry()` に
  `_NOTE_REQUIRED_FINDING_KINDS = frozenset({<新 kind>})` を置き、所属 kind で note 空なら
  `RuntimeError`。既存 kind の `note=""` は従来どおり許す。
- **(P3)** kind 定数名は `MALFORMED_AI_AGENT = "malformed-ai-agent"`。
- **(P4)** `ruling` 文字列は **worklog 番号を使わない**。fold の採番は land まで確定せず並行 land で
  ずれるため、rulings-inbox の file 名 + 日付で書く。既存 7 件の `worklog(284)` 形式とは
  異なる表記になる。
- **(P5)** 22 件の `note` は 1 行ずつ個別に書き、`role=orchestrator` と `model=claude-opus-5[1m]` の
  どちらが不適合かと、当該 commit の変更 path 種別 (実装面 / merge / docs / 変異台帳) を含める。
- **(P6)** probe の移行先は同 `verbatim/probe_split_window.md`。冒頭に元 path と元 bytes の
  sha256 を書き、本体を ```python fenced block へ入れる。repo 外の実行可能体は作らない
  (再実行の需要が現時点で無いため)。

## 分割方針

実装単位は 1 本 (`tools/check_ai_provenance.py` + `orchestrator/tests/test_check_ai_provenance.py` +
probe 2 ファイル)。kind 追加と 23 件登録は同一 dict / 同一検証関数に触れるため素集合に割れない。
probe 移行は独立だが小さく、同一子に含めて往復を減らす。
`README.md` / `package.md` の path 表記更新は docs なので親が行う。
