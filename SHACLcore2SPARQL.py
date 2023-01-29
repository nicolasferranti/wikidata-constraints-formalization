import sys
import requests
import rdflib
from rdflib import Graph
from rdflib import BNode
from rdflib import Namespace
from rdflib import paths

# property paths - these should be defined in rdflib.paths, but it didn't work, so I manually redefined them...
ZeroOrMore = "*"
OneOrMore = "+"
ZeroOrOne = "?"

#define some namespaces I need:
SH = Namespace("http://www.w3.org/ns/shacl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
#this one is jusrt used for a dirty hack below.... TODO : fix
AUX = Namespace("")

def rewriteShape(current_subject,current_target,g):
    query = ""
    for t in g.triples((current_subject,None,None)):
        #sh:closed : xsd:boolean
        # TODO: not yet supported
        #sh:or : rdf:List
        if(t[1] == SH["or"]):
            or_branches = g.triples((current_subject, ((SH["or"]/RDF.rest*ZeroOrMore/RDF.first)), None))
            l=["{ "+rewriteShape(str(o[2]),current_target)+" }" for o in  or_branches]                
            query += "{ "+" UNION ".join(l)+" }"
        #sh:not : sh:Shape
        elif(t[1] == SH["not"]):
            query +=  " FILTER NOT EXISTS { " + rewriteShape(t[2],current_target,g) + " }"   
        #sh:property : sh:PropertyShape
        elif(t[1] == SH.property):
            query = rewritePropertyShape(t[2],current_target,g)   
    return query

def rewritePropertyShape(current_subject,current_target,g):
    target= "?T"+str(current_target)
    # FWIW, we assume that all value restrions are conjunctive - TODO: check with Nicolas!
    val   = rewriteValueShape(current_subject,current_target,g)
    query = ""

    # We assume there's always exactly one path: 
    #sh:path : rdfs:Resource
    triples = list(g.triples((current_subject,SH.path,None)))
    assert(len(triples)==1) #there should be exactly 1 path per property shape
    path= rewritePathShape(triples[0][2],g)
    # The query without any further restrictions on the path: 
    query= " "+target+" "+path+" "+val

    # We assume there can be the following restricitons on the path:
    
    
    # 1) sh:minCount : minCount 
    #  .... i.e. there have to be at least minCount occurrences of this path
    # we initialize to -1 indicating "unset"
    minCount = -1
    triples = list(g.triples((current_subject,SH.minCount,None)))
    if(len(triples)):
        assert(len(triples)==1) #there should be max 1 sh:minCount per property shape
        minCount=int(str(triples[0][2]))
        #Hint: MinCount = 0 or smaller does't make sense
        assert( minCount > 0 )
        

    # 2) sh:maxCount : minCount
    # we initialize to -1 indicating "unset"
    maxCount = -1
    #  .... i.e. there have to be at most maxCount occurrences of this path
    triples = list(g.triples((current_subject,SH.maxCount,None)))
    if(len(triples)):
        assert(len(triples)==1) #there should be max 1 sh:maxCount per property shape
        maxCount=int(str(triples[0][2]))
        #Hint: MaxCount < 0  does't make sense
        assert( maxCount >=0 )
 
    # For checking minCounts and maxCounts we use a COUNT query with a FILTER... 
    # TODO, I am not sure this works as intended in connection with the NOT EXISTS, need to test!!! 
    if (minCount>=1 or maxCount>=0):
        cnt_var = "?CNT"+str(current_target)
        query_new = "{ SELECT ( COUNT(*) AS "+cnt_var+") WHERE { "+target+" "+path+" "+val+" } } FILTER ( " 
        if(maxCount > 0):
            query_new += (cnt_var+" <= "+str(maxCount))  
        if(maxCount > 0 and minCount >=1):
            query_new += " && "
        if(minCount >=1):
            query_new += (cnt_var+" >= "+str(minCount))
        query_new += ") "

    if(maxCount >= 0):
        # We need to handle maxCount in a special manner: the counting with COUNT only works if the actual count is > 0, i.e. if it exists,
        # that is, a maxCount is also "fulfilled, in case of NOT EXISTS, which we need to add as a UNION...
        maxcount0_query = "FILTER NOT EXISTS { "+ query +" }  " 

    if (minCount>1 or maxCount>0):
        query = query_new
    else:
        pass
        # we don't nee the complicated FILTER COUNT query for only minCount = 1... in that case it suffices to check for path existence.
        # so we can leave the original query unchanged


    # Note: As per the SHACL spec maxCount = 0 should be treated as negation, i.e. should be replaced by sh:not...
    if(maxCount == 0):
        print("#### WARNING: TODO: maxCount = 0 is boiling down to a simple NOT EXISTS, However, we need to copy the target pattern for this case, otherwise it does") 
        print("###           not work, i.e.,SPARQL does not do well with directly nested FILTER NOT EXISTS, due to the evaluation mechanics of SPARQL!")
        query = maxcount0_query
    elif(maxCount > 0 and minCount == 0):
        # TODO: Afraid this does not work! NEEDS TESTING WITH A SMALL DATASET!
        query = "{{ " + maxcount0_query + " } UNION { "+query+" }}"
        
    # minCount > maxCount should not be allowed!
    assert(minCount <= maxCount)
    
        #sh:class : rdfs:Resource
        #sh:datatype : rdfs:Resource
        #sh:node : sh:NodeShape
        #sh:name : xsd:string or rdf:langString
        #sh:description : xsd:string or rdf:langString
        #sh:defaultValue : any
        #sh:group : sh:PropertyGroup
        
        
        
    return query
        

    
def rewritePathShape(current_subject,g):
    if(type(current_subject) == rdflib.term.BNode ):
        triples = list(g.triples((current_subject, (RDF.rest*ZeroOrMore/RDF.first), None)))
        if (len(triples)):
            l=[rewritePathShape(t[2],g) for t in triples]
            return "/".join(l)
        else:
            #sh:inversePath
            triples = list(g.triples((current_subject, SH.inversePath, None)))
            if(len(triples)): 
                assert(len(list(triples))==1) #there can only be exactly 1 inversePath
                l=[rewritePathShape(t[2],g) for t in triples]
                return "^("+rewritePathShape(triples[0][2],g)+")"
            #sh:zeroOrMorePath
            triples = list(g.triples((current_subject, SH.zeroOrMorePath, None)))
            if(len(triples)): 
                assert(len(list(triples))==1) #there can only be exactly 1 zeroOrMorePath
                return "("+rewritePathShape(triples[0][2],g)+")*"
            #sh:oneOrMorePath
            triples = list(g.triples((current_subject, SH.oneOrMorePath, None)))
            if(len(triples)): 
                assert(len(list(triples))==1) #there can only be exactly 1 oneOrMorePath
                return "("+rewritePathShape(triples[0][2],g)+")+"
            #sh:alternativePath
            triples = list(g.triples((current_subject, (SH.alternativePath/((RDF.rest*ZeroOrMore/RDF.first))), None)))
            if (len(triples)):
                l=[rewritePathShape(t[2],g) for t in triples]
                return "("+"|".join(l)+")"            
    elif(type(current_subject) == rdflib.term.URIRef ):
        return  serializeRDFTerm(current_subject) 
    else:
        print(str(current_subject))
        assert(False) # should have covered all cases, i.e. e.g. no literals in paths allowed.
        

def serializeRDFTerm(term):
    if(type(term) == rdflib.term.BNode ):
        return "_:"+str(term)
    elif(type(term) == rdflib.term.URIRef ):
        return "<"+str(term)+">"
    elif(type(term) == rdflib.term.Literal ):
        #poor man's hack...
        g_aux =Graph() 
        g_aux.add(AUX.aux,AUX.aux,term)
        return g_aux.serialize(format="ntriples").replace("<aux ","")[:-2]
    else:
        assert(False)
                
def rewriteValueShape(current_subject,current_target,g):
    val="?V"+str(current_target)
    filterExpr = ""

    #sh:pattern
    triples = list(g.triples((current_subject, SH.pattern, None)))
    if(len(triples)): 
        assert(len(list(triples))==1) #there can only be exactly 1 pattern
        filterExpr += " FILTER( REGEX( "+val+", \""+triples[0][2]+"\" ))"

    #sh:in
    triples = list(g.triples((current_subject, (SH["in"]/((RDF.rest*ZeroOrMore/RDF.first))), None)))
    if(len(triples)): 
        l=[serializeRDFTerm(t[2]) for t in triples]
        filterExpr += " FILTER(  "+val+" IN( "+ ",".join(l)+" ))"

    #sh:hasValue
    triples = list(g.triples((current_subject, SH.hasValue, None)))
    if(len(triples)): 
        
        assert(len(list(triples))==1) #there can only be exactly 1 hasValue
        # to be sure, we also verify that triples[0][2] is not a BNode (wouldn't make sense):
        assert(type(triples[0][2]) != rdflib.term.BNode)
        
        val = triples[0][2]
        
        # TODO: What if hasValue is combined with another constraint, e.g. another shape...?
        # ... would not make much sense but this following alternative translation wouuld still work then:
        # filterExpr += " FILTER(  "+val+" = "+ triples[0][2] +")"
    
    #sh:minLength
    #TODO
    #sh:maxLength
    #TODO
    
    return val+" . "+filterExpr

def MyShacl2Sparql(url, format="turtle", localfile=False):
    g = Graph()
    #FWIW, this should work, but gives me a 404 when run against github, so we go via requests, which works...
    #g.parse(source=url,format=format)
    #.... alternative:
    if (localfile == True):
        g.parse(url,format=format)        
    else:
        r=requests.get(url)
        g.parse(data=r.text,format=format)
    print ("### original SHACL graph:")
    for l in g.serialize(format="turtle").split("\n"):
        print ("# ",l)
    print ("###")

    target_pattern=""

    # find the "root" of the shape(s).
    # Use variable ?T for target nodes
    target_defs = 0
    for t in g:
        if(t[1] == SH.targetClass):
            target_defs += 1
            target_patterny += "?T1 a <"+str(t[2])+"> ."
            current_subject = t[0]
        elif(t[1] == SH.targetObjectsOf):
            target_defs += 1
            target_pattern += "[] <"+str(t[2])+"> ?T1 . "
            current_subject = t[0]
        elif(t[1] == SH.targetSubjectsOf):
            target_defs += 1
            target_pattern += "?T1 <"+str(t[2])+"> [] . "
            current_subject = t[0]
    assert(target_defs == 1) # there should only be one target definition! TODO:maybe if we wanted to allow SHAPE files that have several shapes, we should generalize this!
    assert(current_subject)

    query=""
    for ns,prefix in g.namespaces():
        query += "PREFIX "+ns+":"+serializeRDFTerm(prefix)+"\n"

    # Following [Corman et al. 2019] Vioations are targets such that the SHAPE cannot be verified, i.e. NOT EXISTS:
    query = query + "SELECT * WHERE { \n"+target_pattern + " FILTER NOT EXISTS { " + target_pattern + rewriteShape(current_subject,1,g)+"\n } }"
    # TODO: As an optimization, can we replace any "FILTER NOT EXISTS {  FILTER NOT EXISTS" with 
    # * just " { " ... avoiding "double negation"
    # * or do we need to rather copy the target pattern inside? Can we use MINUS?
    # ... FWIW, this does all in one go, i.e. should compute all violated targets.

    return(query)


def main():
    args = sys.argv[1:]
    # for the moment, we assume the first argument to be a URL
    print(MyShacl2Sparql(args[0]))
    # args is a list of the command line args
    #File could be called by 
    # print(MyShacl2Sparql(args[0]), localfile=True)

if __name__ == "__main__":
    main()
