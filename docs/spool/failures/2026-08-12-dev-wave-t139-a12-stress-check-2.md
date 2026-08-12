---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t139-a12-stress-check
seq: 2
---

## 新規

### {{F:codex-nfc-evidence-loss}}. codex 子の成果物が 1 文字の非 NFC で全損した [コンテキスト浪費]

- 事象: 段 2 の plan 子が 29,958 bytes の正常な成果物を出し `codex_exit_code=0`・
  `validator_rc=0` だったが、`accepted=false` で捨てられた。1,332 秒と 12 model call が無駄になった。
  再投入した段 6 の fix 子も、別の理由 (下記) で 2 度目の全損を起こした。
- 根本原因: `tools/codex_worker_launch.py` は stdout event と rollout の JSONL 各行が
  Unicode NFC であることを要求する。**落ちるのは「結合文字がある」ときではなく、
  「合成済み文字が存在するのに分解形で書かれた列」があるとき**である。22,474 文字の出力のうち
  原因はただ 1 箇所、`G-bar` を `G`(U+0047) + `U+0304` で書いた列だった (合成形 `U+1E20` が存在)。
  同じ出力の `N-bar` `H-bar` `D-bar` `x-bar` `v-hat` は合成形が無く分解形のままで NFC として
  正当なので無害だった。**どの記号が地雷かは目視で区別できない。**
  一次資料 (追補 A の a11/a12 節) がこの記法を使うため、その wave の子は全員再現する。
- 恒久対応: 数式・統計記法を扱う wave では prompt 冒頭に「出力に Unicode 結合文字
  (U+0300〜U+036F) を 1 文字も使うな。`G-bar` `v-hat` `^T` と ASCII で書け。仕様書の記法を
  引用・再現するな」を置き、段 2・3・5・6 の**全部の子**へ入れる。**prompt 自身も rollout に
  載る**ので投入前に prompt の NFC を検査する。memory `codex-output-must-be-nfc`。
- **制約の書き方に二次の罠がある。** 「ASCII で書け」と広く書くと、子は必須の日本語見出し
  `## 総括` を HTML 数値文字参照 (`&#32207;&#25324;`) へ変換し、`check_codex_output.py` が
  `validator_rc=1` で落とす (本 wave で実測、これが 2 度目の全損)。制約は**数式・記号にだけ**
  掛け、「日本語はそのまま書け。`## 総括` を実体参照にするな」を必ず併記する。
- 再発検知: `rc=1` を見たら receipt の `attempts[0].evidence_status` を先に読む。
  `invalid` なら NFC 側、`complete` かつ `validator_rc=1` なら書式側。原因行は
  `attempt-0001.events.jsonl` の各行を `unicodedata.normalize('NFC', s) == s` で走査すると出る。

### {{F:pbs-directive-violations-need-submission}}. PBS script の規約違反 4 点が静的レビューを通り抜けた [テスト代表性]

- 事象: 実装子が書いた `tools/pegasus/t139_a12_stress_check.pbs` が、そのままでは本走に使えなかった。
  段 3 の敵対相談 2 本と段 6 の敵対レビュー 2 本はいずれも検出せず、**親が実際に `qsub` して
  初めて 4 点が判明**した。
  (1) `#PBS -A SFC` 欠落 → `Please specify -A <Group>.` で拒否。
  (2) `#PBS -l select=1:ncpus=60:mem=14gb` は NQSV の書式でない → `Request not queued.`。
  (3) `#PBS -j oe` も拒否される → 他行を同一にした最小の対照実験で確定 (`-j o` は受理)。
  (4) `python3` 直呼び — 計算ノードの `python3` は **3.9.13 (Intel) / numpy 1.21.4**、
  `python3.10` が 3.10.12 / numpy 2.2.6 (probe 907280 で実測)。**このままなら正本の本走が
  別 interpreter・別 numpy で回っていた。**
- 根本原因: PBS script は「投入して初めて検証される」種類の成果物であり、静的レビューは
  scheduler の受理述語を持たない。実装子も read-only レビュー子も job を投入できない
  (sandbox が scheduler socket を拒む)。**投入は親にしかできず、親が投入するまで誰も検証しない。**
- 恒久対応: PBS script を成果物に含む wave では、**親が段 6 の受入前に最小の対照 job を
  実際に投入して directive の受理を確認する**。runbook の逐語 (`-A` / `-q` /
  `-l elapstim_req` / `-j o` と interpreter 吸収) を prompt へ前渡しする。
- 再発検知: `qsub` の `Request not queued. : <script>` と `Script file line <N>.` は
  directive 不正の signature。job が走った場合も、job log の interpreter と library の版を
  transcript へ記録して login 側と突き合わせる。
