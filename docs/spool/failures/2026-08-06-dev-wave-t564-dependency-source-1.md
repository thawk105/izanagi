---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t564-dependency-source
seq: 1
---

## 新規

### {{F:artifact-ingest-breaks-corpus-completeness}}. 取得した成果物を取り込んだだけで、物理コピーの網羅検査が赤くなった [テスト代表性] [手順漏れ]

- 事象: certification job が成功して新しい試行 directory を 1 つ増やしたところ、
  `output/env/pegasus` 配下の probe 出力の**物理コピーを漏れなく列挙する** golden corpus
  (`test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies`) が
  `calibration.md` の未登録で赤くなった。コードは 1 行も変えていない。
- 根本原因: 「実物が増えると赤くなる」網羅検査が存在するのに、job 成果物の取り込みを
  コード変更と別扱いし、取り込み後に受入を再走させる手順を親の受理手順へ書いていなかった。
  段 6 までの受入は成果物取り込み**前**の tip で緑だった。
- 恒久対応: `DW-O18` の「親がテスト・受入を走らせる」義務は tree を変えた全操作に掛かる。
  job 成果物の取り込みも tree 変更であり、取り込み commit の後に受入を再走させる。
  本 wave では実際に再走させて land 前に検出した (near miss)。
  再走を省いて land していれば local main が赤くなっていた。
- 再発検知: 網羅検査自体が検知器である。取り込み後の受入再走を省かなければ必ず発火する。

### {{F:second-artifact-turns-single-element-pick-nondeterministic}}. 成果物が 2 本目になった瞬間、単一要素前提の選択が非決定へ倒れた [誤前提] [計測汚染]

- 事象: 登録済み較正が 1 本しか無かった間、`next(glob("calibration-*.json"))` は曖昧さなく
  唯一の較正を選んでいた。本 wave が 2 本目を取得したことで、この選択は filesystem の
  列挙順に依存するようになった。選ばれた較正の `samples_mhz` は corpus 全体に対する
  ±2% 基準に使われるため、順序が変われば判定が変わりうる。
- 根本原因: 「いま 1 個しかない」という**実行時の偶然**を、選択の一意性の根拠にしていた。
  成果物が増えるのは正常な運用であり、増えた瞬間に検査が非決定になる。
- 恒久対応: 環境契約が現に指す較正 (`env_contract.lookup(...).calibration_ref`) を明示的に読み、
  参照 bytes の sha256 が契約の値と一致することも検査する
  (`orchestrator/tests/test_env_attestation.py`)。較正が 1 本だった時点の意味は保存している。
- 再発検知: 契約が指す較正が実在しない・bytes が食い違えば同検査が赤くなる。
  実 repo を対象に同型の単一要素前提が他に無いことは静的に確認した
  (他の `next(glob(...))` はいずれも tmp fixture 上であり、独立 2 例の族一般化は成立しない)。

## 再発

### F134

- **再発: 2026-08-06** — certify 再投入で `certify_calibration.sh.o<ID>` / `.e<ID>` が再び repo 直下へ
  返り、clean 要求のある land を塞ぎうる状態になった。`submit_certify.sh` は `qsub` へ
  repo 外の `-o` / `-e` を渡さず、job 側が `PBS_O_WORKDIR` を repo root と解釈するため cwd も
  変えられない。前回 job と同じく job-staging directory へ移して clean 化した。
  submitter 側の恒久対応は本 wave の scope 外として裁定パッケージへ返した。
