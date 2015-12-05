#!/usr/bin/env python3

import os, sys, random, json, re
import spacy
from random import choice, sample
from numpy import dot
from numpy.linalg import norm
from spacy.en import English

global nlp, all_words, all_motifs
nlp = None; all_words = None; all_motifs = None

# with open('primary_indices.json') as indices:
#     primary_indices = json.load(indices)
def populate_motifs(infile="motifs.txt"):
    global all_motifs
    with open(infile) as f:
        all_motifs = list(l.strip() for l in f.readlines())
    return all_motifs

# used when computing similarity of vectors
cosine = lambda v1, v2: dot(v1, v2) / (norm(v1) * norm(v2))
vector_similarity = lambda w, target: -1 * cosine(w.vector, target)

def init_nlp(**kwargs):
    global nlp, all_words
    nlp = nlp or English(**kwargs)
    # custom stop words:
    # TODO: why isn't this working?
    nlp.vocab['\'s'].is_stop = True
    nlp.vocab['St.'].is_stop = True

    # gather all known words, take only lowercased versions
    all_words = list({w for w in nlp.vocab if w.has_vector and w.orth_.islower()})

    return nlp

# Get vector for a string, which we assume is a single word.
def vector(w):
    if type(w) == str:
        vector = nlp(w)[0].vector
    elif type(w) == spacy.lexeme.Lexeme or spacy.tokens.token.Token:
        vector = w.vector
    else:
        vector = None
    return vector

def find_similar(target, count=10, offset=0):
    if type(target) == str:
        target_vector = vector(target)
    elif type(target) == spacy.lexeme.Lexeme or spacy.tokens.token.Token:
        target_vector = target.vector
    elif type(target) == numpy.ndarray:
        target_vector = target
    else:
        print("Invalid target for finding similar word by vector...")
        return []

    all_words.sort(key=lambda w: vector_similarity(w, target_vector))
    similar = all_words[offset:offset+count]
    return similar

def mutation_candidates(tokens):
    return list(t for t in tokens if not (t.is_stop or t.is_punct))

def get_mutation_substitute(w):
    return choice(find_similar(w, 8, 25)).orth_

def ok_to_tweet(m):
    # too long to tweet?
    if len(m) > 140:
        return False
    # any words that aren't real?
    elif any([w.is_oov for w in nlp(m)]):
        return False
    # TODO: filter bad words
    else:
        return True

def mutate(motif, verbose=False, index=None):
    try:
        pieces      = motif.split()  # => ["A13.1.1", "Cow", "as", "creator."]
        index       = index or pieces[0]     # => "A13.1.1"
        body        = " ".join(pieces[1:])  # => "Cow as creator."
        tokens      = nlp(body)
        candidates  = mutation_candidates(tokens)

        if len(candidates) < 2:
            if verbose:
                print("Motif is not a good candidate for mutation:\n\t%s" % body)
            else:
                print(".", end="")
            return None
        new_motif = body

        if verbose:
            print("Finding ~similar words for %s" % candidates)
        to_sub = list((c.orth_, get_mutation_substitute(c)) for c in candidates)

        for candidate,replacement in to_sub:
            if verbose:
                print("Replacing", candidate, "with", replacement)
            new_motif = re.sub(r"%s"%candidate, replacement, new_motif, count=1)

        index = index or motif.index
        if ok_to_tweet(new_motif) is False:
            if verbose:
                print("Mutated motif is not a good candidate to tweet:\n\t%s" % new_motif)
            return None
        new_motif = "%s %s" % (index, new_motif)
        if not verbose:
            print(".", end="")
        return new_motif
    except:
        return None

def make_new_motifs(count=1, fileout=None, wipe=False, verbose=False):
    old_motifs = sample(all_motifs, count)
    new_motifs = list(mutate(m, verbose) for m in old_motifs)

    # remove bad motifs:
    for i,m in enumerate(new_motifs):
        if m is None:
            old_motifs[i] = None
    old_motifs = list(filter(None, old_motifs))
    new_motifs = list(filter(None, new_motifs))

    transforms = list("'%s' \n\t=> '%s'" % (old_motifs[i], n) for i,n in enumerate(new_motifs) if n)
    if verbose:
        for t in transforms:
            print(t)

    if fileout:
        with open(fileout, 'w' if wipe else 'a') as f:
            print("\n".join(new_motifs), file=f)

    return new_motifs

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Mutate lines using SpaCy")
    parser.add_argument("-o", "--outfile", type=str, default="new_motifs.txt",
            help="append to given file")
    parser.add_argument("-i", "--infile", type=str, default="motifs.txt",
            help="readlines from given file")
    parser.add_argument("-c", "--count", type=int, default=1,
            help="generate this many mutated motifs")
    parser.add_argument("-v", "--verbose", action="store_true",
            help="verbose stdout printing")
    parser.add_argument("-w", "--wipe", action="store_true",
            help="wipe out contents of outfile instead of appending")
    args = parser.parse_args()

    if args.verbose:
        print("Mutating %s motifs from %s and writing out to %s" % (args.count, args.infile, args.outfile))
    else:
        print("Mutating %s motifs..." % args.count)

    all_motifs = populate_motifs(args.infile)

    print("Loading spacy parser...")
    nlp = init_nlp(entity=False,matcher=False,serializer=False)

    print("Making motifs:")
    make_new_motifs(args.count, args.outfile, args.wipe, args.verbose)