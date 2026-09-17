---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2491-injected-closure-fail-closed
seq: 2
---

## {{D:injected-closure-unswallowed-rule}}. 閉包検査の injected-* 経路は、helper の明示的な拒否を捕まえる最初の handler の再送出だけを検査し、変換再送出以後は追跡しない

**決定:** D1882 の実装として、閉包検査の injected-* 特殊経路は、sink の代入名を第 1 引数にもつ返却物検査 call を、
次の条件を満たすときだけ被覆に数える。満たすかどうか判定できない形は被覆に数えない (fail-closed)。

- check は文の値そのものの call である (lambda・内包表記・短絡式の中の call は記録しない)。
- check を囲む try に `except*` が無く、finally 節に return / break / continue が無い。
- 内側から外側へ、position が body の try の handler を順に見る。helper の error class E (s1 の `DriverError`) を
  確実に捕まえる handler (bare / `BaseException` / `Exception` / `RuntimeError` / E の import 束縛名 / E を定義する module の
  `class DriverError`) は、body に脱出文が無く末尾が `raise` であること。E を捕まえうる不確かな型 (Attribute 等の式、
  他 module からの import 名、束縛不明の名前、module / 局所 / 字句的親関数 / 引数で再束縛された名前) の handler は末尾が bare `raise` であること。
  本 file の module scope class (E 以外) の handler は E を捕まえないので読み飛ばす。
- bare 再送出 (`raise` / 再束縛されていない as 名 / E の再構築) は E のまま外側の try へ追跡を続ける。本 file の module scope class
  (module / 局所 / 引数で再束縛されていない名前) への変換再送出は追跡を止めて被覆に数える。それ以外の raise (`raise SystemExit(0)`、
  Attribute、非 Call) は被覆に数えない。

保証するのは「helper の明示的な拒否を捕まえる最初の handler が握り潰さない」ことだけであり、変換再送出の後の外側の扱い、
不確かな型の handler が実際に E を捕まえて bare 再送出する未変換経路、`with` の `__exit__` による抑止、条件 guard、代入名の再束縛、
finalbody 内の check、helper の非明示例外は検査しない。この限界は code comment に書き、名乗らない。

**理由:**

- F918 が実測した穴は「call の位置と第 1 引数名だけが被覆の根拠」であり、拒否の握り潰しを見ないことにある。握り潰しを見るには
  handler の再送出を検査するしかなく、その最小形は「最初に捕まえる handler が再送出するか」である。
- 変換再送出の後まで追跡すると、既存の production (s8b_oracle_driver の外側 `except Exception` は `if evaluate_started: raise` の
  条件付き再送出で、`break` 終端) を誤拒否する。条件付き再送出を静的に証明するのは D1882 が却下した支配関係解析であり、
  その sink を繰延べ台帳へ移すのは台帳変更で本件の scope 外である。追跡を止める位置は、F918 が配線側へ課した義務
  (「握り潰さず変換して再送出する」) の形と一致する。
- 不確かな型の handler を「捕まえない」と決めるのは、E の親 class が組込みだけで外来名が E の親になれないという前提に依存する。
  fail-closed に倒し、bare 再送出でなければ被覆に数えない。
- 名前の再束縛を module 直下の単純代入・現関数と字句的親関数・引数・handler body まで見るのは、段 6 レビューが実在の反例 3 つ
  (変換先の module 再代入、親関数と引数での束縛、as 名の再代入) を示したためで、いずれも production の 4 sink には無い形である。
- 前提 (helper の明示的な拒否 raise は base `DriverError`、`class DriverError(RuntimeError)`) を assert で固定する案は D1869 の
  最小形に従い落とし、定数と comment に留めた。

**却下した選択肢:**

- 全 enclosing try に同じ規則を当てる — s8b_oracle_driver の injected sink を誤拒否する (段 2 plan の指摘)。
- 変換後の例外 class を追跡して外側の handler も検査する — 上と同じ誤拒否になり、避けるには条件付き再送出の flow 証明が要る。
- campaign 経路の import 真正性・shadow 検査 (`_has_unshadowed_returned_evidence_helper`) を injected 経路へ流用する — D1882 の却下範囲であり、
  helper を定義する s1 module では False を返すので s1 の injected sink 2 つを誤拒否する。
- module scope の alias chain (`X = S1DriverError`) を解決して DEFINITE に含める — production にも変異にも不要で、最小形を超える (段 3 の推奨)。
- 不確かな型の handler を「捕まえない」と扱う — 前提への依存を保証に含めることになり fail-closed でない。
