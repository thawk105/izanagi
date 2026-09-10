# [T-522] 段 1 brief — Pegasus admission registry を `tools/pegasus/` 側の機械可読正本にする

## 裁定 (確定済み・攻撃対象外)

worklog (235) の [T-522]: 2026-08-05 /rulings で択 **(b) + grandfather 追認**。

- admission registry は `tools/pegasus/` 側の machine-readable 正本とし、`hooks/guard_bash.py` と
  `tools/check_docs.py` が**投影**してドリフトを機械で止める。
- 未実測 4 本は落とさない。`legacy-admitted (未実測)` ラベルを維持したまま **grandfather を追認**し、
  [T-520] の測定経路確定後に順次実測して昇格する。

## scope (実装する)

- **S1.** `tools/pegasus/` 配下に registry の機械可読正本を新設する。現行 24 entry の
  `path → {class, reason, primary_gate, evidence}` を**文字列 1 文字も変えずに**移す。
- **S2.** `hooks/guard_bash.py` は S1 を投影する。二重表を作らない (`_SANCTIONED_PATHS` の
  local-ok 導出は現行どおり維持)。
- **S3.** `tools/check_docs.py` に registry ↔ docs の投影検査を新設する。三者
  (規範 = `docs/pegasus-runbook.md` §7.0 / 手順 = `tools/pegasus/README.md` / 防壁 = hook データ) の
  食い違いを機械で止める (F122 の恒久対応の残り)。
- **S4.** 裁定を docs に反映する。§7.0 の「`legacy-admitted` を実測へ移すか許可を撤回するかは
  裁定待ち」を、追認済み + [T-520] 後に順次昇格、へ改める。正本の所在も hook から S1 へ移す。
- **S5.** 段 1 実測で見つかった**現行の三者食い違い 2 件**を、受理集合を変えずに docs 側で正直に閉じる
  (下記「実測で判明した新事実」)。

## scope 外

class の反転・新規実測・規範値の変更・自動 dispatch `TASKS` 表の変更・
開発 harness の暫定例外 (§7.0) の見直し・[T-482] の入力 cap。

## 不変条件

- **受理集合を 1 綴りも変えない** (D175 決定 6)。24 entry の class と evidence 文字列は不変、
  local-ok は現行 5 本のまま。
- `orchestrator/tests/test_hooks.py` の `_PEGASUS_EXPECTED_CLASSES` は**独立 golden として literal のまま
  残す**。正本 JSON を読む形へ書き換えると検査が恒真になる。
- registry が読めない・schema 違反・未知 class のときは**許可へ倒れない** (`tools/pegasus/` 配下を
  全拒否し、`_SANCTIONED_PATHS` から pegasus 由来を全除去。非 pegasus の 2 本は影響を受けない)。
- 成果物 (certified 選択・proof chain・凍結 bytes・3 台帳) は本 wave では不変
  (D175「研究状態への影響」と同じ射程)。

## 成果物影響 (DW-G05)

実装しなければ F122 の三者食い違いは人手でしか見つからず、(a) 手順書どおりの操作が防壁に拒否される
(F123 の循環)、(b) 規範が `unknown` と書く実行体が防壁では `local-ok` のまま通る、が再発する。
影響するのは**開発 harness の Bash 受理集合**であり、campaign 成果物の値・受理集合・参照は本 wave では
不変である。

## 実測で判明した新事実 (段 4 で再裁定する)

1. **`submit_silo_ladder_rung1.sh` の矛盾。** 規範 §7.0 の「`unknown` と判明している login 側経路」表は
   同 path を「login で外部 3 repo を clone」として `unknown` に列挙するのに、registry は
   `local-ok` (`legacy-admitted (未実測)`) で hook が許可している。
2. **`collect_receipt.py` の矛盾 (F122 の当該事例が未閉)。** 手順 `tools/pegasus/README.md` §3 は
   login node で `python3 tools/pegasus/collect_receipt.py` を打つ手順を今も書いているが、registry は
   `unknown` で hook が拒否する。F122 は「手順書の方が間違い」と結論済みなのに手順書が直っていない。
