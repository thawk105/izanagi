---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t419-u2-recalibration
seq: 2
---

## {{D:certify-clock-gate-early-and-published-recheck}}. 較正取得の自己整合検査を benchmark 前後の二重に置き、publish 済み bytes を独立に再読する

**決定:**

1. 較正取得 CLI の `_acquisition_reasons` に effective clock の自己整合検査を **追加**する。
   判定は canonical 述語を経由し、帯計算を再実装しない。benchmark を開始する前に拒否できる。
2. **benchmark 後の既存 gate は削除しない。** early と late の両方を残す。
3. publish の直前に「attempt 開始時に profile へ書いた `tolerance_pct` が publish 時点の
   policy 定数と一致する」ことを独立に検査し、不一致は fail-closed で拒否する。
4. publish (rename) の後に publish 先の bytes を読み直し、process 内部の profile や dict を
   一切参照せずに canonical 述語を適用して専用 receipt へ記録する。不一致は非 0 終了とし、
   content-addressed な published artifact は削除しない。
5. early 拒否の成果物には、評価に使った effective clock 入力・`attestation_profile` 全体・
   canonicalization 識別子・その SHA-256・評価されなかった検査の一覧を残す。
   **成果物だけから hash と判定を再計算できる**ことを要件とする。
6. 帯評価は `input_valid` / `policy_matches` / `band_pass` に分解し、canonical 述語は 3 者の連言とする。
   診断値 (帯外件数・違反位置) を受理判断に使わない。

**理由:**

- 取得 job は build と cooldown と benchmark を含む長時間実行であり、clock が帯外なら
  benchmark を回す意味がない。早期化は費用の問題であって受理集合の問題ではない。
- しかし early だけにすると受理集合が変わる。policy 定数は実行中に再束縛でき、
  「開始時 policy で通し、終了時 policy と食い違ったまま publish する」経路が開く。
  late gate と publish 直前の policy 同一性検査がこの窓を閉じる。
- publish 後の再読を入れないと、成果物が「自分の帯検査を通った」証拠を持たない。
  CLI 内部の判定は内部状態への信頼に依存しており、独立検査ではない。
- 拒否成果物に導出値 (中央値・上下限・違反位置) だけを残すと、第三者が失敗した profile を
  再計算できず「決定的事実」にならない。preimage を成果物に含めて自己完結させる。
- 帯計算の可換な性質 (numeric string や任意幅 tolerance を許す) は歴史的に別の呼び手が
  使っており、canonical 述語だけが 3 者を連言する。分解しないと診断の帯外 0 件を
  合格と読み替える経路が生まれる。

**射程 (この決定が保証しないこと):**

- benchmark 中および benchmark 後の clock は依然として検査されない。外側の post probe は
  publish より後に走り、publish を取り消さない。この窓は本決定の対象外である。
- 別 process による完全独立の検証と、その判定を最終 receipt へ束縛することは含まない。
  ここで言う独立は「同一 process 内で内部状態を参照せず publish 先 bytes を読み直す」までである。
- 取得経路の source acquisition proof (第三者 source の head・cache identity・transport) は
  依然として束縛されない。本決定は clock 面だけを扱う。

**却下した選択肢:**

- 検査を benchmark 後から前へ**移動**する — policy 再束縛経路で accepted publish 集合が変わる。
  節約のために受理集合を動かすことになる。
- loader 側にも同じ self-pass を課す — 現行の登録済み較正が読めなくなり、承認外の受理縮小になる。
  loader self-pass は新較正の登録と同時に課す既定方針を変えない。
- 別 job の生死 driver で計算ノードの帯内性を先に確かめてから取得 job を投入する —
  allocation・host・boot・時刻が異なるので後続 job の許可証にならず、
  新しい出力先・PBS・guard registry 項目という運用負債だけが残る。
  同一 allocation 内の early gate が同じ役割を果たす。
- 拒否時に published artifact を削除する — content-addressed で immutable な公開領域を
  事後に壊すことになり、並行 publish との race も生む。
