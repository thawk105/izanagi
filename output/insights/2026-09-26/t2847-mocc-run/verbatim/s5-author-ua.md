pin C `68106660` 向けの patch 2 本を作成しました。編集した所有 path は次の 2 つだけです。

| patch | macro | `#if` site 数 | 変更位置（pin C の行） | `apply --check` |
|---|---|---:|---|---:|
| [V25](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-ua/patches/broken-mocc-skip-canonical-restore.patch) | `IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE` | 5 | `cc/mocc/transaction.cc:835–859`、診断は `190`・`1279` 付近 | rc=0 |
| [V34](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mc-ua/patches/control-mocc-negated-temperature-predicate.patch) | `IZANAGI_BREAK_MOCC_NEGATED_TEMPERATURE_PREDICATE` | 9 | 同 `:297,460,567,971`、診断は `190`・`1279` 付近 | rc=0 |

**V25** は `vioctr > 0` で reached を加算します。upgrade ではなく、直後の RLL_ loop が再取得する key と保持中の CLL_ suffix が重ならず、対象 tuple も CLL_ に無い場合だけ復元を省き、changed と `skipped_locks=vioctr` を加算します。その取引の commit 成功時に committed を加算します。対象 tuple の既存保持と RLL_ の再取得先を gate で除くため、この変更による同一 tuple の二重取得・CLL_ 重複は生じず、`unlockCLL()` の二重解放にもつながりません。gate 不成立時は元の復元を実行します。

**V34** は指定の 4 述語を置換しました。`Epotemp::temp` は unsigned の `uint64_t` bitfield、閾値は `DEFINE_uint64` なので、`>=` と `!(<)` は同じ比較結果です。971 行の `||` は括弧で結合を保っています。reached は各 site の述語評価時だけ増え、`site297` などと `boundary297` なども site ごとに記録します。297 行は `else if` 左辺で記録し、971 行は `||` の評価前に記録するため、元の短絡条件を変えません。changed は定義どおり常に 0、committed は reached を含む取引の commit 成功数です。

両 patch とも、`unifdef` が無いため scratch の枝除去スクリプトで**macro 無効時の全文が pin C とバイト単位で一致**することを確認しました。scratch は削除済みです。診断は macro 有効時だけの relaxed atomic と通常終了時の static destructor に置きました。`ycsb_mocc.cc` の通常経路は `main` の `return 0` で、確認した main と runner に `quick_exit`・`_exit` はありません。timeout kill 時の診断行は保証されません。

`g++ -fsyntax-only` は V25 の有効・無効枝と V34 の有効枝で試しましたが、いずれも依存先 `masstree_wrapper.hh` が要求する `config.h` が無く、patch 本文の構文に到達する前に停止しました。構文確認は**未完了**です。build・実走は行っていません。

所有外の後続作業は、`condition_meaning_gate.py` と `screening_driver.py` の登録、対応する 4 test file、`patches/README.md` の記載です。これらは編集していません。

## 総括

2 本とも単独適用の事前確認と無効枝の完全一致を通過しました。構文確認と発火診断の実測は後続の build・run で確認が必要です。