3. 規範 §7.0 の `unknown` 表の直後に、表から切り離された孤立行
   (`| tools/codex_worker_launch.py / ... |`) がある。表 parse の障害になる。

## 前提の実測 (段 1 で実施済み)

- baseline: `python3 tools/run_tests.py orchestrator/tests/test_hooks.py -q` → **92 passed, 1 skipped**
  (計算ノードへ自動 dispatch、child rc=0)。`python3 tools/check_docs.py` → **違反なし**。
- 外出しコスト: 24 entry ≈ 6.4 KB の JSON を `open + json.load` するのに **0.49 ms**、
  同機の `python3` process 起動 1 回が **15.0 ms** (= 起動の 3.3%)。hook は Bash ごとに新 process を
  起こすので、外出しは実運用の待ち時間を有意に変えない
  (`logs/probe_json_cost.py`)。
- コード側 consumer は `hooks/guard_bash.py` と `orchestrator/tests/test_hooks.py` の 2 つだけ
  (`_PEGASUS_ADMISSION_REGISTRY` / `_SANCTIONED_PATHS` の全文検索で確認)。
- 先例: `tools/check_docs.py` は既に「runbook の表 ↔ `dispatch_compute.py` の `TASKS`」を照合している
  (`_DISPATCH_RUNBOOK` / `_DISPATCH_SOURCE`)。S3 はこの型の第 2 例である。

## 純増検出力 (検査を増やす wave の要件)

対象 vector = 「registry のデータと、docs が書く実行場所・分類の食い違い」。既存被覆を性質で検索した結果、
`test_bash_pegasus_execution_inventory_is_synchronized` (registry key ↔ 実行体 inventory の同期) と
`test_bash_pegasus_registry_schema_and_fixed_classes` (class/evidence の独立 golden) の 2 本があるが、
**どちらも docs を一切読まない**。docs 側記述との一致を見る検査は現在 0 本。
純増は「規範文・手順文と防壁データの矛盾検出」であり、上記「新事実」1・2 が現に検出対象になる。

## provisional 裁定 (親の暫定であり攻撃対象)

- **(P1)** 正本は `tools/pegasus/admission_registry.json` 1 本 + 共有 loader/validator module を
  `tools/pegasus/` 側に置き、hook と check_docs が同じ validator を通す。
  hook 側の import 失敗は fail-closed で吸収する。
- **(P2)** S3 の照合は bytes 一致ではなく (path, class) / (path, evidence 種別) の**集合一致**で行う。
- **(P3)** 新事実 1 は単調性を守って hook を変えず、docs 側に grandfather 例外として明記する。
  検査は「`unknown` 表に載る pegasus path が registry で local-ok なら、evidence が
  `legacy-admitted` で始まること」を要求する。
- **(P4)** 手順側の検査は、docs の fenced block 中の command 行から `tools/pegasus/<path>` を抽出し、
  **login で直接実行する形** (bare / `bash` / `python3` prefix) なら `local-ok`、
  **`qsub` の引数**なら `local-ok` でないこと、を要求する。新事実 2 はこれで赤になるので、
  README §3 を「login では拒否される。現行の正規経路は ...」へ直す。
- **(P5)** 新事実 3 の孤立行は S3 の parse 対象なので、本 wave で表へ戻す (docs 整形のみ)。

## 成果物の形

registry JSON 1 本 + loader module、hook 差分、check_docs 新検査 + そのテスト、
docs 差分 (runbook §7.0 / README §3 / 孤立行)、変異 matrix、worklog / decisions fragment。

## 分割方針

実装子 2 本を所有分離で並列投入する。
- **A**: `tools/pegasus/` の正本 JSON + loader + `hooks/guard_bash.py` の投影 + hook 側テスト。
- **B**: `tools/check_docs.py` の新検査 + `orchestrator/tests/test_check_docs.py` のテスト。
docs 本文は親が書く (実装子は docs を編集しない)。

## 環境

受入・実測は `python3 tools/run_tests.py` (login から計算ノードへ自動 dispatch)。
docs 検査は `python3 tools/check_docs.py` (login 実行が §7.0 の暫定例外)。
worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry`、
branch = `worktree-dev-wave-t522-admission-registry`、基準 = 67175e1a。
