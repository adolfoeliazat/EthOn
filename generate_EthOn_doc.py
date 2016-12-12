#!/usr/bin/env python
# Command line tool for using alethio-scraper

import argparse
import ontospy
from jinja2 import Environment, FileSystemLoader
from rdflib import *
import collections
import string


def slicedict(d, s):
    return {k: v for k, v in d.iteritems() if k.startswith(s)}


def bootstrapDesc(onto):
    """
    Extract whatever could be used as a description for the ontology
    """
    DCTERMS = Namespace('http://purl.org/dc/terms/')
    DC = Namespace('http://purl.org/dc/elements/1.1/')
    VANN = Namespace('http://purl.org/vocab/vann/')
    VOCAB = Namespace('http://www.w3.org/2003/06/sw-vocab-status/ns#')
    OWL = Namespace('http://www.w3.org/2002/07/owl#')

    DCcontributors = ", ".join([x for x in onto.rdfgraph.objects(onto.ontologyURI, DC.contributor)])
    DCcreators = ", ".join([x for x in onto.rdfgraph.objects(onto.ontologyURI, DC.creator)])
    VANNprefPrefix = ", ".join([x for x in onto.rdfgraph.objects(onto.ontologyURI, VANN.preferredNamespacePrefix)])
    DCtitle = ", ".join([x for x in onto.rdfgraph.objects(onto.ontologyURI, DC.title)])
    VOCABterm_status = ", ".join([x for x in onto.rdfgraph.objects(onto.ontologyURI, VOCAB.term_status)])
    OWLimports = [x for x in onto.rdfgraph.objects(onto.ontologyURI, OWL.imports)]
    OWLversionIRI = ", ".join([x for x in onto.rdfgraph.objects(onto.ontologyURI, OWL.versionIRI)])
    OWLversionInfo = ", ".join([x for x in onto.rdfgraph.objects(onto.ontologyURI, OWL.versionInfo)])
    RDFSseeAlso = [x for x in onto.rdfgraph.objects(onto.ontologyURI, RDFS.seeAlso)]
    RDFScomment = "\n".join([x for x in onto.rdfgraph.objects(onto.ontologyURI, RDFS.comment)])

    return {
        "comment": RDFScomment,
        "contributors": DCcontributors,
        "creators": DCcreators,
        "prefix": VANNprefPrefix,
        "title": DCtitle,
        "term_status": VOCABterm_status,
        "imports": OWLimports,
        "versionIRI": OWLversionIRI,
        "versionInfo": OWLversionInfo,
        "uri": onto.ontologyURI,
        "seeAlso": RDFSseeAlso
    }


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def makeGlossary(onto):
    terms = {}
    glossary = collections.OrderedDict()
    az = string.uppercase[:26]

    for term in onto.classes:
        terms[term.locale] = ", ".join([x for x in term.rdfgraph.objects(term.uri, RDFS.comment)])
    for term in onto.properties:
        terms[term.locale] = ", ".join([x for x in term.rdfgraph.objects(term.uri, RDFS.comment)])

    for letter in az:
        glossary[letter] = collections.OrderedDict(
            sorted(merge_dicts(slicedict(terms, letter), slicedict(terms, letter.lower())).items()))

    return glossary


def main():
    ETHON = Namespace('http://consensys.net/ethereum-ontology/')
    VOCAB = Namespace('http://www.w3.org/2003/06/sw-vocab-status/ns#')
    ontospy.BOOTSTRAP_ONTOLOGIES.append('http://consensys.net/ethereum-ontology/')

    onto = ontospy.Ontospy("EthOn.rdf")
    onto.ontologyURI = onto.ontologies[0].uri
    onto.namespaces.append(("ethon", URIRef("http://consensys.net/ethereum-ontology/")))

    for c in onto.classes:
        c.RDFScomment = ", ".join([x for x in c.rdfgraph.objects(c.uri, RDFS.comment)])
        c.RDFSlabel = ", ".join([x for x in c.rdfgraph.objects(c.uri, RDFS.label)])
        c.ETHONsuggestedStringRepresentation = ", ".join(
            [x for x in c.rdfgraph.objects(c.uri, ETHON.suggestedStringRepresentation)])
        c.VOCABterm_status = ", ".join([x for x in c.rdfgraph.objects(c.uri, VOCAB.term_status)])
        c.RDFSseeAlso = [x for x in c.rdfgraph.objects(c.uri, RDFS.seeAlso)]
        c.RDFSisDefinedBy = [x for x in c.rdfgraph.objects(c.uri, RDFS.isDefinedBy)]

    for p in onto.properties:
        p.RDFScomment = ", ".join([x for x in p.rdfgraph.objects(p.uri, RDFS.comment)])
        p.RDFSlabel = ", ".join([x for x in p.rdfgraph.objects(p.uri, RDFS.label)])
        p.ETHONsuggestedStringRepresentation = ", ".join(
            [x for x in p.rdfgraph.objects(p.uri, ETHON.suggestedStringRepresentation)])
        p.VOCABterm_status = ", ".join([x for x in p.rdfgraph.objects(p.uri, VOCAB.term_status)])
        p.RDFSseeAlso = [x for x in p.rdfgraph.objects(p.uri, RDFS.seeAlso)]
        p.RDFSisDefinedBy = [x for x in p.rdfgraph.objects(p.uri, RDFS.isDefinedBy)]

    env = Environment(loader=FileSystemLoader('doc_resources/templates'))

    # Render specification website
    spec_template = env.get_template('EthOn_spec_template.html')
    spec = spec_template.render(
        meta=bootstrapDesc(onto),
        classes_tree=onto.toplayer,
        properties_tree=onto.toplayerProperties,
        classes=onto.classes,
        properties=onto.properties,
        a_properties=onto.annotationProperties,
        d_properties=onto.datatypeProperties,
        o_properties=onto.objectProperties
    )
    with open("EthOn_spec.html", "wb") as fh:
        fh.write(spec)

    # Render glossary
    glossary_template = env.get_template('EthOn_glossary_template.md')
    glossary = glossary_template.render(glossary=makeGlossary(onto))

    with open("EthOn_glossary.md", "wb") as fh:
        fh.write(glossary)


main()