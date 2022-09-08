# wikidata-constraints-formalization

Repository containing the SPARQL queries to retrieve violations of Wikidata property constraints and the SHACL shapes for the constraints translatable to SHACL

```
├── <constraint_type>       # Each folder contains the SPARL queries and SHACL shapes for a specific WD property constraint type
  ├── sparql                # Folder containing the SPARQL queries (*.rq) when there are multiple queries for the same constraint type
  ├── shacl_shape_PID.ttl   # SHACL shape example file for a specific constraint type
└── README.md
```

## SHACL Shape checking

Currently, our Shacl Shapes are checked using an [online tool](https://rdfshape.herokuapp.com/validate) for RDF validation in combination with Wikidata's [Linked Data interface](https://www.wikidata.org/wiki/Wikidata:Data_access). Taking the running example from the paper, one can check [item-requires-statement constraint](https://www.wikidata.org/wiki/Q21503247) for [Thiago Neves](https://www.wikidata.org/wiki/Q370014) by collecting the [Turtle file](https://www.wikidata.org/wiki/Special:EntityData/Q370014.ttl) and use the validator to test the shape. The [result](<https://rdfshape.herokuapp.com/validate?dataURL=https%3A%2F%2Fwww.wikidata.org%2Fwiki%2FSpecial%3AEntityData%2FQ370014.ttl&dataFormat=turtle&schema=prefix%20%3A%20%20%20%20%20%20%20%20%3Chttp%3A%2F%2Fexample.org%2F%3E%0Aprefix%20wdt%3A%20%20%20%20%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fprop%2Fdirect%2F%3E%0Aprefix%20wd%3A%20%20%20%20%20%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fentity%2F%3E%0Aprefix%20sh%3A%20%20%20%20%20%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Fshacl%23%3E%20%0A%0A%0A%3AP1469_ItemRequiresStatementShape%20%0A%09a%20sh%3ANodeShape%20%3B%0A%09sh%3AtargetSubjectsOf%20wdt%3AP1469%20%3B%0A%09sh%3Aproperty%20%5B%0A%20%20%20%20%09sh%3Apath%20wdt%3AP106%20%3B%0A%20%20%20%20%20%20%20%20sh%3AminCount%201%3B%0A%20%20%20%20%20%20%20%20sh%3Ain%20(wd%3AQ937857%20wd%3AQ18515558%20wd%3AQ21057452%20wd%3AQ628099)%20%3B%0A%20%20%09%5D%20.&schemaFormat=Turtle&schemaEngine=SHACLex&triggerMode=TargetDecls&schemaEmbedded=false&inference=NONE&activeDataTab=%23dataUrl&activeSchemaTab=%23schemaTextArea&activeShapeMapTab=%23shapeMapTextArea&&shapeMap=>) can be checked online.
