import Std

/- README Repository and ACCEPTANCE duplicate-delivery contracts, expressed as
   a simpler mathematical store. Keys stand for opaque delivery identities;
   Nat payload tokens stand for equality classes of input hashes. -/
abbrev Store := Nat → Option Nat
inductive Decision where
  | created | duplicate | conflict
  deriving Repr, BEq

def persist (store : Store) (key value : Nat) : Store × Decision :=
  match store key with
  | none => ((fun q => if q = key then some value else store q), .created)
  | some previous => if previous = value then (store, .duplicate) else (store, .conflict)

theorem duplicate_preserves_store (s : Store) (k v : Nat) (present : s k = some v) :
    persist s k v = (s, .duplicate) := by simp [persist, present]

theorem conflict_preserves_store (s : Store) (k old fresh : Nat)
    (present : s k = some old) (different : old ≠ fresh) :
    persist s k fresh = (s, .conflict) := by simp [persist, present, different]

theorem creation_stores_value (s : Store) (k v : Nat) (absent : s k = none) :
    (persist s k v).1 k = some v := by simp [persist, absent]

theorem creation_preserves_other_keys (s : Store) (k v q : Nat)
    (absent : s k = none) (different : q ≠ k) :
    (persist s k v).1 q = s q := by simp [persist, absent, different]

theorem created_value_is_idempotent (s : Store) (k v : Nat) (absent : s k = none) :
    persist (persist s k v).1 k v = ((persist s k v).1, .duplicate) := by
  apply duplicate_preserves_store
  exact creation_stores_value s k v absent

#print axioms duplicate_preserves_store
#print axioms conflict_preserves_store
#print axioms creation_stores_value
#print axioms creation_preserves_other_keys
#print axioms created_value_is_idempotent

/- Each command-line argument is an isolated trace, k,v;k,v;... . -/
def main (args : List String) : IO UInt32 := do
  for trace in args do
    let mut store : Store := fun _ => none
    let mut answers : List String := []
    for operation in trace.splitOn ";" do
      match operation.splitOn "," with
      | [key, value] =>
        match key.toNat?, value.toNat? with
        | some k, some v =>
          let (next, outcome) := persist store k v
          store := next
          let code := match outcome with
            | .created => "C"
            | .duplicate => "D"
            | .conflict => "X"
          let actual := (store k).getD 0
          answers := answers ++ [code ++ ":" ++ toString actual]
        | _, _ =>
          IO.eprintln "non-natural trace token"
          return 2
      | _ =>
        IO.eprintln "malformed trace operation"
        return 2
    IO.println (String.intercalate ";" answers)
  return 0
