# wikidata-constraints-formalization
Repository containing the SPARQL queries to retrieve violations of Wikidata property constraints and the SHACL shapes for the constraints translatable to SHACL

.
├── <constraint_type>       # Each folder contains the SPARL queries and SHACL shapes for a specific WD property constraint type
  ├── sparql                # Folder containing the SPARQL queries (*.rq) when there are multiple queries for the same constraint type
  ├── shacl_shape_PID.ttl   # SHACL shape example file for a specific constraint type
└── README.md
