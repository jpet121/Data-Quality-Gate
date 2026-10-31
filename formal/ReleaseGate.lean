import Std

/- Verification contract V:P_CORE12 and V:P_SEC17: a missing mandatory
   obligation or approval must never produce eligibility. This models the
   verification gate, not event business semantics or external delivery. -/
def eligible (requirements : List Bool)
    (evidence tests calibration oracle mutations human : Bool) : Bool :=
  (!requirements.isEmpty) && requirements.all id && evidence && tests &&
  calibration && oracle && mutations && human

theorem empty_requirements_never_clear (e t c o m h : Bool) :
    eligible [] e t c o m h = false := by
  simp [eligible]

theorem missing_requirement_never_clears (before after : List Bool)
    (e t c o m h : Bool) :
    eligible (before ++ false :: after) e t c o m h = false := by
  simp [eligible, List.all_append]

theorem missing_human_never_clears (r : List Bool) (e t c o m : Bool) :
    eligible r e t c o m false = false := by
  simp [eligible]

theorem missing_evidence_never_clears (r : List Bool) (t c o m h : Bool) :
    eligible r false t c o m h = false := by
  simp [eligible]

theorem failed_tests_never_clear (r : List Bool) (e c o m h : Bool) :
    eligible r e false c o m h = false := by
  simp [eligible]

theorem failed_calibration_never_clears (r : List Bool) (e t o m h : Bool) :
    eligible r e t false o m h = false := by
  simp [eligible]

theorem missing_oracle_never_clears (r : List Bool) (e t c m h : Bool) :
    eligible r e t c false m h = false := by
  simp [eligible]

theorem unaccepted_mutations_never_clear (r : List Bool) (e t c o h : Bool) :
    eligible r e t c o false h = false := by
  simp [eligible]

theorem all_declared_conditions_suffice (r : List Bool)
    (nonempty : r.isEmpty = false) (clear : r.all id = true) :
    eligible r true true true true true true = true := by
  simp [eligible, nonempty, clear]

#print axioms empty_requirements_never_clear
#print axioms missing_requirement_never_clears
#print axioms missing_human_never_clears
#print axioms missing_evidence_never_clears
#print axioms failed_tests_never_clear
#print axioms failed_calibration_never_clears
#print axioms missing_oracle_never_clears
#print axioms unaccepted_mutations_never_clear
#print axioms all_declared_conditions_suffice

/- Executable correspondence interface: six gate-condition bits followed by
   zero or more mandatory-obligation bits. Each argument is one case. -/
def main (args : List String) : IO UInt32 := do
  for text in args do
    if !(text.toList.all (fun c => c == '0' || c == '1')) then
      IO.eprintln "invalid bit input"
      return 2
    let bits := text.toList.map (fun c => c == '1')
    match bits.take 6 with
    | [e,t,c,o,m,h] =>
      IO.println (if eligible (bits.drop 6) e t c o m h then "1" else "0")
    | _ =>
      IO.eprintln "six condition bits required"
      return 2
  return 0
