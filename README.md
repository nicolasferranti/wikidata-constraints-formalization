# SHACL Generator

This tool is meant to generate SHACL property shapes for WD properties, using Nicolas Ferranti's [SHACL Templates](https://github.com/nicolasferranti/wikidata-constraints-formalization)

```
├── query results       # This folder contains the JSON for a specific WD property returned by their query service
  ├── PID.json          # Property JSON
├── <constraint_type>   # Each folder contains the SHACL shapes for a specific WD property constraint type
  ├── PID.ttl           # SHACL shape for a specific constraint type
└── main.py
└── README.md
```

## Constraint Checklist

- [ ] allowed entity types constraint
- [ ] allowed qualifiers constraint
- [ ] allowed units constraint
- [ ] citation needed constraint
- [ ] commons link constraint
- [ ] conflicts-with constraint
- [ ] contemporary constraint
- [ ] description in language constraint
- [ ] difference-within-range constraint
- [ ] distinct-values constraint
- [ ] format constraint
- [ ] integer constraint
- [ ] item-requires-statement constraint 
- [ ] label in language constraint
- [ ] lexeme requires language constraint
- [ ] lexeme requires lexical category constraint
- [ ] lexeme value requires lexical category constraint
- [ ] multi-value constraint
- [ ] no-bounds constraint
- [ ] none-of constraint
- [ ] one-of constraint
- [ ] one-of qualifier value property constraint 
- [ ] property scope constraint
- [ ] range constraint
- [ ] required qualifier constraint 
- [ ] single-best-value constraint
- [ ] single-value constraint
- [ ] symmetric constraint
- [x] type constraint
- [ ] value-requires-statement constraint 
- [ ] value-type constraint