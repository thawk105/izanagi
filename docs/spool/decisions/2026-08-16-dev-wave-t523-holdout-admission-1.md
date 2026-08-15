---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t523-holdout-admission
seq: 1
---

## {{D:holdout-observation-boundary}}. freeze 由来 holdout を実測へ渡す下位境界に admission と一回性台帳を置く

**決定:** 検証済み freeze から導出した保護 signature に一致する workload を ccbench で実測する
経路は、共通の実行 gateway (`orchestrator/calibrator/runner.run_once`) で sealed な観測許可
なしには通さない。許可は、共有 durable root 上で cell を `O_EXCL` により一度だけ確保し、
凍結済み schedule から導出した attempt ticket を実測直前に durable 消費した経路だけが発行する。
8b floor campaign をこの境界へ実結線する。

**族一般化の根拠 (DW-G03):** 同型欠陥が独立 2 producer で再現した。8c launcher は registry の
admission を通す一方、8b floor campaign は trial registry も lifecycle 台帳も参照せず
(実測: 当該 module に両者の文字列が 0 箇所)、実 freeze から列挙した 12 セルの holdout 識別子は
8c 側の保護 workload 集合と完全に同一だった。producer ごとに gate を置く方式は、
まさにこの「片方だけ塞がれた」状態を生む。

**設計の要点:**

- **保護対象は hardcode 表でなく検証済み freeze から導出**し、中立表との exact 集合一致を
  発行時に要求する。一致しなければ fail-closed で拒否する。将来 holdout が増えても
  「未知だから非保護」と判定しない。
- **判定は gflags の型意味論に合わせる。** ccbench は google gflags を使うため
  `--flagfile` / `--fromenv` / `--tryfromenv` を拒否し、`FLAGS_` 接頭辞の環境変数を除去した
  閉じた環境でのみ起動する。比率は canonical decimal に限定し、字句別名を拒否する。
  引数列は gateway 冒頭で不変 snapshot に固定し、判定と実行 argv に同一物を使う。
- **一回性 key は測定効果で構成する** — `(freeze bytes hash, freeze holdout key,
  configuration id, ccbench pin, env tag)`。protocol の hash を key に入れない
  (入れると自由 field を変えるだけで同じセルを別実験として測り直せる)。
  protocol / manifest / run 座標は証跡として台帳行に残すが key にしない。
- **許可は attempt と回数に束縛する。** 許可証は自分の保護 signature を持ち回り、実行時の
  実効比率と同じ lock 内で照合する。ある signature 向けの許可証は別 signature を認可しない。
- **台帳 root は全 worktree 共有の物理位置** (`git rev-parse --git-common-dir` 由来) とする。
  checkout ごとの出力位置を使うと、worktree を 2 つ作るだけで同じセルを二重に確保できる。
- **pilot は緩和理由にならない。** pilot が canonical holdout を観測すると official の一回性を
  消費するため、不可逆であることの明示的な承認を必須にし (既定は拒否)、承認の事実を台帳へ残す。
  承認しても消費と記録は必ず行う。
- **一回性の単位は既に凍結済みの実験計画から導出する** — planned session 数と凍結済み retry 枠。
  新しい実験単位を定義しない (実験単位の再定義は別タスクの scope)。
- **key は観測者の役割 (observation role) を含む。** 値は閉じた集合とし、未知の役割は
  fail-closed で拒否する。**これは緩和ではない** — 同じ holdout セルを測る正規の観測者が
  複数存在する (床値の観測者と、正解を作る観測者) ため、役割ごとに一回性を保つ。
  役割を跨いだ再観測は依然として不可能である。役割を持たない旧行は受理しない。
- **producer は起票時の 2 つではなく 3 つだった。** 実結線の受入で第 3 の producer
  (正解を作る観測者) が freeze 由来 holdout を実測していることが実測で判明し、同じ経路へ通した。
  その発行根拠は、検証済み manifest と launch 検証済み freeze の組に限定し、測る cell も
  許可回数も manifest から導出する (呼び手が指定する口を作らない)。
  **「この producer は例外」という素通り経路を作らない。**
- **台帳行の座標は改変検出の証跡であって束縛ではない。** holdout 束縛へ全軸を足す変更は
  別タスクの scope であり、本決定では判定条件へ昇格させない。

**受理集合の変更 (D96 手続):** 保護比率の測定は、code path 由来か手打ちかを問わず許可を要求する。
これまで通っていた手動の calibration 指定 (保護比率を含むもの) は拒否される。
偏りや rmw が freeze と異なっていても、実効比率が保護比率なら許可を要求する
(規律 2 の方向であり、緩める側へは倒さない)。境界テストは同じ変更単位で追随させた。

**この設計が保証しないこと (明示):**

1. 台帳の無い測定結果を下流の verifier / ratified closure / report が拒否すること。
   本境界は「台帳を通さずに実測できない」までを保証し、成果物側の参照結線は別 scope である。
2. 将来の producer が実行 gateway を通らず直接 process を起動する経路の機械的封鎖。
   起動箇所の構造検査は**検出**であって封鎖ではなく、認識する起動 API も限定表である。
3. 未 commit の台帳ファイルを同じ権限で削除する行為への保護。
4. 独立 clone 間の一回性。共有するのは 1 repository の worktree 群までである。
5. **private な Python API を直接 import できる呼び手に対する保護。** 発行経路を非公開に
   したのは正当な公開 API 経由での迂回を塞ぐためであり、import 権限を持つコードによる
   偽造を防ぐものではない。Python ではこの境界を機構的に封じられない。

**却下した選択肢:**

- **producer 側だけに gate を置く** — 本件の失敗そのもの (独立 2 producer で片方だけ塞がれた) を
  再生産する。3 番目の producer が現れても自動では塞がらない。
- **freeze loader に置く** — loader は bytes と hash の leaf であり、非計測の読み込みでも
  一回性を消費してしまう。
- **既存 durable 書込み経路の共通化 refactor を同時に行う** — 成果物の値・受理集合・参照は
  1 つも変わらず、proof chain を壊す risk だけが増える。
- **許可証を campaign 単位で 1 枚にする** — 1 枚を使い回して測定回数を任意に増やせる。
- **pilot を一回性の対象外にする** — holdout を観測した事実は消えない。緩和側へ倒さない。
